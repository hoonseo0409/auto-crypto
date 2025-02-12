# encoding: utf-8
from telethon import TelegramClient, events, tl
from telegram import Bot
import time, traceback
import Utils
import threading, datetime, sys


class MessageHandler:
    NoOfMessage = 0
    def __init__(self, token, toID, chat_id, telegramAPIID, telegramAPIHash, phoneNumber, iLogHandler, iConstant_data, iParser, iCSVHandler, iChangeable_data):
        self.token = token
        self.toID = toID
        self.chat_id = chat_id
        self.bot = Bot(token=token)  # bot을 선언합니다.
        self.iLogHandler = iLogHandler
        self.iConstant_data = iConstant_data
        self.numChannelPeriod = 0
        self.channelBlock = False
        self.iParser = iParser
        self.iTrader = None
        self.client = None
        self.telegramAPIID = telegramAPIID
        self.telegramAPIHash = telegramAPIHash
        self.phoneNumber = phoneNumber
        self.iCSVHandler = iCSVHandler
        self.fbLst = []
        self.iChangeable_data = iChangeable_data
        self.iMarket = None
        self.iPredictor = None
        self.kill = False


    def my_sendmessage(self, text):
        try:
            MessageHandler.NoOfMessage = MessageHandler.NoOfMessage + 1
            self.bot.sendMessage(self.chat_id, text, timeout=30)
        except Exception as ex:
            print(text)
            self.iLogHandler.myLogger.error('다음과 같은 텔레그램 메세지를 보내는데 실패했습니다. \n{}'.format(text))
            self.iLogHandler.saveException(ex)
            time.sleep(3)
            try:
                self.bot.sendMessage(self.chat_id, text, timeout=30)
            except Exception as ex:
                self.iLogHandler.myLogger.error(ex, exc_info=True)

    def set_client(self):
        self.client = TelegramClient('../session', self.telegramAPIID, self.telegramAPIHash, update_workers=1)
        print('Telethon Connection status : ', self.client.connect())
        if not self.client.is_user_authorized():
            self.client.send_code_request(self.phoneNumber)
            self.client.sign_in(self.phoneNumber, input('Enter the code: '))

    def set_Trader(self, iTrader):
        self.iTrader = iTrader

    def set_Market(self, iMarket):
        self.iMarket = iMarket

    def set_Predictor(self, iPredictor):
        self.iPredictor = iPredictor

    def telethon_main(self):
        def callback(update):
            try:
                print(update)
                if update.is_channel and update.original_update.message.to_id.channel_id == 1379897604 and not self.channelBlock:  # 새우 channel_id=1379897604, 앞에 original은 수신자 정보 뒤에 message는 발신자 정보
                    # 새우방에 '아무나 올린' 글
                    gettingTime = update.original_update.message.date
                    tradeStartTime = time.time()
                    print('새우방 입니다')
                    print(update.original_update.message.to_id.channel_id)
                    print(update.original_update.message.message)
                    message = update.original_update.message.message

                    filter_result = self.iParser.filter_saewoo(message, self.iTrader.pastListedDict, self.iTrader.tradeDict)
                    print(filter_result)
                    if (filter_result[0] != -1) and (self.numChannelPeriod <= self.iConstant_data.possibleChannelNum):
                        t1 = threading.Thread(target=self.iTrader.buy_sell_nonStop_anywhere_exce, args=(
                            filter_result[0], min(0.6, 1.8 * filter_result[2] / 10.), 1, filter_result[1], self.iConstant_data.waitforselling, 0.8, 'writing', True, [self.iTrader.get_buy_first_fnt(), self.iTrader.get_buy_second_fnt()],
                            self.iTrader.get_sell_fnt()))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        tradeComplTime = time.time()
                        self.my_sendmessage('새우방 글 감지에서 자동 매수 시도까지의 시간 차이{}초, 텔레그램 메세지 시간{}, 파이썬 시작시간{}, 파이썬 거래 종료 시간{}'.format(datetime.datetime.utcfromtimestamp(tradeComplTime) - gettingTime, gettingTime, datetime.datetime.utcfromtimestamp(tradeStartTime),
                                                                                                                                datetime.datetime.utcfromtimestamp(tradeComplTime)))
                        self.my_sendmessage('새우방에서 받은 아래와 같은 메세지에 대해 {}를 매수하는데 {}거래소에서는 거래하지 않습니다.\n\n{}'.format(filter_result[0], filter_result[1], message))
                        self.iCSVHandler.write_ourData(filter_result[0], filter_result[1], message, self.iTrader, filter_result[2])
                        numChannelPeriod = self.numChannelPeriod + 1
                    else:
                        if filter_result[2] == -2:
                            self.my_sendmessage("---새우배로부터--- 아래와 같은 메세지를 받았습니다. 하지만 메세지에서 의미있는 코인을 추출하지 못해서 거래하지 않습니다. 걸린 시간 {}초 \n\n{}".format(datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message))
                        elif filter_result[2] == -3:
                            self.my_sendmessage("---새우배로부터--- 아래와 같은 메세지를 받았습니다. 하지만 메세지에서 {}이 과거에 {} 거래소에서 상장됐던 코인이라 거래하지 않습니다. 걸린 시간 {}초 \n\n{}".format(filter_result[0], filter_result[1], datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message))
                        elif filter_result[2] == -4:
                            self.my_sendmessage("---새우배로부터--- 아래와 같은 메세지를 받았습니다. 하지만 스코어가 작아서 거래하지 않습니다. 걸린 시간 {}초 \n\n{}".format(datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message))
                    return message

                elif update.is_channel and update.original_update.message.to_id.channel_id == 1267236509 and not self.channelBlock:  # 새우 channel_id=1379897604, 앞에 original은 수신자 정보 뒤에 message는 발신자 정보
                    # 새우방에 '아무나 올린' 글
                    gettingTime = update.original_update.message.date
                    tradeStartTime = time.time()
                    print('상장감시봇 입니다')
                    print(update.original_update.message.to_id.channel_id)
                    print(update.original_update.message.message)
                    message = update.original_update.message.message

                    filter_result = self.iParser.filter_sgb(message, self.iTrader.pastListedDict, self.iTrader.tradeDict)
                    print(filter_result)
                    if (filter_result[0] != -1) and (self.numChannelPeriod <= self.iConstant_data.possibleChannelNum):
                        t1 = threading.Thread(target=self.iTrader.buy_sell_nonStop_anywhere_exce, args=(
                            filter_result[0], min(0.6, 0.5 * filter_result[2] / 10.), 1, filter_result[1], self.iConstant_data.waitforselling, 0.8, 'writing', True, [self.iTrader.get_buy_first_fnt(), self.iTrader.get_buy_second_fnt()],
                            self.iTrader.get_sell_fnt()))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        tradeComplTime = time.time()
                        self.my_sendmessage('상장감시봇 글 감지에서 자동 매수 시도까지의 시간 차이{}초, 텔레그램 메세지 시간{}, 파이썬 시작시간{}, 파이썬 거래 종료 시간{}'.format(datetime.datetime.utcfromtimestamp(tradeComplTime) - gettingTime, gettingTime, datetime.datetime.utcfromtimestamp(tradeStartTime),
                                                                                                                                  datetime.datetime.utcfromtimestamp(tradeComplTime)))
                        self.my_sendmessage('상장감시봇에서 받은 아래와 같은 메세지에 대해 {}를 매수하는데 {}거래소에서는 거래하지 않습니다.\n\n{}'.format(filter_result[0], filter_result[1], message))
                        self.iCSVHandler.write_ourData(filter_result[0], filter_result[1], message, self.iTrader, filter_result[2])
                        numChannelPeriod = self.numChannelPeriod + 1
                    else:
                        if filter_result[2] == -2:
                            self.my_sendmessage("---상장감시봇으로부터--- 아래와 같은 메세지를 받았습니다. 하지만 메세지에서 의미있는 코인을 추출하지 못해서 거래하지 않습니다. 걸린 시간 {}초 \n\n{}".format(datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message))
                        elif filter_result[2] == -3:
                            self.my_sendmessage("---상장감시봇으로부터--- 아래와 같은 메세지를 받았습니다. 하지만 메세지에서 추출된 코인이 과거에 해당 거래소에서 상장됐던 코인이라 거래하지 않습니다. 걸린 시간 {}초 \n\n{}".format(datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message))
                        elif filter_result[2] == -4:
                            self.my_sendmessage("---상장감시봇으로부터--- 아래와 같은 메세지를 받았습니다. 하지만 스코어가 작아서 거래하지 않습니다. 걸린 시간 {}초 \n\n{}".format(datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message))
                    return message


                elif update.is_private and update.message.from_id == self.chat_id and update.original_update.message.to_id.user_id == self.toID:
                    # mylist 또는 test방에서(toID에 의해 결정) '내가' 쓴 글
                    print(update.message.message.split(' '))
                    message = update.message.message.split(' ')

                    if message[0] == '/stat':
                        # my_sendmessage(chat_id, "거래 리스트는 {}입니다. ".format(tradeDict))
                        # self.my_sendmessage("Trade_dict : {}".format(self.iTrader.tradeDict))
                        self.my_sendmessage(self.iTrader.tradeDict_to_str())

                    elif message[0] == '/clstat':
                        tradeDict = {}
                        # my_sendmessage(chat_id, "거래리스트가 초기화 되었습니다.{} ".format(tradeDict))
                        self.my_sendmessage("Trade_dict is initialized : {} ".format(self.iTrader.tradeDict))

                    elif message[0] == '/fb':
                        if len(message) == 1:
                            if len(self.fbLst) < 4:
                                self.fbLst.append([self.iChangeable_data.seconds, self.iMarket.get_balance(self.iLogHandler)])
                            else:
                                del self.fbLst[0]
                                self.fbLst.append([self.iChangeable_data.seconds, self.iMarket.get_balance(self.iLogHandler)])
                            # my_sendmessage(chat_id, '나의 자산은 추이는 다음과 같습니다: \n{}'.format(fbLst))
                            self.my_sendmessage('My asset history is : \n{}'.format(self.fbLst))
                        elif len(message) == 2:
                            resultDict = self.iMarket.get_balance(self.iLogHandler, targetSym=message[1])
                            self.my_sendmessage('You have {}:\n\t\t{}'.format(message[1], resultDict))

                    elif message[0] == '/exit':
                        # my_sendmessage(chat_id, '프로그램을 종료합니다.')
                        self.my_sendmessage('Kill program running')
                        self.kill = True

                    elif message[0] == '/cas':
                        self.iTrader.canceledSellingLst.append(message[1].upper())
                        self.my_sendmessage('{}의 자동매도를 1회 취소합니다.'.format(message[1].upper()))
                    
                    elif message[0] == '/icas' and len(message)==2:
                        self.iTrader.instantCancelSymbolLst.append(message[1].upper())
                        self.my_sendmessage(
                            '{} is appended to instantCancelSymbolLst'.format(message[1].upper()))

                    elif message[0] == '/sc':
                        self.channelBlock = True
                        self.my_sendmessage('채널들에서 오는 메세지에 대해 자동매수를 하지 않습니다. /fc로 해제하기 전까지')

                    elif message[0] == '/fc':
                        self.channelBlock = False
                        self.my_sendmessage('채널들에서 오는 메세지에 대해 자동매수를 수행합니다')

                    elif message[0] == '/aol':
                        coin = message[1].upper()
                        market = message[2].lower()
                        if market not in self.iTrader.pastListedDict.keys():
                            self.iTrader.pastListedDict[market] = [coin]
                        else:
                            self.iTrader.pastListedDict[market].append(coin)
                        self.iCSVHandler.write_ourData(coin, market, "No text", self.iTrader)
                        self.my_sendmessage('{} 거래소에서 {}의 상장이 감지되더라도 자동거래하지 않습니다.'.format(market, coin))

                    elif message[0] == '/prd':
                        if len(message) == 3:
                            if message[2] == 'binance':
                                current, predict = self.iPredictor.get_current_predict_price(message[1], self.iMarket.binance_ccxt, 60, start_min=0)
                                self.my_sendmessage('Currency pair: {}, Market: {}, current : {}, predicted : {}'.format(message[1], message[2], current, predict))
                            elif message[2] == 'bittrex':
                                current, predict = self.iPredictor.get_current_predict_price(message[1], self.iMarket.bittrex_ccxt, 60, start_min=0)
                                self.my_sendmessage('Currency pair: {}, Market: {}, current : {}, predicted : {}'.format(message[1], message[2], current, predict))
                            elif message[2] == 'okex':
                                current, predict = self.iPredictor.get_current_predict_price(message[1], self.iMarket.okexCcxt, 60, start_min=0)
                                self.my_sendmessage('Currency pair: {}, Market: {}, current : {}, predicted : {}'.format(message[1], message[2], current, predict))
                            elif message[2] == 'gateio':
                                current, predict = self.iPredictor.get_current_predict_price(message[1], self.iMarket.gateioCcxt, 60, start_min=0)
                                self.my_sendmessage('Currency pair: {}, Market: {}, current : {}, predicted : {}'.format(message[1], message[2], current, predict))
                            elif message[2] == 'huobi':
                                current, predict = self.iPredictor.get_current_predict_price(message[1], self.iMarket.huobiCcxt, 60, start_min=0)
                                self.my_sendmessage('Currency pair: {}, Market: {}, current : {}, predicted : {}'.format(message[1], message[2], current, predict))
                            elif message[2] == 'kucoin':
                                current, predict = self.iPredictor.get_current_predict_price( message[1], self.iMarket.kucoinCcxt, 60, start_min=0)
                                self.my_sendmessage('Currency pair: {}, Market: {}, current : {}, predicted : {}'.format(message[1], message[2], current, predict))
                            elif message[2] == 'hitbtc':
                                current, predict = self.iPredictor.get_current_predict_price(message[1], self.iMarket.hitbtcCcxt, 60, start_min=0)
                                self.my_sendmessage('Currency pair: {}, Market: {}, current : {}, predicted : {}'.format(message[1], message[2], current, predict))
                            else:
                                self.my_sendmessage('Wrong market name, type /prd Currency_pair Market, \nmarket name should be in : binance, bittrex, okex, gateio, huobi, kucoin, hitbtc')
                        elif len(message) == 2:
                            for market in self.iMarket.marketsCcxt:
                                current, predict = self.iPredictor.get_current_predict_price(message[1], market, 60, start_min=0)
                                self.my_sendmessage('Currency pair: {}, Market: {}, current : {}, predicted : {}'.format(message[1], market.id, current, predict))
                        else:
                            self.my_sendmessage('Wrong number of arguments, type /prd Currency_pair Market')

                    elif message[0] == '/bs':
                        if len(message) == 2:
                            t1 = threading.Thread(target=self.iTrader.buy_sell_nonStop_anywhere_exce, args=(message[1].upper(), self.iConstant_data.marketpt, 1, 'no exception', self.iConstant_data.waitforselling, self.iConstant_data.sellingrate, 'not writing', False, [self.iTrader.get_buy_first_fnt(), self.iTrader.get_buy_second_fnt()],
                                                                                                            self.iTrader.get_sell_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                        elif len(message) == 3:
                            t1 = threading.Thread(target=self.iTrader.buy_sell_nonStop_anywhere_exce, args=(
                                message[1].upper(), float(message[2]), 1, 'no exception', self.iConstant_data.waitforselling, self.iConstant_data.sellingrate, 'not writing', False, [self.iTrader.get_buy_first_fnt(), self.iTrader.get_buy_second_fnt()],
                                self.iTrader.get_sell_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                        elif len(message) == 4:
                            t1 = threading.Thread(target=self.iTrader.buy_sell_nonStop_anywhere_exce, args=(
                                message[1].upper(), float(message[2]), int(message[3]), 'no exception', self.iConstant_data.waitforselling, self.iConstant_data.sellingrate, 'not writing', False, [self.iTrader.get_buy_first_fnt(), self.iTrader.get_buy_second_fnt()],
                                self.iTrader.get_sell_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                        elif len(message) == 5:
                            t1 = threading.Thread(target=self.iTrader.buy_sell_nonStop_anywhere_exce, args=(
                                message[1].upper(), float(message[2]), int(message[3]), message[4], self.iConstant_data.waitforselling, self.iConstant_data.sellingrate, 'not writing', False, [self.iTrader.get_buy_first_fnt(), self.iTrader.get_buy_second_fnt()],
                                self.iTrader.get_sell_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()

                    elif message[0] == '/b':
                        if len(message) == 2:
                            t1 = threading.Thread(target=self.iTrader.anywhere_nonStop_exce, args=('no exception', message[1].upper(), self.iConstant_data.marketpt, 1, self.iConstant_data.tries, *self.iTrader.get_buy_first_fnt(), *self.iTrader.get_buy_second_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                        elif len(message) == 3:
                            t1 = threading.Thread(target=self.iTrader.anywhere_nonStop_exce, args=('no exception', message[1].upper(), float(message[2]), 1, self.iConstant_data.tries, *self.iTrader.get_buy_first_fnt(), *self.iTrader.get_buy_second_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                        elif len(message) == 4:
                            t1 = threading.Thread(target=self.iTrader.anywhere_nonStop_exce, args=('no exception', message[1].upper(), float(message[2]), int(message[3]), self.iConstant_data.tries, *self.iTrader.get_buy_first_fnt(), *self.iTrader.get_buy_second_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                        elif len(message) == 5:
                            t1 = threading.Thread(target=self.iTrader.anywhere_nonStop_exce, args=(message[4], message[1].upper(), float(message[2]), int(message[3]), self.iConstant_data.tries, *self.iTrader.get_buy_first_fnt(), *self.iTrader.get_buy_second_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()

                    elif message[0] == '/s':
                        if len(message) == 2:
                            t1 = threading.Thread(target=self.iTrader.anywhere_nonStop_exce, args=('no exception', message[1].upper(), self.iConstant_data.marketpt, 1, self.iConstant_data.tries, *self.iTrader.get_sell_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                        elif len(message) == 3:
                            t1 = threading.Thread(target=self.iTrader.anywhere_nonStop_exce, args=('no exception', message[1].upper(), float(message[2]), 1, self.iConstant_data.tries, *self.iTrader.get_sell_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                        elif len(message) == 4:
                            t1 = threading.Thread(target=self.iTrader.anywhere_nonStop_exce, args=('no exception', message[1].upper(), float(message[2]), int(message[3]), self.iConstant_data.tries, *self.iTrader.get_sell_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                        elif len(message) == 5:
                            t1 = threading.Thread(target=self.iTrader.anywhere_nonStop_exce, args=(message[4], message[1].upper(), float(message[2]), int(message[3]), self.iConstant_data.tries, *self.iTrader.get_sell_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()

                    elif message[0] == '/stest' and len(message) == 3:
                        # 새우방에 '아무나 올린' 글
                        gettingTime = update.original_update.message.date
                        tradeStartTime = time.time()
                        print('This is Shirimp Test.')

                        filter_result = self.iParser.filter_saewoo(message[1], self.iTrader.pastListedDict, self.iTrader.tradeDict)
                        print(filter_result)
                        if (filter_result[0] != -1) and (self.numChannelPeriod <= self.iConstant_data.possibleChannelNum) and self.iConstant_data.test_mode:
                            t1 = threading.Thread(target=self.iTrader.buy_sell_nonStop_anywhere_exce, args=(
                                filter_result[0], min(0.6, 1.8 * filter_result[2] / 10.), 1, filter_result[1], self.iConstant_data.waitforselling, 0.8, 'no writing', True, [self.iTrader.get_buy_first_fnt(), self.iTrader.get_buy_second_fnt()],
                                self.iTrader.get_sell_fnt()))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                            tradeComplTime = time.time()
                            self.my_sendmessage('새우방 글 감지에서 자동 매수 시도까지의 시간 차이{}초, 텔레그램 메세지 시간{}, 파이썬 시작시간{}, 파이썬 거래 종료 시간{}'.format(datetime.datetime.utcfromtimestamp(tradeComplTime) - gettingTime, gettingTime, datetime.datetime.utcfromtimestamp(tradeStartTime),
                                                                                                                                    datetime.datetime.utcfromtimestamp(tradeComplTime)))
                            self.my_sendmessage('새우방에서 받은 아래와 같은 메세지에 대해 {}를 매수하는데 {}거래소에서는 거래하지 않습니다.\n\n{}'.format(filter_result[0], filter_result[1], message[1]))
                            if int(message[2]):
                                self.iCSVHandler.write_ourData(filter_result[0], filter_result[1], message[1], self, filter_result[2])
                            self.numChannelPeriod = self.numChannelPeriod + 1
                        else:
                            if not self.iConstant_data.test_mode:
                                self.my_sendmessage("This is Shrimp Test, but test_mode == False, thus do nothing. 걸린 시간 {}초 \n\n{}".format(datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message[1]))
                            elif filter_result[2] == -2:
                                self.my_sendmessage("---새우배로부터--- 아래와 같은 메세지를 받았습니다. 하지만 메세지에서 의미있는 코인을 추출하지 못해서 거래하지 않습니다. 걸린 시간 {}초 \n\n{}".format(datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message[1]))
                            elif filter_result[2] == -3:
                                self.my_sendmessage("---새우배로부터--- 아래와 같은 메세지를 받았습니다. 하지만 메세지에서 {}이 과거에 {} 거래소에서 상장됐던 코인이라 거래하지 않습니다. 걸린 시간 {}초 \n\n{}".format(filter_result[0], filter_result[1], datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message[1]))
                            elif filter_result[2] == -4:
                                self.my_sendmessage("---새우배로부터--- 아래와 같은 메세지를 받았습니다. 하지만 스코어가 작아서 거래하지 않습니다. 걸린 시간 {}초 \n\n{}".format(datetime.datetime.utcfromtimestamp(time.time()) - gettingTime, message[1]))

                        return message


            except (BrokenPipeError, IOError):
                self.my_sendmessage('BrokenPipeError occured, disconnet telethon and exit: {}'.format(traceback.format_exc()))
                self.client.disconnect()
                sys.stderr.close()
                sys.exit(1)
                # Exit only this thread? check it later..
            except Exception as ex:
                self.iLogHandler.saveException(ex)
                time.sleep(60)
                self.my_sendmessage('telethon_main 함수에서 다음 예외가 발생했습니다: {}'.format(traceback.format_exc()))

        # client = TelegramClient('../session', settings.telegramAPIID, settings.telegramAPIHash, update_workers=2)
        # print ('Telethon 사용자 계정 접속 상태 : ',client.connect())
        #
        # if not client.is_user_authorized():
        #     client.send_code_request(settings.phoneNumber)
        #     client.sign_in(settings.phoneNumber, input('Enter the code: '))
        self.client.add_event_handler(callback, events.NewMessage)  # events.NewMessage: 새로운 메세지 올때만, 수정되거나 지워지는거 감지 못함. Raw: 안에 중요한 것만 옴

