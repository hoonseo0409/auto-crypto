# -*- coding: utf-8 -*-

# Written by Hoon Seo, seohoon@mines.edu, with MIT license
# Tested on MacOSX, Pycharm, Python 3.6.4

import sys
# file_dir = os.path.dirname(__file__)
# sys.path.append(file_dir)
# print(sys.path)
# from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
# from telegram.ext.dispatcher import run_async
from telethon import TelegramClient, events, tl
import settings
from selenium import webdriver
# from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
# from binance.client import Client
from telegram import Bot
import requests, os, re, hashlib, hmac, datetime, random, time, threading, subprocess, csv, copy, traceback, logging
from bittrex.bittrex import *
from HuobiUtil import *
from bittrexV2 import *
import ccxt
import importlib
import asyncio
import signs_dict
from keras.models import model_from_json
import preprocessing
from numpy import array
import CSVHandler, LogHandler, MessageHandler, Utils, Market, Parser, Trader, Predictor, Meta_data

test_mode = True

print(settings.__file__)


importlib.reload(sys)
# sys.setdefaultencoding('utf-8')

kill=0

iLogHandler = LogHandler.LogHandler("my", '../my.log')

# Load saved model
json_file = open('./best_model/best_model.json', 'r')
loaded_model_json = json_file.read()
loaded_model = model_from_json(loaded_model_json)
# Load weights
loaded_model.load_weights("./best_model/best_model_weights.h5")
loaded_model._make_predict_function()
print('Prediction model is loaded from disk')

marketpt = 0.2 #투자 비중의 기본값
waitforselling = 600  # 매수후 절반을 매도하기까지 기다리는 시간 단위는 초
tries=1
sellingrate=0.8
standardBTC=1
similimit=0.92
possibleChannelNum = 5
reduceShirimpPeriod = 300

avoid = ['ETH', 'BTC', 'SMS', 'GAS', 'PRO', 'VISA', 'ICO', 'USD', 'KRW', 'ERC', 'STO', 'ADD', 'PC',
         'BNB', 'API', 'KST', 'FAQ', 'QNA', 'USDT', 'HADAX', 'OPEN', 'AWS', 'TOP', 'PORTAL', 'HADAX',
         'EURS', 'R', 'USD', 'XRP']

iConstant_data = Meta_data.Constant_data(test_mode = test_mode, marketpt = marketpt, waitforselling = waitforselling,
                                             tries = tries, sellingrate = sellingrate, standardBTC = standardBTC, similimit = similimit,
                                             possibleChannelNum = possibleChannelNum, reduceShirimpPeriod = reduceShirimpPeriod,
                                             avoid = avoid)
iChangeable_data = Meta_data.Changeable_data()

canceledSellingLst=[]
validCurrencies = []
fbLst = []

seconds = 0

chat_id = settings.chat_id  # 각자 id 기입
jugiChatId = settings.jugiChatId
iCSVHandler = CSVHandler.CSVHandler()
pastListedDict = iCSVHandler.get_pastListedDict('./data/ourData.csv')

print (pastListedDict)

iParser = Parser.Parser(settings, iLogHandler, iConstant_data)

if test_mode:
    iMessageHandler = MessageHandler.MessageHandler(settings.my_test_token, settings.testToID, settings.chat_id,
                                                    settings.telegramAPIID, settings.telegramAPIHash, settings.phoneNumber, iLogHandler, iConstant_data,
                                                    iParser, iCSVHandler, iChangeable_data)
else:
    iMessageHandler = MessageHandler.MessageHandler(settings.my_token, settings.actualToID, settings.chat_id,
                                                    settings.telegramAPIID, settings.telegramAPIHash, settings.phoneNumber, iLogHandler, iConstant_data,
                                                    iParser, iCSVHandler, iChangeable_data)

iMarket = Market.Market(settings, iLogHandler, iMessageHandler)
iMarket.loadMarkets()
iMessageHandler.set_Market(iMarket)
iParser.set_iMessageHandler(iMessageHandler)

iPredictor = Predictor.Predictor(loaded_model, iMarket)

Trader.marketpt = marketpt
Trader.Trader.test_mode = test_mode
iTrader = Trader.Trader(settings, iMessageHandler, iLogHandler, iMarket, iPredictor, iCSVHandler, pastListedDict)
iMessageHandler.set_Trader(iTrader)
iParser.set_iTrader(iTrader)

iMessageHandler.set_Predictor(iPredictor)
iMessageHandler.set_client()

if test_mode:
    iConstant_data.waitforselling=1
    print ('This is test mode. Actual trading will not occur.')
    iMessageHandler.my_sendmessage('This is test mode. Actual trading will not occur.')
else:
    print ('This is actual mode. Actual trading will occur.')
    iMessageHandler.my_sendmessage('This is actual mode. Actual trading will occur.')


def anywhere(coin, marketpt=marketpt, standardBTC=1, tries=tries, *args):
    try:
        result=-1
        tmp=0
        while(tmp<tries):
            #my_sendmessage(chat_id, '{}회째 거래를 시도합니다.'.format(tmp+1))
            tmp=tmp+1
            for func in args:
                result=func(coin, marketpt, standardBTC)
                if result!=-1:
                    return 1
            time.sleep(0.5)
        return -1
    except Exception as ex:
        iMessagehandler.my_sendmessage(chat_id, 'anywhere 함수에서 다음과 같은 예외가 발생했습니다:{}'.format(traceback.format_exc(limit=1)))
        return -1

def buy_sell_anywhere(coin, marketpt=marketpt, standardBTC=1, tries=tries, waitforselling=waitforselling, sellingrate=sellingrate,  *args):
    try:
        NoMarket=len(args)
        result=-1
        result2=-1
        tmp=0
        for x in range(tries):
            for i in range(NoMarket):
                result=anywhere(coin, marketpt, standardBTC=standardBTC, tries=1, *[args[i][0]])
                if result != -1:
                    my_sendmessage(chat_id, '매도를 위해 {}초간 대기합니다.'.format(waitforselling))
                    time.sleep(waitforselling)
                    if coin in canceledSellingLst:
                        my_sendmessage(chat_id, '{}는 취소요청한 코인 목록에 있어서 자동매도를 취소합니다.'.format(coin))
                        canceledSellingLst.remove(coin)
                        return 1
                    else:
                        my_sendmessage(chat_id, '매도를 위한 {}초간의 대기가 끝났습니다. 매도를 시작합니다.'.format(waitforselling))
                        for tr in range(tries):
                            result2=anywhere(coin, marketpt*sellingrate, standardBTC=standardBTC, tries=1, *[args[i][1]])
                            if result2 != -1:
                                return 1
                    return -1
            time.sleep(0.5)
        return -1
    except:
        my_sendmessage(chat_id, 'buy_sell_anywhere 함수에서 다음과 같은 예외가 발생했습니다:{}'.format(traceback.format_exc(limit=1)))
        return -1

def anywhere_exce(exce, coin, marketpt = marketpt, standardBTC = 1, tries = tries, *args):
    try:
        result=-1
        tmp=0
        while(tmp<tries):
            #my_sendmessage(chat_id, '{}회째 거래를 시도합니다.'.format(tmp+1))
            tmp=tmp+1
            for func in args:
                if exce not in func.__name__:
                    result=func(coin, marketpt, standardBTC)
                    if result!=-1:
                        return 1
            time.sleep(0.5)
        return -1
    except Exception as ex:
        # my_sendmessage(chat_id, 'anywhere 함수에서 다음과 같은 예외가 발생했습니다:{}'.format(traceback.format_exc(limit=1)))
        return -1

############################################## crawler start ##############################################
def crawler_api_binance():
    before=[]
    # print (binance_client.get_account()['balances'][0]['asset'])
    balances=binance_wallet_client.get_account()['balances']
    alpha=0
    for coin in balances:
        before.append(coin['asset'])
    start = copy.deepcopy(before)
    time.sleep(31)
    epoch=1
    while(1):
        now = []
        if epoch%10 == 1:
            print ('crawler_api_binance가 {}번 api에 요청했습니다.'.format(epoch))
            if alpha>0:
                alpha-=1
        epoch+=1
        try:
            balances=binance_wallet_client.get_account()['balances']
            for coin in balances:
                now.append(coin['asset'])
            for coin in now:
                if (coin not in before) and (coin not in start) and ('binance' not in pastListedDict.keys() or coin not in pastListedDict['binance']):
                    print(now)
                    print(before)
                    t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(coin, marketpt, 1, 'binance', 600,0.6,'writing', True, [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                    t1.daemon = True
                    t1.start()
                    my_sendmessage(chat_id, 'binance api 지갑에서 {}가 상장된 것을 감지하여 자동매수매도를 시작합니다.'.format(coin))
                    time.sleep(2)
                    start = copy.deepcopy(now)
                    write_ourData(coin, 'binance')
            before = copy.deepcopy(now)
            time.sleep(21+alpha)
        except Exception as ex:
            myLogger.error(ex, exc_info=True)
            my_sendmessage(chat_id, 'crawler_api_binance에서 다음과 같은 예외가 발생했습니다.\n\n{}'.format(traceback.format_exc(limit=1)))
            time.sleep(random.randrange(140,180)+alpha*7)
            alpha+=3



def crawler_browser_okcoin():
    alpha=0

    opt = webdriver.ChromeOptions()
    opt.add_extension(settings.imgBlockLocation)
    prefs = {"profile.managed_default_content_settings.images": 2}
    # prefs = {"profile.managed_default_content_settings.images": 2, 'profile':{}}
    # prefs['profile']['default_content_setting_values'] = {"popups": 2}
    opt.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(executable_path=settings.chrome_location, chrome_options=opt)

    driver.get("https://www.okcoinkr.com/account/login?forward=/spot/trade")
    driver.implicitly_wait(60)
    driver.find_element_by_name('username').send_keys('seohoon0409@gmail.com')
    driver.find_element_by_name('password').send_keys(settings.okCoin_ps)
    driver.find_element_by_xpath('//*[@id="loginBox"]/button[1]').click()

    before = []
    arr = driver.find_element_by_xpath('//*[@id="app"]/div/div[2]/div/div/div[1]/div[1]/div[2]/ul/div').text.split('\n')
    for real in arr:
        if 'KRW' in real:
            before.append(str(real[0:-4]))
    del arr
    j=1
    while(1):
        driver.get("https://www.okcoinkr.com/account/login?forward=/spot/trade")
        driver.implicitly_wait(60)
        if j%10==1:
            print ('ok coin {}번 페이지 요청함.'.format(j))
            if alpha>0:
                alpha-=1
        j=j+1
        now=[]
        try:
            arr = driver.find_element_by_xpath('//*[@id="app"]/div/div[2]/div/div/div[1]/div[1]/div[2]/ul/div').text.split('\n')
            for real in arr:
                if 'KRW' in real:
                    now.append(str(real[0:-4]))
            for coin in now:
                if (coin not in before)and ('okcoin' not in pastListedDict.keys() or coin.upper() not in pastListedDict['okcoin']):
                    t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(coin, marketpt*0.7, 1, 'no exception', 240,0.8,'writing', True, [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                    t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                    t1.start()
                    write_ourData(coin.upper(), 'okcoin')
                    my_sendmessage(chat_id, 'https://www.okcoinkr.com/account/login?forward=/spot/trade 에서 {}가 상장된 것을 감지하여 자동매수매도를 시작합니다. url: https://www.okcoinkr.com/account/login?forward=/spot/trade'.format(coin))
            before = copy.deepcopy(now)
            time.sleep(random.randrange(15, 89)+alpha)

        except Exception as ex: #okcoin은 일정 시간 지나면 로그인이 풀려서 XPath로 대상 못 찾는 예외 발생한다. 그 경우를 대비한 코드
            # my_sendmessage(chat_id=chat_id, text="crawler_browser_okcoin 함수에서 {} 인 예외가 발생하였습니다.".format(ex))
            alpha+=3
            while(1):
                try:
                    driver.get("https://www.okcoinkr.com/account/login?forward=/spot/trade")
                    driver.implicitly_wait(60)
                    driver.find_element_by_name('username').send_keys('hhoon0002@naver.com')
                    driver.find_element_by_name('password').send_keys(settings.okCoin_ps)
                    time.sleep(random.randrange(9, 12))
                    driver.find_element_by_xpath('//*[@id="loginBox"]/button[1]').click()
                    driver.implicitly_wait(20)

                    driver.get("https://www.okcoinkr.com/account/login?forward=/spot/trade")
                    driver.implicitly_wait(60)
                    print ('ok coin {}바퀴'.format(j))
                    j = j + 1
                    now = []
                    arr = driver.find_element_by_xpath('//*[@id="app"]/div/div[2]/div/div/div[1]/div[1]/div[2]/ul/div').text.split('\n')
                    for real in arr:
                        if 'KRW' in real:
                            now.append(str(real[0:-4]))

                    for coin in now:
                        if (coin not in before)and ('okcoin' not in pastListedDict.keys() or coin.upper() not in pastListedDict['okcoin']):
                            # global trade_number
                            # trade_number = trade_number + 1
                            t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(coin, marketpt*0.7,1, 'no exception', 240, 0.8,'writing', True, [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                            my_sendmessage(chat_id,'https://www.okcoinkr.com/account/login?forward=/spot/trade 에서 {}가 상장된 것을 감지하여 자동매수매도를 시작합니다. url: https://www.okcoinkr.com/account/login?forward=/spot/trade'.format(coin))
                            write_ourData(coin.upper(), 'okcoin')
                    before = copy.deepcopy(now)
                    time.sleep(random.randrange(180, 240) + alpha)
                    break
                except Exception as ex:
                    myLogger.error(ex, exc_info=True)
                    alpha+=3
                    driver.get("https://www.naver.com/")
                    time.sleep(random.randrange(140,180)+alpha*7)
                    print (traceback.format_exc(limit=1))
                    # my_sendmessage(chat_id=chat_id, text="crawler_browser_okcoin 함수에서 {} 인 예외가 발생하였습니다.".format(ex))
                    pass



def crawler_noticeBithumbPro_rightNoticeBithumb():
    alpha = 0

    # 빗썸 오른쪽 공지 사전 준비
    rnEpoch = 1
    opt = webdriver.ChromeOptions()
    opt.add_extension(settings.imgBlockLocation)
    prefs = {"profile.managed_default_content_settings.images": 2}
    opt.add_experimental_option("prefs", prefs)
    # opt.add_argument("--disable-javascript")
    opt.add_argument("start-maximized")
    # opt.add_argument("enable-popup-blocking")

    driver = webdriver.Chrome(settings.chrome_location, chrome_options=opt)
    # driver.maximize_window()
    driver.refresh()  # 크롬에서는 새로고침 하면 웹창의 뜨는 위치가 바뀌게 돼서 한번 리프레쉬 해주고 시작해야 깔끔하다.
    driver.get('http://bithumb.cafe/')
    # driver.implicitly_wait(60) # for문에서 오류나서 일단 비활성화 해놈
    rnBefore = driver.find_element_by_xpath('//*[@id="sidebar"]/aside/ul/li[1]/div/div/h5/a').text  # li[1]로 해야 정상
    rnNew = []

    # 여기부터는 빗썸프로 사전 준비
    time.sleep(2)
    for hi in range(5):
        try:
            driver.get("https://bithumbpro.com/")
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[2]/div[5]/div/div/div/div/div[2]/div[1]/div/div/div[1]/div")))

            #  아래가 추가내용 (팝업 하루안보기버튼 및 끄기버튼 클릭 추가)
            body_numb = 11   #9부터 감시 시작
            for i in range(4):  # 팝업 최대 연속 4개까지만 고려. 역순으로 찾아 내려가면서 모두 끌 때까지 실행됨.
                try:
                    body_numb -= 2
                    gongzi = driver.find_element_by_xpath(
                        '/ html / body / div[' + str(body_numb) + ']')  # 여기까지 무사히 내려왔다면 해당 body_numb가 존재한다는 증거

                    gongzi_location = gongzi.location  # 공지가 뜬 xpath의 위치를 읽은 후
                    gongzi_location_x = gongzi_location['x']  # x좌표와 y좌표의 value를 읽는다.
                    gongzi_location_y = gongzi_location['y']

                    gongzi_size = gongzi.size  # 공지가 뜬 xpath의 크기
                    gongzi_size_x = gongzi_size['width']  # 크기 또한 x와 y의 수치로 표현한다.
                    gongzi_size_y = gongzi_size['height']
                    time.sleep(0.5)  # 반드시 있어야만 한다. 안그러면 오류가 난다. 꼭 0.5초일 필요는 없다.
                    ActionChains(driver).move_by_offset(gongzi_location_x + 72,
                                                        gongzi_location_y + gongzi_size_y - 23).click().move_by_offset(
                        -72 + gongzi_size_x - 34, 0).click().perform()
                    ActionChains(driver).move_by_offset(-(gongzi_location_x + gongzi_size_x - 34),
                                                        -(gongzi_location_y + gongzi_size_y - 23)).perform()
                    # ActionChains(driver).reset_actions().perform() 먹히지 않음, 따라서 이동한 양을 다시 수동으로 돌려준다.


                except NoSuchElementException:
                    pass

            # 위가 추가내용

            bpBefore = driver.find_element_by_xpath(
                "/html/body/div[2]/div[5]/div/div/div/div/div[2]/div[1]/div/div/div[1]/div").text  # 공지 팝업이 떠있어도 읽어진다.
            break
        except NoSuchElementException:
            time.sleep(5)

    bpEpoch = 0
    bpNew = []

    while (1):
        try:
            # 빗썸프로 공지 크롤러 시작

            bpEpoch += 1
            if bpEpoch % 10 == 1:
                print('https://bithumbpro.com/로 {}번 페이지를 요청하였습니다.'.format(bpEpoch))
                if alpha > 0:
                    alpha -= 0.075
            driver.get("https://bithumbpro.com/")
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                (By.XPATH,
                 "/html/body/div[2]/div[5]/div/div/div/div/div[2]/div[1]/div/div/div[1]/div")))  # @@@@@@@@@@@@@@@@@@@@@@@@@@@@ 추가함
            # driver.implicitly_wait(60) # @@@@@@@@@@@@@@@@@@@@@@@@@@@@ for문에서 오류나서 일단 비활성화 해놈
            # print(len(driver.window_handles))
            # driver.switch_to.frame(1)
            # driver.find_element_by_xpath('//*[@id="1526010652373--lbClose"]').click()
            bpNow = driver.find_element_by_xpath(
                "/html/body/div[2]/div[5]/div/div/div/div/div[2]/div[1]/div/div/div[1]/div").text  # 공지 팝업이 떠있어도 읽어진다.
            if (bpNow != bpBefore):
                was_there = 0
                bpNew.append(bpBefore)

                for notice in bpNew:
                    if str_foinback(bpNow, notice) > similimit:
                        was_there = 1

                if was_there == 0 and scoring_signsDict(bpNow,
                                                        bithumbSubjectSignsDict) >= 1.:
                    sjSymbol = get_symbol(bpNow)

                    try:
                        # 아래가 수정 및 추가내용
                        # time.sleep(0.2)  # 오버레이 차단 프로그램 때문에 줬던 시간인데, 제거함
                        driver.find_element_by_xpath(
                            "/html/body/div[2]/div[5]/div/div/div/div/div[2]/div[1]/div/div/div[1]/div").click()  # 이제는 실제로 클릭을 하자
                        WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                            (By.XPATH, "/ html / body / div[3]")))  # 해당 xpath가 뜨기를 기다리자
                        time.sleep(0.2)  # 여기가 0.2였는데 위에서 시간을 쓰는 바람에 좀 줄여봄...
                        content = driver.find_element_by_xpath(
                            "/ html / body / div[3]").text  # 오버레이 차단 프로그램 안써서 xpath가 불변
                        ctSymbol = get_symbol(content)

                    except NoSuchElementException:
                        try:
                            body_numb = 11
                            for i in range(4):  # 팝업 최대 연속 4개까지만 고려. 역순으로 찾아 내려가면서 모두 끌 때까지 실행됨.
                                try:
                                    body_numb -= 2  # body 9부터 감시 시작
                                    gongzi = driver.find_element_by_xpath(
                                        '/ html / body / div[' + str(
                                            body_numb) + ']')  # 여기까지 무사히 내려왔다면 해당 body_numb가 존재한다는 증거

                                    gongzi_location = gongzi.location  # 공지가 뜬 xpath의 위치를 읽은 후
                                    gongzi_location_x = gongzi_location['x']  # x좌표와 y좌표의 value를 읽는다.
                                    gongzi_location_y = gongzi_location['y']

                                    gongzi_size = gongzi.size  # 공지가 뜬 xpath의 크기
                                    gongzi_size_x = gongzi_size['width']  # 크기 또한 x와 y의 수치로 표현한다.
                                    gongzi_size_y = gongzi_size['height']
                                    time.sleep(0.5)  # 반드시 있어야만 한다. 안그러면 오류가 난다. 꼭 0.5초일 필요는 없다.
                                    ActionChains(driver).move_by_offset(gongzi_location_x + 72,
                                                                        gongzi_location_y + gongzi_size_y - 23).click().move_by_offset(
                                        -72 + gongzi_size_x - 34, 0).click().perform()
                                    ActionChains(driver).move_by_offset(-(gongzi_location_x + gongzi_size_x - 34),
                                                                        -(
                                                                                gongzi_location_y + gongzi_size_y - 23)).perform()
                                    # ActionChains(driver).reset_actions().perform() 먹히지 않음, 따라서 이동한 양을 다시 수동으로 돌려준다.


                                except NoSuchElementException:
                                    pass

                            # time.sleep(0.2)  # 오버레이 차단 프로그램 때문에 줬던 시간인데, 제거함
                            driver.find_element_by_xpath(
                                "/html/body/div[2]/div[5]/div/div/div/div/div[2]/div[1]/div/div/div[1]/div").click()  # 이제는 실제로 클릭을 하자
                            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                                (By.XPATH, "/ html / body / div[3]")))  # 해당 xpath가 뜨기를 기다리자
                            time.sleep(0.2)  # 여기가 0.2였는데 위에서 시간을 쓰는 바람에 좀 줄여봄...
                            content = driver.find_element_by_xpath(
                                "/ html / body / div[3]").text  # 오버레이 차단 프로그램 안써서 xpath가 불변
                            ctSymbol = get_symbol(content)
                        #  위가 수정 및 추가내용
                        except:
                            ctSymbol = None

                    if sjSymbol != None and ('bithumb' not in pastListedDict.keys() or sjSymbol not in pastListedDict['bithumb']):
                        t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(
                        sjSymbol, marketpt, 1, 'no exception', 360, 0.5, 'writing', True,
                        [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        my_sendmessage(chat_id,
                                       'https://bithumbpro.com/ 에서 {}가 상장된 것을 감지하여 자동매수매도를 시작합니다. '.format(sjSymbol))
                        write_ourData(sjSymbol, 'bithumb')

                    elif ctSymbol != None and ('bithumb' not in pastListedDict.keys() or ctSymbol not in pastListedDict['bithumb']):
                        t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(
                        ctSymbol, marketpt / 1.3, 1, 'no exception', 360, 0.5, 'writing', True,
                        [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        my_sendmessage(chat_id,
                                       'https://bithumbpro.com/ {}가 상장된 것을 감지하여 자동매수매도를 시작합니다. '.format(ctSymbol))
                        write_ourData(ctSymbol, 'bithumb')

                    my_sendmessage(chat_id, 'https://bithumbpro.com/ 에 다음과 같은 제목의 공지사항이 추가됨.\n\n{}'.format(bpNow))


            bpBefore = copy.deepcopy(bpNow)
            time.sleep(random.randrange(5, 18) + alpha)
            bpEpoch = bpEpoch + 1

            # 빗썸 오른쪽 공지 크롤러 시작

            if rnEpoch % 10 == 1:
                print ('http://bithumb.cafe/로 {}번 페이지를 요청하였습니다.'.format(rnEpoch))
                if alpha > 0:
                    alpha -= 0.075
            driver.get('http://bithumb.cafe/')
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="sidebar"]/aside/ul/li[1]/div/div/h5/a')))
            rnNow = driver.find_element_by_xpath(
                '//*[@id="sidebar"]/aside/ul/li[1]/div/div/h5/a').text  # 글 제목은 팝업에 상관없이 텍스트를 잘 긁어옴
            if (rnNow != rnBefore) and (
                    rnBefore == driver.find_element_by_xpath('//*[@id="sidebar"]/aside/ul/li[2]/div/div/h5/a').text):
                was_there = 0
                rnNew.append(rnBefore)
                for notice in rnNew:
                    if str_foinback(rnNow, notice) > similimit:
                        was_there = 1
                if was_there == 0 and scoring_signsDict(rnNow,
                                                        bithumbSubjectSignsDict) >= 1.:

                    sjSymbol = get_symbol(rnNow)

                    driver.find_element_by_xpath(
                        '//*[@id="sidebar"]/aside/ul/li[1]/div/div/h5/a').click()  # 이제는 실제로 글 제목을 클릭해서 내용을 봐야한다.
                    WebDriverWait(driver, 60).until(EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="primary-left"]/article/div')))  # 내용에 해당하는 xpath가 뜨기를 기다리자
                    content = driver.find_element_by_xpath('//*[@id="primary-left"]/article/div').text

                    ctSymbol = get_symbol(content)

                    if sjSymbol != None and ('bithumb' not in pastListedDict.keys() or sjSymbol not in pastListedDict['bithumb']):
                        t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(
                        sjSymbol, marketpt, 1, 'no exception', 360, 0.5, 'writing', True,
                        [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        my_sendmessage(chat_id,
                                       'http://bithumb.cafe/ 에서 {}가 상장된 것을 감지하여 자동매수매도를 시작합니다. '.format(sjSymbol))
                        write_ourData(sjSymbol, 'bithumb')
                    elif ctSymbol != None and ('bithumb' not in pastListedDict.keys() or ctSymbol not in pastListedDict['bithumb']):
                        t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(
                        ctSymbol, marketpt / 1.3, 1, 'no exception', 360, 0.5, 'writing', True,
                        [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        my_sendmessage(chat_id, 'http://bithumb.cafe/ {}가 상장된 것을 감지하여 자동매수매도를 시작합니다. '.format(ctSymbol))
                        write_ourData(ctSymbol, 'bithumb')

                    my_sendmessage(chat_id=chat_id,
                                   text="http://bithumb.cafe/ 에서 상장감지\n\n 제목:{} \n\n 내용:{}".format(rnNow, content))

            rnBefore = copy.deepcopy(rnNow)
            time.sleep(random.randrange(5, 18) + alpha)
            rnEpoch = rnEpoch + 1
            # 빗썸 오른쪽 공지 크롤러 끝

        except Exception as ex:
            myLogger.error(ex, exc_info=True)
            alpha += 0.5
            time.sleep(random.randrange(20, 40)+alpha*2)
            driver.get('https://www.naver.com/')
            time.sleep(random.randrange(20, 40)+alpha*2)
            my_sendmessage(chat_id, 'crawler_noticebithumbpro_rightnoticebithumb에서 다음과 같은 예외가 발생하였습니다.\n\n{}'.format(
                traceback.format_exc(limit=1)))




def crawler_nextMobile_notice_bithumb():
    mobile_emulation = {
        "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
      "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"}
    chrome_options = Options()
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

    chrome_options.add_extension(settings.imgBlockLocation)
    prefs = {"profile.managed_default_content_settings.images": 2}
    # prefs = {"profile.managed_default_content_settings.images": 2, 'profile':{}}
    # prefs['profile']['default_content_setting_values'] = {"popups": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(executable_path=settings.chrome_location, chrome_options=chrome_options)
    while(1):
        try:
            driver.get("http://bithumb.cafe")
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="primary-left"]/div/article[1]/h3/a')))      #첫 번째 글이 뜰 때까지 기다린다.
            driver.find_element_by_xpath('//*[@id="primary-left"]/div/article[1]/h3/a').click()   #첫 번째 글을 클릭해 본다.
            before = driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd').text
            while (before != '다음글이 없습니다.'):
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="primary-left"]/div/dl[2]/dd/a')))
                driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd/a').click()  # 빗썸에서 글을 1번만 수정했을 경우
                before = driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd').text
            break
        except Exception as ex:
            try:
                print(ex)
                time.sleep(2)
                driver.find_element_by_xpath('//*[@id="popmake-13905"]/button').click()
                time.sleep(2)
                driver.find_element_by_xpath('//*[@id="primary-left"]/div/article[1]/h3/a').click()  # 첫 번째 글을 클릭해 본다.
                before = driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd').text
                while (before != '다음글이 없습니다.'):
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="primary-left"]/div/dl[2]/dd/a')))
                    driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd/a').click()  # 빗썸에서 글을 1번만 수정했을 경우
                    before = driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd').text
                break
            except Exception as ex:
                myLogger.error(ex, exc_info=True)
                driver.get("https://www.naver.com/")
                time.sleep(5)
    epoch = 1
    alpha = 0
    new = []
    while(1):
        try:
            if epoch % 10 == 1:
                print('빗썸 mobile 공지사항에서 {} 번 페이지를 요청하였습니다.'.format(epoch))
                if alpha > 0:
                    alpha -= 0.3
            driver.refresh()
            time.sleep(random.randrange(5, 18) + alpha)
            now = driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd').text
            if now != before:
                was_there = 0
                new.append(before)
                for notice in new:
                    if str_foinback(now, notice) > similimit:
                        was_there = 1
                if was_there == 0 and scoring_signsDict(now, bithumbSubjectSignsDict)>=1.:

                    subjectSymbol = get_symbol(now)

                    try:
                        driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd/a').click()  # 여기서 클릭이 될 때까지 계속해서 오류가 날 것이다.
                        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="primary-left"]/article/div')))  # 만약에 클릭이 된다면 내용에 해당하는 xpath가 뜨기를 기다릴 것이고
                        content = driver.find_element_by_xpath('//*[@id="primary-left"]/article/div').text

                    except:
                        driver.find_element_by_xpath('//*[@id="popmake-13905"]/button').click()
                        time.sleep(1.5)
                        driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd/a').click()  # 여기서 클릭이 될 때까지 계속해서 오류가 날 것이다.
                        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="primary-left"]/article/div')))  # 만약에 클릭이 된다면 내용에 해당하는 xpath가 뜨기를 기다릴 것이고
                        content = driver.find_element_by_xpath('//*[@id="primary-left"]/article/div').text

                    contentSymbol = get_symbol(content)

                    if subjectSymbol != None and ('bithumb' not in pastListedDict.keys() or subjectSymbol not in pastListedDict['bithumb']):
                        t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(subjectSymbol, marketpt, 1, 'no exception', 240, 0.8,'writing', True, [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        my_sendmessage(chat_id, 'http://bithumb.cafe mobile에서 {}가 상장된 것을 감지하여 자동매수매도를 시작합니다. http://bithumb.cafe/notice'.format(subjectSymbol))
                        write_ourData(subjectSymbol, 'bithumb')

                    elif contentSymbol != None and ('bithumb' not in pastListedDict.keys() or contentSymbol not in pastListedDict['bithumb']):
                        t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(contentSymbol, marketpt/1.3, 1, 'no exception', 240, 0.8,'writing', True, [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        my_sendmessage(chat_id, 'http://bithumb.cafe mobile 에서 {}가 상장된 것을 감지하여 자동매수매도를 시작합니다. http://bithumb.cafe/notice'.format(contentSymbol))
                        write_ourData(contentSymbol, 'bithumb')

                    my_sendmessage(chat_id=chat_id, text="http://bithumb.cafe mobile에서 상장감지\n\n 제목:{} \n\n 내용:{}".format(now, content))
                now = driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd').text
                while (now != '다음글이 없습니다.'):
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="primary-left"]/div/dl[2]/dd/a')))
                    driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd/a').click()  # 빗썸에서 글을 1번만 수정했을 경우
                    now = driver.find_element_by_xpath('//*[@id="primary-left"]/div/dl[2]/dd').text

            before = copy.deepcopy(now)
            epoch = epoch + 1
        except Exception as ex:
            myLogger.error(ex, exc_info=True)
            alpha+=1
            print (traceback.format_exc(limit=1))
            time.sleep(random.randrange(30, 70)+alpha*3)

#
# t1 = threading.Thread(target=selling_agent, args=(coin, buyLst[1], 70))  # 70개의 분봉 데이터
# t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
# t1.start()

def bitrex_pp(arr):
    return arr[1:-1].replace("\"", '').split(',')

def crawler_api_bitfinex():
    # 비트렉스는 분당 5회 request symbols 요청이 한계
    alpha=0
    url = "https://api.bitfinex.com/v1/symbols"
    before = bitrex_pp(requests.request("GET", url).text)
    # print (before)
    time.sleep(31)
    epoch=1
    while(1):
        if epoch%10==1:
            print ('crawler_api_bitfinex 가 {}번 페이지를 요청했습니다.'.format(epoch))
            if alpha>0:
                alpha-=1
        epoch = epoch+1
        try:
            tg=requests.request("GET", url).text
            now=bitrex_pp(tg)
            if (' error: ERR_RATE_LIMIT' in now or len(now)<10) or (now[0]!='btcusd'):
                time.sleep(random.randrange(300,350))
                print (' error: ERR_RATE_LIMIT')
                my_sendmessage(chat_id, 'bitfinex에서  error: ERR_RATE_LIMIT 발생')
                alpha+=3
            else:
                for x in now:
                    if (x not in before) and ('!DO' not in now) and (' NO' not in now) :
                        print (now)
                        # my_sendmessage(chat_id, '자꾸 에러뜨길래 테스트 {}'.format(now))
                        listed=x[0:3].upper()
                        if ('bitfinex' not in pastListedDict.keys() or listed not in pastListedDict['bitfinex']):
                            t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=( listed, marketpt,1, 'no exception', 600, 0.5,'writing', True, [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                            [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                            t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                            t1.start()
                            my_sendmessage(chat_id, 'bitfinex api에서 {}가 상장된 것을 감지하여 자동매수매도를 시작합니다.'.format(listed))
                            my_sendmessage(chat_id, 'now = {}'.format(now))
                            write_ourData(listed, 'bitfinex')
                            time.sleep(5)
                before = copy.deepcopy(now)
            time.sleep(31+alpha)
        except Exception as ex:
            myLogger.error(ex, exc_info=True)
            alpha+=2
            my_sendmessage(chat_id=chat_id, text="crawler_api_bitfinex 함수에서 {} 인 예외가 발생하였습니다.".format(traceback.format_exc(limit=1)))
            time.sleep(random.randrange(300,440)+alpha*20)




def crawler_notice_upbit():
    alpha=0
    epoch = 1

    opt = webdriver.ChromeOptions()
    opt.add_extension(settings.imgBlockLocation)
    prefs = {"profile.managed_default_content_settings.images": 2}
    opt.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(settings.chrome_location, chrome_options=opt)
    driver.get("https://upbit.com/service_center/notice")
    driver.implicitly_wait(60)
    before = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[3]/div/div/section/article/div/div[2]/table/tbody/tr[2]/td[1]/a').text
    new=[]
    while (1):
        try:
            if epoch%10 == 1:
                print ('https://upbit.com/service_center/notice에서 {} 번 페이지를 요청하였습니다.'.format(epoch))
                if alpha>0:
                    alpha-=0.3
            driver.get("https://upbit.com/service_center/notice")
            driver.implicitly_wait(60)
            now = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[3]/div/div/section/article/div/div[2]/table/tbody/tr[2]/td[1]/a').text  #tr[5]로 하면 테스트용 tr[1]로 바꿔야 진짜

            if now != before and (before == driver.find_element_by_xpath('//*[@id="root"]/div/div/div[3]/div/div/section/article/div/div[2]/table/tbody/tr[3]/td[1]/a').text) :
                was_there = 0
                new.append(before)

                for notice in new:
                    if str_foinback(now, notice)>similimit:
                        was_there=1

                if was_there==0 and scoring_signsDict(now, upbitSubjectSignsDict)>=1. :
                    driver.find_element_by_xpath('//*[@id="root"]/div/div/div[3]/div/div/section/article/div/div[2]/table/tbody/tr[2]/td[1]/a').click()
                    driver.implicitly_wait(60)
                    content = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[3]/div/div/section/article/div/div[1]/div[2]').text

                    subjectSymbol = get_symbol(now)
                    contentSymbol = get_symbol(content)
                    if subjectSymbol != None and ('upbit' not in pastListedDict.keys() or subjectSymbol not in pastListedDict['upbit']):
                        t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(subjectSymbol , marketpt, 1, 'no exception', 600, 0.5,'writing', True, [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        my_sendmessage(chat_id, 'https://upbit.com/service_center/notice 에서 {}가 상장된 것을 감지하여 자동매수매도를 시작했습니다. https://upbit.com/service_center/notice '.format(subjectSymbol ))
                        write_ourData(subjectSymbol, 'upbit')
                    elif contentSymbol != None and ('upbit' not in pastListedDict.keys() or contentSymbol not in pastListedDict['upbit']):
                        t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=(contentSymbol , marketpt*0.7, 1, 'no exception', 600, 0.5,'writing', True, [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_huobi, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_bittrex, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_bittrex, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                        t1.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
                        t1.start()
                        my_sendmessage(chat_id, 'https://upbit.com/service_center/notice 에서 {}가 상장된 것을 감지하여 자동매수매도를 시작했습니다. https://upbit.com/service_center/notice '.format(contentSymbol ))
                        write_ourData(contentSymbol, 'upbit')

                my_sendmessage(chat_id, 'https://upbit.com/service_center/notice 에 다음과 같은 공지사항이 올라왔습니다.\n\n{}'.format(now))

            before=copy.deepcopy(now)
            epoch = epoch + 1
            time.sleep(random.randrange(8, 17)+alpha)
        except Exception as ex:
            myLogger.error(ex, exc_info=True)
            alpha+=1
            driver.get("https://www.naver.com/")
            # my_sendmessage(chat_id=chat_id, text="crawler_notice_upbit 함수에서 {} 인 예외가 발생하였습니다.".format(ex))
            time.sleep(random.randrange(60, 100)+alpha*8)


def crawler_api_bittrex():
    alpha=0
    before = []
    balances={'success':False}
    while (not balances['success']):
        balances=my_bittrexV2.get_balances()
        time.sleep(15)
    for coin in balances['result']:
        before.append(coin['Currency']['Currency'])
    time.sleep(31)
    epoch = 1
    while(1):
        try:
            now = []
            if epoch%10 == 1:
                print ('crawler_api_bittrex가 {}번 api에 요청했습니다.'.format(epoch))
                if alpha>0:
                    alpha-=1

            epoch+=1
            balances=my_bittrexV2.get_balances()

            if balances['success']==False:
                alpha+=2
                print ('bittrex 1036')
                print (balances)
                time.sleep(random.randrange(61,121))
            else:
                for coin in balances['result']:
                    now.append(coin['Currency']['Currency'])

                for coin in now:
                    if (coin not in before) and ('bittrex' not in pastListedDict.keys() or coin not in pastListedDict['bittrex']):
                        t1 = threading.Thread(target=buy_sell_nonStop_anywhere_exce, args=( coin, marketpt*1.2, 1, 'bittrex', 600, 0.6,'writing', True, [[buy_ccxt_binance, buy_ccxt_bittrex, buy_ccxt_kucoin, buy_ccxt_hitbtc,  buy_ccxt_gateio], [buy_at_binance, buy_at_huobi]],
                        [sell_ccxt_binance, sell_at_bittrex, sell_ccxt_huobi, sell_ccxt_kucoin, sell_at_binance, sell_at_huobi, sell_ccxt_hitbtc,  sell_ccxt_gateio]))
                        t1.daemon = True
                        t1.start()
                        time.sleep(10)
                        my_sendmessage(chat_id, 'bittrex api 지갑에서 {}가 상장된 것을 감지하여 자동매수매도를 시작합니다.'.format(coin))
                        write_ourData(coin, 'bittrex')

                before = copy.deepcopy(now)
                time.sleep(21+alpha)

        except Exception as ex:
            myLogger.error(ex, exc_info=True)
            alpha+=2
            my_sendmessage(chat_id, 'crawler_api_bittrex에서 다음과 같은 예외가 발생했습니다.\n\n{}'.format(traceback.format_exc(limit=1)))
            time.sleep(random.randrange(140, 180)+alpha*10)



if __name__ == '__main__':

    do_telethon_main= threading.Thread(target=iMessageHandler.telethon_main())
    do_telethon_main.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
    do_telethon_main.start()

    # do_crawler_api_binance = threading.Thread(target=crawler_api_binance)
    # do_crawler_api_binance.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
    # do_crawler_api_binance.start()

    # do_crawler_browser_okcoin = threading.Thread(target=crawler_browser_okcoin)
    # do_crawler_browser_okcoin.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
    # do_crawler_browser_okcoin.start()

    # do_crawler_noticeBithumbPro_rightNoticeBithumb = threading.Thread(target=crawler_noticeBithumbPro_rightNoticeBithumb)
    # do_crawler_noticeBithumbPro_rightNoticeBithumb.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
    # do_crawler_noticeBithumbPro_rightNoticeBithumb.start()

    # do_crawler_api_bitfinex = threading.Thread(target=crawler_api_bitfinex)
    # do_crawler_api_bitfinex.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
    # do_crawler_api_bitfinex.start()
    # #
    # do_crawler_notice_upbit= threading.Thread(target=crawler_notice_upbit)
    # do_crawler_notice_upbit.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
    # do_crawler_notice_upbit.start()
    # #
    # do_crawler_api_bittrex = threading.Thread(target=crawler_api_bittrex)
    # do_crawler_api_bittrex.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
    # do_crawler_api_bittrex.start()
    #
    # do_crawler_nextMobile_notice_bithumb= threading.Thread(target=crawler_nextMobile_notice_bithumb)
    # do_crawler_nextMobile_notice_bithumb.daemon = True  # True이면 부모가 종료될때 같이 종료된다.
    # do_crawler_nextMobile_notice_bithumb.start()

    try:
        iMarket.set_validCurrencies()
        # validCurrencies = iParser.get_validCurrencies()
        # korNameCoinDict = iParser.getKorNameCoinDict(iMarket.validCurrencies)
        # engNameCoinDict = iParser.getEngNameCoinDict(iMarket.validCurrencies)
        iParser.set_NameCoinDict(iMarket.validCurrencies)
        print(iParser.korNameCoinDict)
        print(iParser.engNameCoinDict)

    except Exception as ex:
        iLogHandler.saveException(ex)
        iMessageHandler.my_sendmessage('coinDict를 구하는 과정에서 다음 예외가 발생했습니다: {}'.format(traceback.format_exc()))



while(1):

    if iMessageHandler.kill==True:
        sys.exit(1)
    if len(iTrader.tradeDict)>60 or (MessageHandler.MessageHandler.NoOfMessage > 1000):
        iMessageHandler.my_sendmessage('거래횟수가 {}이 되거나 메세지 보낸 횟수가 {}가 되어서 프로그램을 강제 종료합니다: 거래내역 {}'.format(len(iTrader.tradeDict), MessageHandler.MessageHandler.NoOfMessage, iTrader.tradeDict))
        sys.exit(1)
    # if seconds % 150 == 1:
    #     try:
    #         bot.sendMessage(jugiChatId, "{}초 ".format(seconds), timeout=20)
    #     except:
    #         pass
    if iChangeable_data.seconds % iConstant_data.reduceShirimpPeriod == 1:
        iMessageHandler.numChannelPeriod = iMessageHandler.numChannelPeriod -1
    # seconds=seconds+1
    iChangeable_data.inc_seconds()
    time.sleep(1)



