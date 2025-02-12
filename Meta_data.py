import signs_dict

class Constant_data:
    def __init__(self, test_mode, marketpt, waitforselling, tries, sellingrate, standardBTC, similimit, possibleChannelNum, reduceShirimpPeriod,
                 avoid):
        self.test_mode = test_mode
        self.marketpt = marketpt
        self.waitforselling = waitforselling
        self.tries = tries
        self.sellingrate = sellingrate
        self.standardBTC = standardBTC
        self.similimit = similimit
        self.possibleChannelNum = possibleChannelNum
        self.reduceShirimpPeriod = reduceShirimpPeriod
        self.avoid = avoid

class Changeable_data:
    def __init__(self):
        self.seconds = 0

    def inc_seconds(self):
        self.seconds = self.seconds + 1