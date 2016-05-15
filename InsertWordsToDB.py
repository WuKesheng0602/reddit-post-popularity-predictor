# Script that inserts the words that were distilled from WordNet
# into the 'word' column in the learning_vocabularly' table in the database.

import MySQLdb

HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASS = ''
DB_NAME = 'Reddit_Post_Popularity_Predictor'
TABLE_NAME = 'learning_vocabulary'
WORDS_COLUMN_NAME = 'word'

WORDS_TO_BE_INSERTED_FILE_NAME = "DISTILLED_index.noun.txt"

db = MySQLdb.connect(host=HOST,    
                     user=DB_USER,       
                     passwd=DB_PASS,  
                     db=DB_NAME)        
db.autocommit(True)

# cursor for executing queries
cursor = db.cursor()

wordsToBeInsertedFile = open(WORDS_TO_BE_INSERTED_FILE_NAME, 'r')

for line in wordsToBeInsertedFile:
	query = 'INSERT INTO ' + TABLE_NAME + ' (' + WORDS_COLUMN_NAME + ') VALUES (\"' + line.rstrip("\n") + '\");'
	cursor.execute(query)

db.close()