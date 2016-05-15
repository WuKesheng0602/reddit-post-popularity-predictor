# This script simply parses an index file from the WordNet
# dictionary and outputs a text file with a word on each line.

INDEX_FILE_NAME = 'index.noun'

indexFile = open(INDEX_FILE_NAME, 'r')
wordsDistilled = open('DISTILLED_' + INDEX_FILE_NAME + '.txt', 'w')
lineNumber = 0
for line in indexFile:
	lineNumber += 1
	if lineNumber < 30:
		continue
	else:
		if (lineNumber != 30):
			wordsDistilled.write('\n')
		word = (line.split(' '))[0]
		wordsDistilled.write(word)
indexFile.close()
wordsDistilled.close()