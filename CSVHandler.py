import csv, traceback, time, datetime

class CSVHandler:

    def __init__(self, message = None):
        self.message = message

    def getMessage(self):
        return self.message

    def setMessage(self, message):
        self.message = message

    def saveMessageCSV(self, message, directory):
        with open(directory, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(message)

    def get_pastListedDict(self, directory):
        with open(directory, 'r', encoding="utf-8") as f:
            csvReader = csv.reader(f)
            pastListedDict = {}
            for line in csvReader:
                if line[1] not in pastListedDict.keys():
                    pastListedDict[line[1]] = [line[2]]
                else:
                    pastListedDict[line[1]].append(line[2])
            for key in pastListedDict.keys():
                pastListedDict[key] = list(set(pastListedDict[key]))
        return pastListedDict

    def data_mine_to_csv(self, coin, marketStr, limit, iMarket, iMessageHandler):
        try:
            market = None
            coin = coin.upper()
            if marketStr == 'ance':
                market = iMarket.binance_ccxt
                symbol = coin + '/BTC'
            elif marketStr == 'trex':
                market = iMarket.bittrex_ccxt
                symbol = coin + '/BTC'
            elif marketStr == 'uobi':
                market = iMarket.huobiCcxt
                symbol = coin + '/BTC'
            elif marketStr == 'coin':
                market = iMarket.kucoinCcxt
                symbol = coin + '/BTC'
            elif marketStr == 'tbtc':
                market = iMarket.hitbtcCcxt
                symbol = coin + '/BTC'
            elif marketStr == 'okex':
                market = iMarket.okexCcxt
                symbol = coin + '/USDT'
            elif marketStr == 'teio':
                market = iMarket.gateioCcxt
                symbol = coin + '/USDT'
            else:
                return 0

            now = time.localtime()
            writtingTime = "%04d-%02d-%02d %02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
            ohlcv = iMarket.get_ohlcv(symbol, market, limit)

            if ohlcv != -1:
                marketData = [writtingTime, symbol, marketStr, limit, len(ohlcv)] + ohlcv
                with open(r'./data/marketData.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(marketData)
                iMessageHandler.my_sendmessage('{}에서 상장된 {}의 데이터를 {}로부터 과거 {}개의 분봉 데이터를 csv파일로 저장했습니다.'.format(marketStr, symbol, writtingTime, len(ohlcv)))
            else:
                # my_sendmessage(chat_id, 'selling_agent함수에서 ohlcv를 구하는데 실패')
                return -1

            return marketData
        except Exception as ex:
            iMessageHandler.my_sendmessage('data_mine_to_csv함수에서 다음과 같은 에러 발생 : {}'.format(traceback.format_exc(limit=1)))

    def write_ourData(self, coin, market, text, iTrader, score=-1.):
        iTrader.add_pastListedDict(coin, market)
        market = market.lower()
        coin = coin.upper()
        if market != 'noexception':
            with open(r'./data/ourData.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([datetime.datetime.now(), market, coin, score, text])