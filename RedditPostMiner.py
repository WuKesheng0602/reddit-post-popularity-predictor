# Waits for control unit to send a message, which may contain
# config options. Fetches new Reddit Posts on recieve, and send
# back JSON to control unit.

import calendar
import json
import socket
import logging
import sys 
import time
import urllib2


LOG_FILENAME = 'RedditPostMinerDebug.log'
HOST_IP = 'localhost'
PORT = 3000
SUBREDDIT = 'TIFU'
TIME_ALIVE_UPPER_BOUND = 10000

# Function retrieves new posts that are younger than TIME_ALIVE_UPPER_BOUND
# milliseconds from a given Subreddit.
# A JSON object representing the new posts is returned.
def fetchNewPosts():
    newPostsData = []

    newPostsUrl = 'http://www.reddit.com/r/' + SUBREDDIT + '/new.json?sort=new'
    reqHeader = { 'User-Agent' : 'RedditPostPopularityPredictor' }
    req = urllib2.Request(newPostsUrl, headers=reqHeader)
	newPostsJSON = urllib2.urlopen(req)

	#Python dict storing the new posts
    newPosts = json.load(newPosts)

    for post in newPosts['data']['children']:
    	postDetails = post['data']

		postAuthor = postDetails['author']
		postKarma = 0
		postDateCreated = postDetails['created_utc']
		postTitle = postDetails['title']
		postURL = postDetails['url']
		postId = postDetails['id']

		if (calendar.timegm(time.gmtime()) - postDateCreated) < TIME_ALIVE_UPPER_BOUND:
			postData = {}
			postData['title'] = postTitle
			postData['author'] = postAuthor
			postData['karma'] = postKarma
			postData['url'] = postURL
			postData['id'] = postId
			postData['created_utc'] = postDateCreated

			newPostsData.append(postData)

    newPostsDataJSON = json.dumps(newPostsData)

    return newPostsDataJSON



logger = logging.getLogger('RedditPostMinerDebug')
handler = logging.FileHandler(LOG_FILENAME, mode='w')
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler) 
logger.setLevel(logging.DEBUG)
 
try:
    RedditPostMinerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
     logger.error('Failed to create socket')
     sys.exit()
     
logger.debug('Socket created successfully')

RedditPostMinerSocket.connect( (HOST_IP , PORT) )
 
logger.debug('Socket connected to' + HOST_IP + 'on ' + PORT)
 
while True:
     # Waiting for messages from Control (blocking)
     redditMiningConfigJSON = RedditPostMinerSocket.recv(1024)
     logger.debug('Message recieved from Control')
     redditMiningConfig = json.load(redditMiningConfigJSON)

     if redditMiningConfig['config_changed'] == 1:
          SUBREDDIT = redditMiningConfig['subreddit']
          TIME_ALIVE_UPPER_BOUND = redditMiningConfig['time_alive_upper_bound']
          logger.debug('Config changed')
     
     # Fetch new posts
     newPostsDataJSON = fetchNewPosts()
     logger.debug('Fetched new posts')

     message = newPostsDataJSON
     try :
         RedditPostMinerSocket.sendall(message)
     except socket.error:
          logger.debug('Send failed')
          sys.exit()
     logger.debug('Message sent successfully')