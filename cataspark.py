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
#
# Author:  Jeff McLaughlin, jemclaug@cisco.com
#
# This software is for demonstration purposes only and is not supported
# by Cisco systems.
#
# Currently several major parameters are hardcoded into the script.
# The following parameters must be manually set:
# HOST:  Set to IP address of the device being managed.
# USERNAME:  Username for a privilege 15 user on the switch.
# PASSWORD: Password for the user.
# SPARK_ROOM:  The name of the Spark room to post to.

# my_token:  This is the Spark token of the user running the script.
# bot_token:  This is the Spark token of the bot that will be posting to Spark.
# dropbox_token:  The token for the dropbox account for posting images to Spark.

from ncclient import manager
import time
from spark import *
import json
import xmltodict
import sys
import re
from misc import *
import graphviz as gv
import os
import db

#The next 7 parameters must be set for the script to work!
HOST = ""
USERNAME = ""
PASSWORD = ""
SPARK_ROOM=""
my_token = ""
bot_token = ""
dropbox_token = ""

#  Data models we are accessing
GET_CPU_PROCS = """<cpu-usage xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-process-cpu-oper"/>"""
GET_MEM_PROCS = """<memory-usage-processes xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-process-memory-oper"/>"""
GET_BGP_NEIGHBORS = """<bgp-state xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-bgp-oper"><neighbors/></bgp-state>"""
GET_BGP_NEIGHBOR = """<bgp-state xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-bgp-oper"/>"""
SET_BGP_DOWN = """<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
  <router>
    <bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-bgp">
        <id>{}</id>
        <shutdown/>
    </bgp>
  </router>
</native>"""
IETF_GET_ROUTES = """<routing-state xmlns="urn:ietf:params:xml:ns:yang:ietf-routing"/>"""

# The Google APIs have trouble with IP addresses.  This is a basic regex
# to extract IP addresses from text strings.  There are better ones.
IP_REGEX = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"

#  This is the DropBox prefix where graphics will be stored in order to
#  be transfered to Spark.  Change if needed, but be sure DB is correct.
DB_PREFIX = "/cataspark/"

def nc_get(snippet):

	"""
	NETCONF get using the snippet XML.  Returns the raw XML response.
	To do:  accept arguments for the device instead of using global.
	"""

	with manager.connect(host=HOST, port=830, username=USERNAME,password=PASSWORD,hostkey_verify=False) as m:
	    assert(":validate" in m.server_capabilities)
	    return m.get(("subtree",snippet))

def nc_set(snippet):

	"""
	Pushes the snippet to the device specified globally.
	To do:  accept arguments for the device instead of using global.
	"""

	head = """<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">"""
	tail = "</config>"

	snippet = '{}{}{}'.format(head, snippet, tail)

	with manager.connect(host=HOST, port=830, username=USERNAME,password=PASSWORD,hostkey_verify=False) as m:
		assert(":validate" in m.server_capabilities)
		m.edit_config(target='running', config=snippet,
	    	test_option='test-then-set',error_option=None)	

def get_ietf_routes():

	"""
	This function queries the IETF routing table data model and attempts to
	extract the routing table into a dictionary.
	If it fails it returns None.
	"""

	resp = xmltodict.parse(str(nc_get(IETF_GET_ROUTES)))

	try:
		routes = resp['rpc-reply']['data']['routing-state']['routing-instance'][1]['ribs']['rib'][0]['routes']['route']
	except:
		routes = None

	return routes

def graph_routes(routes):

	"""
	Takes the routes in the form of a dictionary using the IETF model format.
	Then uses graphviz to graph the routes.  The result is saved as a local png
	file.
	"""

	g = gv.Digraph(format='png')
	g.graph_attr['rankdir'] = 'LR'  #  Left-to-Right looks better than top-to-bottom

	for route in routes:
		g.node(route['destination-prefix'])
		if 'next-hop-address' in route['next-hop'].keys():
			g.node(route['next-hop']['next-hop-address'])
			g.edge(route['destination-prefix'],route['next-hop']['next-hop-address'])
		else:
			g.node(route['next-hop']['outgoing-interface'])
			g.edge(route['destination-prefix'],route['next-hop']['outgoing-interface'])

	timestr = time.strftime("%Y%m%d-%H%M%S")
	filename = "{}-route_graph".format(timestr)

	g.render(filename=filename)

	filename = filename + ".png"

	return filename

def send_file_to_db(filename):

	"""
	Sends the file with filename to DropBox.  Returns the url
	to the file.
	"""

	td = db.TransferData(dropbox_token)

	fileto = DB_PREFIX + filename

	meta = td.upload_file(filename, fileto)

	url = meta.url[:-1] + '1'

	return url

def get_cpu_procs():

	"""
	Gets the list of CPU processes from the device.  These are returned in a dictionary.
	Returns None if the NETCONF request fails.
	"""

	resp = xmltodict.parse(str(nc_get(GET_CPU_PROCS)))

	try:
		procs = resp['rpc-reply']['data']['cpu-usage']['cpu-utilization']['cpu-usage-processes']['cpu-usage-process']
	except:
		procs = None

	return procs

def get_mem_procs():

	"""
	Gets the list of memory processes from the device.  These are returned in a dictionary.
	Returns None if the NETCONF request fails.
	"""

	resp = xmltodict.parse(str(nc_get(GET_MEM_PROCS)))

	try:
		procs = resp['rpc-reply']['data']['memory-usage-processes']['memory-usage-process']
	except:
		procs = None

	return procs


def top_mem_proc(procs):

	"""
	If provided a dictionary of memory processes, returns the process
	with the highest allocated memory.
	"""

	am = 0

	if procs:
		for proc in procs:
			if int(proc['allocated-memory']) > am:
				top_proc = proc['name']
				am = int(proc['allocated-memory'])
	else:
		top_proc = 'NETCONF error'

	return top_proc

def top_cpu_proc(procs):

	"""
	If provided a dictionary of CPU processes, returns the process
	with the highest total run time.
	"""

	trt = 0

	if procs:
		for proc in procs:
			if int(proc['total-run-time']) > trt:
				top_proc = proc['name']
				trt = int(proc['total-run-time'])
	else:
		top_proc = 'NETCONF error'

	return top_proc

def get_bgp_neighbors():

	"""
	Returns a dictionary with the BGP neighbors on the switch.
	Due to some problems with the ODM model in 16.5, this is not working properly.
	Thus the loop.
	"""

#	while True:
#		resp = xmltodict.parse(str(nc_get(GET_BGP_NEIGHBORS)))
#		if resp != None:
#			break

	try:
		resp = xmltodict.parse(str(nc_get(GET_BGP_NEIGHBORS)))
		return resp['rpc-reply']['data']['bgp-state']['neighbors']['neighbor']
	except:
		return None

def get_bgp_neighbor(neighbor_ip):

	"""
	The engineering version of 16.5 this was tested with had problems in the BGP model.
	This attempts to return the state of BGP neighbor with IP neighbor_ip.
	"""

	try:
		neighbors = xmltodict.parse(str(nc_get(GET_BGP_NEIGHBOR)))['rpc-reply']['data']['bgp-state']['address-families']['address-family']['bgp-neighbor-summaries']['bgp-neighbor-summary']
		resp = (item for item in neighbors if item['id'] == neighbor_ip).next()
	except:
		resp = None

	return resp

def message_loop():

	"""
	This loop constantly checks for new messages in the Spark room.  Because of where
	this script is intended to run, we cannot use push notifications.
	When a new message is detected, it branches off based on the message type.
	Note that the syntax of the Spark message is fairly restricted.

	The function sleeps for five seconds between polling although this interval can
	be shortened if needed.
	"""

	global room_id


	message_list = json.loads(list_messages(get_room_id(SPARK_ROOM, my_token), my_token))
	try:
		top_id = message_list['items'][0]['id']
	except:
		top_id = json.loads(post_message(" ", room_id, bot_token).text)['id']
	
	while True:

		message_list = json.loads(list_messages(get_room_id(SPARK_ROOM, my_token), my_token))
		new_id = message_list['items'][0]['id']

		if  top_id != new_id:
			new_msg = message_list['items'][0]['text'].lower()
			if  new_msg == "ping":
				top_id = json.loads(post_message("Ping response", room_id, bot_token).text)['id']
			elif new_msg == "show the top cpu process":
				text = 'Please wait while I calculate the top CPU process.  This may take a minute.'
				top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
				text = 'The top CPU process by total run time is "{}".'.format(top_cpu_proc(get_cpu_procs()))
				top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
			elif new_msg == "show the top memory process":
				text = 'Please wait while I calculate the top memory process.  This may take a minute.'
				top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
				text = 'The top memory process is "{}".'.format(top_mem_proc(get_mem_procs()))
				top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
			elif new_msg == "show the bgp neighbors":
				neighbors = get_bgp_neighbors()
				if neighbors:
					for neighbor in neighbors:
						text = neighbor['neighbor-id']
						top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
				else:
					text = "NETCONF error"
					top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
			#  Note:  the following command does not work, any attempt to use will
			#  return a NC error.
			elif new_msg.find("show the bgp state") != -1:
				ip = re.search(IP_REGEX, message_list['items'][0]['text']).group()
				state = get_bgp_neighbor(ip)
				if state:
					status = state['state']
					text = "The BGP state for neighbor {} is {}.".format(ip, status)
				else:
					text = "NETCONF error."
				top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
			elif new_msg == "show the routing table":
				routes = get_ietf_routes()
				if routes:
					for route in routes:
						key = 'outgoing-interface'
						if 'next-hop-address' in route['next-hop'].keys():
							key = 'next-hop-address'
						text = "{}-->{}".format(route['destination-prefix'], route['next-hop'][key])
						top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
				else:
					print "NETCONF error."
			elif new_msg.find("disable bgp neighbor") != -1:
				ip = re.search(IP_REGEX, message_list['items'][0]['text']).group()
				bgp_updown("down", ip,'100', HOST, USERNAME, PASSWORD)
				text = "BGP neighbor {} set to DOWN.".format(ip)
				top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
			elif new_msg.find("enable bgp neighbor") != -1:
						ip = re.search(IP_REGEX, message_list['items'][0]['text']).group()
						bgp_updown("up", ip, '100', HOST, USERNAME, PASSWORD)
						text = "BGP neighbor {} set to UP.".format(ip)
						top_id = json.loads(post_message(text, room_id, bot_token).text)['id']
			elif new_msg == "graph the routing table":
				db_file = send_file_to_db(graph_routes(get_ietf_routes()))
				text = "Routing Table Graph"
				top_id = json.loads(post_message_with_image(text, db_file, room_id, bot_token).text)['id']

			else:
				top_id = new_id

		time.sleep(5)

def main():

	global num_msgs
	global room_id

	room_id = get_room_id(SPARK_ROOM, my_token)
	
	message_loop()

if __name__ == "__main__":

	main()
