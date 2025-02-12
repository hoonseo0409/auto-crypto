import logging
import traceback

class LogHandler:
    def __init__(self, fileName, directory):
        self.myLogger = logging.getLogger(fileName)
        self.myLogger.setLevel(logging.ERROR)
        self.formatter = logging.Formatter('------------------------------------------------------------------------------------\n\r%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_handler = logging.FileHandler(directory)
        self.file_handler.setFormatter(self.formatter)
        self.myLogger.addHandler(self.file_handler)

    def saveException(self, ex, verbose = False):
        self.myLogger.error(ex, exc_info=True)
        if verbose:
            print(traceback.format_exc(limit=1))