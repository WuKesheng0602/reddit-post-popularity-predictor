# Waits for control unit to send a message, which may contain
# config options. Fetches Top Reddit Posts on recieve, and send
# back JSON to control unit.

import calendar
import json
import socket
import logging
import sys 
import time
import urllib2


LOG_FILENAME = 'reddit_post_rank_discoverer_debug.log'
HOST_IP = 'localhost'
PORT = 3000
SUBREDDIT = 'TIFU'
TIME_ALIVE_UPPER_BOUND = 10000
REQUEST_HEADER = { 'User-Agent' : 'RedditPostPopularityPredictor' }

# Function retrieves top posts that are younger than TIME_ALIVE_UPPER_BOUND
# milliseconds from a given Subreddit.
# A JSON object representing the top posts is returned.
def getTopPosts():
    topPostsData = {}

    topPostsUrl = 'http://www.reddit.com/r/' + SUBREDDIT + '/top.json?sort=top&t=' + str(TIME_ALIVE_UPPER_BOUND)
    req = urllib2.Request(topPostsUrl, headers=REQUEST_HEADER)
    topPostsJSON = urllib2.urlopen(req)

	#Python dict storing the top posts
    topPosts = json.load(topPostsJSON)

    postRankNumber = 0
    for post in topPosts['data']['children']:
        postRankNumber += 1
        postDetails = post['data']

        postId = postDetails['id']
        topPostsData[postId] = postRankNumber


    topPostsDataJSON = json.dumps(topPostsData)

    return topPostsDataJSON



logger = logging.getLogger('RedditPostRankDiscovererDebug')
handler = logging.FileHandler(LOG_FILENAME, mode='w')
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler) 
logger.setLevel(logging.DEBUG)
 
logger.debug('\n\n' + '=================     ALIVE     =================' + '\n')

try:
    RedditPostRankDiscovererSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
     logger.error('Failed to create socket')
     sys.exit()
     
logger.debug('Socket created successfully')

RedditPostRankDiscovererSocket.connect( (HOST_IP , PORT) )
 
logger.debug('Socket connected to' + HOST_IP + 'on ' + str(PORT))
 
while True:
     # Waiting for messages from Control (blocking)
     redditPostRankDiscoveryConfigJSON = RedditPostRankDiscovererSocket.recv(1024)
     logger.debug('Message recieved from Control')
     redditPostRankDiscoveryConfig = json.load(redditMiningConfigJSON)

     if redditPostRankDiscoveryConfig['config_changed'] == 1:
          SUBREDDIT = redditPostRankDiscoveryConfig['subreddit']
          TIME_ALIVE_UPPER_BOUND = redditPostRankDiscoveryConfig['time_alive_upper_bound']
          logger.debug('Config changed')
     
     # Fetch top posts
     topPostsDataJSON = getTopPosts()
     logger.debug('Fetched top posts')

     message = topPostsDataJSON
     try :
         RedditPostRankDiscovererSocket.sendall(message)
     except socket.error:
          logger.debug('Send failed')
          sys.exit()
     logger.debug('Message sent successfully')