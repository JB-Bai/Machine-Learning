
import pandas as pd
import numpy as np
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.models import Sequential
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import time
import warnings


def preprocess():
    for i in range(1,8):
        df = pd.read_csv('train_TTI_6plus3'+'.csv')
        #dic = {}
        for (id_road, time), group in df.groupby(['id_road', 'time']):
            lst = np.delete(group.values, [0, 1, 2 ,12], axis=1).tolist()
            pdlst=pd.DataFrame(lst, columns=['-60', '-50', '-40','-30', '-20', '-10','0','10','20'])
            pdlst.to_csv('lstm2/'+str(id_road)+'_'+str(time)+'.csv')
            #print(lst)
            # for index, row in df.iterrows():
            #    lst.append([row['1'],row['2'],row['3'],row['4'],row['5'],row['6'],row['7']])
            # dic[(id_road,time)]=lst

        #print(dic)
def load_data(filename,trainrate=1):
    df=pd.read_csv(filename)
    #print(df)
    result=df.values#.tolist()
    row = round(trainrate * result.shape[0])
    train = result[:row, :]
    np.random.shuffle(train)
    x_train = train[:, :-2]
    y_train = train[:, -1:]
    #print(y_train)
    x_test = result[row:, :-2]
    y_test = result[row:, -1]

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

    return [x_train, y_train, x_test, y_test]

def build_model(layers):  #layers [1,6,10,1]
    #print(layers[0],layers[1],layers[2],layers[3])
    model = Sequential()

    model.add(LSTM(input_dim=layers[0],output_dim=layers[1],return_sequences=True))
    model.add(Dropout(0.2))

    model.add(LSTM(layers[2],return_sequences=False))
    model.add(Dropout(0.2))

    model.add(Dense(output_dim=layers[3]))
    model.add(Activation("linear"))

    start = time.time()
    model.compile(loss="mse", optimizer="rmsprop")
    #print("Compilation Time : ", time.time() - start)
    return model

def predict_point_by_point(model, data):
    predicted = model.predict(data)
    #print('predicted shape:',np.array(predicted).shape)  #(412L,1L)
    predicted = np.reshape(predicted, (predicted.size,))
    return predicted

def calc_mae(y_true,y_pred):
    return mean_absolute_error(y_true,y_pred)

def lstm():
    model = build_model([1, 6, 100, 1])
    df6 = pd.concat([pd.read_csv('toPredict_noLabel.csv'), pd.read_csv('toPredict_train_TTI.csv')])
    df6['time'] = pd.to_datetime(df6['time'])
    df7 = pd.DataFrame(columns=['id_sample', 'TTI'])
    count=0
    for name, group in df6.groupby('id_road'):
        group.sort_values('time', inplace=True)
        group.set_index('time', inplace=True)
        #group.index = group.index.time
        for i in range(6, len(group), 9):
            mydir = str('lstm2/' + str(int(group.iloc[i][1])) + '_' + str(group.index.time[i]) + '.csv')
            X_train, y_train, X_valid, y_valid = load_data(mydir)

            #print(X_train.shape,y_train.shape,y_train)

            model.fit(X_train, y_train,verbose=0, batch_size=25, nb_epoch=100, validation_split=0.05)
            count+=1
            print(count)
            X_test0=group.iloc[i-6:i,0].values
            #print(X_test.shape)
            X_test =np.reshape(X_test0,(1, X_test0.shape[0], 1))
            #print(X_test,X_test.shape)

            point_by_point_predictions = predict_point_by_point(model, X_test)
            df7.loc[len(df7)] = [group.iloc[i][2],point_by_point_predictions[0]]

            #tmp=X_test.tolist()#__add__()
            group.iloc[i,0]=point_by_point_predictions[0]

            mydir = str('lstm2/' + str(int(group.iloc[i+1][1])) + '_' + str(group.index.time[i+1]) + '.csv')
            X_train, y_train, X_valid, y_valid = load_data(mydir)

            # print(X_train.shape,y_train.shape,y_train)

            model.fit(X_train, y_train, verbose=0, batch_size=25, nb_epoch=100, validation_split=0.05)

            X_test1 = group.iloc[i - 5:i+1, 0].values
            # print(X_test.shape)
            X_test = np.reshape(X_test1, (1, X_test1.shape[0], 1))

            point_by_point_predictions = predict_point_by_point(model, X_test)
            df7.loc[len(df7)] = [group.iloc[i+1][2], point_by_point_predictions[0]]

            group.iloc[i+1, 0] = point_by_point_predictions[0]

            mydir = str('lstm2/' + str(int(group.iloc[i+2][1])) + '_' + str(group.index.time[i+2]) + '.csv')
            X_train, y_train, X_valid, y_valid = load_data(mydir)

            # print(X_train.shape,y_train.shape,y_train)

            model.fit(X_train, y_train, verbose=0, batch_size=25, nb_epoch=100, validation_split=0.05)

            X_test2 = group.iloc[i - 4:i + 2, 0].values
            # print(X_test.shape)
            X_test = np.reshape(X_test2, (1, X_test2.shape[0], 1))

            point_by_point_predictions = predict_point_by_point(model, X_test)
            df7.loc[len(df7)] = [group.iloc[i + 2][2], point_by_point_predictions[0]]

            group.iloc[i + 2, 0] = point_by_point_predictions[0]

            #df7.loc[len(df7)] = [group.iloc[i+1][2], point_by_point_predictions[1]]
            #df7.loc[len(df7)] = [group.iloc[i+2][2], point_by_point_predictions[2]]
            # df = df5.loc[name, group.index[i]]
            # # model = make_pipeline(PolynomialFeatures(2), LinearRegression())
            # model = RandomForestRegressor(n_estimators=10)
            # model.fit(df.iloc[:, :6], df.iloc[:, 6:])
            # group.iloc[i:i + 3, 2] = model.predict(group.iloc[i - 6:i, 2].values.reshape(1, -1)).ravel()
            # df7 = df7.append(group.iloc[i:i + 3, [0, 2]])
        df7.to_csv('a-simple-try3.csv')

if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    #pred() #useless
    #preprocess()

    lstm()