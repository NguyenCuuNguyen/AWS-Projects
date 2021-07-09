import requests
import json

URL ="https://d3gsnj71eleazo.cloudfront.net/test/iris_alexa_webpage"
headers={"authorizationToken":"allow", "x-api-key":"a5TrJVohq38lWiueQNb186gAuvKl6pLt7UpGaNBU"}
response = requests.get(URL, headers=headers)

body={
	"user": "iris",
	"pass": "%ByTheWay"
}
response2 = requests.request("POST", URL, headers=headers, data=body) #autoformat into a json

print(response.status_code)
print(response.text)

print(response.status_code)
print(response2.text)
