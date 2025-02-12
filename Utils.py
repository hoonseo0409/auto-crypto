import requests
import hmac, hashlib
import time
import settings
import traceback


def str_foinback(str1, str2):
    same=0
    for ch in str1:
        if ch in str2:
            same+=1
    return same/float(len(str2))

def format_float(f, num):
    return ("%."+str(num)+"f") % f

def signed_request(url):
    now = time.time()
    url += '&nonce=' + str(now)
    # signed = hmac.new(settings.bittrex_SECRET, url.encode('utf-8'), hashlib.sha512).hexdigest()
    signed = hmac.new(bytes(settings.bittrex_SECRET, encoding='utf-8'), url.encode('utf-8'), hashlib.sha512).hexdigest()

    headers = {'apisign': signed}
    r = requests.get(url, headers=headers)
    return r.json()

def simple_request(url):
    r = requests.get(url)
    return r.json()


def try_again_func(func, tries=5, record=True, *args, **kwargs):
    for i in range(tries):
        try:
            # print('{}를 {}번째 시도'.format(func.__name__, i + 1))
            print('try {}, {} times'.format(func.__name__, i + 1))
            return func(*args, **kwargs)

        except Exception as ex:
            print ('exception in', func.__name__)
            time.sleep(1.)
    return -1

def get_sell_amount_with_sell_fnt(sell_list, sell_fnt):
    for i in range(len(sell_list)):
        if sell_list[i][0] == sell_fnt:
            return sell_list[i][1]
    return None

def filter_toSell_2_by_name(toSell_2, name_lst):
    toSell_2_result = []
    for i in range(len(toSell_2)):
        for name in name_lst:
            if name in toSell_2[i][0].__name__:
                toSell_2_result.append(toSell_2[i])
                # break
    return toSell_2_result

def get_pair_from_trading_fnt(symbol, fnt):
    if fnt.__name__[-4:] == 'okex' or fnt.__name__[-4:] == 'teio':
        pair = symbol + '/USDT'
    else:
        pair = symbol + '/BTC'
    return pair






