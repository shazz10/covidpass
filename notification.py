import requests
import json

def createSpecificNotification(player_ids, title, message):
	# todo: check for valid format of player ids. Check if all of them are strings. 

	# Do not change this part. 
	header = {"Content-Type": "application/json; charset=utf-8"}

	payload = {"app_id": "a447ef5f-5633-4c56-b2c3-43a9910c7fcf",
	           "include_player_ids": player_ids,
	           "contents": {"en": message},
	           "headings": {"en": title}}
	 
	req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
	#  do not change till here.

	# Todo: modify this print so, that it sends the response to the log, or the somewhere where it can be monitored.
	#print(req.status_code, req.reason)


def createGeneralNotification(title, message):
	header = {"Content-Type": "application/json; charset=utf-8","Authorization": "Basic MDI2OTUzYTgtNTBhMi00MTIyLWE1MjktMTM3M2NhODRkNzll"}

	payload = {"app_id": "a447ef5f-5633-4c56-b2c3-43a9910c7fcf",
	           "included_segments": ["All"],
	           "contents": {"en": message},
	           "headings" : {"en": title}}
	 
	req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
	 
	#print(req.text)

