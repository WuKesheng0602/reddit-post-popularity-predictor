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
firstNetworkReady = False
newNetworkTrained = False

def loadSavedModelAsTrainingModel():
    savedModelArchitectureFile = open(SAVED_MODEL_ARCHITECTURE_JSON)
    savedModelArchitectureJSON = savedModelArchitectureFile.read()
    savedModelArchitectureFile.close()

    trainingModel = model_from_json(savedModelArchitectureJSON)
    trainingModel.load_weights(SAVED_MODEL_WEIGHTS_H5)
    trainingModel.compile(
        optimizer=MODEL_OPTIMIZER, 
        loss=MODEL_LOSS
        )

def savePredictionModel():
    modelArchitectureJSON = predictionModel.to_json()

    savedModelArchitectureFile = open(SAVED_MODEL_ARCHITECTURE_JSON, 'w')
    savedModelArchitectureFile.write(modelArchitectureJSON)
    savedModelArchitectureFile.close()

    predictionModel.save_weights(SAVED_MODEL_WEIGHTS_H5)

def createTrainingModel():
    trainingModel = Sequential()

    # First hidden layer with the features as input and 
    # NUMBER_OF_UNITS_HIDDEN_LAYER_1 as hidden units. Uses the sigmoid function.
    trainingModel.add(Dense(
        input_dim=NUMBER_OF_FEATURES,
        output_dim=NUMBER_OF_UNITS_HIDDEN_LAYER_1)
    )
    trainingModel.add(Activation('sigmoid'))

    # Output layer with the softmax activation function, which is similar
    # to sigmoid except that all units must sum to 1.
    trainingModel.add(Dense(
        output_dim=NUMBER_OF_CLASSES)
    )
    trainingModel.add(Activation('softmax'))

    # Compiles the model to run effificiently on CPU/GPU
    trainingModel.compile(
        loss=MODEL_LOSS, 
        optimizer=MODEL_OPTIMIZER
        )


def neuralNetworkTrainingThread():
    try:
        NeuralNetworkTrainingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
         logger.error('Failed to create training socket')
         sys.exit()
         
    logger.debug('Training socket created successfully')

    NeuralNetworkTrainingSocket.connect( (HOST_IP , PORT) )
     
    logger.debug('Training socket connected to' + HOST_IP + 'on ' + str(PORT))

    while True:
        trainingOptionsJSON = NeuralNetworkTrainingSocket.recv(16384*4)
        
        logger.debug('Training message recieved from Control')

        trainingOptions = json.load(trainingOptionsJSON)
        trainingModelConfig = trainingOptions['model_config']

        if trainingOptions['load_model'] == 'new':
            NUMBER_OF_FEATURES = trainingModelConfig['number_of_features']
            NUMBER_OF_CLASSES = trainingModelConfig['number_of_classes']
            NUMBER_OF_UNITS_HIDDEN_LAYER_1 = trainingModelConfig['number_of_units_hidden_layer_1']
            MODEL_OPTIMIZER = trainingModelConfig['optimizer']
            MODEL_LOSS = trainingModelConfig['loss']

            createTrainingModel()
        elif trainingOptions['load_model'] == 'saved':
            loadSavedModelAsTrainingModel()
        elif trainingOptions['load_model'] == 'train':
            # List of numpy arrays for NN with multiple inputs
            trainingX = [np.array( trainingOptions['features'] )]

            outputVector = [0] * NUMBER_OF_CLASSES

            # One hot encode with respect to the class that the training 
            # example belongs to, i.e. class = 4.
            # TODO: Right now, we are assuming that classes range from 1-5
            outputVector[ trainingOptions['classification'] - 1 ] = 1-5

            trainingY = [np.array( outputVector )]
            trainingModel.train_on_batch(trainingX, trainingY)

        newNetworkTrained = True
        firstNetworkReady = True

        # A new network is trained. Wait until the prediction thread is ready
        # to acknowledge the new model.
        while newNetworkTrained:
            pass

        # Tell control that it is ready for another message/further training
        acknowledgementMessageToControl = ["READY"]
        acknowledgementMessageToControlJSON = json.dumps(acknowledgementMessageToControl)
        message = acknowledgementMessageToControlJSON

        try :
            NeuralNetworkTrainingSocket.sendall(message)
        except socket.error:
            logger.debug('Send failed')
            sys.exit()
        logger.debug('Message sent successfully')


# Two threads; main thread to listen for prediction prompts,
# secondary thread to listen for training prompts
try:
   thread.start_new_thread( neuralNetworkTrainingThread, () )
except:
    logger.error('Failed to start secondary thread')


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
    # TODO: Create more sockets for the server, so that different threads listen for different messages on different ports.
    # Waiting for prediction prompts from Control (blocking)
    featuresJSON = NeuralNetworkPredictionSocket.recv(16384*4)
    
    logger.debug('Prediction message recieved from Control')

    # List of feature values
    features = json.load(featuresJSON)

    # NN not configured yet. Thread will delay here until it is ready.
    # Control will not pass any further messages until it recieves
    # a "ready" message from this thread.
    while not firstNetworkReady:
        pass

    # Another version of the NN has been trained.
    # Replace the main model with the trained version before predicting.
    if newNetworkTrained:
        predictionModel = trainingModel
        newNetworkTrained = False

        # save new prediction model
        savePredictionModel()

    prediction = (predictionModel.predict_classes(np.array(features), batch_size=1, verbose=1))[0]

    predictionJSON = json.dumps(prediction)
    message = predictionJSON

    try :
        NeuralNetworkPredictionSocket.sendall(message)
    except socket.error:
        logger.debug('Send failed')
        sys.exit()
    logger.debug('Message sent successfully')