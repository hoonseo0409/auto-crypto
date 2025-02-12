# -*- coding: utf-8 -*-

import base64
import hmac
import hashlib
import json

import urllib
import datetime
import requests
# import urllib2
# import urlparse
import settings
from urllib import parse as urlparse

# timeout in 5 seconds:
TIMEOUT = 5

API_HOST = "api.huobi.pro"

SCHEME = 'https'

# language setting: 'zh-CN', 'en':
LANG = 'zh-CN'

DEFAULT_GET_HEADERS = {
    'Accept': 'application/json',
    'Accept-Language': LANG,
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
}

DEFAULT_POST_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Language': LANG,
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
}
# 此处填写APIKEY

ACCESS_KEY = settings.huobi_APIKEY
SECRET_KEY = settings.huobi_SECRET


# 首次运行可通过get_accounts()获取acct_id,然后直接赋值,减少重复获取。
ACCOUNT_ID = None


# API 请求地址
MARKET_URL = TRADE_URL = "https://api.huobi.pro"

#各种请求,获取数据方式
def http_get_request(url, params, add_to_headers=None):
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = urlparse.urlencode(params)
    try:
        response = requests.get(url, postdata, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status":"fail"}
    except Exception as e:
        print("httpGet failed, detail is:%s" %e)
        return {"status":"fail","msg":e}

def http_post_request(url, params, add_to_headers=None):
    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json',
        "User-Agent": "Chrome/39.0.2171.71",
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = json.dumps(params)
    try:
        response = requests.post(url, postdata, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            return response.json()
    except Exception as e:
        print("httpPost failed, detail is:%s" % e)
        return {"status":"fail","msg":e}


def api_key_get(params, request_path):
    method = 'GET'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params.update({'AccessKeyId': ACCESS_KEY,
                   'SignatureMethod': 'HmacSHA256',
                   'SignatureVersion': '2',
                   'Timestamp': timestamp})

    host_name = host_url = TRADE_URL
    host_name = urlparse.urlparse(host_url).hostname
    host_name = host_name.lower()


    params['Signature'] = createSign(params, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path
    return http_get_request(url, params)


def api_key_post(params, request_path):
    method = 'POST'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params_to_sign = {'AccessKeyId': ACCESS_KEY,
                      'SignatureMethod': 'HmacSHA256',
                      'SignatureVersion': '2',
                      'Timestamp': timestamp}

    host_url = TRADE_URL
    host_name = urlparse.urlparse(host_url).hostname
    host_name = host_name.lower()
    params_to_sign['Signature'] = createSign(params_to_sign, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path + '?' + urlparse.urlencode(params_to_sign)
    return http_post_request(url, params)


def createSign(pParams, method, host_url, request_path, secret_key):
    sorted_params = sorted(pParams.items(), key=lambda d: d[0], reverse=False)
    encode_params = urlparse.urlencode(sorted_params)
    payload = [method, host_url, request_path, encode_params]
    payload = '\n'.join(payload)
    payload = payload.encode(encoding='UTF8')
    secret_key = secret_key.encode(encoding='UTF8')
    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature

############################ old moved huobi ############################

def huobi_get_accounts():
    """
    :return:
    """
    path = "/v1/account/accounts"
    params = {}
    return api_key_get(params, path)

ACCOUNT_ID = 0

def huobi_get_balance(acct_id=None):
    """
    :param acct_id
    :return:
    """
    global ACCOUNT_ID

    if not acct_id:
        try:
            accounts = huobi_get_accounts()
            acct_id = ACCOUNT_ID = accounts['data'][0]['id']
        except BaseException as e:
            print ('get acct_id error.%s' % e)
            acct_id = ACCOUNT_ID

    url = "/v1/account/accounts/{0}/balance".format(acct_id)
    params = {"account-id": acct_id}
    return api_key_get(params, url)

def huobi_get_depth(symbol, type):
    """
    :param symbol:
    :param type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
    :return:
    """
    params = {'symbol': symbol,
              'type': type}

    url = MARKET_URL + '/market/depth'
    return http_get_request(url, params)

def huobi_send_order(amount, source, symbol, _type, price=0):
    """
    :param amount:
    :param source: 如果使用借贷资产交易，请在下单接口,请求参数source中填写'margin-api'
    :param symbol:
    :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
    :param price:
    :return:
    """
    try:
        accounts = huobi_get_accounts()
        acct_id = accounts['data'][0]['id']
    except BaseException as e:
        print ('get acct_id error.%s' % e)
        acct_id = ACCOUNT_ID

    params = {"account-id": acct_id,
              "amount": amount,
              "symbol": symbol,
              "type": _type,
              "source": source}
    if price:
        params["price"] = price

    url = '/v1/order/orders/place'
    return api_key_post(params, url)

def huobi_get_trade(symbol):
    """
    :param symbol: 可选值：{ ethcny }
    :return:
    """
    params = {'symbol': symbol}

    url = MARKET_URL + '/market/trade'
    return http_get_request(url, params)

def huobi_get_detail(symbol):
    """
    :param symbol: 可选值：{ ethcny }
    :return:
    """
    params = {'symbol': symbol}

    url = MARKET_URL + '/market/detail'
    return http_get_request(url, params)

def huobi_order_info(order_id):
    """
    :param order_id:
    :return:
    """
    params = {}
    url = "/v1/order/orders/{0}".format(order_id)
    return api_key_get(params, url)

