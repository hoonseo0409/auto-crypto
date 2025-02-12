import time
import hmac
import hashlib

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import requests


API_V1_1 = 'v1.1'
API_V2_0 = 'v2.0'

BASE_URL_V1_1 = 'https://bittrex.com/api/v1.1{path}?'
BASE_URL_V2_0 = 'https://bittrex.com/api/v2.0{path}?'

PROTECTION_PUB = 'pub'  # public methods
PROTECTION_PRV = 'prv'  # authenticated methods

def using_requests(request_url, apisign):
    return requests.get(
        request_url,
        headers={"apisign": apisign},
        timeout=10
    ).json()


class BittrexV2(object):

    def __init__(self, api_key, api_secret, calls_per_second=1, dispatch=using_requests, api_version=API_V1_1):
        self.api_key = str(api_key) if api_key is not None else ''
        self.api_secret = str(api_secret) if api_secret is not None else ''
        self.dispatch = dispatch
        self.call_rate = 1.0 / calls_per_second
        self.last_call = None
        self.api_version = api_version

    def wait(self):
        if self.last_call is None:
            self.last_call = time.time()
        else:
            now = time.time()
            passed = now - self.last_call
            if passed < self.call_rate:
                # print("sleep")
                time.sleep(self.call_rate - passed)

            self.last_call = time.time()

    def _api_query(self, protection=None, path_dict=None, options=None):

        if not options:
            options = {}

        if self.api_version not in path_dict:
            raise Exception('method call not available under API version {}'.format(self.api_version))

        request_url = BASE_URL_V2_0 if self.api_version == API_V2_0 else BASE_URL_V1_1
        request_url = request_url.format(path=path_dict[self.api_version])

        nonce = str(int(time.time() * 1000))

        if protection != PROTECTION_PUB:
            request_url = "{0}apikey={1}&nonce={2}&".format(request_url, self.api_key, nonce)

        request_url += urlencode(options)

        try:
            apisign = hmac.new(self.api_secret.encode(),
                               request_url.encode(),
                               hashlib.sha512).hexdigest()

            self.wait()

            return self.dispatch(request_url, apisign)

        except Exception:
            return {
                'success': False,
                'message': 'NO_API_RESPONSE',
                'result': None
            }

    def get_balances(self):

        return self._api_query(path_dict={
            API_V1_1: '/account/getbalances',
            API_V2_0: '/key/balance/GetBalances'
        }, protection=PROTECTION_PRV)