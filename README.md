Cataspark
=======

This script demonstrates reading NETCONF data from a Catalyst switch and displaying it in a Cisco Spark room.  This is a limited demonstration of a ChatOps scenario  and not intended for fully managing a network.  However, it could be expanded and built upon.  Currently the script is limited to interacting with one switch.  The script works as follows:

1.  Poll the Spark room for new messages.  (Push is not used due to my desire to execute the script on my laptop which does not have a public IP address.)
2.  Branch off to the appropriate action based on the message content, or ignore it.
3.  Post the response back to the room.

>  Note:  Some versions of the demo used Google's Natural Language APIs.  I removed that from here because (a) Google started charging me to use the API and (b) it was overkill and didn't work very well.  Please contact me if you want to see that version of the code.

>  Note 2:  I always make the caveat that I am a network engineer and not a software engineer.  There are almost certainly non-Pythonic usages in here, sub-optimal code, etc.  The point is, you don't have to be an expert to do this sort of thing, and you can always fix your code later as you improve your skills!

# Requirements
The data models used are based on IOS XE 16.5.  They will not work with IOS XE 16.3 or 16.4.  The testing of the script was done using a Catalyst 3850 running an engineering build of 16.5.  In theory they should work on a CSR1kv or other device running 16.5, although I have not tested this.

# Installation

Please familiarize yourself with Python virtual environments.  Create and activate one in a new directory before running the following steps.

```
git clone https://github.com/ccie14023/cataspark
pip install -r requirements.txt
```

# Configuration

At the top of the script is a section that looks like this:

```
HOST = ""
USERNAME = ""
PASSWORD = ""
SPARK_ROOM=""
my_token = ""
bot_token = ""
dropbox_token = ""
```

Into this, insert the following:

* HOST = IP address of the switch
* USERNAME = Username for NETCONF purposes
* PASSWORD = Password for this user
* SPARK_ROOM = The name of the Spark room 
* my_token = Your personal Spark token as retrieved with the directions below
* bot_token = The bot's Spark token
* dropbox_token = The dropbox token for the app you created below

#  Using

Activate your VirtualEnvironment.  Then simply:

```
python cataspark.py
```
The script will run without any output until it is stopped with ctrl-C.

Commands you can use in the Spark room (case insensitive):

* ping:  Generates a response from the script, not the switch.  Verifies the script is up and running.
* show the top CPU process:  Pulls the list of processes and returns the top by CPU total run time.
* show the top memory process:  Pull the list of processes and returns the top by allocated memory.
* show the bgp neighbors:  Displays the BGP neighbors' IP addresses only.
* show the routing table:  Displays the routing table.  Subnets and the interface/next hop.
* graph the routing table:  Outputs the routing table as a PNG graph and posts to the spark room.
* disable bgp neighbor x.x.x.x:  Disables the BGP neighbor with IP address x.x.x.x
* enable bgp neighbor x.x.x.x:  Enables the BGP neighbor with IP address x.x.x.x

# Enabling NETCONF

On your switch (or router) do the following:

```
aaa authentication login default local
aaa authorization exec default local
username <username> password <password>
username <username> privilege 15
netconf-yang
netconf-yang cisco-odm polling-enable
line vty 0 15
transport input all
```

# Spark Bot

The script uses your own user account to read messages, and a bot to write them.  Thus, all messages posted to the room come from the bot.  Create a bot with the directions here:

https://developer.ciscospark.com/bots.html

When you generate the bot you will see a field called "Access Token."  You must copy and save the bot token as we will use it later.

You will also need your own token.  You can find it here, under "Authentication":

https://developer.ciscospark.com/getting-started.html

Save this token as well.

Create a Spark room and add the bot to it.

# DropBox
The script uses DropBox to host the graph of the routing table.  This is because Spark does not allow a direct transfer of a file to a Spark room via the API.  Instead, Spark requires the file to be reachable via a public URL.  We use DropBox to host the graph PNG image.  First, the image is generated into the directory we are running the script from.  Then the image is uploaded to DB and the URL for the image sent to Spark.  We are not being very clean here;  the graph file and PNG remain in the directory locally and in DB, and must be cleaned up by the end user.  You will need to creat an App in DropBox and then save the token.

1.  Go here:  https://www.dropbox.com/developers/apps/create
2.  Select "Dropbox API"
3.  Select "App Folder"
4.  Name the app anything you want and click "create".
5.  Click the "generate" button under "Generated access token".  Save the token.

#  Caveats/Things to fix

1.  Enable/disable of BGP neighbors using NETCONF is broken and currently uses PExpect workaround.  Should be fixed in release versions of 16.5, but need to re-write the code to use NC instead of Expect.  ASN 100 is hardcoded into the cataspark file.
2.  Showing the BGP neighbor state doesn't work.
3.  Should have the script automatically remove the graph image files from the directory and dropbox.
4.  The polling mechanism stops working when the Spark room hits 50 messages.  To work around either:
	*  Delete and recreate Spark room.  Add the bot back.
	*  Open a Python interactive shell.  Import the spark.py library and run the cleanup_room function twice.  Once with your token, once with the bot's token.



