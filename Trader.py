from binance.client import Client
import Utils
import traceback
from bittrexV2 import *
from HuobiUtil import *
from bittrex.bittrex import *
import asyncio, threading




class Trader:
    marketpt = 0.2
    test_mode = 1
    tries = 3

    def __init__(self, settings, iMessageHandler, iLogHandler, iMarket, iPredictor, iCSVHandler, pastListedDict):
        self.settings = settings
        self.iMessageHandler = iMessageHandler
        self.iLoghandler = iLogHandler
        self.iMarket = iMarket
        self.binance_client = Client(settings.binance_APIKEY, settings.binance_SECRET)
        self.binance_wallet_client = Client(settings.binance_wallet_APIKEY, settings.binance_wallet_SECRET)
        self.my_bittrex = Bittrex(settings.bittrex_APIKEY, settings.bittrex_SECRET)
        self.my_bittrexV2 = BittrexV2(api_key = settings.bittrex_wallet_APIKEY, api_secret = settings.bittrex_wallet_SECRET, api_version = API_V2_0)
        self.iPredictor = iPredictor
        self.iCSVHandler = iCSVHandler
        self.tradeDict = {}
        self.pastListedDict = pastListedDict
        self.canceledSellingLst = []
        self.instantCancelSymbolLst = []

    def buy_ccxt_binance(self, targetcoin, marketpt=marketpt, standardBTC=1):

        try:
            targetcoin = targetcoin.upper()
            standardBTC = int(standardBTC)

            symbol = targetcoin + '/BTC'
            type = 'limit'  # or 'market'
            side = 'buy'  # or 'buy'

            params = {
                'test': True,  # test if it's valid, but don't actually place it
            }

            NoOfMarket = -1
            # my_sendmessage(chat_id=chat_id, text="바이낸스에서 {}매수를 시작합니다.".format(targetcoin))
            # hoga = binance_client.get_order_book(symbol=targetcoin+'BTC')    #bids 매수 : 비싼 매수가격부터 싼 매수가격으로 내려옴, 매도 : 싼 매도가격부터 비싼 매도가격으로 올라옴
            recentPrice = self.iMarket.binance_ccxt.fetch_trades(symbol=symbol, limit=1)[0]['price']
            myLastPrice = 0.

            if standardBTC == 1:
                balance = self.binance_client.get_asset_balance(asset='BTC')
            else:
                balance = self.binance_client.get_asset_balance(asset=targetcoin)
            BfBalance = float(balance['free'])

            info = self.binance_client.get_symbol_info(targetcoin + 'BTC')
            # LOT variables
            minQty = float(info['filters'][2]['minQty'])

            # LOT 규격에 맞게 시장가 주문할 코인 갯수 결정
            overPrice = float(recentPrice) * 1.3

            if standardBTC == 1:
                if marketpt * BfBalance / float(recentPrice) >= minQty:  # 투자금액이 최소 매수 가능 수량의 가격보다 크거나 같을 경우
                    NoOfMarket = float(marketpt * BfBalance / float(recentPrice))
                else:
                    NoOfMarket = float(minQty)
            else:
                if marketpt * BfBalance >= minQty:  # 투자금액이 최소 매수 가능 수량의 가격보다 크거나 같을 경우
                    NoOfMarket = float(marketpt * BfBalance)
                else:
                    NoOfMarket = float(minQty)

            # NoOfMarket = float(binance_ccxt.amount_to_lots(symbol, NoOfMarket))
            overPrice = float(self.iMarket.binance_ccxt.price_to_precision(symbol, overPrice))

            # minNotional 에러 뜨면 아래 주석처리한거 실행해라
            if float(info['filters'][3]['minNotional']) > NoOfMarket * overPrice:
                print('min Notional')
                type = 'market'
            if not Trader.test_mode:
                order = self.iMarket.binance_ccxt.create_order(symbol, type, side, NoOfMarket, overPrice)
                print(order)
                self.add_tradeDict(targetcoin.upper(), NoOfMarket, 'binance', 'buy', float(recentPrice))
                trade_result = self.iMarket.binance_client.get_my_trades(symbol=targetcoin + 'BTC')
                if len(trade_result) != 0:
                    myLastPrice = trade_result[-1]['price']
                self.iMessageHandler.my_sendmessage("(성공 매수)binance_ccxt에서 {}를 {}만큼 자산비중 {}에 매수하는데 성공하였습니다. 최근 호가는 {}였고 우리의 체결가격은 {}이고 결과: {}".format(targetcoin, NoOfMarket, marketpt, recentPrice, myLastPrice, order))

                return NoOfMarket
            else:
                self.iMessageHandler.my_sendmessage("(성공 매수)binance_ccxt에서 {}를 {}만큼 바이낸스에서 성공하였습니다. 최근 호가는 {}였고 우리의 체결가격은 {}".format(targetcoin, NoOfMarket, recentPrice, myLastPrice))
                self.add_tradeDict(targetcoin.upper(), NoOfMarket, 'binance', 'buy', recentPrice)
                return 2
        except:
            self.iMessageHandler.my_sendmessage("(실패 매수)binance_ccxt에서 {}를 매수하는데 실패하였습니다. 예외 이름은 {}".format(targetcoin, traceback.format_exc(limit=1)))
            return -1

    def sell_ccxt_binance(self, targetcoin, marketpt=marketpt, standardBTC=1):

        try:
            targetcoin = targetcoin.upper()
            standardBTC = int(standardBTC)

            symbol = targetcoin + '/BTC'
            type = 'limit'  # or 'market'
            side = 'sell'  # or 'buy'

            params = {
                'test': True,  # test if it's valid, but don't actually place it
            }

            NoOfMarket = -1
            # my_sendmessage(chat_id=chat_id, text="바이낸스에서 {}매도를 시작합니다.".format(targetcoin))
            # hoga = binance_client.get_order_book(symbol=targetcoin+'BTC')    #bids 매수 : 비싼 매수가격부터 싼 매수가격으로 내려옴, 매도 : 싼 매도가격부터 비싼 매도가격으로 올라옴
            recentPrice = self.iMarket.binance_ccxt.fetch_trades(symbol=symbol, limit=1)[0]['price']
            myLastPrice = 0.

            if standardBTC == 1:
                balance = self.binance_client.get_asset_balance(asset='BTC')
            else:
                balance = self.binance_client.get_asset_balance(asset=targetcoin)
            BfBalance = float(balance['free'])

            info = self.binance_client.get_symbol_info(targetcoin + 'BTC')

            # LOT variables
            minQty = float(info['filters'][2]['minQty'])

            # LOT 규격에 맞게 시장가 주문할 코인 갯수 결정
            overPrice = float(recentPrice) * 0.7
            if standardBTC == 1:
                if marketpt * BfBalance / recentPrice >= minQty:  # 투자금액이 최소 매수 가능 수량의 가격보다 크거나 같을 경우
                    NoOfMarket = float(marketpt * BfBalance / recentPrice)
                else:
                    NoOfMarket = float(minQty)
            else:
                if marketpt * BfBalance >= minQty:  # 투자금액이 최소 매수 가능 수량의 가격보다 크거나 같을 경우
                    NoOfMarket = float(marketpt * BfBalance)
                else:
                    NoOfMarket = float(minQty)

            # NoOfMarket = float(binance_ccxt.amount_to_lots(symbol, NoOfMarket))
            overPrice = float(self.iMarket.binance_ccxt.price_to_precision(symbol, overPrice))

            # minNotional 에러 뜨면 아래 주석처리한거 실행해라
            if float(info['filters'][3]['minNotional']) > NoOfMarket * overPrice:
                type = 'market'
            if not Trader.test_mode:
                order = self.iMarket.binance_ccxt.create_order(symbol, type, side, NoOfMarket, overPrice)
                print(order)

                self.add_tradeDict(targetcoin.upper(), -NoOfMarket, 'binance', 'sell', recentPrice)
                trade_result = self.binance_client.get_my_trades(symbol=targetcoin + 'BTC')
                if len(trade_result) != 0:
                    myLastPrice = trade_result[-1]['price']
                self.iMessageHandler.my_sendmessage("(성공 매도)binance에서 {}를 {}만큼 자산비중 {}에 매도하는데 성공하였습니다. 최근 호가는 {}였고 우리의 체결가격은 {}이고 결과는: {}".format(targetcoin, NoOfMarket, marketpt, recentPrice, myLastPrice, order))
                return -NoOfMarket

            else:
                self.iMessageHandler.my_sendmessage("(성공 매도)binance에서 {}를 {}만큼 매도하는데 성공하였습니다. 최근 호가는 {}였고 우리의 체결가격은 {}".format(targetcoin, NoOfMarket, recentPrice, myLastPrice))
                self.add_tradeDict(targetcoin.upper(), -NoOfMarket, 'binance', 'sell', recentPrice)
                return 2
        except:
            self.iMessageHandler.my_sendmessage("(실패 매도)binance에서 {}를 매도하는데 실패하였습니다. 예외 이름은 {}".format(targetcoin, traceback.format_exc(limit=1)))
            return -1

    def buy_ccxt_bittrex(self, targetcoin, marketpt=marketpt, standardBTC=1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = targetcoin.upper()
            symbol = targetcoin + '/BTC'

            recentPrice = self.iMarket.bittrex_ccxt.fetch_trades(symbol, limit=1)[0]['price']

            if standardBTC == 1:
                myBalance = self.iMarket.bittrex_ccxt.fetch_free_balance()['BTC']
                amount = float(self.iMarket.bittrex_ccxt.amount_to_precision(symbol, myBalance * marketpt / recentPrice))
            else:
                myBalance = self.iMarket.bittrex_ccxt.fetch_free_balance()[targetcoin]
                amount = float(self.iMarket.bittrex_ccxt.amount_to_precision(symbol, myBalance * marketpt))

            myPrice = float(self.iMarket.bittrex_ccxt.price_to_precision(symbol, recentPrice * 1.3))

            if not Trader.test_mode:
                order = self.iMarket.bittrex_ccxt.create_order(symbol=symbol, type='limit', side='buy', amount=amount,
                                                  price=myPrice)  # kucoin은 base 기준인듯 amount, how much of currency you want to trade. This usually refers to base currency of the trading pair symbol, though some exchanges require the amount in quote currency and a few of them require base or quote amount depending on the side of the order. See their API docs for details.
                print(order)
                if order['info']['success'] == True:
                    self.iMessageHandler.my_sendmessage('(성공 매수)bittrex에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    self.add_tradeDict(targetcoin.upper(), amount, 'bittrex', 'buy', recentPrice)
                    return amount
                else:
                    self.iMessageHandler.my_sendmessage('(실패 매수)bittrex에서 {}를 매수하는데 실패했습니다: 거래 장부는 다음과 같습니다: {}'.format(targetcoin, order))
                    return -1
            else:
                self.iMessageHandler.my_sendmessage('(성공 매수)bittrex에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), amount, 'bittrex', 'buy', recentPrice)
                return 2
        except:
            self.iMessageHandler.my_sendmessage('(실패 매수)buy_ccxt_bittrex 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def sell_ccxt_bittrex(self, targetcoin, marketpt=marketpt, standardBTC=1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = targetcoin.upper()
            symbol = targetcoin + '/BTC'

            recentPrice = self.iMarket.bittrex_ccxt.fetch_trades(symbol, limit=1)[0]['price']

            if standardBTC == 1:
                myBalance = self.iMarket.bittrex_ccxt.fetch_free_balance()['BTC']
                amount = float(self.iMarket.bittrex_ccxt.amount_to_precision(symbol, myBalance * marketpt / recentPrice))
            else:
                myBalance = self.iMarket.bittrex_ccxt.fetch_free_balance()[targetcoin]
                amount = float(self.iMarket.bittrex_ccxt.amount_to_precision(symbol, myBalance * marketpt))

            myPrice = float(self.iMarket.bittrex_ccxt.price_to_precision(symbol, recentPrice * 0.8))

            if not Trader.test_mode:
                order = self.iMarket.bittrex_ccxt.create_order(symbol=symbol, type='limit', side='sell', amount=amount,
                                                  price=myPrice)  # kucoin은 base 기준인듯 amount, how much of currency you want to trade. This usually refers to base currency of the trading pair symbol, though some exchanges require the amount in quote currency and a few of them require base or quote amount depending on the side of the order. See their API docs for details.
                print(order)
                if order['info']['success'] == True:
                    self.iMessageHandler.my_sendmessage('(성공 매도)bittrex에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    self.add_tradeDict(targetcoin.upper(), -amount, 'bittrex', 'sell', recentPrice)
                    return -amount
                else:
                    self.iMessageHandler.my_sendmessage('(실패 매도)bittrex에서 {}를 매도하는데 실패했습니다: 거래 장부는 다음과 같습니다: {}'.format(targetcoin, order))
                    return -1
            else:
                self.iMessageHandler.my_sendmessage('(성공 매도)bittrex에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), -amount, 'bittrex', 'sell', recentPrice)
                return 2
        except:
            self.iMessageHandler.my_sendmessage('(실패 매도)sell_ccxt_bittrex 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def buy_ccxt_huobi(self, coin, marketpt, standardBTC=1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = coin.upper()
            symbol = targetcoin + '/BTC'

            recentPrice = self.iMarket.huobiCcxt.fetch_trades(symbol, limit=1)[0]['price']

            if standardBTC == 1:
                myBalance = self.iMarket.huobiCcxt.fetch_free_balance()['BTC']
                # amount = float(huobiCcxt.amount_to_lots(symbol, myBalance * marketpt/recentPrice))
                amount = myBalance * marketpt / recentPrice
            else:
                myBalance = self.iMarket.huobiCcxt.fetch_free_balance()[targetcoin]
                # amount = float(huobiCcxt.amount_to_lots(symbol, myBalance * marketpt))
                amount = myBalance * marketpt

            myPrice = float(self.iMarket.huobiCcxt.price_to_precision(symbol, recentPrice * 1.05))

            if not Trader.test_mode:
                order = self.iMarket.huobiCcxt.create_order(symbol=symbol, type='limit', side='buy', amount=amount, price=myPrice)  # amount가 targetcoin에 관계없이 BTC 단위다
                print(order)
                if order['info']['status'] == 'ok':
                    self.iMessageHandler.my_sendmessage('(성공 매수)huobi에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    self.add_tradeDict(targetcoin.upper(), amount, 'huobi', 'buy', recentPrice)
                    # return amount/recentPrice
                    return amount
                else:
                    self.iMessageHandler.my_sendmessage('(실패 매수)huobi에서 {}를 매수하는데 실패했습니다: 거래 장부는 다음과 같습니다: {}'.format(targetcoin, order))
                    return -1
            else:
                self.iMessageHandler.my_sendmessage('(성공 매수)huobi에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), amount, 'huobi', 'buy', recentPrice)
                return 2
        except:
            self.iMessageHandler.my_sendmessage('(실패 매수)buy_ccxt_huobi 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def sell_ccxt_huobi(self, coin, marketpt, standardBTC=1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = coin.upper()
            symbol = targetcoin + '/BTC'

            recentPrice = self.iMarket.huobiCcxt.fetch_trades(symbol, limit=1)[0]['price']

            if standardBTC == 1:
                myBalance = self.iMarket.huobiCcxt.fetch_free_balance()['BTC']
                # amount = float(huobiCcxt.amount_to_lots(symbol, myBalance * marketpt/recentPrice))
                amount = myBalance * marketpt / recentPrice
            else:
                myBalance = self.iMarket.huobiCcxt.fetch_free_balance()[targetcoin]
                # amount = float(huobiCcxt.amount_to_lots(symbol, myBalance * marketpt))
                amount = myBalance * marketpt

            myPrice = float(self.iMarket.huobiCcxt.price_to_precision(symbol, recentPrice * 0.92))

            if not Trader.test_mode:
                order = self.iMarket.huobiCcxt.create_order(symbol=symbol, type='limit', side='sell', amount=amount, price=myPrice)  # amount가 base 기준이다 huobipro는
                print(order)
                if order['info']['status'] == 'ok':
                    self.iMessageHandler.my_sendmessage('(성공 매도)huobi에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    self.add_tradeDict(targetcoin.upper(), -amount, 'huobi', 'sell', recentPrice)
                    # return amount/recentPrice
                    return -amount
                else:
                    self.iMessageHandler.my_sendmessage('(실패 매도)huobi에서 {}를 매도하는데 실패했습니다: 거래 장부는 다음과 같습니다: {}'.format(targetcoin, order))
                    return -1
            else:
                self.iMessageHandler.my_sendmessage('(성공 매도)huobi에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), -amount, 'huobi', 'sell', recentPrice)
                return 2
        except:
            self.iMessageHandler.my_sendmessage('(실패 매도)sell_ccxt_huobi 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def buy_ccxt_kucoin(self, targetcoin, marketpt=marketpt, standardBTC=1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = targetcoin.upper()
            symbol = targetcoin + '/BTC'

            recentPrice = self.iMarket.kucoinCcxt.fetch_trades(symbol, limit=1)[0]['price']
            # recentPrice = kucoinCcxt.fetch_ticker(symbol=symbol)['close']

            if standardBTC == 1:
                myBalance = self.iMarket.kucoinCcxt.fetch_free_balance()['BTC']
                # amount = float(kucoinCcxt.amount_to_lots(symbol, myBalance * marketpt/recentPrice))
                amount = myBalance * marketpt / recentPrice
            else:
                myBalance = self.iMarket.kucoinCcxt.fetch_free_balance()[targetcoin]
                # amount = float(kucoinCcxt.amount_to_lots(symbol, myBalance * marketpt))
                amount = myBalance * marketpt

            myPrice = float(self.iMarket.kucoinCcxt.price_to_precision(symbol, recentPrice * 1.3))

            if not Trader.test_mode:
                order = self.iMarket.kucoinCcxt.create_order(symbol=symbol, type='limit', side='buy', amount=amount,
                                                price=myPrice)  # kucoin은 base 기준인듯 amount, how much of currency you want to trade. This usually refers to base currency of the trading pair symbol, though some exchanges require the amount in quote currency and a few of them require base or quote amount depending on the side of the order. See their API docs for details.
                if order['info']['success'] == True:
                    self.iMessageHandler.my_sendmessage('(성공 매수)kucoin에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    self.add_tradeDict(targetcoin.upper(), amount, 'kucoin', 'buy', recentPrice)
                    # return amount/recentPrice
                    return amount
                else:
                    self.iMessageHandler.my_sendmessage('(실패 매수)kucoin에서 {}를 매수하는데 실패했습니다: 거래 장부는 다음과 같습니다: {}'.format(targetcoin, order))
                    return -1
            else:
                self.iMessageHandler.my_sendmessage('(성공 매수)kucoin에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), amount, 'kucoin', 'buy', recentPrice)
                return 2


        except:
            self.iMessageHandler.my_sendmessage('(실패 매수)buy_ccxt_kucoin 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def sell_ccxt_kucoin(self, targetcoin, marketpt=marketpt, standardBTC=1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = targetcoin.upper()
            symbol = targetcoin + '/BTC'

            recentPrice = self.iMarket.kucoinCcxt.fetch_trades(symbol, limit=1)[0]['price']
            # recentPrice = kucoinCcxt.fetch_ticker(symbol=symbol)['close']

            if standardBTC == 1:
                myBalance = self.iMarket.kucoinCcxt.fetch_free_balance()['BTC']
                # amount = float(kucoinCcxt.amount_to_lots(symbol, myBalance * marketpt/recentPrice))
                amount = myBalance * marketpt / recentPrice
            else:
                myBalance = self.iMarket.kucoinCcxt.fetch_free_balance()[targetcoin]
                # amount = float(kucoinCcxt.amount_to_lots(symbol, myBalance * marketpt))
                amount = myBalance * marketpt

            myPrice = float(self.iMarket.kucoinCcxt.price_to_precision(symbol, recentPrice * 0.8))

            if not Trader.test_mode:
                order = self.iMarket.kucoinCcxt.create_order(symbol=symbol, type='limit', side='sell', amount=amount, price=myPrice)  # amount가 targetcoin에 관계없이 BTC 단위다
                if order['info']['success'] == True:
                    self.iMessageHandler.my_sendmessage('(성공 매도)kucoin에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    self.add_tradeDict(targetcoin.upper(), -amount, 'kucoin', 'sell', recentPrice)
                    # return amount/recentPrice
                    return -amount
                else:
                    self.iMessageHandler.my_sendmessage('(실패 매도)kucoin에서 {}를 매도하는데 실패했습니다: 거래 장부는 다음과 같습니다: {}'.format(targetcoin, order))
                    return -1
            else:
                self.iMessageHandler.my_sendmessage('(성공 매도)kucoin에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), -amount, 'kucoin', 'sell', recentPrice)
                return 2


        except:
            self.iMessageHandler.my_sendmessage('(실패 매도)sell_ccxt_kucoin 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def buy_ccxt_hitbtc(self, targetcoin, marketpt=marketpt, standardBTC=1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = targetcoin.upper()
            symbol = targetcoin + '/BTC'

            recentPrice = self.iMarket.hitbtcCcxt.fetch_trades(symbol, limit=1)[0]['price']
            print(1, recentPrice)

            if standardBTC == 1:
                myBalance = self.iMarket.hitbtcCcxt.fetch_free_balance()['BTC']
                print('my BTC balance', myBalance)
                amount = float(self.iMarket.hitbtcCcxt.amount_to_precision(symbol, myBalance * marketpt / recentPrice))
            else:
                myBalance = self.iMarket.hitbtcCcxt.fetch_free_balance()[targetcoin]
                print('my nonBTC balance', myBalance)
                amount = float(self.iMarket.hitbtcCcxt.amount_to_precision(symbol, myBalance * marketpt))

            myPrice = float(self.iMarket.hitbtcCcxt.price_to_precision(symbol, recentPrice * 1.3))

            if not Trader.test_mode:
                order = self.iMarket.hitbtcCcxt.create_order(symbol=symbol, type='limit', side='buy', amount=amount,
                                                price=myPrice)  # kucoin은 base 기준인듯 amount, how much of currency you want to trade. This usually refers to base currency of the trading pair symbol, though some exchanges require the amount in quote currency and a few of them require base or quote amount depending on the side of the order. See their API docs for details.
                print(order)
                self.iMessageHandler.my_sendmessage('(성공 매수)hitbtcCcxt에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                self.add_tradeDict(targetcoin.upper(), amount, 'hitbtc', 'buy', recentPrice)
                # return amount/recentPrice
                return amount
            else:
                self.iMessageHandler.my_sendmessage('(성공 매수)hitbtcCcxt에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), amount, 'hitbtc', 'buy', recentPrice)
                return 2

        except:
            print(traceback.format_exc())
            self.iMessageHandler.my_sendmessage('(실패 매수)buy_ccxt_hitbtc 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def sell_ccxt_hitbtc(self, targetcoin, marketpt=marketpt, standardBTC=1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = targetcoin.upper()
            symbol = targetcoin + '/BTC'

            recentPrice = self.iMarket.hitbtcCcxt.fetch_trades(symbol, limit=1)[0]['price']
            print(1, recentPrice)

            if standardBTC == 1:
                myBalance = self.iMarket.hitbtcCcxt.fetch_free_balance()['BTC']
                print('my BTC balance', myBalance)
                amount = float(self.iMarket.hitbtcCcxt.amount_to_precision(symbol, myBalance * marketpt / recentPrice))
            else:
                myBalance = self.iMarket.hitbtcCcxt.fetch_free_balance()[targetcoin]
                print('my nonBTC balance', myBalance)
                amount = float(self.iMarket.hitbtcCcxt.amount_to_precision(symbol, myBalance * marketpt))

            myPrice = float(self.iMarket.hitbtcCcxt.price_to_precision(symbol, recentPrice * 0.7))

            if not Trader.test_mode:
                order = self.iMarket.hitbtcCcxt.create_order(symbol=symbol, type='limit', side='sell', amount=amount,
                                                price=myPrice)  # kucoin은 base 기준인듯 amount, how much of currency you want to trade. This usually refers to base currency of the trading pair symbol, though some exchanges require the amount in quote currency and a few of them require base or quote amount depending on the side of the order. See their API docs for details.
                print(order)
                self.iMessageHandler.my_sendmessage('(성공 매도)hitbtcCcxt에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                self.add_tradeDict(targetcoin.upper(), -amount, 'hitbtc', 'sell', recentPrice)
                # return amount/recentPrice
                return amount
            else:
                self.iMessageHandler.my_sendmessage('(성공 매도)hitbtcCcxt에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), -amount, 'hitbtc', 'sell', recentPrice)
                return 2


        except:
            print(traceback.format_exc())
            self.iMessageHandler.my_sendmessage('(실패 매도)sell_ccxt_hitbtc 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc()))
            return -1

    def sell_ccxt_gateio(self, targetcoin, marketpt=marketpt, standardBTC=1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = targetcoin.upper()
            symbol = targetcoin + '/USDT'

            recentPrice = self.iMarket.gateioCcxt.fetch_trades(symbol, limit=1)[0]['price']
            print(1, recentPrice)

            if standardBTC == 1:
                myBalance = self.iMarket.gateioCcxt.fetch_free_balance()['USDT']
                print('my USDT balance', myBalance)
                amount = float(self.iMarket.gateioCcxt.amount_to_precision(symbol, myBalance * marketpt / recentPrice))
                print('my USDT amount', amount)
            else:
                myBalance = self.iMarket.gateioCcxt.fetch_free_balance()[targetcoin]
                print('my nonUSDT balance', myBalance)
                amount = float(self.iMarket.gateioCcxt.amount_to_precision(symbol, myBalance * marketpt))
                print('my nonUSDT amount', amount)

            myPrice = float(self.iMarket.gateioCcxt.price_to_precision(symbol, recentPrice * 0.7))

            if not Trader.test_mode:
                order = self.iMarket.gateioCcxt.create_order(symbol=symbol, type='limit', side='sell', amount=amount, price=myPrice)
                print(order)
                if order['info']['result'] == 'true':
                    self.iMessageHandler.my_sendmessage('(성공 매도)gateioCcxt에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    self.add_tradeDict(targetcoin.upper(), -amount, 'gateio', 'sell', recentPrice)
                    # return amount/recentPrice
                    return -amount
                else:
                    self.iMessageHandler.my_sendmessage('(실패 매도)gateioCcxt에서 {}를 {}비중에 {}만큼 매도하는데 실패했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    return -1

            else:
                self.iMessageHandler.my_sendmessage('(성공 매도)gateioCcxt에서 {}를 {}비중에 {}만큼 매도하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), -amount, 'gateio', 'sell', recentPrice)
                return 2

        except:
            self.iMessageHandler.my_sendmessage('(실패 매도)sell_ccxt_gateio 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def buy_ccxt_gateio(self, targetcoin, marketpt=marketpt, standardBTC = 1):
        try:
            standardBTC = int(standardBTC)
            targetcoin = targetcoin.upper()
            symbol = targetcoin + '/USDT'

            recentPrice = self.iMarket.gateioCcxt.fetch_trades(symbol, limit=1)[0]['price']
            print (1, recentPrice)

            if standardBTC==1:
                myBalance = self.iMarket.gateioCcxt.fetch_free_balance()['USDT']
                print ('my USDT balance', myBalance)
                amount = float(self.iMarket.gateioCcxt.amount_to_precision(symbol, myBalance * marketpt/recentPrice))
                print ('my USDT amount', amount)
            else:
                myBalance = self.iMarket.gateioCcxt.fetch_free_balance()[targetcoin]
                print ('my nonUSDT balance', myBalance)
                amount = float(self.iMarket.gateioCcxt.amount_to_precision(symbol, myBalance * marketpt))
                print ('my nonUSDT amount', amount)

            myPrice = float(self.iMarket.gateioCcxt.price_to_precision(symbol, recentPrice * 1.3))

            if not Trader.test_mode:
                order = self.iMarket.gateioCcxt.create_order(symbol = symbol, type = 'limit', side = 'buy', amount=amount, price=myPrice)
                print (order)
                if order['info']['result']=='true':
                    self.iMessageHandler.my_sendmessage('(성공 매수)gateioCcxt에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    self.add_tradeDict(targetcoin.upper(), amount, 'gateio', 'buy', recentPrice)
                    # return amount/recentPrice
                    return amount
                else:
                    self.iMessageHandler.my_sendmessage('(실패 매수)gateioCcxt에서 {}를 {}비중에 {}만큼 매수하는데 실패했고 최근 체결 가격은 {}입니다. 거래 장부는 다음과 같습니다: {}'.format(targetcoin, marketpt, amount, recentPrice, order))
                    return -1

            else:
                self.iMessageHandler.my_sendmessage('(성공 매수)gateioCcxt에서 {}를 {}비중에 {}만큼 매수하는데 성공했고 최근 체결 가격은 {}입니다.'.format(targetcoin, marketpt, amount, recentPrice))
                self.add_tradeDict(targetcoin.upper(), amount, 'gateio', 'buy', recentPrice)
                return 2

        except:
            self.iMessageHandler.my_sendmessage('(실패 매수)buy_ccxt_gateio 함수에서 다음과 같은 예외 발생 : {}'.format(traceback.format_exc(limit=1)))
            return -1

    def buy_at_binance(self, targetcoin, marketpt=marketpt, standardBTC=1):

        try:
            targetcoin = targetcoin.upper()
            standardBTC = int(standardBTC)

            NoOfMarket = -1
            targetcoin = targetcoin.upper()
            standardBTC = int(standardBTC)

            hoga = self.binance_client.get_order_book(symbol=targetcoin + 'BTC')  # bids 매수 : 비싼 매수가격부터 싼 매수가격으로 내려옴, 매도 : 싼 매도가격부터 비싼 매도가격으로 올라옴
            myLastPrice = 0.

            trades = self.binance_client.get_recent_trades(symbol=targetcoin + 'BTC')
            LastPrice = float(trades[0]['price'])
            info = self.binance_client.get_symbol_info(targetcoin + 'BTC')

            # LOT variables
            quotePrecision = int(info['quotePrecision'])
            minQty = float(info['filters'][2]['minQty'])
            stepSize = float(info['filters'][2]['stepSize'])
            maxQty = float(info['filters'][2]['maxQty'])

            # Price variables
            tickSize = float(info['filters'][0]['tickSize'])
            minPrice = float(info['filters'][0]['minPrice'])

            # LOT 규격에 맞게 지정가 주문할 코인 갯수 결정
            LowestBids10up = float(hoga['bids'][0][0]) * 1.30000000000000000000000000000000000
            LimitPrice = int((LowestBids10up - minPrice) / tickSize) * tickSize + minPrice

            # 해당 심볼의 잔액 구하기
            if standardBTC == 1:
                balance = self.binance_client.get_asset_balance(asset='BTC')
            else:
                balance = self.binance_client.get_asset_balance(asset=targetcoin)
            BfBalance = float(balance['free'])

            if round(marketpt * BfBalance, quotePrecision) <= maxQty * LastPrice:  # 투자금액이 최대 매수 가능 수량의 가격보다 같거나 작을 경우
                if round(marketpt * BfBalance, quotePrecision) >= minQty * LastPrice:  # 투자금액이 최소 매수 가능 수량의 가격보다 크거나 같을 경우
                    if standardBTC == 1:
                        NoOfMarket = int(((marketpt * BfBalance / LastPrice) - minQty) / stepSize) * stepSize + minQty
                    else:
                        NoOfMarket = int(((marketpt * BfBalance) - minQty) / stepSize) * stepSize + minQty
                else:
                    print('예외 발생')
                    raise Exception('최소 구매 수량도 못 살 정도로 투자금이 부족합니다')
            else:
                NoOfMarket = maxQty

            if not Trader.test_mode:
                # order = client.order_market_buy(symbol=targetcoin+'BTC',quantity=NoOfMarket)   #시장가 매수
                self.iMessageHandler.my_sendmessage("LimitPrice = {}".format(LimitPrice))
                order = self.binance_client.order_limit_buy(symbol=targetcoin + 'BTC', quantity=NoOfMarket, price=LimitPrice)
                print(order)
                self.add_tradeDict(targetcoin, NoOfMarket, 'binance', 'buy', LastPrice)

                if len(self.binance_client.get_my_trades(symbol=targetcoin + 'BTC')) != 0:
                    myLastPrice = self.binance_client.get_my_trades(symbol=targetcoin + 'BTC')[-1]['price']
                    self.iMessageHandler.my_sendmessage("(성공 매수)binance에서 {}를 {}만큼 자산비중 {}에 매수하는데 성공하였습니다. 최근 타인들의 체결가격은 {}였고 우리의 체결가격은 {}이고 결과: {}".format(targetcoin, NoOfMarket, marketpt, LastPrice, myLastPrice, order))
                return NoOfMarket
            else:
                self.iMessageHandler.my_sendmessage("(성공 매수)binance에서 {}를 {}만큼 매수하는데 성공하였습니다. 최근 타인들의 체결가격은 {}였고 우리의 체결가격은 {}".format(targetcoin, NoOfMarket, LastPrice, myLastPrice))
                self.add_tradeDict(targetcoin, NoOfMarket, 'binance', 'buy', LastPrice)
                return 2
        except:
            self.iMessageHandler.my_sendmessage("(실패 매수)binance에서 {}를 매수하는데 실패하였습니다. 예외 이름은 {}".format(targetcoin, traceback.format_exc(limit=1)))
            return -1

    def sell_at_binance(self, targetcoin, marketpt=marketpt, standardBTC=1):

        try:
            NoOfMarket = -1
            targetcoin = targetcoin.upper()
            standardBTC = int(standardBTC)

            hoga = self.binance_client.get_order_book(symbol=targetcoin + 'BTC')  # bids 매수 : 비싼 매수가격부터 싼 매수가격으로 내려옴, 매도 : 싼 매도가격부터 싼 매도가격으로 내려옴
            myLastPrice = 0.
            if standardBTC == 1:
                balance = self.binance_client.get_asset_balance(asset='BTC')
            else:
                balance = self.binance_client.get_asset_balance(asset=targetcoin)
            BfBalance = float(balance['free'])

            trades = self.binance_client.get_recent_trades(symbol=targetcoin + 'BTC')
            LastPrice = float(trades[0]['price'])
            info = self.binance_client.get_symbol_info(targetcoin + 'BTC')

            # market LOT variables
            quotePrecision = int(info['quotePrecision'])
            minQty = float(info['filters'][2]['minQty'])
            stepSize = float(info['filters'][2]['stepSize'])
            maxQty = float(info['filters'][2]['maxQty'])

            # Price variables
            tickSize = float(info['filters'][0]['tickSize'])
            minPrice = float(info['filters'][0]['minPrice'])

            LowestBids10up = float(hoga['asks'][0][0]) * 0.70000000000000000000000000000000000000000000
            LimitPrice = int((LowestBids10up - minPrice) / tickSize) * tickSize + minPrice

            # LOT 규격에 맞게 시장가 주문할 코인 갯수 결정
            if round(marketpt * BfBalance, quotePrecision) <= maxQty * LastPrice:  # 투자금액이 최대 매수 가능 수량의 가격보다 같거나 작을 경우
                if round(marketpt * BfBalance, quotePrecision) >= minQty * LastPrice:  # 투자금액이 최소 매수 가능 수량의 가격보다 크거나 같을 경우
                    if standardBTC == 1:
                        NoOfMarket = int(((marketpt * BfBalance / LastPrice) - minQty) / stepSize) * stepSize + minQty
                    else:
                        NoOfMarket = int(((marketpt * BfBalance) - minQty) / stepSize) * stepSize + minQty
                else:
                    print('예외 발생')
                    raise Exception('최소 구매 수량도 못 살 정도로 투자금이 부족합니다')
            else:
                NoOfMarket = maxQty

            # 실제 매도하는 코드인데 테스트할때는 아래를 주석처리
            if not Trader.test_mode:
                # order = client.order_market_sell(symbol=targetcoin+'BTC',quantity=NoOfMarket)  #시장가 매도
                order = self.binance_client.order_limit_sell(symbol=targetcoin + 'BTC', quantity=NoOfMarket, price=LimitPrice)

                print(order)
                self.add_tradeDict(targetcoin.upper(), -NoOfMarket, 'binance', 'sell', LastPrice)
                if len(self.binance_client.get_my_trades(symbol=targetcoin + 'BTC')) != 0:
                    myLastPrice = self.binance_client.get_my_trades(symbol=targetcoin + 'BTC')[-1]['price']
                self.iMessageHandler.my_sendmessage("(성공 매도)binance에서 {}를 {}만큼 자산비중{}에 매도하는데 성공하였습니다. 최근 타인들의 체결가격은 {}였고 우리의 체결가격은 {}이고 결과: {}".format(targetcoin, NoOfMarket, marketpt, LastPrice, myLastPrice, order))
                # return NoOfMarket
                return -NoOfMarket
            else:
                self.iMessageHandler.my_sendmessage("(성공 매도)binance에서 {}를 {}만큼 매도하는데 성공하였습니다. 최근 타인들의 체결가격은 {}였고 우리의 체결가격은 {}".format(targetcoin, NoOfMarket, LastPrice, myLastPrice))
                self.add_tradeDict(targetcoin.upper(), -NoOfMarket, 'binance', 'sell', LastPrice)
                return 2.
        except:
            self.iMessageHandler.my_sendmessage("(실패 매도)binance에서 {}를 매도하는데 실패하였습니다. 예외 이름은 {}".format(targetcoin, traceback.format_exc(limit=1)))
            return -1

    def buy_at_bittrex(self, coin, marketpt, standardBTC=1):
        try:
            # market:a string literal for the market (ex: BTC-LTC) quantity: the amount to purchase rate: the rate at which to place the order(price)
            coin = coin.upper()
            standardBTC = int(standardBTC)
            marketpt = float(marketpt)

            if standardBTC == 1:
                MyBalance = self.my_bittrex.get_balance('BTC')['result']['Available']
                last = -1
                market_summary = Utils.simple_request('https://bittrex.com/api/v1.1/public/getmarketsummary?market=' + 'btc-' + coin.lower())
                last = market_summary['result'][0]['Last']
                if last == -1:
                    self.iMessageHandler.my_sendmessage('{}를 bittrex에서 찾지 못해서 매수에 실패했습니다.'.format(coin))
                    return -1
                quantity = MyBalance * marketpt / (last)

            else:
                MyBalance = self.my_bittrex.get_balance(coin)['result']['Available']
                last = -1
                market_summary = Utils.simple_request('https://bittrex.com/api/v1.1/public/getmarketsummary?market=' + 'btc-' + coin.lower())
                last = market_summary['result'][0]['Last']
                if last == -1:
                    self.iMessageHandler.my_sendmessage('{}를 bittrex에서 찾지 못해서 매수에 실패했습니다.'.format(coin))
                    return -1
                quantity = MyBalance * marketpt

            rate = last * 1.3
            result = False
            url = 'https://bittrex.com/api/v1.1/market/buylimit?apikey=' + self.settings.bittrex_APIKEY + '&market=' + 'BTC-' + coin + '&quantity=' + str(quantity) + '&rate=' + Utils.format_float(rate, 8)
            if not Trader.test_mode:
                order = Utils.signed_request(url)
                result = order['success']
            else:
                order = 'test mode'
                result = True
            if result == True:
                self.iMessageHandler.my_sendmessage('(성공 매수)bittrex에서 {}를 {}BTC에 {}개 자산비중 {}에 지정가 매수하는데 성공했습니다. 타인의 최근 체결가는 {}입니다. 결과: {}'.format(coin, rate, quantity, marketpt, last, order))
                self.add_tradeDict(coin.upper(), quantity, 'bittrex', 'buy', last)
                return quantity
            else:
                self.iMessageHandler.my_sendmessage('(실패 매수)bittrex에서 {}를 {}BTC에 {}개 지정가 매수하는데 실패했습니다. 타인의 최근 체결가는 {}입니다. 결과: {}'.format(coin, rate, quantity, last, order))
                return -1
        except:
            self.iMessageHandler.my_sendmessage('(실패 매수)bittrex에서 {}를 {}비중으로 매수하는데 다음과 같은 예외가 발생하였습니다: {}'.format(coin, marketpt, traceback.format_exc(limit=1)))
            return -1

    def sell_at_bittrex(self, coin, marketpt, standardBTC=1):
        try:
            # market:a string literal for the market (ex: BTC-LTC) quantity: the amount to purchase rate: the rate at which to place the order(price)
            coin = coin.upper()
            standardBTC = int(standardBTC)
            marketpt = float(marketpt)

            if standardBTC == 1:
                MyBalance = self.my_bittrex.get_balance('BTC')['result']['Available']
                last = -1
                market_summary = Utils.simple_request('https://bittrex.com/api/v1.1/public/getmarketsummary?market=' + 'btc-' + coin.lower())
                last = market_summary['result'][0]['Last']
                if last == -1:
                    self.iMessageHandler.my_sendmessage('{}를 bittrex에서 찾지 못해서 매수에 실패했습니다.'.format(coin))
                    return -1
                quantity = MyBalance * marketpt / (last)

            else:
                MyBalance = self.my_bittrex.get_balance(coin)['result']['Available']
                last = -1
                market_summary = Utils.simple_request('https://bittrex.com/api/v1.1/public/getmarketsummary?market=' + 'btc-' + coin.lower())
                last = market_summary['result'][0]['Last']
                if last == -1:
                    self.iMessageHandler.my_sendmessage('{}를 bittrex에서 찾지 못해서 매수에 실패했습니다.'.format(coin))
                    return -1
                quantity = MyBalance * marketpt

            rate = last * 0.7
            result = False
            url = 'https://bittrex.com/api/v1.1/market/selllimit?apikey=' + self.settings.bittrex_APIKEY + '&market=' + 'BTC-' + coin + '&quantity=' + str(quantity) + '&rate=' + Utils.format_float(rate, 8)
            if not Trader.test_mode:
                # print (signed_request(url))
                order = Utils.signed_request(url)
                result = order['success']
            else:
                order = 'test mode'
                result = True
            if result == True:
                self.iMessageHandler.my_sendmessage('(성공 매도)bittrex에서 {}를 {}BTC에 {}개 자산비중 {}에 지정가 매도하는데 성공했습니다. 타인의 최근 체결가는 {}입니다. 결과: {}'.format(coin, rate, quantity, marketpt, last, order))
                self.add_tradeDict(coin.upper(), -quantity, 'bittrex', 'sell', last)
                # return quantity
                return -quantity

            else:
                self.iMessageHandler.my_sendmessage('(실패 매도)bittrex에서 {}를 {}BTC에 {}개 지정가 매도하는데 실패했습니다. 타인의 최근 체결가는 {}입니다. 결과: {} '.format(coin, rate, quantity, last, order))
                return -1

        except:
            self.iMessageHandler.my_sendmessage('(실패 매도)bittrex에서 {}를 {}비중으로 매도하는데 다음과 같은 예외가 발생하였습니다: {}'.format(coin, marketpt, traceback.format_exc(limit=1)))
            return -1

    def buy_at_huobi(self, coin, marketpt, standardBTC=1):
        halfSymbol = coin.lower()
        coin = coin.lower() + 'btc'
        standardBTC = int(standardBTC)

        try:
            get_trade = huobi_get_trade(coin)['tick']['data'][0]
            amount_precision = len((str(get_trade['amount'])).split('.')[1])
            price = get_trade['price']
            price_precision = len((str(price)).split('.')[1])
            price = round(price * 1.100000000000000, price_precision)
            balances = huobi_get_balance()

            if standardBTC == 1:  # BTC기준으로 투자액 정할때 거래량 계산
                for i in balances['data']['list']:
                    if i['currency'] == 'btc' and i['type'] == 'trade':  # 같은 usdt라도 trade와 frozen 두개가 있어서
                        my_btc = float(i['balance'])
                        break
                amount = round((my_btc * marketpt) / (price * 1.1), amount_precision)
            else:
                for i in balances['data']['list']:
                    if i['currency'] == halfSymbol and i['type'] == 'trade':
                        my_amount = float(i['balance'])
                        break
                amount = round((my_amount * marketpt), amount_precision)

            result = -1
            if Trader.test_mode:
                self.iMessageHandler.my_sendmessage('(성공 매수)huobi에서 {}를 {}가격에 {}만큼 자산비중 {}에 지정가 매수하는데 성공했습니다.'.format(coin, price, amount, marketpt))
                self.add_tradeDict(halfSymbol.upper(), amount, 'huobi', 'buy', get_trade['price'])
                return 1
            elif not Trader.test_mode:
                result = huobi_send_order(amount, 'api', coin, 'buy-limit', price)
                print(result)
                if result['status'] == 'ok':
                    order_info = huobi_order_info(result['data'])
                    self.iMessageHandler.my_sendmessage('(성공 매수)huobi에서 {}를 {}가격에 {}만큼 자산비중 {}에 지정가 매수하는데 성공했습니다. 최근 체결가는 {}이고 결과: {}'.format(coin, price, amount, marketpt, get_trade['price'], result))
                    self.add_tradeDict(halfSymbol.upper(), amount, 'huobi', 'buy', get_trade['price'])
                    # return order_info['data']['amount']
                    return float(order_info['data']['amount'])

                else:
                    self.iMessageHandler.my_sendmessage('(실패 매수)huobi에서 {}를 {}가격에 {}만큼 자산비중 {}에 지정가 매수하는데 실패했습니다. 결과: {}'.format(coin, price, amount, marketpt, result))
                    return -1
        except:
            self.iMessageHandler.my_sendmessage('(실패 매수)huobi에서 {}를 {}비중으로 구매하는데서 다음과 같은 예외가 발생하였습니다:\n\n {}'.format(coin, marketpt, traceback.format_exc(limit=1)))
            return -1

    def sell_at_huobi(self, coin, marketpt, standardBTC=1):
        halfSymbol = coin.lower()  # standardBTC로 밑에 잔액 구할때 쓰려고
        coin = coin.lower() + 'btc'
        standardBTC = int(standardBTC)

        try:
            get_trade = huobi_get_trade(coin)['tick']['data'][0]  # 최근거래정보
            amount_precision = len((str(get_trade['amount'])).split('.')[1])  # 요구 거래량 정확도
            price = get_trade['price']  # 최근가격
            # price_precision = len(str(price % 1)) - 2
            price_precision = len((str(price)).split('.')[1])  # 최근 가격을 이용해 가격 정확도 구하기
            price = round(price * 0.90000000000, price_precision)  # 요구 정확도에 맞추기
            balances = huobi_get_balance()  # 계좌 잔액들 정보

            if standardBTC == 1:  # BTC기준으로 투자액 정할때 거래량 계산
                for i in balances['data']['list']:
                    if i['currency'] == 'btc' and i['type'] == 'trade':  # 같은 usdt라도 trade와 frozen 두개가 있어서
                        my_btc = float(i['balance'])
                        break
                amount = round((my_btc * marketpt) / (price * 1.1), amount_precision)
            else:
                for i in balances['data']['list']:
                    if i['currency'] == halfSymbol and i['type'] == 'trade':
                        my_amount = float(i['balance'])
                        break
                amount = round((my_amount * marketpt), amount_precision)

            result = -1
            if Trader.test_mode:
                self.iMessageHandler.my_sendmessage('(성공 매도)huobi에서 {}를 {}가격에 {}만큼 자산비중 {}에 지정가 매도하는데 성공했습니다.'.format(coin, price, amount, marketpt))
                return 1
            elif not Trader.test_mode:
                result = huobi_send_order(amount, 'api', coin, 'sell-limit', price)
                print(result)
                if result['status'] == 'ok':
                    order_info = huobi_order_info(result['data'])
                    self.iMessageHandler.my_sendmessage('(성공 매도)huobi에서 {}를 {}가격에 {}만큼 자산비중 {}에 지정가 매도하는데 성공했습니다. 최근 체결가는 {}이고 결과: {}'.format(coin, price, amount, marketpt, get_trade['price'], result))
                    self.add_tradeDict(halfSymbol.upper(), -amount, 'huobi', 'sell', get_trade['price'])
                    # return order_info['data']['amount']
                    return -float(order_info['data']['amount'])
                else:
                    self.iMessageHandler.my_sendmessage('(실패 매도)huobi에서 {}를 {}가격에 {}만큼 자산비중 {}에 지정가 매도하는데 실패했습니다. 결과: {}'.format(coin, price, amount, marketpt, result))
                    return -1
        except:
            self.iMessageHandler.my_sendmessage('(실패 매도)huobi에서 {}를 {}비중으로 매도하는데서 다음과 같은 예외가 발생하였습니다:\n\n {}'.format(coin, marketpt, traceback.format_exc(limit=1)))
            return -1

    def anywhere_nonStop_exce_each_amount(self, exce, coin, marketpt, standardBTC=1, tries = tries, decrementTpl=None, *args):  # args[i] == [trade_fnt, amount(0~1)]
        try:
            # cancellist 뺐으니 유의 20180508 1851
            successTrade = []
            result = -1
            for tr in range(tries):
                for list in args:
                    name = list[0].__name__
                    if exce not in name and name[-4:] not in successTrade:
                        if decrementTpl == None:
                            result = list[0](coin, list[1] * marketpt, standardBTC) #list[1] is proportion
                            if result != -1:
                                successTrade.append(name[-4:])
                            time.sleep(0.5)
                        else:
                            for pp in decrementTpl:
                                result = list[0](coin, list[1] * pp * marketpt, standardBTC)
                                if result != -1:
                                    successTrade.append(name[-4:])
                                    break
                                time.sleep(0.5)
                time.sleep(0.5)
            if len(successTrade) > 0:
                return successTrade
            else:
                return -1

        except:
            # my_sendmessage(chat_id, 'anywhere_nonStop_exce 함수에서 다음과 같은 예외가 발생했습니다:{}'.format(traceback.format_exc(limit=1)))
            return -1

    def sell_LSTM(self, toSell, coin, marketpt, standardBTC=1, selling_period=55, exce='no exception'):
        self.iMessageHandler.my_sendmessage('Sell {} automatically following LSTM'.format(coin))
        sell_amount = []
        for i in range(len(toSell)):
            sell_amount.append([toSell[i], 0.])
        for minutes in range(0, selling_period):  # 55*60 should be less than below 3600
            if coin in self.instantCancelSymbolLst:
                self.instantCancelSymbolLst.remove(coin)
                self.iMessageHandler.my_sendmessage('selling {} is instantly canceled'.format(coin))
                return 1
            toSell_2 = []
            sum_proportion = 0.
            num_proportion = 0.
            for selling_fnt in toSell:
                pair = Utils.get_pair_from_trading_fnt(coin, selling_fnt)
                market = self.iMarket.get_market_from_fnt(selling_fnt)
                current, prediction = self.iPredictor.get_current_predict_price(pair, market, 60, start_min=minutes)
                if current != None:
                    proportion = min((prediction - current) * 200. / current, 0.5)
                    sell_amount_here = Utils.get_sell_amount_with_sell_fnt(sell_amount, selling_fnt)
                    # proportion = min(proportion, (1. - sell_amount_here) / (100. * marketpt * sellingrate))
                    print(proportion)
                    if proportion > 0. and proportion + sell_amount_here >= 1.:
                        proportion = 1. - sell_amount_here

                    sum_proportion = sum_proportion + proportion
                    num_proportion = num_proportion + 1.
                    if proportion > 0. and proportion < 1.:
                        toSell_2.append([selling_fnt, proportion])
            if sum_proportion > 0. and coin not in self.canceledSellingLst:
                # my_sendmessage(chat_id, 'Sell {}, with proportion {}'.format(coin, min(marketpt * sellingrate, marketpt * sellingrate * proportion * 100.)))
                successTrade = Trader.anywhere_nonStop_exce_each_amount(exce, coin, marketpt, standardBTC, 1, None, *toSell_2)
                # t1 = threading.Thread(target=anywhere_nonStop_exce_each_amount, args=(exce, coin, standardBTC, tries, *toSell_2))
                # t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                # t1.start()
                if successTrade != -1 and len(successTrade) > 0:
                    toSell_2 = Utils.filter_toSell_2_by_name(toSell_2, successTrade)
                    for i in range(len(toSell_2)):
                        for j in range(len(sell_amount)):
                            if sell_amount[j][0] == toSell_2[i][0]:
                                sell_amount[j][1] = sell_amount[j][1] + toSell_2[i][1]
            time.sleep(60)

        self.iMessageHandler.my_sendmessage("start to sell remainings: {}".format(coin))
        self.anywhere_nonStop_exce('no exception', coin, 1.0, 0, 1, *self.get_sell_fnt())

        # sell_amount_reverse_proportion = []
        # for i in range(len(sell_amount)):
        #     sell_amount_reverse_proportion.append([sell_amount[i][0], 1. - sell_amount[i][1]])
        #     successTrade = self.anywhere_nonStop_exce_each_amount(exce, coin, 1.0, False, 1, (1.0, 0.99, 0.97, 0.94, 0.9), *sell_amount_reverse_proportion)

    def anywhere_nonStop_exce(self, exce, coin, marketpt=marketpt, standardBTC=1, tries=tries, *args):
        try:
            # cancellist 뺐으니 유의 20180508 1851
            successTrade = []
            result = -1
            for tr in range(tries):
                for func in args:
                    name = func.__name__
                    if exce not in name and name[-4:] not in successTrade:
                        result = func(coin, marketpt, standardBTC)
                        if result != -1:
                            successTrade.append(name[-4:])
                time.sleep(0.5)
            if len(successTrade) > 0:
                return 1
            else:
                return -1

        except:
            # my_sendmessage(chat_id, 'anywhere_nonStop_exce 함수에서 다음과 같은 예외가 발생했습니다:{}'.format(traceback.format_exc(limit=1)))
            return -1
    def boolean_funtHasSymbol(self, fnt, symbol):
        pair = Utils.get_pair_from_trading_fnt(symbol, fnt)
        for market in self.iMarket.marketsCcxt:
            print(fnt.__name__[-4:])
            if fnt.__name__[-4:] in market.id:
                if pair in market.symbols:
                    return True
                else:
                    return False
        print("cannot find: ", symbol)

    def buy_sell_nonStop_anywhere_exce(self, coin, marketpt=marketpt, standardBTC=1, exce='no exception', waitforselling=3600, sellingrate=0.8, writingOhlcv='writing', LSTM_sell=True, *args):
        start = time.time()
        exce = exce.lower()

        async def anywhere_async_exce(trade, coin, marketpt=marketpt, standardBTC=1, exce='no exception'):  # here trade means trade function such as buy_at_huobi
            if exce not in trade.__name__:
                result = await loop.run_in_executor(None, trade, coin, marketpt, standardBTC)
                return [result, trade.__name__[-4:]]
            else:
                return [-1, 'exception']

        async def buy_sell_async_anywhere_exce(self, coin, marketpt=marketpt, standardBTC=1, exce='no exception', waitforselling=waitforselling, sellingrate=sellingrate, writingOhlcv='writing', *args):
            # if self.boolean_funtHasSymbol(buyFirst, symbol) 
            buyResults = [asyncio.ensure_future(anywhere_async_exce(buyFirst, coin, marketpt, standardBTC, exce)) for buyFirst in args[0][0] if self.boolean_funtHasSymbol(buyFirst, coin)]
            buyResultsGather = await asyncio.gather(*buyResults)
            print(buyResultsGather)
            toBuySecond = []
            for buySecond in args[0][1]:
                for buyLst in buyResultsGather:
                    if buyLst[1] in buySecond.__name__ and buyLst[0] == -1:
                        toBuySecond.append(buySecond)
            buyResults = [asyncio.ensure_future(anywhere_async_exce(buySecond, coin, marketpt, standardBTC, exce)) for buySecond in toBuySecond if self.boolean_funtHasSymbol(buySecond, coin)]
            secondBuyResultGather = await asyncio.gather(*buyResults)
            buyResultsGather = buyResultsGather + secondBuyResultGather
            print(buyResultsGather)

            toSell = []
            for sellingTrade in args[1]:
                for buyLst in buyResultsGather:
                    if buyLst[1] in sellingTrade.__name__ and buyLst[0] != -1:
                        toSell.append(sellingTrade)

            if len(toSell) > 0:
                if not LSTM_sell:
                    self.iMessageHandler.my_sendmessage('매도를 위해 {}초간 대기합니다.'.format(waitforselling))
                    time.sleep(waitforselling)
                    if coin in self.instantCancelSymbolLst:
                        self.instantCancelSymbolLst.remove(coin)
                        self.iMessageHandler.my_sendmessage('selling {} is instantly canceled'.format(coin))
                        return 1

                    self.iMessageHandler.my_sendmessage('매도를 위한 {}초간의 대기가 끝났습니다. 매도를 시작합니다.'.format(waitforselling))
                    if coin not in self.canceledSellingLst:
                        t1 = threading.Thread(target=self.anywhere_nonStop_exce, args=(exce, coin, marketpt * sellingrate, standardBTC, 3, *toSell))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()

                else:
                    t1 = threading.Thread(target=self.sell_LSTM, args=(toSell, coin, marketpt, standardBTC, 55, exce))
                    t1.daemon = True
                    t1.start()

                if writingOhlcv == 'writing':
                    time.sleep(3600 - (time.time() - start))  # 상장 후 3600초가 지난 뒤에 지난 70분간의 데이터를 기록한다는 가정
                    for buyLst in buyResultsGather:
                        if buyLst[0] != -1:
                            t1 = threading.Thread(target=self.iCSVHandler.data_mine_to_csv, args=(coin, buyLst[1], 70, self.iMarket, self.iMessageHandler))  # 70개의 분봉 데이터
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()

        # loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(buy_sell_async_anywhere_exce(self, coin, marketpt, standardBTC, exce, waitforselling, sellingrate, writingOhlcv, *args))
        loop.close()

    def get_buy_first_fnt(self):
        return [self.buy_ccxt_binance, self.buy_ccxt_bittrex, self.buy_ccxt_huobi, self.buy_ccxt_kucoin, self.buy_ccxt_hitbtc,  self.buy_ccxt_gateio]

    def get_buy_second_fnt(self):
        return [self.buy_at_binance, self.buy_at_bittrex, self.buy_at_huobi]

    def get_sell_fnt(self):
        return [self.sell_ccxt_binance, self.sell_at_bittrex, self.sell_ccxt_huobi, self.sell_ccxt_kucoin, self.sell_at_binance,
                self.sell_at_huobi, self.sell_ccxt_bittrex, self.sell_ccxt_hitbtc,  self.sell_ccxt_gateio]

    def add_tradeDict(self, coin, amount, market, side, lastPrice):
        if len(self.tradeDict) < 12:
            coin = coin.upper()
            if not ((amount>=0. and side == 'buy') or (amount<=0. and side == 'sell')):
                print('\nADDTRADICT ERROR', market, amount, side)
            # assert (amount>=0. and side == 'buy') or (amount<=0. and side == 'sell')
            if coin not in self.tradeDict.keys():
                # self.tradeDict[coin] = [amount, [market, side, lastPrice]]
                self.tradeDict[coin] = {market : [amount, {side : [lastPrice]}]}
            else:
                if market not in self.tradeDict[coin].keys():
                    self.tradeDict[coin][market] = [amount, {side : [lastPrice]}]
                else:
                    if side not in self.tradeDict[coin][market][1].keys():
                        self.tradeDict[coin][market][0] += amount
                        self.tradeDict[coin][market][1][side] = [lastPrice]
                    else:
                        self.tradeDict[coin][market][0] += amount
                        self.tradeDict[coin][market][1][side].append(lastPrice)
                # self.tradeDict[coin][0] += amount
                # self.tradeDict[coin].append([market, side, lastPrice])
        else:
            self.tradeDict = {}

    def tradeDict_to_str(self):
        result = '--tradeDict--\n'
        for key in self.tradeDict.keys():
            result += key + '\n'
            for market in self.tradeDict[key].keys():
                result += '\t  ' + market + ':' + str(self.tradeDict[key][market][0]) + '\n'
                for side in self.tradeDict[key][market][1].keys():
                    result += '\t\t    ' + side + ': ' + str(self.tradeDict[key][market][1][side]) + '\n'
                # for i in range(1, len(self.tradeDict[key][market])):
                #     result += '\t\t    ' + str(self.tradeDict[key][market][i]) + '\n'
        return result

    def add_pastListedDict(self, coin, market):
        if market not in self.pastListedDict.keys():
            self.pastListedDict[market] = [coin]
        else:
            self.pastListedDict[market].append(coin)
