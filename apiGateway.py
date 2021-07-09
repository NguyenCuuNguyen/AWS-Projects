import requests

headers={"authorizationToken":"allow", "x-api-key":"ROpXuNgwQx3ItpH5QXvIg2Pq9lI6I9bT9YW3Vor6", "isid":"ummaneni"} #authorization token, add #header: Unauthorized => Forbidden


response = requests.get("https://d058vyzce4.execute-api.us-east-1.amazonaws.com/test/assignments?Market=United%20States&Department=HH%20IT&Ready_to_Train=True", headers=headers)

#API key puts another limitation on our request

#Internal server error = ISE = Lambda function doesn't exist.


body={
	"unique_id": "2_german.pdf",
	"Market": "United States",
	"Updated_tags": {
	"content_pillar": "value1",
	"cta_category": "value2"
}
}


response2 = requests.post("https://d058vyzce4.execute-api.us-east-1.amazonaws.com/test/feedback", json=body, headers=headers) #autoformat into a json

print(response.json())
print(response2.json())
