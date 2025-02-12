from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
import requests, traceback
import signs_dict

class MarketNo:
    def __init__(self, num=None, name=None):
        self.num = num
        self.name = name

class Parser:
    shrimpSignsDict = signs_dict.shrimpSignsDict
    upbitSubjectSignsDict = signs_dict.upbitSubjectSignsDict
    bithumbSubjectSignsDict = signs_dict.bithumbSubjectSignsDict
    binanceNoticeSignsDict = signs_dict.binanceNoticeDict
    okexSubjectSignsDict = signs_dict.okexSubjectSignsDict
    huobiSubjectSignsDict = signs_dict.huobiSubjectSignsDict
    sgbSignsDict = signs_dict.sgbSignsDict

    def __init__(self, settings, iLogHandler, iConstant_data):
        self.settings = settings
        self.iLogHandler = iLogHandler
        self.engNameCoinDict = None
        self.korNameCoinDict = None
        self.iConstant_data = iConstant_data
        self.iMessageHandler = None
        self.iTrader = None

    def set_iMessageHandler(self, iMessageHandler):
        self.iMessageHandler = iMessageHandler

    def set_iTrader(self, iTrader):
        self.iTrader = iTrader

    def getKorNameCoinDict(self, validCurrencies):
        korNameCoinDict = {}

        driver = webdriver.Chrome(self.settings.chrome_location)
        driver.get("https://coinmarketsum.com/ko/currencies/")
        WebDriverWait(driver, 80).until(EC.presence_of_element_located((By.XPATH, '//*[@id="coin_table"]/tbody/tr[17]/td[2]')))
        i = 2
        while (1):
            try:
                tmp = (driver.find_element_by_xpath('//*[@id="coin_table"]/tbody/tr[' + str(i) + ']/td[2]').text).split('\n')
                if tmp[1] in validCurrencies:
                    korNameCoinDict[tmp[0]] = tmp[1]
                i += 1

            except:
                # print('{}개의 korNameCoinDict 반환됨'.format(len(korNameCoinDict.keys())))
                print('{} korNameCoinDict is parsed'.format(len(korNameCoinDict.keys())))
                driver.quit()
                return korNameCoinDict

    def getEngNameCoinDict(self, validCurrencies):
        try:
            engNameCoinDict = {}

            headers = {'User-Agent': 'firefox'}

            dicts = (requests.get('https://api.coinmarketcap.com/v2/listings/', headers=headers)).json()['data']

            for dict in dicts:
                if dict['symbol'] in validCurrencies:
                    engNameCoinDict[dict['name'].lower()] = dict['symbol']

            # print('{}개의 engNameCoinDict 반환됨'.format(len(EngNameCoinDict)))
            print('{} engNameCoinDict is parsed'.format(len(engNameCoinDict)))
            return engNameCoinDict
        except Exception as ex:
            self.iLogHandler.saveException(ex)

    def set_NameCoinDict(self, validCurrencies):
        self.engNameCoinDict = self.getEngNameCoinDict(validCurrencies)
        self.korNameCoinDict = self.getKorNameCoinDict(validCurrencies)

    def filter_saewoo(self, text, pastListedDict, tradeDict):
        try:
            lowered = text.lower()

            score = self.scoring_signsDict(text, Parser.shrimpSignsDict, self.iMessageHandler)
            if score >= 1.:
                print('거래하기로 함')

                exceMarket = self.get_marketName(lowered)

                print(exceMarket)
                if exceMarket in ['bittrex', 'upbit']:
                    score *= 2.

                targetcoin = self.get_symbol(text, self.iConstant_data, tradeDict)

                if targetcoin != None:
                    if exceMarket in pastListedDict.keys() and targetcoin in pastListedDict[exceMarket]:
                        return [-1, -1, -3]
                    else:
                        return [targetcoin, exceMarket, score]
                else:
                    return [-1, -1, -2]
            else:
                return [-1, -1, -4]

        except Exception as ex:
            self.iLogHandler.saveException(ex)
            self.iMessageHandler.my_sendmessage('filter_saewoo 함수에서 다음과 같은 예외 발생:\n\n {}'.format(traceback.format_exc(limit=1)))
            return [-1, -1, -1]

    def filter_sgb(self, text, pastListedDict, tradeDict):
        try:
            lowered = text.lower()

            score = self.scoring_signsDict(text, Parser.sgbSignsDict, self.iMessageHandler)
            if score >= 1.:
                print('거래하기로 함')

                exceMarket = self.get_marketName(lowered)

                print(exceMarket)
                if exceMarket in ['bittrex', 'upbit']:
                    score *= 2.

                targetcoin = self.get_symbol(text, self.iConstant_data, tradeDict)

                if targetcoin != None:
                    if exceMarket in pastListedDict.keys() and targetcoin in pastListedDict[exceMarket]:
                        return [targetcoin, exceMarket, -3]
                    else:
                        return [targetcoin, exceMarket, score]
                else:
                    return [-1, -1, -2]
            else:
                return [-1, -1, -4]

        except Exception as ex:
            self.iLogHandler.saveException(ex)
            self.iMessageHandler.my_sendmessage('filter_saewoo 함수에서 다음과 같은 예외 발생:\n\n {}'.format(traceback.format_exc(limit=1)))
            return [-1, -1, -1]

    def has_upper(self, text):
        for string in text:
            if string in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'):
                return 1
        return 0

    def get_symbol(self, text, iConstant_data, tradeDict):
        coin_dict = {}
        # upperLst = []
        lowered = text.lower()

        upper = ''
        for i in text:
            if i.isupper() or i in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                upper = upper + i
            elif (len(upper) >= 2) and (upper not in iConstant_data.avoid) and (upper not in tradeDict.keys()) and self.has_upper(upper):
                if len(upper) == 3:
                    if upper not in coin_dict.keys():
                        coin_dict[upper] = 0.4
                    else:
                        coin_dict[upper] += 0.4
                    upper = ''
                elif len(upper) >= 4:
                    if upper not in coin_dict.keys():
                        coin_dict[upper] = 0.3
                    else:
                        coin_dict[upper] += 0.3
                    upper = ''
                elif len(upper) == 2:
                    if upper not in coin_dict.keys():
                        coin_dict[upper] = 0.26
                    else:
                        coin_dict[upper] += 0.26
                    upper = ''
            else:
                upper = ''

        for coin in self.engNameCoinDict.values():
            if coin in text and coin not in self.iConstant_data.avoid:
                if coin not in coin_dict.keys():
                    coin_dict[coin] = 1
                else:
                    coin_dict[coin] += 1

        for name in self.engNameCoinDict.keys():
            if name in lowered:
                coin = self.engNameCoinDict[name]
                if coin not in self.iConstant_data.avoid:
                    if coin not in coin_dict.keys():
                        coin_dict[coin] = 1
                    else:
                        coin_dict[coin] += 1

        for name in self.korNameCoinDict.keys():
            if name in text:
                coin = self.korNameCoinDict[name]
                if coin not in self.iConstant_data.avoid:
                    if coin not in coin_dict.keys():
                        coin_dict[coin] = 1
                    else:
                        coin_dict[coin] += 1

        tmp = 0
        targetcoin = ''
        if len(coin_dict) > 0:
            for key in coin_dict.keys():
                if coin_dict[key] > tmp:
                    tmp = coin_dict[key]
                    targetcoin = key
        else:
            return None

        if tmp >= 0.4:
            return targetcoin
        else:
            return None

    def scoring_signsDict(self, text, SignsDict, iMessageHanlder):
        score = 0.
        lowered = text.lower()
        for i in SignsDict.keys():
            try:
                if type(i) is str:
                    if i in lowered:
                        score = score + SignsDict[i]
                else:
                    if type(i[0]) is tuple:
                        includeAll = 1
                        excludeAll = 1
                        for inclue in i[0]:
                            if inclue not in lowered:
                                includeAll = 0
                                break
                        for exclude in i[1]:
                            if exclude in lowered:
                                excludeAll = 0
                                break
                        if includeAll == 1 and excludeAll == 1:
                            score = score + SignsDict[i]
                    else:
                        all = 1
                        for word in i:
                            if word not in lowered:  # 튜플 내의 원소 중 하나라도 안 들어 있으면
                                all = 0
                                break
                        if all == 1:  # 튜플 내의 원소가 다 들어있으면
                            score = score + SignsDict[i]
            except Exception as ex:
                iMessageHanlder.my_sendmessage('scoring_signsDict Error in {}'.format(traceback.format_exc(limit=1)))
        return score

    def get_marketName(self, text):
        binance, bittrex, huobi, kucoin, hitbtc, okex, gateio, bibox, bitfinex, bitflyer, coinbase, coinone, coinrail, gopax, hadax, qryptos, quoinex, upbit, bithumb = MarketNo(0, 'binance'), MarketNo(0, 'bittrex'), MarketNo(0, 'huobi'), MarketNo(0, 'kucoin'), MarketNo(0, 'hitbtc'), MarketNo(0,
                                                                                                                                                                                                                                                                                                     'okex'), MarketNo(
            0, 'gateio'), MarketNo(0, 'bibox'), MarketNo(0, 'bitfinex'), MarketNo(0, 'bitflyer'), MarketNo(0, 'coinbase'), MarketNo(0, 'coinone'), MarketNo(0, 'coinrail'), MarketNo(0, 'gopax'), MarketNo(0, 'hadax'), MarketNo(0, 'qryptos'), MarketNo(0, 'quoinex'), MarketNo(0, 'upbit'), MarketNo(0,
                                                                                                                                                                                                                                                                                                       'bithumb'),

        MarketNames = {'binance': binance,
                       '바이낸스': binance, '바이넨스': binance, '바넨': binance, '바낸': binance,

                       'bittrex': bittrex,
                       'bitrex': bittrex, '비트렉스': bittrex, '비트랙스': bittrex,

                       'huobi': huobi,
                       '후오비': huobi, '훠비': huobi,

                       'kucoin': kucoin,
                       'cucoin': kucoin, '쿠코인': kucoin, '쿠 코인': kucoin,

                       'hitbtc': hitbtc,
                       '힛빗': hitbtc, '히트비티씨': hitbtc, '히트 비티씨': hitbtc, '히트비티시': hitbtc, '히트 비티시': hitbtc, '히트비트': hitbtc,
                       '히트 비트': hitbtc,
                       '히트빗': hitbtc, '히트 빗': hitbtc, '힛비티씨': hitbtc, '힛 비티씨': hitbtc, '힛비티시': hitbtc, '힛 비티시': hitbtc,

                       'okex': okex,
                       '오케이엑스': okex, '오케이액스': okex,
                       '오케이 엑스': okex, '오케이 액스': okex,

                       'gateio': gateio,
                       '게이트아이오': gateio, '게이트 아이오': gateio, 'gate.io': gateio, 'gate io': gateio,
                       'gate_io': gateio,

                       'bibox': bibox,
                       '비박스': bibox, '바이박스': bibox,

                       'bitfinex': bitfinex,
                       '비트파이넥스': bitfinex, '비트 파이넥스': bitfinex, '빗파이넥스': bitfinex, '빗 파이넥스': bitfinex,
                       'bitflyer': bitflyer,
                       '비트플라이어': bitflyer, '비트 플라이어': bitflyer, '빗플라이어': bitflyer, '빗 플라이어': bitflyer,

                       'coinbase': coinbase,
                       '코인베이스': coinbase, '코인 베이스': coinbase,

                       'coinone': coinone,
                       '코인원': coinone, '코인 원': coinone,

                       'coinrail': coinrail,
                       '코인레일': coinrail, '코인 레일': coinrail, '코인 래일': coinrail, '코인래일': coinrail,

                       'gopax': gopax,
                       '고팍스': gopax, '고파스': gopax, '고팍': gopax,

                       'hadax': hadax,
                       '하닥스': hadax, '하덱스': hadax, '하댁스': hadax,

                       'qryptos': qryptos,
                       '크립토스': qryptos, '크립토쓰': qryptos,

                       'quoinex': quoinex,
                       '쿠오이넥스': quoinex, '쿠워넥스': quoinex, '콰이넥스': quoinex,
                       '큐오넥스': quoinex, '쿼넥스': quoinex, '쿠오이낵스': quoinex, '쿠워낵스': quoinex, '콰이낵스': quoinex, '큐오낵스': quoinex, '쿼낵스': quoinex,

                       'upbit': upbit,
                       '업비트': upbit, '업빗': upbit,

                       'bithumb': bithumb,
                       'bithum': bithumb, 'bitthumb': bithumb, 'bitumb': bithumb, '빗썸': bithumb, '빗섬': bithumb, '비썸': bithumb, }

        lowered = text.lower()
        for key in MarketNames.keys():
            MarketNames[key].num += lowered.count(key)

        exceMarket = 'no exception'
        tmp = 0
        for key in MarketNames.keys():
            item = MarketNames[key]
            if item.num > tmp:
                tmp = item.num
                exceMarket = item.name

        return exceMarket