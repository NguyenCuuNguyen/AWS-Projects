import boto3
import json
import logging #use logger to traceback error, include aws_request_id for Insight query
import sys
from boto3.dynamodb.conditions import Key, Attr #To add conditions to scanning and querying the table

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('alexa_items_list')

# def check_dynamodb(event):
#     #ProjectionExpression: to get only some, not all attributes 
    
    
def lambda_handler(event, context):
    print("Lambda is triggered")
    reponse = ""
    ProjectionExpression = "id, color, price, item, password"
    print(event)
    matched_id = table.query( #queries for all of the users with matched userID
        KeyConditionExpression=Key("id").eq(event['user']) #& Key('password')
    )
    if not matched_id['Items']:
        print("Login failed, try again!")
    else:
        for i in matched_id['Items']:
            if i['password'] == event['pass']:  #Matched, return all attributes
                response = table.get_item(Key={'id':event["user"]}) 
                print(response)
                print("Found item in database!")
            else:
                print("ID or password does not match. Try again!")
            #update password: #table.put_item(Item={'id':event["user"], 'password': event['pass']})
        
    return {
        "statusCode": 200,
        'body': response,
        "headers": {
            "Access-Control-Allow-Origin" : "*",
            "Access-Control-Allow-Credentials" : True
            
        }
    }
    
 
    # return response
 
