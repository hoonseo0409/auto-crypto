# Written by Hoon Seo, seohoon@mines.edu, with MIT license
# Tested on MacOSX, Pycharm, Python 3.6.4

import preprocessing
from keras.layers import LSTM
from keras.layers import Dense
from keras.models import Sequential
from keras.layers import Flatten
from keras.models import model_from_json
from numpy import hstack
from numpy import array
from sklearn.metrics import mean_squared_error
from math import sqrt
import random
from keras.layers import ConvLSTM2D
from keras.layers import Dropout
import matplotlib.pyplot as plt
import copy

steps = 10
features = 3 #price, volume, time

data = preprocessing.get_data(mmrange = (-1., 1.))
random.shuffle(data)    #To escape from data local stiffness, this may occur higher mse in training_set than mse in test_set, sometimes.

def split_data(data, n_test):
    return data[n_test:], data[:n_test]   #train, test

def data_to_xy(data, n_steps):  #data: (n, 3, 70) price, volume, time
    X = []
    y = []
    for i in range(len(data)):
        for j in range(len(data[i][0])-n_steps):   #j is start index of each sample, 0~59
            sample = []
            for k in range(n_steps):
                row = []
                for l in range(len(data[i])):
                    row.append(data[i][l][j+k])
                sample.append(row)
            X.append(sample)

    for i in range(len(data)):
        for j in range(n_steps, len(data[i][0])):   #10~69
            y.append(data[i][0][j])

    # print("len(X): {}".format(len(X)))
    # print("len(y): {}".format(len(y)))
    return array(X), array(y)

def data_to_2D_xy(data, n_steps):
    X = []
    y = []
    for i in range(len(data)):
        sub_X = []
        for j in range(len(data[i][0]) - n_steps):  # j is start index of each sample
            sample = []
            for k in range(n_steps):
                row = []
                for l in range(len(data[i])):
                    row.append(data[i][l][j + k])
                sample.append(row)
            sub_X.append(sample)
        X.append(sub_X)

    for i in range(len(data)):
        sub_y = []
        for j in range(n_steps, len(data[i][0])):
            sub_y.append(data[i][0][j])
        y.append(sub_y)

    # print("len(X): {}".format(len(X)))
    # print("len(y): {}".format(len(y)))
    return array(X), array(y)

def get_parameters():
    # steps = [10]
    # nodes = [[20, 10],
    #          [15, 20, 30],
    #          ]  #number of nodes of first layer, second layer ...
    # epochs = [40]
    # batch_size = [-1, 70]   #batch_size == -1 means no batch size
    # dropout_rate = [0.3]
    # activation = ['relu', 'tanh']
    # shuffle = [True, False]
    steps = [10]
    nodes = [[20, 30],
            [10, 20],
             ]  #number of nodes of first layer, second layer ...
    epochs = [30]
    batch_size = [60, 61, 59, -1]   #batch_size == -1 means no batch size
    dropout_rate = [0.3]
    activation = ['relu', 'tanh']
    shuffle = [False]
    prd_reset = [True]


    parameters = []
    for i in steps:
        for j in nodes:
            for k in epochs:
                for l in batch_size:
                    for m in dropout_rate:
                        for n in activation:
                            for o in shuffle:
                                for p in prd_reset:
                                    el = [i, j, k, l, m, n, o, p]
                                    parameters.append(el)

    print('Total number of combinations: {}'.format(len(parameters)))
    return parameters

def get_mse(expect, predict):
    return mean_squared_error(expect, predict)

def fit_LSTM_model(train, parameter):
    steps, nodes, epochs, batch_size, dropout_rate, activation, shuffle, prd_reset = parameter
    X_train, y_train = data_to_xy(train, steps)

    model = Sequential()
    model.add(LSTM(nodes[0], activation=activation, input_shape=(steps, 3)))
    model.add(Dropout(dropout_rate))
    for i in range(1, len(nodes)):  # First layer was already made above line
        model.add(Dense(nodes[i], activation=activation))
        model.add(Dropout(dropout_rate))
    model.add(Dense(1)) #Number of nodes of last layer should be always 1, because it predicts single floating number.
    model.summary()
    model.compile(optimizer='adam', loss='mse')
    if batch_size == -1:    #batch_size == -1 means default batch size
        model.fit(X_train, y_train, epochs=epochs, verbose=0, shuffle = shuffle)
    else:
        model.fit(X_train, y_train, epochs=epochs, verbose=0, batch_size = batch_size, shuffle = shuffle)

    return model

def fit_stateful_LSTM_model(train, parameter):  #not implemented
    steps, nodes, epochs, batch_size, dropout_rate = parameter
    X_train, y_train = data_to_xy(train, steps)

    model = Sequential()
    # model.add(LSTM(nodes[0], activation='relu', input_shape=(steps, 3)))
    model.add(LSTM(nodes[0], activation='relu', batch_input_shape=(60, steps, 3), stateful=True))
    model.add(Dropout(dropout_rate))
    for i in range(1, len(nodes)):  # First layer was already made above line
        model.add(Dense(nodes[i], activation='relu'))
        model.add(Dropout(dropout_rate))
    model.add(Dense(1))  # Number of nodes of last layer should be always 1, because it predicts single floating number.
    model.summary()
    model.compile(optimizer='adam', loss='mse')
    if batch_size == -1:  # batch_size == -1 means no batch size
        model.fit(X_train, y_train, epochs=epochs, verbose=0, batch_size=60)
    else:
        model.fit(X_train, y_train, epochs=epochs, verbose=0, batch_size=batch_size)

    return model

def calculate_conv_shape(X, K, padding=0, stride=1):
    print(X.shape)
    print(K.shape)
    Y_w = (X.shape[0] - K.shape[0] + 2 * padding) / float(stride) + 1
    Y_h = (X.shape[1] - K.shape[1] + 2 * padding) / float(stride) + 1
    return (int(Y_w), int(Y_h))

def fit_ConvLSTM_model(train, parameter):   #not implemented
    steps, nodes, epochs, batch_size = parameter
    X_train, y_train = data_to_2D_xy(train, steps)
    kernel_size = (3, 10)    # 3 is number of features
    filters = 64
    n_seq = 10
    print(X_train.shape)
    X_train = X_train.reshape((X_train.shape[0], 1, 60, steps, 3))
    print(X_train.shape)

    model = Sequential()
    model.add(ConvLSTM2D(filters=filters, kernel_size = kernel_size, activation='relu', input_shape=(1, 60, steps, 3)))
    model.add(Flatten())
    for i in range(1, len(nodes)):  # First layer was already made above line
        model.add(Dense(nodes[i], activation='relu'))
    model.add(Dense(1))  # Number of nodes of last layer should be always 1, because it predicts single floating number.
    model.summary()
    model.compile(optimizer='adam', loss='mse')

    model.fit(X_train, y_train, epochs=epochs, verbose=0)

    return model

def eval_parameter(data, n_test, parameter):
    prd_reset = parameter[7]
    predictions_test = []
    predictions_train = []
    train, test = split_data(data, n_test)
    print('Length of Training data: {}\tTest data: {}'.format(len(train), len(test)))

    model = fit_LSTM_model(train, parameter)
    # model = fit_ConvLSTM_model(train, parameter)
    X_train, y_train = data_to_xy(train, parameter[0])
    X_test, y_test = data_to_xy(test, parameter[0])
    print('Shape of X_train: {}\t y_train: {}\nShape of X_test: {}\t y_test: {}'.format(X_train.shape, y_train.shape, X_test.shape, y_test.shape))
    for i in range(len(X_test)):
        X_test[i] = X_test[i].reshape((1, parameter[0], 3))
    for i in range(len(X_train)):
        X_train[i] = X_train[i].reshape((1, parameter[0], 3))
    # X_test, y_test = data_to_2D_xy(test, parameter[0])

        # predictions_test.append((model.predict(X_test[i].reshape((1, parameter[0], 3)), verbose=0))[0][0])
    if prd_reset:
        # model.reset_states()
        for i in range(len(X_test)):
            predictions_test.append(model.predict(X_test[i].reshape((1, parameter[0], 3)))[0][0])
            model.reset_states()
        for i in range(len(X_train)):
            predictions_train.append(model.predict(X_train[i].reshape((1, parameter[0], 3)))[0][0])
            model.reset_states()
        # predictions_test = model.predict(X_test, batch_size=60, verbose=0)
        # predictions_train = model.predict(X_train, batch_size=60, verbose=0)
    else:
        predictions_test = model.predict(X_test, verbose=0)
        predictions_train = model.predict(X_train, verbose=0)
        # Below is for stateful LSTM
        # print(X_test[i].shape)
        # print(model.predict(X_test[i].reshape((60, parameter[0], 3)), verbose=0, batch_size=60))
        # predictions.append((model.predict(X_test[i].reshape((60, parameter[0], 3)), verbose=0, batch_size=60))[0][0])

        # predictions_train.append((model.predict(X_train[i].reshape((1, parameter[0], 3)), verbose=0))[0][0])
    print(len(predictions_test))
    print('First 5 samples: ')
    for i in range(5):
        print('y_test_{}: {}'.format(i, y_test[i]))
        print('predictions_{}: {}'.format(i, predictions_test[i]))

    mse_test = get_mse(y_test, predictions_test)
    mse_train = get_mse(y_train, predictions_train)
    print('parameter: {}\nmse on test set: {}\nmse on train set: {}\n'.format(parameter, mse_test, mse_train))
    return mse_test, model, predictions_test

def grid_search(data, parameters, n_test):
    best_model = None
    best_mse = 999
    best_parameter = None
    best_predictions_test = None
    train, test = split_data(data, n_test)
    X_test, y_test_raw = data_to_xy(test, 10)

    for parameter in parameters:
        error, model, predictions_test_raw = eval_parameter(data, n_test, parameter)

        if error <= best_mse:
            best_mse = error
            best_model = model
            best_parameter = copy.deepcopy(parameter)
            best_predictions_test = copy.deepcopy(predictions_test_raw)

    print('Best mse : {}\nBest parameter : {}'.format(best_mse, best_parameter))
    return best_parameter, best_model, y_test_raw, best_predictions_test, best_mse

def save_model_weights(model, best_mse, check = True):
    if check:
        file = open('./best_model/score.txt', 'r')
        line = file.read()
        previous_mse = float(line)

        if (previous_mse>best_mse):
            model_json = model.to_json()
            with open("./best_model/best_model.json", "w") as json_file:
                json_file.write(model_json)
            model.save_weights("./best_model/best_model_weights.h5")

            file.close()
            file = open('./best_model/score.txt', 'w')
            file.write("%.9f" % best_mse)
            file.close()
            print("Model and it's weights are saved to disk.")
        else:
            print('mse of previous best model {} is smaller than mse of this best model {}, so this model will not be saved.'.format(previous_mse, best_mse))
            file.close()
    else:
        model_json = model.to_json()
        with open("./best_model/best_model.json", "w") as json_file:
            json_file.write(model_json)
        model.save_weights("./best_model/best_model_weights.h5")

        file = open('./best_model/score.txt', 'w')
        file.write("%.9f" % best_mse)
        file.close()
        print("Model and it's weights are saved to disk.")

if __name__ == '__main__':
    best_parameter, best_model, y_test, best_predictions_test, best_mse = grid_search(data, get_parameters(), int(0.1*len(data)))
    save_model_weights(best_model, best_mse, True)
    plt.plot(y_test, label="y_true")
    plt.plot(best_predictions_test, label="y_prediction")
    plt.title("Prediction vs True on test set of Configuration : {}".format(best_parameter))
    plt.xlabel("Index")
    plt.ylabel("Price")
    plt.legend()
    plt.show()

# parameters = get_parameters()
# for parameter in parameters:
#     eval_parameter(data, int(0.1*len(data)), parameter)

# train, test = split_data(data, int(0.1*len(data)))

# X_train, y_train = data_to_xy(train, steps)
# X_test, y_test = data_to_xy(test, steps)
# print('X_train.shape: {}\n y_train.shape: {}\n'.format(X_train.shape, y_train.shape))
# print('X_test.shape: {}\n y_test.shape: {}\n'.format(X_test.shape, y_test.shape))

# for i in range(len(X)):
#     print('X_{}::\n{}'.format(i, X[i]))
#     print('y_{}::{}.'.format(i, y[i]))
#     print('\n')

# model = Sequential()
# model.add(LSTM(50, activation='relu', input_shape=(steps, features)))
# model.add(Dense(20, activation = 'relu'))
# model.add(Dense(1))
# model.compile(optimizer='adam', loss='mse')
# model.fit(X_train, y_train, epochs=10)


# for i in range(len(X_test)):
#     x_input = X_test[i]
#     y_expect = y_test[i]
#     x_input = x_input.reshape((1, steps, features))
#     yhat = model.predict(x_input, verbose=0)
#     print('y_expect = {}\n y_predict = {}'.format(y_expect, yhat))