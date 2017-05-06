#!/usr/bin/env python
#
#  ----------------------------------------------------------------
# Copyright 2017 Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------

import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json


def create_room(room_name, token):

	"""
	Creates a Spark room with the name "room_name" using the token provided.
	Returns a JSON-encoded response.
	"""
	
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	headers = {'Authorization':'Bearer '+token,
				'Content-Type':'application/json'}
	body = json.dumps({'title':room_name})

	resp = requests.post('https://api.ciscospark.com/v1/rooms',
	verify=False,headers=headers,data=body)

	print resp

def list_rooms(token):

	"""
	Lists all of the rooms available to the given token.
	Returns a JSON-encoded response.
	"""
	
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	headers = {'Authorization':'Bearer '+token,
				'Content-Type':'application/json'}
	resp = requests.get('https://api.ciscospark.com/v1/rooms',
	verify=False,headers=headers)

	return resp

def get_room_id(room_name, token):

	"""
	Spark REST APIs require a room ID.  This function returns the room ID
	given the room_name and token.
	"""

	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	id = ""

	headers = {'Authorization':'Bearer '+token,
				'Content-Type':'application/json'}
	resp = requests.get('https://api.ciscospark.com/v1/rooms',
	verify=False,headers=headers)

	if resp.status_code == 200:
		
		rooms = json.loads(resp.text)['items']

		for room in rooms:
			if room['title'] == room_name:
				id = room['id']

	return id

def list_messages(room_id, token):

	"""
	Lists all of the messages in a Spark room.  Right now this is limited to 50
	messages.  Need to fix this.
	Takes a room_id and token.
	Returns a JSON-encoded list of messages.
	"""

	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	headers = {'Authorization':'Bearer '+token,
				'Content-Type':'application/json'}
	resp = requests.get('https://api.ciscospark.com/v1/messages?roomId={}'.format(room_id),
						verify=False,headers=headers)
	return resp.text

def post_message(message_text, room_id, token):

	"""
	Posts the message_text to the Spark room with the ID of room_id using the token.
	Returns the JSON-encoded response.
	"""

	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	headers = {'Authorization':'Bearer '+token,
				'Content-Type':'application/json'}

	body = json.dumps({'roomId':room_id,'text':message_text})

	resp = requests.post('https://api.ciscospark.com/v1/messages',
	verify=False,headers=headers,data=body)

	return resp

def post_message_with_image(message_text, img_url, room_id, token):

	"""
	Posts the message_text and an image located at img_url to the room with
	room_id using the token.  img_url must be a publically-accessible URL
	directly pointing to the image.  
	Returns the JSON-encoded response.
	"""

	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	headers = {'Authorization':'Bearer '+token,
				'Content-Type':'application/json'}

	body = json.dumps({'roomId':room_id,'text':message_text, 'files':img_url})

	resp = requests.post('https://api.ciscospark.com/v1/messages',
	verify=False,headers=headers,data=body)

	return resp

def cleanup_room(room_id, token):

	"""
	Deletes all of the messages in the room with room_id using token.
	This will only delete the messages of the user associated with the token provided.
	"""

	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	messages = json.loads(list_messages(room_id, my_token))

	headers = {'Authorization':'Bearer '+token,
				'Content-Type':'application/json'}

	for message in messages['items']:

		resp = requests.delete('https://api.ciscospark.com/v1/messages/{}'.format(message['id']),
					verify=False,headers=headers)
		print resp.status_code



def main():
	pass

if __name__ == "__main__":

	main()