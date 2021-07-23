# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 17:04:39 2020

@author: wilkincr
"""
import os
import sys
import time
import json
import math
import query
import requests
import botocore
import subprocess
import pandas as pd
import base64 as b64
import gc
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from elasticsearch import Elasticsearch, RequestsHttpConnection,helpers
from botocore.client import Config
import PyPDF2
import shutil

threshold=100*1024                #100 MB threshold otherwise raise warning or error
logToDB = True

config = Config(connect_timeout=5, retries={'max_attempts': 0})
#db = boto3.client('dynamodb', config=config)

reverseMap = {'Primary Brand': 'PrimaryBrand', 'Professional / Consumer': 'ProfessionalConsumer', 'Secondary Brand': 'SecondaryBrands', 'Date Submitted': 'DateSubmitted', 'Label Review No. (Biologics)': 'LabelingReviewNo', 'Application Type': 'ApplicationType', 'FDA Material Code': 'FDAMaterialCode', 'Dissemination/Publication Date': 'DisseminationPublicationDate', 'Previous Review No. (if applicable) / date (PLA Submission Comments)': 'PreviousReviewNo', "Applicant's Material ID Code and/or Description": 'CurrentPackage', 'Reg Comments to FDA': 'RegCommentsToFDA', 'Responsible Official': 'ResponsibleOfficial', 'APLB Final': 'AplbFinalType', 'PI': 'PI'}
reverseMonthMap = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

dataMappings = json.load(open("dataMappings2.json", "r"))

class Error(Exception):
    """Base class for other exceptions"""
    pass

class DiskSpaceRunOutError(Error):
    #send an email
    message="""Warning! Disk Space is running out"""
    def __init__(self, message=message):
        self.message = message
        super().__init__(self.message)
    pass

class NoSuchPrefix(Error):
    #send an email
    message="""no such folder/prefix in S3"""
    def __init__(self, message=message):
        self.message = message
        super().__init__(self.message)
    pass

def funcTime(func):
    def timed(*args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()
        print(f"{func.__name__} | {round(end-start,2)} secs")
        return result
    return timed

def index_builder(elasticSearchUrl, indexDetails, awsauth):
    print("creating an index:", elasticSearchUrl)
    if indexDetails["type"] != "logging":
         body = {
             "settings": {
                  "index": {
                       "number_of_shards": indexDetails["shards"],  
                       "number_of_replicas": indexDetails["replicas"],
                       "max_result_window" : indexDetails["maxSearch"]
                  },
                  "analysis": {
                          "analyzer": {
                                  "lowercasespaceanalyzer": {
                                          "type": "custom",
                                          "tokenizer": "whitespace",
                                          "filter": [
                                                  "lowercase"
                                                  ]
                                          }
                                  }
                           }
               }
           }
    else:
         body = {
           "mappings": {
                   "properties": {
                           "logTime": {
                                   "type": "date",
                                   "format": "yyyy-MM-dd HH:mm:ss.SSSSSS"
                                   }
                           }
                   }
           }
    resp = requests.put(elasticSearchUrl + "/" + indexDetails["indexName"], json=body, auth=awsauth)
    print(resp, resp.text)
    if indexDetails["type"] != "logging":
        resp = requests.put(elasticSearchUrl + "/" + indexDetails["indexName"] + "/_mapping", json=dataMappings, auth=awsauth)
    print(resp, resp.text)
    return resp.text

#log just count and utc time of the request in elasticsearch doc
def logMetrics(elasticSearchUrl, metric, awsauth, event, s3=None):
    respVal = requests.get(elasticSearchUrl + "/_count", json={"query": {"match_all": {}}},  auth=awsauth)              
    if "200" in str(respVal):
        count = json.loads(respVal.text)["count"]
        print("Current log count:", count)
        if "Records" in event:
            fileName = event["Records"][0]['s3']["object"]["key"]
            s3.download_file(event["Records"][0]['s3']["bucket"]["name"], fileName, "/tmp/" + fileName.split("/")[-1])
            users = pd.read_csv("/tmp/" + fileName.split("/")[-1])
            uCount = 0
            for index, row in users.iterrows():
                ymd = row["UserLastModifiedDate"].split(" ")[0]
                ymd2 = fileName.split("_")[2].split("-")[0] + "-" + fileName.split("_")[0].split("report")[1] + "-" + str(int(fileName.split("_")[1])-1).zfill(2)
#                print(ymd, ymd2)
                if ymd == ymd2:
                    metricVal = {"requestType": metric,
                                 "logTime": str(pd.to_datetime(row["UserLastModifiedDate"])).split("+")[0],
                                 "isid": row["Username"]}
                    resp = requests.put(elasticSearchUrl + "/_doc/" + str(count + 1), json=metricVal, auth=awsauth)
                    print("Response from logging metrics:", resp, resp.text)
                    checkResp = requests.get(elasticSearchUrl + "/_doc/" + str(count + 1), auth=awsauth)
                    if "200" in str(checkResp):
                        count += 1
                        uCount += 1
                    else:
                        print("error adding user metric")
                        print(checkResp, checkResp.text)
            return "Added " + str(uCount) + " user logins for the day"
        else:
            metricVal = {"requestType": metric,
                         "logTime": str(datetime.utcnow()),
                         "isid": event["Username"]}
            resp = requests.put(elasticSearchUrl + "/_doc/" + str(count + 1), json=metricVal, auth=awsauth)
            print("Response from logging metrics:", resp, resp.text)
            checkResp = requests.get(elasticSearchUrl + "/_doc/" + str(count + 1), auth=awsauth)
            print(checkResp, checkResp.text)
            return resp.text
    else:
        print(respVal, respVal.text)
        return respVal.text

@funcTime
def spaceChecker():
    gc.collect()
    detail="--------EXAMINING REMAINING FILE SYSTEM SPACE--------\n"
    out = subprocess.Popen(["df","-k"], stdout=subprocess.PIPE)
    for line in out.stdout:
        splitline = line.decode().split()
        detail+=str(line)[2:-3]+"\n"
        if splitline[5] == "/tmp":
            disk_space=int(splitline[3])
    detail+=f"Total free disk space is {disk_space} KB\n"
    detail+="-----------------------------------------------------\n"
    try:
        if disk_space<=threshold:
            raise DiskSpaceRunOutError
        else:
            detail+="Disk Space is healthy"
    except DiskSpaceRunOutError as e:
        print(str(e))
    space={"disk_space":disk_space,"detail":detail}
    mem_free=None
    out = subprocess.Popen(["cat","/proc/meminfo"], stdout=subprocess.PIPE)
    for line in out.stdout:
        splitline=line.decode().split()
        if splitline[0] == "MemFree:":
            mem_free=int(splitline[1]) 
            break
    print(f"free mem: {mem_free} KB\n")
    
    space["mem_free"]=mem_free
    gc.collect()
    return space

@funcTime
def list_s3_objects(s3, data_prefix, bucket_name):
    folder_dict = {}
    count = len(data_prefix.split("/"))
#    print("listing s3 objects")
    kwargs = {"Bucket": bucket_name, "Prefix": data_prefix,"MaxKeys":10}
    while True:
        try:
            response = s3.list_objects_v2(**kwargs)
        except botocore.exceptions.ClientError as e:
            print("ERROR in bucketname\n"+str(e))
            return
        try:
            if response["KeyCount"]>0:
                for obj in response["Contents"]:
                    if ".csv" in str(obj["Key"]):
#                        print(obj["Key"])
                        tmp_array = obj["Key"].split('/')
                        if len(tmp_array) == count:
                            if tmp_array[count-2] not in folder_dict:
                                folder_dict[tmp_array[count-2]] = []
                            if tmp_array[count-1] != "":
                                object={"fileName":tmp_array[count-1],"fileSize":obj["Size"]}
                                folder_dict[tmp_array[count-2]].append(object)
                        else:
                            print("Path not added to S3 list")
                            print(tmp_array, count)
                try:
                    kwargs["ContinuationToken"] = response["NextContinuationToken"]
                except KeyError:
                    #NextContinuationToken not found
                    break
            else:
                raise NoSuchPrefix
                break
        except NoSuchPrefix as e:
            print("ERROR!" +data_prefix +str(e))
            return
    return folder_dict

@funcTime
def readEncode(name,encode=False):
    #res=readEncode("cogsley_sales.csv")
    if os.path.isfile(name):
        if not encode:
            df= pd.read_csv(name)
            return df
        else:
            file = open(name, "rb")
            fileVal = b64.b64encode(file.read()).decode('utf-8')
            file.close()
            return fileVal
    else:
        print(f"{name}: file not found")
        return None

@funcTime
def s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,file,read=False,encode=False):
    #res=s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,file,read=False,encode=False)        -->headObject fileSize only
    #res=s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,file,read=True,encode=False)        -->read as pd.DataFrame
    #res=s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,file,read=True,encode=True)        -->read as b64 decoded str
    if file == "N/A":
        return None
    elif file.startswith("/"):
        file = file.split("/",1)[1]

    if data_prefix.startswith("/"):
        data_start = data_prefix.split("/", 1)[1]
    else:
        data_start = data_prefix
        
    if data_start != "" and not file.startswith(data_start):
        data_path = data_start + "/" + file
    else:
        data_path = file

    if len(data_path.split(".")) > 2:
        print("Multiple file extensions found:", data_path)
        data_path = data_path.rsplit(".", 1)[0] 
#    print(data_path)
    tmpfile= '/tmp/' + ''.join(data_path.split("/"))
    if os.path.isfile(tmpfile):
        os.remove(tmpfile)
    try:
        meta = s3.head_object(Bucket=bucket_name,Key=data_path)
        res = round(meta['ContentLength']/1024, 2)
        if read and not data_path.endswith(".mp4"):
            s3.download_file(bucket_name,data_path,tmpfile)
            #print(f"{tmpfile} downloaded")
            res=tmpfile
            if encode:
                res=readEncode(tmpfile,encode=True)         #res-->b64 decoded str
#                print(f"{tmpfile} read as df")
            else:
                res=readEncode(tmpfile,encode=False)        #res-->pd.DataFrame
#                print(f"{tmpfile} read and b64 decoded")
            os.remove(tmpfile)
        #res-->fileSize in KB float
        return res
    except botocore.exceptions.ClientError as e:
        print(f"There was an error getting the file: {data_path}\n"+str(e))
        return None

@funcTime
def multiThread(func,**kwargs):
    keys=kwargs.keys()
    results={}
    funcName=func.__name__
    if func==s3DownloadReadEncodeSize:
        files=kwargs["file"]
        total=len(files)
        s3=[kwargs["s3"]]*total
        bucket_names=[kwargs["bucket_name"]]*total
        data_prefixes=[kwargs["data_prefix"]]*total
        if "read" in keys:
            if "encode" in keys:
                indexes=list(range(total))
                reads=[kwargs["read"]]*total
                encodes=[kwargs["encode"]]*total
                n=total
                with ThreadPoolExecutor(8) as executor:
                    for index,file,res in zip(indexes,files,executor.map(func,s3,bucket_names,data_prefixes,files,reads,encodes)):
                        results[file]=res
                        if isinstance(res,type(None)):        
                            #-->error in getting file None, otherwise: 00-->fileSize or 10-->pd.DataFrame or 11-->b64 decoded str
                            n=n-1
                            print(f"ERROR! {index} {kwargs['data_prefix']}/{file} not downloaded or read")
        print(f"{n}/{total} files downloaded and read")
        return results
    else:
        print(f"{funcName} not meant for multiThreading")

@funcTime
def checkSize(fileSize,spaceInitial,spaceNow):
    try:
        if spaceInitial["disk_space"]-fileSize<threshold or fileSize>spaceInitial["mem_free"]:
            raise DiskSpaceRunOutError
        else:
            check=spaceNow["disk_space"]-fileSize>threshold and fileSize<spaceNow["mem_free"]
            return check
    except DiskSpaceRunOutError as e:
        print(e)
        return False

@funcTime
def index(s3, data_prefix, bucket_name, elasticSearchUrl, jobList, indexName, awsauth):
    tmpDir = os.listdir("/tmp")
    if len(tmpDir) > 0:
        print("tmp directory still contains object from prior indexing!", tmpDir)
        for tmpObj in tmpDir:
            if not os.path.isdir("/tmp/" + tmpObj):
                os.remove("/tmp/" + tmpObj)
            else:
                shutil.rmtree("/tmp/" + tmpObj)
    host = elasticSearchUrl.split("https://")[1]
    port = 443
    es = Elasticsearch(hosts=[{'host': host, 'port': port}],http_auth=awsauth,use_ssl=True,connection_class=RequestsHttpConnection)
    print("indexing")
    space=spaceChecker()
    print(space["detail"])
    bytesTotal = 0
    maxDescriptionLength = 0
    def downloadListIndex(folderContent,fileFormat="",encode=False,indexBool=False):
        #downloadListIndex(folder,fileFormat=".csv",encode=False)
        spaceInitial=spaceNow=spaceChecker() #KB
        infoDict={}
        if indexBool:
            infoDict["bytesTotal"]=0
        filesList=[]
        objectList=[]
        filesSize=0
        total=len(folderContent)
        for j,object in enumerate(folderContent):
            try:
                objectFileName = object["fileName"]
                objectFileSize = object["fileSize"]
            except KeyError:
#                print("Error finding file name or file size (without source key). Object keys:", object.keys())
                objectFileName = object["_source"]["fileName"]
                objectFileSize = object["_source"]["fileSize"]
            if (fileFormat in objectFileName):
                if data_prefix != "":
                    data_path = data_prefix+"/Jobs/"+folder
                else:
                    data_path = "Jobs/" + folder
                if checkSize(objectFileSize,spaceInitial,spaceNow):
                    filesSize=filesSize+objectFileSize
                    filesList.append(objectFileName)
                    spaceNow["disk_space"]=spaceNow["disk_space"]-objectFileSize
                    spaceNow["mem_free"]=spaceNow["mem_free"]-objectFileSize
                    if indexBool:
                        del objectFileSize,objectFileName # not included in ESJson
                        objectList.append(object)
                    if (j==total-1):
                        if not indexBool:
                            res=multiThread(s3DownloadReadEncodeSize,s3=s3,bucket_name=bucket_name,data_prefix=data_path,file=filesList,read=True,encode=encode)     #-->csv files download and read as df
                            infoDict.update(res)
                            del res
                        else:
                            #then index them immediately then free the memory
                            res=list(multiThread(s3DownloadReadEncodeSize,s3=s3,bucket_name=bucket_name,data_prefix=data_path,file=filesList,read=True,encode=encode).values())     #-->csv files download and read as b64 str
                            for i in range(len(res)):
                                if res[i] == None:
                                    if "pipeline" in objectList[i].keys():
                                        objectList[i].pop("pipeline")
                                else:
                                    objectList[i]["_source"]["data"]=res[i]
                            bytesAmount= sys.getsizeof(str(objectList))        #Bytes
                            infoVals = esParallelBulk(indexName,objectList)
                            if isinstance(infoVals, dict): 
                                infoDict.update(infoVals)
                            else:
                                print(infoVals)
                                print(type(infoVals))
                            infoDict["bytesTotal"]+=bytesAmount
                            del objectList,res
                            gc.collect()
                else:
                    if not indexBool:
                        res=multiThread(s3DownloadReadEncodeSize,s3=s3,bucket_name=bucket_name,data_prefix=data_path,file=filesList,read=True,encode=encode)     #-->csv files download and read as df
                        infoDict.update(res)
                        del res
                    else:
                        #then index them immediately then free the memory
                        res=list(multiThread(s3DownloadReadEncodeSize,s3=s3,bucket_name=bucket_name,data_prefix=data_path,file=filesList,read=True,encode=encode).values())     #-->csv files download and read as b64 str
                        for i in range(len(res)):
                            if res[i] == None:
                                if "pipeline" in objectList[i].keys():
                                    objectList[i].pop("pipeline")
                            else:                           
                                objectList[i]["_source"]["data"]=res[i]
                        bytesAmount= sys.getsizeof(str(objectList))        #Bytes
                        infoVals = esParallelBulk(indexName,objectList)
                        if isinstance(infoVals, dict): 
                            infoDict.update(infoVals)
                        infoDict["bytesTotal"]+=bytesAmount
                        del objectList,res
                        gc.collect()
                        objectList = []
                        res = None
                    filesSize=filesSize+objectFileSize
                    filesList.append(objectFileName)
                    spaceNow["disk_space"]=spaceNow["disk_space"]-objectFileSize
                    spaceNow["mem_free"]=spaceNow["mem_free"]-objectFileSize
                    if indexBool:
                        del objectFileSize,objectFileName # not included in ESJson
                        objectList.append(object)
                        del res
                        gc.collect()
                    if (j==total-1):
                        if not indexBool:
                            res=multiThread(s3DownloadReadEncodeSize,s3=s3,bucket_name=bucket_name,data_prefix=data_path,file=filesList,read=True,encode=encode)     #-->csv files download and read as df
                            infoDict.update(res)
                        else:
                            #then index them immediately then free the memory
                            res=list(multiThread(s3DownloadReadEncodeSize,s3=s3,bucket_name=bucket_name,data_prefix=data_path,file=filesList,read=True,encode=encode).values())     #-->csv files download and read as b64 str
                            for i in range(len(res)):
                                objectList[i]["data"]=res[i]
                            bytes= sys.getsizeof(json.dumps(str(objectList)))
                            infoDict.update(esParallelBulk(indexName,objectList))
                            infoDict["bytesTotal"]+=bytes
                            del objectList, res
                            gc.collect()
        return infoDict

    def esParallelBulk(indexName,actions):
        results={}
        thread_count=8
        fixList = []
        splitActions = [[]]
        actionDel = []
        failed_index = []
        retry_index = []
        res_list = []
        global_n = 0
        def actionIndex(actions, n, failed_index, retry_index, indexes):
            for index,(status, res) in zip(indexes,helpers.parallel_bulk(client=es, index=indexName,thread_count=thread_count, actions=actions,chunk_size=chunk_size,max_chunk_bytes=1*1024*1024*1024,request_timeout=3*60,raise_on_error=True,raise_on_exception =True,)):
                if not status:
                    n=n-1
                    results[index]={"status":status,"error":res}
                    print(str(index) + ": " + str(actions[index]))
                    print(f"ERROR! {index} could not be indexed")
                    print(res['index']['status'], res['index']['error'])
                    if res['index']['status'] == 413:
                        failed_index.append(index)
                        print("Transport Error!")
                    elif res['index']['status'] == 400:
                        print("Parsing Error! Attempting to extract text locally.")
                        file = open("/tmp/" + str(actions[index]["_source"]["JobId"]) + ".pdf", "wb")
                        file.write(b64.b64decode(actions[index]["_source"]["data"].encode('utf-8')))
                        file.close()
                        actions[index]["_source"].pop("data")
                        actions[index]["_source"]["attachment"] = {"content": ""}
                        pdfReader = PyPDF2.PdfFileReader(open("/tmp/" + str(actions[index]["_source"]["JobId"]) + ".pdf", "rb"))
                        for j in range(pdfReader.numPages):
                            pageObject = pdfReader.getPage(j)
                            try:
                                actions[index]["_source"]["attachment"]["content"] += pageObject.extractText()
                            except Exception as e:
                                print("Error finding page contents", j)
                                print(e)
                        actions[index].pop("pipeline")
                        retry_index.append(actions[index])
                else:
                    results[index]={"status":status,"id":res['index']['_id']}
                    if actions[index]["_source"]["fileType"] == "Job":
                        print("Successful Indexing of JobId: " + str(actions[index]["_source"]["JobId"]))
                    print(f"index: {index} {res['index']['_id']} is succesfully indexed")
            return n, failed_index, results, retry_index
        if sys.getsizeof(json.dumps(str(actions))) > 104857600:
            for i in range(len(actions)):
                action = actions[i]
                print("Current object size is:", sys.getsizeof(json.dumps(str(actions))))
                print("Maximum object size is:", 104857600)
                if sys.getsizeof(json.dumps(str(action))) > 104857600:
                    print("Object is too large!")
                    extraPageJSON = {}
                    for key in action:
                        if key != "_source":
                            extraPageJSON[key] = action[key]
                        else:
                            extraPageJSON["_source"] = {"data": "", "fileType": "extraPage", "JobId": action[key]["JobId"]}
                    if "data" in action["_source"]:
                        proposedSize = sys.getsizeof(json.dumps(str(action["_source"]["data"]))) + sys.getsizeof(json.dumps(extraPageJSON))
                        print("Minimized object size:", proposedSize)
                        print("Maximum object size is:", 104857600)
                        if proposedSize > 104857600:
                            print("Minimized object is too large. Breaking up pages for JobId:", action["_source"]["JobId"])
                            file = open("/tmp/" + str(action["_source"]["JobId"]) + ".pdf", "wb")
                            file.write(b64.b64decode(action["_source"]["data"].encode('utf-8')))
                            file.close()
                            action["_source"].pop("data")
                            pdfReader = PyPDF2.PdfFileReader(open("/tmp/" + str(action["_source"]["JobId"]) + ".pdf", "rb"))
                            print("Number of pages found:", pdfReader.numPages)
                            if pdfReader.numPages == 1:
                                print("Error! Could not split PDF")
                                print("Pulling out the text locally")
                                action["_source"]["attachment"] = {"content": ""}
                                for j in range(pdfReader.numPages):
                                    pageObject = pdfReader.getPage(j)
                                    try:
                                        action["_source"]["attachment"]["content"] += pageObject.extractText()
                                    except Exception as e:
                                        print("Error finding page contents", j)
                                        print(e)
                                del pdfReader
                                os.remove("/tmp/" + str(action["_source"]["JobId"]) + ".pdf")
                                action.pop("pipeline")
                            else:
                                for j in range(pdfReader.numPages):
                                    print("adding page", j)
                                    pFile = open("/tmp/" + str(action["_source"]["JobId"]) + "page_" + str(j) + ".pdf", "wb")
                                    output = PyPDF2.PdfFileWriter()
                                    try:
                                        output.addPage(pdfReader.getPage(j))
                                    except Exception:
                                        print("No Page Contents found for page", j)
                                    output.write(pFile)
                                    pFile.close()
                                    del output
                                    pFile = open("/tmp/" + str(action["_source"]["JobId"]) + "page_" + str(j) + ".pdf", "rb")
                                    extraPageJSON = {}
                                    for key in action:
                                        if key != "_source":
                                            extraPageJSON[key] = action[key]
                                        else:       
                                            if j == 0:
                                                actionDel.append(i)
                                                extraPageJSON[key] = action[key]
                                                extraPageJSON[key]["data"] = b64.b64encode(pFile.read()).decode('utf-8')
                                            else:
                                                extraPageJSON[key] = {"JobId": action["_source"]["JobId"], 
                                                                      "fileType": "extraPage",
                                                                      "data": b64.b64encode(pFile.read()).decode('utf-8')}
                                    if sys.getsizeof(json.dumps(extraPageJSON)) > 104857600:
                                        print("Page object too large! Pulling out the text locally")
                                        extraPageJSON["_source"]["attachment"] = {"content": ""}
                                        extraPageJSON["_source"].pop("data")
                                        extraPageJSON.pop("pipeline")
                                        try:
                                            extraPageJSON["_source"]["attachment"]["content"] += pdfReader.getPage(j).extractText()
                                        except Exception:
                                            print("No Page Contents found for page", j)
                                        if sys.getsizeof(json.dumps(extraPageJSON)) > 104857600:
                                            print("Page too large. Splitting raw text")
                                            tempContent = extraPageJSON["_source"]["attachment"]["content"]
                                            for letter in tempContent:
                                                extraPageJSON["_source"]["attachment"]["content"] = ""
                                                if sys.getsizeof(json.dumps(extraPageJSON)) < 104857600:
                                                    extraPageJSON["_source"]["attachment"]["content"] += letter
                                                else:
                                                    tempLetters = ""
                                                    while extraPageJSON["_source"]["attachment"]["content"][-1] != " ":
                                                        tempLetters = extraPageJSON["_source"]["attachment"]["content"][-1] + tempLetters
                                                        extraPageJSON["_source"]["attachment"]["content"] = extraPageJSON["_source"]["attachment"]["content"].rsplit(extraPageJSON["_source"]["attachment"]["content"][-1], 1)[0]
                                                    print(sys.getsizeof(json.dumps(extraPageJSON)))
                                                    fixList.append(extraPageJSON)
                                                    extraPageJSON["_source"]["attachment"]["content"] = tempLetters
                                            del tempContent
    ########### SPLIT THE FULL TEXT EXTRACT ###############
                                    fixList.append(extraPageJSON)
                                    pFile.close()
                                    os.remove("/tmp/" + str(action["_source"]["JobId"]) + "page_" + str(j) + ".pdf")
                                    del pFile
                                    space=spaceChecker()
                                    print(space)
                                    if space["disk_space"] < 1000 or space["mem_free"] < 1800000:
                                        total = len(fixList)
                                        for i in range(total):
                                            indexes=[0]
                                            chunk_size=-(-1//thread_count)        #chunk size is an ceiling integer
                                            n2, failed_index, results, retry_index = actionIndex([fixList[0]], 1, failed_index, retry_index, indexes)
                                            res_list.extend(results)
                                            global_n -= (total-n2)
                                            del fixList[0]
                                            gc.collect()
                                    if len(retry_index) > 0:
                                        total=len(retry_index)
                                        indexes=list(range(total))
                                        chunk_size=-(-len(retry_index)//thread_count)        #chunk size is an ceiling integer
                                        n2, failed_index, results, retry_index2 = actionIndex(retry_index, total, failed_index, [], indexes)
                                        res_list.extend(results)
                                        global_n -= (total-n2)
                                        space=spaceChecker()
                                        if space["disk_space"] < 1000 or space["mem_free"] < 1800000:
                                            del retry_index
                                            gc.collect()

                                print("Extra page list length:", len(fixList))
                                del pdfReader
                                os.remove("/tmp/" + str(action["_source"]["JobId"]) + ".pdf")
                        else:
                            extraPageJSON["_source"]["data"] = action["_source"]["data"]
                            action.pop("pipeline")
                            action["_source"].pop("data")
                            fixList.append(extraPageJSON)
                    else:
                        print("Data too large and no data field found!")
                        print("fileType:", action["_source"]["fileType"])
            for val in actionDel:
                actions.pop(val)
            print("actions before fixList", len(actions))
            actions.extend(fixList)
            print("actions after fixList", len(actions))
        actionLength = len(actions)
        aLength = 0
        print("splitting actions apart for smaller indexing")
        while aLength < actionLength:
            actionSize = sys.getsizeof(json.dumps(str(splitActions[-1]))) + sys.getsizeof(json.dumps(str(actions[0]))) 
            if actionSize > 104857600:
                print("Appending to current actionSize:", sys.getsizeof(json.dumps(str(splitActions[-1]))))
                splitActions.append([])
            splitActions[-1].append(actions.pop(0))
            print("current actionSize:", sys.getsizeof(json.dumps(str(splitActions[-1]))))
            aLength += 1
        del actions
        print("Total calls to make:", len(splitActions))
        print("splitActions :", splitActions)
        global_n = 0
        for val in splitActions:
            print(sys.getsizeof(json.dumps(str(val))), 104857600)
            global_n += len(val)

        it = 0
        while it < len(splitActions):
            total=len(splitActions[it])
            indexes=list(range(total))
            chunk_size=-(-len(splitActions[it])//thread_count)        #chunk size is an ceiling integer
            n2, failed_index, results, retry_index = actionIndex(splitActions[it], 1, failed_index, retry_index, indexes)
            res_list.extend(results)
            global_n -= (total-n2)
            space=spaceChecker()
            if space["disk_space"] < 1000 or space["mem_free"] < 1800000:
                del splitActions[it]
                gc.collect()
            else:
                it += 1
        if len(retry_index) > 0:
            total=len(retry_index)
            indexes=list(range(total))
            chunk_size=-(-len(retry_index)//thread_count)        #chunk size is an ceiling integer
            n2, failed_index, results, retry_index2 = actionIndex(retry_index, total, failed_index, [], indexes)
            res_list.extend(results)
            global_n -= (total-n2)
            space=spaceChecker()
            if space["disk_space"] < 1000 or space["mem_free"] < 1800000:
                del retry_index
                gc.collect()
        return res_list

    i=0
    jobRelationships=s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,'JobRelationships.csv',read=True,encode=False)
    references=s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,'References.csv',read=True,encode=False)
    referenceCreationDate = s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,'Organon Modified/organon_reference_creation_dates.csv',read=True,encode=False)
    FDAvalues = s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,'Organon Modified/organon_2253_global_product_names.csv',read=True,encode=False)
    UploaderComments = s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,'Organon Modified/organon_uploader_comments.csv',read=True,encode=False)
    Products = s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,'Config/Products.csv',read=True,encode=False)

    
    folderDict = {}
    jobDataDict = {}
    
    def dataFiller(jobDataRaw, duplicateObjectLogger, createdJobCount, jobData):
        for jD in jobDataRaw:
            addNL = True
            if jD["_source"]["fileType"] == "Job":
                createdJobCount += 1

            for nL in jobData:
                if len(jobData) > 0:
                    if (nL["_source"]["fileType"] == "Job") and (jD["_source"]["fileType"] == "Job"):
                        print("Duplicate Job Found")
                        addNL = False
                        if jD not in duplicateObjectLogger:
                            duplicateObjectLogger.append(jD)
                    elif nL["_source"] == jD["_source"]:
                        addNL = False
                        if jD not in duplicateObjectLogger:
                            duplicateObjectLogger.append(jD)
                    elif jD["_source"]["fileType"] == "ReferenceLinks":
                        addNL = False
                        if jD not in duplicateObjectLogger:
                            duplicateObjectLogger.append(jD)                        
            if addNL:
                jobData.append(jD)
        return duplicateObjectLogger, jobData, createdJobCount

    def valueChecker(valueName, ESJson, jobDataDict):
        addVal = True
        for jD in jobDataDict[ESJson["_source"]["JobId"]]["jobData"]:
            if ESJson["_source"] == jD["_source"]:
                print(valueName + " already in elasticsearch!")
                addVal = False
            elif jD["_source"]["fileType"] == "Job" and ESJson["_source"]["fileType"] == "Job":
                addVal = False                
        if addVal:
            print(valueName + " not in elasticsearch!")
        return addVal

    chunkSize = int(os.environ["resultsChunks"])    
    for job in jobList:
        requestBody = {"query": {"JobId": job}}
        response = query.search(requestBody, elasticSearchUrl + "/" + indexName + "/_search/", awsauth)
        jobDataRaw = response["results"]
        createdJobCount = 0
        deletedJobCount = 0
        duplicateObjectLogger = []
        jobData = []
        duplicateObjectLogger, jobData, createdJobCount = dataFiller(jobDataRaw, duplicateObjectLogger, createdJobCount, jobData)
        print(math.ceil((response["searchCount"] - chunkSize)/100))
        if math.ceil((response["searchCount"] - chunkSize)/100) > 0:
            for j in range(0, math.ceil((response["searchCount"] - chunkSize)/100)):
                resp = query.search(requestBody, elasticSearchUrl + "/" + indexName + "/_search/", awsauth, page=j + 2)
                response2 = resp
                jobDataRaw = response2["results"]
                duplicateObjectLogger, jobData, createdJobCount = dataFiller(jobDataRaw, duplicateObjectLogger, createdJobCount, jobData)
        if duplicateObjectLogger != []:
            print("Found " + str(len(duplicateObjectLogger)) + " duplicate files!")
            for deleteVal in duplicateObjectLogger:
                headers={"Content-type": "application/json"}
                print("Deleting", deleteVal["_id"], "FileType", deleteVal["_source"]["fileType"])
                if deleteVal["_source"]["fileType"] == "Job":
                    deletedJobCount += 1
                resp = requests.delete(elasticSearchUrl + "/" + indexName + "/_doc/" + deleteVal["_id"], headers=headers, auth=awsauth)
                print(resp)
        if createdJobCount == 0:
            print("No Job Record Found for Id: " + str(job))
        elif createdJobCount == 1:
            print("A Job Record Was Found for Id: " + str(job))
        else:
            print("Duplicate Jobs Found for Id: " + str(job) + " Found " + str(createdJobCount) + " Deleted " + str(deletedJobCount))

        if data_prefix != "":
            data_path = data_prefix + "/Jobs/" + str(job) + "/"
        else:
            data_path = "Jobs/" + str(job) + "/"
        folderDict.update(list_s3_objects(s3, data_path, bucket_name))
        jobDataDict[job] = {"jobData": jobData}
        #print(folderDict)

    print(f"listed {len(folderDict)} jobs")
    for folder in folderDict:
        infoDict=downloadListIndex(folderDict[folder],fileFormat=".csv",encode=False,indexBool=False)
        bulkJobs=[]
        bulkNonJobs=[]
        print("CSV Files Found:", infoDict.keys())
        for key in infoDict.keys():
            #print(key, len(infoDict[key]), infoDict[key])
            rawKey = key.split(".csv")[0]
            if rawKey not in ["JobRelationships", "FieldLabels"]:
                keys = infoDict[key].keys()
                for index, row in infoDict[key].iterrows():
                    ESJson = {"_source": {}}
                    ESJson["_index"] = indexName   #environ
                    ESJson["_source"]["fileType"] = rawKey
                    for rowKey in keys:
                        if "Unnamed" not in rowKey:
                            if str(row[rowKey]) in ["nan", "NaN"]:
                                ESJson["_source"][rowKey] = None
                            else:
                                ESJson["_source"][rowKey] = row[rowKey]
#                                if rowKey == "Quantity":
#                                    try:
#                                        ESJson["_source"][rowKey] = int(ESJson["_source"][rowKey])
#                                    except ValueError:
#                                        print(ESJson["_source"][rowKey])
#                                        try:
#                                            ESJson["_source"][rowKey] = int(ESJson["_source"][rowKey].replace(",", ""))
#                                        except ValueError:       
#                                            ESJson["_source"][rowKey] = None       
#                                if rowKey == "PRTMeetingAllocatedTime":
#                                    try:
#                                        ESJson["_source"][rowKey] = int(ESJson["_source"][rowKey])
#                                    except ValueError:
#                                        print(ESJson["_source"][rowKey])
#                                        try:
#                                            if "min" in ESJson["_source"][rowKey]:
#                                                ESJson["_source"][rowKey] = int(ESJson["_source"][rowKey].replace("min", "").split(" ")[0])
#                                            elif "hour" in ESJson["_source"][rowKey]:
#                                                ESJson["_source"][rowKey] = int(ESJson["_source"][rowKey].replace("hour", "").split(" ")[0])*60
#                                            elif "day" in ESJson["_source"][rowKey]:
#                                                ESJson["_source"][rowKey] = int(ESJson["_source"][rowKey].replace("day", "").split(" ")[0])*60*24
#                                            else:
#                                                ESJson["_source"][rowKey] = None       
#                                        except ValueError:       
#                                            ESJson["_source"][rowKey] = None                                                          
                    if rawKey == "Job" and createdJobCount != 1:
                        print("Working on JobId:" + str(ESJson["_source"]["JobId"]))
                        #print("FDAvalues",FDAvalues)
                        #print("ESJson",ESJson)
                        
                        FDATypeMatch = FDAvalues[FDAvalues["JobId"] == ESJson["_source"]["JobId"]].reset_index()
                        #print("FDATypeMatch",FDATypeMatch)
                        if len(FDATypeMatch) != 0:
                            for val in FDATypeMatch:
                                #print(val)
                                if val not in ["JobId", "index"]:
#                                    print(val, reverseMap[val], reverseMap[val] in ESJson["_source"])
                                    if (reverseMap[val] not in ESJson["_source"]) or (str(ESJson["_source"][reverseMap[val]]) in ["nan", "NaN", "", "None"]):
                                        if (str(FDATypeMatch[val][0]) in ["nan", "NaN"]):
                                            ESJson["_source"][reverseMap[val]] = None
                                        else:
                                            ESJson["_source"][reverseMap[val]] = FDATypeMatch[val][0]
                                            for m in reverseMonthMap:
                                                if m in ESJson["_source"][reverseMap[val]]:
                                                    ESJson["_source"][reverseMap[val]].replace(m, reverseMonthMap[m])
                        else:
                            for val in FDAvalues:
                                #print(val)
                                if val not in ["JobId", "index"]:
                                    if (reverseMap[val] not in ESJson["_source"]) or (str(ESJson["_source"][reverseMap[val]]) in ["nan", "NaN", "", "None"]):
                                        ESJson["_source"][reverseMap[val]] = None                        
                        UploaderMatch = UploaderComments[UploaderComments["JobId"] == ESJson["_source"]["JobId"]].reset_index()
                        UploaderMatch = pd.DataFrame(UploaderMatch, columns=["JobId", "Circulation", "Uploader Comment"])
                        if len(UploaderMatch) != 0:
                            ESJson["_source"]["UploaderComments"] = {}
                            for val in UploaderMatch:
                                ESJson["_source"]["UploaderComments"][val] = []
                                if val not in ["JobId", "index"]:
                                    for uplIt in range(len(UploaderMatch[val])):
                                        if (str(UploaderMatch[val][uplIt]) in ["nan", "NaN"]):
                                            ESJson["_source"]["UploaderComments"][val].append(None)
                                        else:
                                            ESJson["_source"]["UploaderComments"][val].append(UploaderMatch[val][uplIt])

                        ProductMatch = Products[Products["Name"] == ESJson["_source"]["Product"]].reset_index()
                        ProductMatch = pd.DataFrame(ProductMatch, columns=["Name", "EstablishedName", "ProprietaryName", "NdaNumber", "ManufacturerName", "FdaApplicationCode"])
                        if len(ProductMatch) != 0:
                            print("matched on " + str(len(ProductMatch)) + " products!" )
                            for val in ProductMatch:
                                if val not in ["Name", "index"]:
                                    if str(ProductMatch[val][0]) in ["nan", "NaN"]:
                                        if val != "FdaApplicationCode":
                                            ESJson["_source"][val] = None
                                    else:
                                        if ESJson["_source"]['ApplicationType'] == None and val == "FdaApplicationCode":
                                            ESJson["_source"]['ApplicationType'] = ProductMatch[val][0]        
                                        else:
                                            ESJson["_source"][val] = ProductMatch[val][0]

                        if isinstance(infoDict[key]["Objective"][0], str):
                            if maxDescriptionLength < len(infoDict[key]["Objective"][0]):
                                maxDescriptionLength = len(infoDict[key]["Objective"][0])
                        if isinstance(infoDict[key]["FinalArtwork"][0], str) and (infoDict[key]["FinalArtwork"][0] != "No file"):
                            try:
                                finalArt = infoDict[key]["FinalArtwork"][0].replace("\\", "/")
                                fileSize = s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,finalArt,read=False,encode=False)
                                if not finalArt.endswith(".mp4"):
                                    ESJson["pipeline"]="attachment"
                                ESJson["_source"]["fileName"] = finalArt
                                ESJson["_source"]["fileSize"] = fileSize
                            except botocore.exceptions.ClientError as e:
                                print("There was an error getting the final artwork file: " + str(infoDict[key]["FinalArtwork"][0]) +" " + str(e))
                        else:
                            print("The file's final artwork link doesn't appear to be available: " + str(infoDict[key]["FinalArtwork"][0]))
                            ESJson["_source"]["fileName"] = "N/A"
                            ESJson["_source"]["fileSize"]= 0                            
                        ESJson["_source"]["parents"] = []
                        ESJson["_source"]["children"] = []
                        ESJson["_source"]["linkedJobs"] = []
                        ESJson["_source"]["predecessors"] = []
                        ESJson["_source"]["successors"] = []
                        ESJson["_source"]["reapprovals"] = []

                        if "JobRelationships.csv" in infoDict.keys():
                            print("Job Relationships exist")
                            for index, row in jobRelationships[(jobRelationships.JobId == ESJson["_source"]["JobId"]) | (jobRelationships.RelatedJobId == ESJson["_source"]["JobId"])].iterrows():
                                print("Matched Job Relationship to JobId", row)
                                if str(row["Reason"]) in ["nan", "NaN"]:
                                    row["Reason"] = None
                                if str(row["Creator"]) in ["nan", "NaN"]:
                                    row["Creator"] = None
                                if row["RelationshipType"] == "ParentChild":
                                    if row["RelatedJobId"] == infoDict[key]["JobId"][0]:
                                        ESJson["_source"]["parents"].append({"JobId": row["JobId"], "Reason": row["Reason"], "Creator": row["Creator"]})
                                    elif row["JobId"] == infoDict[key]["JobId"][0]:
                                        ESJson["_source"]["children"].append({"JobId": row["RelatedJobId"], "Reason": row["Reason"], "Creator": row["Creator"]})
                                elif row["RelationshipType"] == "Linked":
                                    if row["RelatedJobId"] == infoDict[key]["JobId"][0]:
                                        ESJson["_source"]["linkedJobs"].append({"JobId": row["JobId"], "Reason": row["Reason"], "Creator": row["Creator"]})
                                    elif row["JobId"] == infoDict[key]["JobId"][0]:
                                        ESJson["_source"]["linkedJobs"].append({"JobId": row["RelatedJobId"], "Reason": row["Reason"], "Creator": row["Creator"]})
                                elif row["RelationshipType"] == "PredecessorSuccessor":
                                    if row["RelatedJobId"] == infoDict[key]["JobId"][0]:
                                        ESJson["_source"]["predecessors"].append({"JobId": row["JobId"], "Reason": row["Reason"], "Creator": row["Creator"]})
                                    elif row["JobId"] == infoDict[key]["JobId"][0]:
                                        ESJson["_source"]["successors"].append({"JobId": row["RelatedJobId"], "Reason": row["Reason"], "Creator": row["Creator"]})
                                elif row["RelationshipType"] == "Reapproval":
                                    if row["RelatedJobId"] == infoDict[key]["JobId"][0]:
                                        ESJson["_source"]["reapprovals"].append({"JobId": row["JobId"], "Reason": row["Reason"], "Creator": row["Creator"]})
                                    elif row["JobId"] == infoDict[key]["JobId"][0]:
                                        ESJson["_source"]["reapprovals"].append({"JobId": row["RelatedJobId"], "Reason": row["Reason"], "Creator": row["Creator"]})
                                else:
                                    print("Relationship for Job ID: " + str(infoDict[key]["JobId"][0]) + "is invalid!\n    Relationship Name: " + str(row["RelationshipType"]))

                        if valueChecker("Job ID", ESJson, jobDataDict):
                            bulkJobs.append(ESJson)
                            for jD in jobDataDict[ESJson["_source"]["JobId"]]["jobData"]:
                                if jD["_source"]["fileType"] == "Job":
                                    print("Job Not Found " + str(ESJson["_source"]["JobId"]))
                                    headers={"Content-type": "application/json"}
                                    resp = requests.delete(elasticSearchUrl + "/" + indexName + "/_doc/" + jD["_id"], headers=headers, auth=awsauth)
                                    print(resp)
                    elif rawKey == "Artworks":
                        #print("ES json : ",ESJson)
                        if isinstance(ESJson["_source"]["ArtworkFileName"], str) and (ESJson["_source"]["ArtworkFileName"] != "No file"):
                            try:
                                artVal = ESJson["_source"]["ArtworkFileName"].replace("\\", "/")
                                #print("ART val : ",artVal)
                                fileSize=s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,artVal,read=False,encode=False)
                                ESJson["_source"]["fileSize"] = fileSize
                                if valueChecker("Artwork", ESJson, jobDataDict):
                                    bulkNonJobs.append(ESJson)
                            except botocore.exceptions.ClientError as e:
                                print("There was an error getting the artwork file: " + ESJson["_source"]["ArtworkFileName"], str(e))
                        else:
                            print("The artwork link doesn't appear to be available: " + str(ESJson["_source"]["ArtworkFileName"]) + " JobId: " + str(ESJson["_source"]["JobId"]))
                            ESJson["_source"]["fileName"] = "N/A"
                            ESJson["_source"]["fileSize"]= 0   
                            if valueChecker("Artwork", ESJson, jobDataDict):
                                bulkNonJobs.append(ESJson)
                    
                    elif rawKey == "GalleryItems":
                        if isinstance(ESJson["_source"]["FileName"], str) and (ESJson["_source"]["FileName"] != "No file"):
                            try:
                                galVal = ESJson["_source"]["FileName"].replace("\\", "/")
                                fileSize=s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,galVal,read=False,encode=False)
                                ESJson["_source"]["fileSize"] = fileSize
                                if valueChecker("Gallery Item", ESJson, jobDataDict):
                                    bulkNonJobs.append(ESJson)
                            except botocore.exceptions.ClientError as e:
                                print("There was an error getting the file: " + ESJson["_source"]["FileName"], str(e))
                        else:
                            print("The gallery item link doesn't appear to be available: " + str(ESJson["_source"]["FileName"]) + " JobId: " + str(ESJson["_source"]["JobId"]))
                            ESJson["_source"]["fileName"] = "N/A"
                            ESJson["_source"]["fileSize"]= 0  
                            if valueChecker("Gallery Item", ESJson, jobDataDict):
                                bulkNonJobs.append(ESJson)
                    
                    elif rawKey == "ReferenceLinks":
                        listHeaders = list(references)
                        rowFound = False
#                        print("Reference IDs", infoDict[key]["ReferenceId"])
#                        print("Before manipulation", ESJson["_source"])
                        for index2, row2 in references[(references.ReferenceId == ESJson["_source"]["ReferenceId"])].iterrows():
                            if not rowFound:
                                for h in listHeaders:
                                    if h not in ESJson["_source"].keys():
                                        if str(row2[h]) in ["nan", "NaN"]:
                                            ESJson["_source"][h] = None
                                        else:
                                            ESJson["_source"][h] = row2[h]
                                    elif h == "FileName":
                                        ESJson["_source"]["FullReferenceFileName"] = row2[h]
                                        ESJson["_source"]["FullReferenceFileSize"]=s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,ESJson["_source"]["FullReferenceFileName"].replace("\\", "/"),read=False,encode=False)
                                rowFound = True
#                                print("found row:", index2)
#                            else:
#                                print("Found duplicate row:", index2)
#                        print("After manipulation", ESJson["_source"])
                            RefMatch = referenceCreationDate[referenceCreationDate["ReferenceId"] == ESJson["_source"]["ReferenceId"]].reset_index()
                            RefMatch = pd.DataFrame(RefMatch, columns=["ReferenceId", "CreationDate", "UserProfile", "PartnerUserProfile"])
                            if len(RefMatch) != 0:
                                for val in RefMatch:
                                    if val not in ["ReferenceId", "index"]:
                                        if (str(RefMatch[val][0]) in ["nan", "NaN"]):
                                            ESJson["_source"][val] = None
                                        else:
                                            ESJson["_source"][val] = RefMatch[val][0]

                            try:                      
                                if isinstance(ESJson["_source"]["FileName"], str) and (ESJson["_source"]["FileName"] != "No file"):
                                    refVal = ESJson["_source"]["FileName"].replace("\\", "/") 
                                    fileSize=s3DownloadReadEncodeSize(s3,bucket_name,data_prefix,refVal,read=False,encode=False)
                                    ESJson["_source"]["fileSize"] = fileSize
                                else:
                                    print("The referenceLink doesn't appear to be available: " + str(ESJson["_source"]["FileName"]))
                                    ESJson["_source"]["fileName"] = "N/A"
                                    ESJson["_source"]["fileSize"]= 0

                                if valueChecker("ReferenceLink", ESJson, jobDataDict):
                                    bulkNonJobs.append(ESJson)
                            except botocore.exceptions.ClientError as e:
                                print("There was an error getting the referenceLink file: " + ESJson["_source"]["FileName"], str(e))


        i+=(len(bulkJobs)+len(bulkNonJobs))
#        print(bulkNonJobs)
        jobDict=downloadListIndex(bulkJobs,fileFormat="",encode=True,indexBool=True)
        if 'status' in jobDict:
            if jobDict['status'] == 413:
                print("Job file is too large to parse!")
            else:
                bytesTotal+=jobDict["bytesTotal"]
            del jobDict,bulkJobs
        nonJobDict=esParallelBulk(indexName,bulkNonJobs)
        if 'status' in nonJobDict:
            if nonJobDict['status'] == False:
                print("error indexing non-jobs")
            else:
                bytesTotal+=sys.getsizeof(str(bulkNonJobs))
            del nonJobDict,bulkNonJobs
    return bytesTotal, i, maxDescriptionLength
        

