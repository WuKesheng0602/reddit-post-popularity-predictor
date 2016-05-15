# Waits for control unit to send a message, which includes 
# relevant post data for formulating a set of formulating
# for the Neural Network

# Features include:
# User comment karma
# User link karma
# User gold
# User account age
# Post topic
# Post length
# Title length

import calendar
import MySQLdb
import json
import socket
import logging
import rake
import sys 
import time

COMMENT_KARMA_MAX = 20000
LINK_KARMA_MAX = 100000
ACCOUNT_AGE_MAX = 94610000  # 3 years in seconds
POST_LENGTH_MAX = 3000  # 3000 characters
TITLE_LENGTH_MAX = 140  # 140 characters


HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASS = ''
DB_NAME = 'Reddit_Post_Popularity_Predictor'
TABLE_NAME = 'learning_vocabulary'
WORDS_COLUMN_NAME = 'word'
ID_COLUMN_NAME = 'id'

LOG_FILENAME = 'debug.log'
HOST_IP = 'localhost'
PORT = 3000

logger = logging.getLogger('log')
handler = logging.FileHandler(LOG_FILENAME, mode='w')
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler) 
logger.setLevel(logging.DEBUG)
 
logger.debug('\n\n' + '=================     ALIVE     =================' + '\n')


def commentKarmaToFeature(commentKarma):
    featureValue = 0.0
    if commentKarma > COMMENT_KARMA_MAX:
        featureValue = 1.0
    elif commentKarma < 0:
        featureValue = 0.0
    else:
        featureValue = float(commentKarma)/COMMENT_KARMA_MAX
    return featureValue

def linkKarmaToFeature(linkKarma):
    featureValue = 0.0
    if linkKarma > LINK_KARMA_MAX:
        featureValue = 1.0
    elif linkKarma < 0:
        featureValue = 0.0
    else:
        featureValue = float(linkKarma)/LINK_KARMA_MAX
    return featureValue

def givenGoldToFeature(givenGold):
    featureValue = 0.0
    if givenGold:
        featureValue = float(1)
    else:
        featureValue = float(0)
    return featureValue

def userAccountAgeToFeature(accountCreationTimestamp):
    featureValue = 0.0
    currentTimestamp = calendar.timegm(time.gmtime())
    secondsAlive = currentTimestamp - accountCreationTimestamp
    if secondsAlive > ACCOUNT_AGE_MAX:
        featureValue = float(1)
    else:
        featureValue = float(secondsAlive)/ACCOUNT_AGE_MAX
    return featureValue

def postLengthToFeature(post):
    featureValue = 0.0
    featureValue = len(post)
    if (featureValue > POST_LENGTH_MAX):
        featureValue = 1.0
    else:
        featureValue = float(featureValue)/POST_LENGTH_MAX
    return featureValue

def titleLengthToFeature(title):
    featureValue = 0.0
    featureValue = len(post)
    if (featureValue > TITLE_LENGTH_MAX):
        featureValue = 1.0
    else:
        featureValue = float(featureValue)/TITLE_LENGTH_MAX
    return featureValue

def extractPostKeywords(title, post):
    keywords = []

    # Module used to mine text for keywords, parameters are:
    # word stop list, keyword min length, keyphrase min length, and keyword frequency
    rakeTextMiner = rake.Rake("SmartStoplist.txt", 3, 3, 1)
    textToAnalyze = title + " " + post
    # List of tuples (keyword, score)
    keywordsAndPhrases = rakeTextMiner.run(textToAnalyze)


    for wordOrPhraseTuple in keywordsAndPhrases:
        tokenizedPhrase = wordOrPhraseTuple[0].split(' ')

        phrase = tokenizedPhrase[-1]
        keywords.append(phrase)

        wordNumber = 0
        for word in reversed(tokenizedPhrase):
            if wordNumber == 0:
                wordNumber += 1
                continue
            keywords.append(word)
            phrase = word + '_' + phrase
            keywords.append(phrase)

    return keywords

def getIdOfKeywordsFromDatabase(keywords):
    query = 'SELECT * from ' + TABLE_NAME + ' WHERE '
    keywordNumber = 0
    for keyword in keywords:
        if keywordNumber == 0:
            keywordNumber += 1
            query += WORDS_COLUMN_NAME + '=\"' + keyword + '\"'
        else:
            query += ' OR ' + WORDS_COLUMN_NAME + '=\"' + keyword + '\"'
    query += ';'
    cursor.execute(query)

    keywordIds = cursor.fetchall()
    return keywordIds




db = MySQLdb.connect(host=HOST,    
                 user=DB_USER,       
                 passwd=DB_PASS,  
                 db=DB_NAME)   

logger.debug('Database connection established')

# cursor for executing queries
cursor = db.cursor()

query = 'SELECT COUNT(*) FROM ' + TABLE_NAME + ';'
cursor.execute(query)

numberOfFeatures = (cursor.fetchall())[0][0]
print numberOfFeatures
features = [0.0] * numberOfFeatures

redditPostDetails = [{  
      "author":{  
         "name":"LemonInYourEyes",
         "created_utc":1409337861.0,
         "link_karma":3606,
         "comment_karma":7719,
         "is_gold":False,
         "id":"i3z3z"
      },
      "url":"https://www.reddit.com/r/tifu/comments/4je5vk/tifu_by_playing_ultimate_frisbee/",
      "title":"TIFU by playing Ultimate Frisbee",
      "created_utc":1463277307.0,
      "selftext":"This happened a few years ago.\n\nI was in high school at the time and we were playing UF. I was going for a catch and was running forward with my head turned around. I was about to catch the Frisbee when I collided with a metal bench. My shin made impact with the 'seat' part of the bench, and I somersaulted over the back of the bench. I landed face first onto the rubber track, did a scorpion, and finally came to rest. \n\nPart of the skin on my leg tore off and stuck to the bench. The students gathered around noted the hairs. I didn't bother looking at it. \n\nI ended up needing 16 stitches, but the part that hurt the worst was my face. I got major road rash on my cheek. I can provide pics of my leg in the doctor's office. The scar is still pretty slick.\n\nTL;DR: ran into a bench. Flesh removal, blood, and wild scorpions ensued. People judged me for being a gym class hero for the next two years.",
      "id":"4je5vk"
   }]


for post in redditPostDetails:

    # extracting features from post and title topic/keywords
    keywords = extractPostKeywords(post['title'], post['selftext'])
    keywordIds = getIdOfKeywordsFromDatabase(keywords)
    print(len(keywordIds))
    for keywordRow in keywordIds:
        keywordId = keywordRow[0]
        # since the auto increment of MySql DB starts at 1, we subtract
        # 1 so that it aligns with out features vector
        features[keywordId - 1] = 1.0

    # extracting features from user comment karma
    featureValueForCommentKarma = commentKarmaToFeature(post['author']['comment_karma'])
    features.append(featureValueForCommentKarma)

    # extracting features from link comment karma
    featureValueForLinkKarma = linkKarmaToFeature(post['author']['link_karma'])
    features.append(featureValueForLinkKarma)

    # extracting features from whether or not if user is given gold before
    featureValueForGivenGold = givenGoldToFeature(post['author']['is_gold'])
    features.append(featureValueForGivenGold)

    # extracting features from the account age of user
    featureValueForAccountAge = userAccountAgeToFeature(post['author']["created_utc"])
    features.append(featureValueForAccountAge)

    # extracting features from  post length
    featureValueForPostLength = postLengthToFeature(post['selftext'])
    features.append(featureValueForPostLength)

    # extracting features from  post length
    featureValueForTitleLength = titleLengthToFeature(post['title'])
    features.append(featureValueForTitleLength)

featuresJSON = json.dumps(features)

message = featuresJSON
logger.debug(message)