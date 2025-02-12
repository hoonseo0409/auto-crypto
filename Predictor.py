import preprocessing
from numpy import array
import time

class Predictor:
    def __init__(self, model, iMarket):
        self.model = model
        self.iMarket = iMarket

    def get_prediction(self, symbol, market, steps=10, limit=60, get_normalized=False, start_min=0, pastInMilli=0):
        symbol = symbol.upper()
        sample = self.iMarket.get_ohlcv(symbol, market, limit, pastInMilli=pastInMilli)
        data = preprocessing.get_data_for_prediction(sample, start_min=start_min, steps=steps)  # return (result, price_maxi, price_mini, volume_maxi, volume_mini, range)
        prediction = self.model.predict(array(data[0]).reshape(1, steps, 3))
        if get_normalized:
            return prediction[0][0]
        else:
            return preprocessing.recover_minmax_scaler(prediction[0][0], data[2], data[1], data[5])

    def get_current_predict_price(self, symbol, market, limit, start_min=0, pastInMilli=0):
        symbol = symbol.upper()
        sample = self.iMarket.get_ohlcv(symbol, market, limit, pastInMilli=pastInMilli)
        if sample == -1:
            for i in range(1, min(int(limit / 10), 6)):
                sample = self.iMarket.get_ohlcv(symbol, market, limit - 10 * i, pastInMilli=pastInMilli, verbose=False)
                if sample != -1:
                    break
                time.sleep(1.)
            if sample == -1:
                return None, None
        else:
            # print(sample)
            data = preprocessing.get_data_for_prediction(sample, start_min=start_min, steps=10)
            # print(data)
            prediction = self.model.predict(array(data[0]).reshape(1, 10, 3))
            return preprocessing.recover_minmax_scaler(data[0][-1][0], data[2], data[1], data[5]), preprocessing.recover_minmax_scaler(prediction[0][0], data[2], data[1], data[5])