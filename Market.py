from HuobiUtil import *
from bittrexV2 import *
from bittrex.bittrex import *
from binance.client import Client
import ccxt
import time
import Utils
import traceback
from datetime import datetime

import asyncio

class Market:
    def __init__(self, settings, iLogHandler, iMessageHandler):
        self.iLogHandler = iLogHandler

        self.binance_client = Client(settings.binance_APIKEY, settings.binance_SECRET)
        self.binance_wallet_client = Client(settings.binance_wallet_APIKEY, settings.binance_wallet_SECRET)
        self.binance_ccxt = ccxt.binance({'apiKey': settings.binance_APIKEY,
                                     'secret': settings.binance_SECRET,
                                     'enableRateLimit': True, })

        self.kucoinCcxt = ccxt.kucoin({
            'apiKey': settings.kucoin_APIKEY,
            'secret': settings.kucoin_SECRET,
            'enableRateLimit': True,
        })

        self.my_bittrex = Bittrex(settings.bittrex_APIKEY, settings.bittrex_SECRET)
        self.my_bittrexV2 = BittrexV2(api_key=settings.bittrex_wallet_APIKEY, api_secret=settings.bittrex_wallet_SECRET, api_version=API_V2_0)
        self.bittrex_ccxt = ccxt.bittrex({
            'apiKey': settings.bittrex_APIKEY,
            'secret': settings.bittrex_SECRET,
            'enableRateLimit': True,
        })

        self.huobiCcxt = ccxt.huobipro({
            'apiKey': settings.huobi_APIKEY,  # huobi는 잘 안 되고 huobipro는 잘 되네 api 키는 같은듯 huobi랑
            'secret': settings.huobi_SECRET,
            'enableRateLimit': True,
        })

        self.hitbtcCcxt = ccxt.hitbtc2({
            'apiKey': settings.hitbtc_APIKEY,
            'secret': settings.hitbtc_SECRET,
            'enableRateLimit': True,
        })

        self.okexCcxt = ccxt.okex({
            'apiKey': settings.okex_APIKEY,
            'secret': settings.okex_SECRET,
            'enableRateLimit': True,
        })

        self.gateioCcxt = ccxt.gateio({
            'apiKey': settings.gateio_APIKEY,  # huobi는 잘 안 되고 huobipro는 잘 되네 api 키는 같은듯 huobi랑
            'secret': settings.gateio_SECRET,
            'enableRateLimit': True,
        })

        self.marketsCcxt = [self.binance_ccxt, self.bittrex_ccxt, self.huobiCcxt, self.kucoinCcxt, self.hitbtcCcxt, self.gateioCcxt]
        self.validCurrencies = []
        self.iMessageHandler = iMessageHandler

    def loadMarkets(self):
        async def async_load_markets_func(self, market):
            for i in range(5):
                try:
                    print('try {}, {} times'.format(market, i + 1))
                    await loop.run_in_executor(None, market.load_markets)
                    return 1
                except Exception as ex:
                    print('exception in', market)
                    self.iLogHandler.saveException(ex)
                    time.sleep(1.)
            return -1

        async def async_load_markets_main(self):
            futures = [asyncio.ensure_future(async_load_markets_func(self, market)) for market in self.marketsCcxt]
            await asyncio.gather(*futures)

        loop = asyncio.get_event_loop()  # 이벤트 루프를 얻음
        loop.run_until_complete(async_load_markets_main(self))  # main이 끝날 때까지 기다림
        loop.close()

    def set_validCurrencies(self):
        self.validCurrencies = []
        for market in self.marketsCcxt:
            for currency in market.currencies.keys():
                self.validCurrencies.append(currency)
        list(set(self.validCurrencies))
        # print('우리가 취급하는 거래소의 ccxt API에서 {}개의 코인이름들이 추출되었습니다.'.format(len(validCurrencies)))
        print('{} Coin names have been extracted from the ccxt API of our exchanges.'.format(len(self.validCurrencies)))
        # return validCurrencies

    def get_ohlcv(self, symbol, market, limit, pastInMilli=0, verbose=True):
        try:
            if market == self.bittrex_ccxt:
                ohlcv = Utils.try_again_func(market.fetch_ohlcv, 3, True, symbol, '1m', limit=limit, since=self.bittrex_ccxt.milliseconds() -480000 - pastInMilli - 60000 * limit)
                ''' 
                이상하게 3을 더해줘야 limit 수만큼 나옴, since는 과거시점이고 since부터 현재쪽으로 다가오는거
                , since=(self.bittrex_ccxt.milliseconds() -0 - pastInMilli) - 60000 * (limit + 0), 
                시간이 다르게 나오는 이유 : bittrex fetch_ohlcv에 문제가 있어서 가끔 데이터 받아오지 못하고 건너뛰는 tick이 있다. 
                따라서 갯수가 limit이랑 같지 않고 랜덤하게 달라진다. 
                '''
                # for i in range(20):
                #     ohlcv = Utils.try_again_func(market.fetch_ohlcv, 3, True, symbol, '1m', limit=limit,
                #                                  since=(self.bittrex_ccxt.milliseconds() - 480000 + 60000*i - pastInMilli) - 60000 * (limit + 0))  # 이상하게 3을 더해줘야 limit 수만큼 나옴, since는 과거시점이고 since부터 현재쪽으로 다가오는거 , since=(self.bittrex_ccxt.milliseconds() -0 - pastInMilli) - 60000 * (limit + 0)
                #     print("Bittrex~~~: ", datetime.fromtimestamp(ohlcv[-1][0] / 1000).strftime('%d %B %Y %H:%M:%S'))
                #     time.sleep(5.)

                if len(ohlcv) != limit:
                    for i in range(limit - len(ohlcv)):
                        # print('bittrex', ohlcv)
                        tmp = ohlcv[-1]
                        ohlcv.append(tmp)
            elif market == self.gateioCcxt:
                headers = {'User-Agent': 'firefox'}
                splitedSymbol = symbol.lower().split('/')
                ohlcv = (Utils.try_again_func(requests.get, 3, True, 'http://data.gateio.io/api2/1/candlestick2/' + splitedSymbol[0] + '_' + splitedSymbol[1] + '?group_sec=60&range_hour=' + str(limit * 1 / 60.), headers=headers)).json()['data']
                result = []
                print(market, datetime.fromtimestamp(int(ohlcv[-1][0]) / 1000).strftime('%d %B %Y %H:%M:%S'))
                for data in ohlcv:
                    result.append(str(int(data[0]) - int(ohlcv[0][0])) + '@' + str(data[4]) + '@' + str(data[5]))
                return result
            elif market == self.okexCcxt:
                ohlcv = Utils.try_again_func(market.fetch_ohlcv, 3, True, symbol)[-limit:]
            else:
                ohlcv = Utils.try_again_func(market.fetch_ohlcv, 3, True, symbol, '1m', limit=limit)

            print(market, datetime.fromtimestamp(ohlcv[-1][0]/1000).strftime('%d %B %Y %H:%M:%S'))
            result = []
            for data in ohlcv:
                result.append(datetime.fromtimestamp(data[0]/1000).strftime('%d %B %Y %H:%M:%S') + '@' + str(data[4]) + '@' + str(data[5]))
            return result
        except Exception as ex:
            # if type(ex) == type(KeyError) and market == self.gateioCcxt:    #in case that cannot find ticker data of given symbol
            #     if limit <= 10:
            #         return -1
            #     else:
            #         return self.get_ohlcv(symbol, market, limit - 1, pastInMilli, verbose)
            self.iLogHandler.saveException(ex)
            if verbose:
                self.iMessageHandler.my_sendmessage('get_ohlcv 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def get_market_from_fnt(self, fnt):
        name_ends = fnt.__name__[-4:]
        if name_ends == 'ance':
            return self.binance_ccxt
        elif name_ends == 'trex':
            return self.bittrex_ccxt
        elif name_ends == 'uobi':
            return self.huobiCcxt
        elif name_ends == 'tbtc':
            return self.hitbtcCcxt
        elif name_ends == 'okex':
            return self.okexCcxt
        elif name_ends == 'teio':
            return self.gateioCcxt
        elif name_ends == 'coin':
            return self.kucoinCcxt
        else:
            self.iMessageHandler.my_sendmessage('Unrecognized function name : {}'.format(fnt.__name__))
            return None

    def get_balance(self, iLogHandler, targetSym = None):
        try:    #get main asset
            if targetSym == None:
                BalBTC = 0
                BalUSDT = 0
                SuccessMarket = {}
                for market in self.marketsCcxt:
                    if market == self.gateioCcxt or market == self.okexCcxt:
                        for i in range(3):
                            try:
                                usdt = market.fetch_total_balance()['USDT']
                                BalUSDT += usdt
                                SuccessMarket[market.id] = str(usdt) + ' ' + 'usdt'
                                break
                            except Exception as ex:
                                iLogHandler.saveException(ex)
                    else:
                        for i in range(3):
                            try:
                                btc = market.fetch_total_balance()['BTC']
                                BalBTC += btc
                                SuccessMarket[market.id] = str(btc) + ' ' + 'btc'
                                break
                            except Exception as ex:
                                iLogHandler.saveException(ex)
                                time.sleep(1)
                for i in range(3):
                    try:
                        btcUsdt = self.binance_ccxt.fetch_ticker('BTC/USDT')['close']
                        break
                    except Exception as ex:
                        iLogHandler.saveException(ex)
                        time.sleep(1)
                return (SuccessMarket, BalBTC, BalUSDT, BalUSDT + BalBTC * btcUsdt)
            else:   #get required asset
                resultDict = {}
                targetSym = targetSym.upper()
                for market in self.marketsCcxt:
                    if market == self.gateioCcxt or market == self.okexCcxt:
                        if targetSym+'/USDT' in market.symbols:
                            resultDict[market.id] = market.fetch_total_balance()[targetSym]
                    else:
                        if targetSym+'/BTC' in market.symbols:
                            resultDict[market.id] = market.fetch_total_balance()[targetSym]

                return resultDict
        except Exception as ex:
            iLogHandler.saveException(ex)
            print(traceback.format_exc(limit=1))
            return (-1, -1, -1)
    
