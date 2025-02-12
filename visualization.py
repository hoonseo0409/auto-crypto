import learn
import preprocessing
from keras.models import model_from_json
import matplotlib.pyplot as plt

json_file = open('./best_model/best_model.json', 'r')
loaded_model_json = json_file.read()
loaded_model = model_from_json(loaded_model_json)
loaded_model.load_weights("./best_model/best_model_weights.h5")
loaded_model._make_predict_function()

data = preprocessing.get_data()

X_test, y = learn.data_to_xy(data, 10)
predictions = []
true_data = []


for i in range(len(X_test)):
    predictions.append((loaded_model.predict(X_test[i].reshape((1, 10, 3)), verbose=0))[0][0])

y.tolist()
true_y = []
predict_y = []

for i in range(105):
    true_y.append(y[i*100])

for i in range(105):
    predict_y.append(predictions[i*100])
index = [str(i*100) for i in range(0,len(y))]
plt.plot(true_y, label = "True future value")
plt.plot(predict_y,label = "Predicted future value")
plt.title("Prediction vs True")
plt.xlabel("Index * 100")
plt.ylabel("Value")
plt.legend()
plt.show()


#there is some outlier values that were removed so from 186 to 174 because low is all 000

#this is for figure 2 to visualize the plot

test = preprocessing.get_data()

pricelist = []
volumelist = []

columns = len(test[0][0])
for col in range(0,columns):
    for i in range(len(test)):
        sumofprices =+ test[i][0][col]
        sumofvolume =+ test[i][1][col]
    avgvol = sumofvolume/len(test)
    avgprice = sumofprices/len(test)
    pricelist.append(avgprice)
    volumelist.append(avgvol)

plt.plot(pricelist, label = "Actual Average Price")
plt.plot(volumelist,label = "Actual Average Volume")
plt.title("Price In Relation to Volume")
plt.xlabel("Time")
plt.ylabel("Price & Volume")
plt.legend()
plt.show()
#
#
# avgprice = sumofprices/len(test)

#
# # test = array(test)
# # for i in test:
# #     print(i)
# #
# # print(test.shape)
# # print(type(test))

#there is some outlier values that were removed so from 186 to 174 because low is all 000