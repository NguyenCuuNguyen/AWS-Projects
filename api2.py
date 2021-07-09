import requests
import json

URL ="https://sn83xpfcp4.execute-api.us-east-1.amazonaws.com/test/iris_alexa_webpage"
headers={"x-api-key":"a5TrJVohq38lWiueQNb186gAuvKl6pLt7UpGaNBU", "Content-Type":"application/json"}
response = requests.get(URL, headers=headers)

body={
	"user": "iris",
	"pass": "%ByTheWay"
}
# response2 = requests.request("POST", URL, headers=headers, data=body) #autoformat into a json
response2 = requests.post(URL, json=body, headers=headers)
print(response.status_code)
print(response.text)

print(response.status_code)
print(response2.text)
