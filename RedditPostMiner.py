# Waits for control unit to send a message, which may contain
# config options. Fetches New Reddit Posts on recieve, and send
# back JSON to control unit.

import calendar
import json
import socket
import logging
import sys 
import time
import urllib2


LOG_FILENAME = 'reddit_post_miner_debug.log'
HOST_IP = 'localhost'
PORT = 3000
SUBREDDIT = 'TIFU'
TIME_ALIVE_UPPER_BOUND = 10000
REQUEST_HEADER = { 'User-Agent' : 'RedditPostPopularityPredictor' }


# Function retrieves data/details for a specific Reddit user.
def getUserData(username):
    userData = {}

    userAccountUrl = 'https://www.reddit.com/user/' + username +'/about.json'
    req = urllib2.Request(userAccountUrl, headers=REQUEST_HEADER)
    userInfoJSON = urllib2.urlopen(req)
    userInfo = json.load(userInfoJSON)

    userDetails = userInfo['data']

    userData['created_utc'] = userDetails['created_utc']
    userData['link_karma'] = userDetails['link_karma']
    userData['comment_karma'] = userDetails['comment_karma']
    userData['is_gold'] = userDetails['is_gold']
    userData['id'] = userDetails['id']

    return userData

def getPostSelfText(postUrl):
    postUrlJSON = postUrl + '.json'
    req = urllib2.Request(postUrlJSON, headers=REQUEST_HEADER)
    postInfoJSON = urllib2.urlopen(req)
    postInfo = json.load(postInfoJSON)

    postSelfText = postInfo[0]['data']['children'][0]['data']['selftext']

    return postSelfText

# Function retrieves new posts that are younger than TIME_ALIVE_UPPER_BOUND
# milliseconds from a given Subreddit.
# A JSON object representing the new posts is returned.
def getNewPosts():
    newPostsData = []

    newPostsUrl = 'http://www.reddit.com/r/' + SUBREDDIT + '/new.json?sort=new'
    req = urllib2.Request(newPostsUrl, headers=REQUEST_HEADER)
    newPostsJSON = urllib2.urlopen(req)

	#Python dict storing the new posts
    newPosts = json.load(newPostsJSON)

    for post in newPosts['data']['children']:
    	postDetails = post['data']

        postAuthor = postDetails['author']
        postDateCreated = postDetails['created_utc']
        postTitle = postDetails['title']
        postUrl = postDetails['url']
        postId = postDetails['id']

        if (calendar.timegm(time.gmtime()) - postDateCreated) < TIME_ALIVE_UPPER_BOUND:
			postData = {}
			postData['title'] = postTitle    
            postData['url'] = postUrl
            postData['id'] = postId
            postData['created_utc'] = postDateCreated
			
            postData['selftext'] = getPostSelfText(postUrl)

            userData = getUserData(postAuthor)
            postData['author'] = userData
            postData['author']['name'] = postAuthor

			newPostsData.append(postData)

    newPostsDataJSON = json.dumps(newPostsData)

    return newPostsDataJSON



logger = logging.getLogger('RedditPostMinerDebug')
handler = logging.FileHandler(LOG_FILENAME, mode='w')
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler) 
logger.setLevel(logging.DEBUG)
 
logger.debug('\n\n' + '=================     ALIVE     =================' + '\n')

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
     newPostsDataJSON = getNewPosts()
     logger.debug('Fetched new posts')

     message = newPostsDataJSON
     try :
         RedditPostMinerSocket.sendall(message)
     except socket.error:
          logger.debug('Send failed')
          sys.exit()
     logger.debug('Message sent successfully')