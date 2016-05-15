# Waits for control unit to send a message, which includes 
# relevant post data for formulating a set of formulating
# for the Neural Network
import json
import socket
import logging
import sys 
import thread
import time

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math

from keras.models import Sequential
from keras.layers.core import Dense, Activation
from keras.models import model_from_json

HOST_IP = 'localhost'
PORT = 3000
LOG_FILENAME = 'neural_network_debug.log'

SAVED_MODEL_ARCHITECTURE_JSON = 'my_model_architecture.json'
SAVED_MODEL_WEIGHTS_H5 = 'my_model_weights.h5'

NUMBER_OF_FEATURES = 117798 + 6
NUMBER_OF_CLASSES = 5

NUMBER_OF_UNITS_HIDDEN_LAYER_1 = int((NUMBER_OF_FEATURES + NUMBER_OF_CLASSES) * float(2)/3)

MODEL_OPTIMIZER = 'sgd'
MODEL_LOSS = 'mean_squared_error'

# Logger set up
logger = logging.getLogger('NeuralNetworkDebug')
handler = logging.FileHandler(LOG_FILENAME, mode='w')
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler) 
logger.setLevel(logging.DEBUG)
 
logger.debug('\n\n' + '=================     ALIVE     =================' + '\n')

#################################################################################

predictionModel = None
trainingModel = None
networkReady = False
trainingNetworkReady = False

def loadSavedModel():
    savedModelArchitectureFile = open(SAVED_MODEL_ARCHITECTURE_JSON)
    savedModelArchitectureJSON = savedModelArchitectureFile.read()
    savedModelArchitectureFile.close()

    model = model_from_json(savedModelArchitectureJSON)
    model.load_weights(SAVED_MODEL_WEIGHTS_H5)
    model.compile(
        optimizer=MODEL_OPTIMIZER, 
        loss=MODEL_LOSS
        )

    return model

def saveModel(model):
    modelArchitectureJSON = predictionModel.to_json()

    savedModelArchitectureFile = open(SAVED_MODEL_ARCHITECTURE_JSON, 'w')
    savedModelArchitectureFile.write(modelArchitectureJSON)
    savedModelArchitectureFile.close()

    model.save_weights(SAVED_MODEL_WEIGHTS_H5)

def createModel():
    model = Sequential()

    # First hidden layer with the features as input and 
    # NUMBER_OF_UNITS_HIDDEN_LAYER_1 as hidden units. Uses the sigmoid function.
    model.add(Dense(
        input_dim=NUMBER_OF_FEATURES,
        output_dim=NUMBER_OF_UNITS_HIDDEN_LAYER_1)
    )
    model.add(Activation('sigmoid'))

    # Output layer with the softmax activation function, which is similar
    # to sigmoid except that all units must sum to 1.
    model.add(Dense(
        output_dim=NUMBER_OF_CLASSES)
    )
    model.add(Activation('softmax'))

    # Compiles the model to run effificiently on CPU/GPU
    model.compile(
        loss=MODEL_LOSS, 
        optimizer=MODEL_OPTIMIZER
        )

    return model


def neuralNetworkTrainingThread():
    try:
        NeuralNetworkTrainingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
         logger.error('Failed to create training socket')
         sys.exit()
         
    logger.debug('Training socket created successfully')

    NeuralNetworkTrainingSocket.connect( (HOST_IP , PORT) )
     
    logger.debug('Training socket connected to' + HOST_IP + 'on ' + str(PORT))




# Two threads; main thread to listen for prediction prompts,
# secondary thread to listen for training prompts
try:
   thread.start_new_thread( neuralNetworkTrainingThread, () )
except:
    logger.error('Failed to start thread')


try:
    NeuralNetworkPredictionSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
     logger.error('Failed to create prediction socket')
     sys.exit()
     
logger.debug('Prediction socket created successfully')

NeuralNetworkPredictionSocket.connect( (HOST_IP , PORT) )
 
logger.debug('Prediction socket connected to' + HOST_IP + 'on ' + str(PORT))

while True:
    # TODO: Create a buffer for recv...for all servers.
    # will be addressed at a later date!
    # Waiting for prediction prompts from Control (blocking)
    featuresJSON = NeuralNetworkPredictionSocket.recv(16384*4)
    
    logger.debug('Message recieved from Control')
    features = json.load(featuresJSON)

    # NN not configured yet
    while not networkReady:
        pass

    # Another version of the NN has been trained.
    # Replace the main model with the trained version before predicting
    if trainingNetworkReady:
        predictionModel = trainingModel
        trainingNetworkReady = False

    prediction = predictFromFeatures(features)

    predictionJSON = json.dumps(prediction)
    message = predictionJSON

    try :
        NeuralNetworkPredictionSocket.sendall(message)
    except socket.error:
        logger.debug('Send failed')
        sys.exit()
    logger.debug('Message sent successfully')