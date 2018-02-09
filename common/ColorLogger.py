# coding:utf-8
#
#       带颜色的打印输出日志
#
import logging, time, os, sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
import ColorLogging


class MyFormatter(logging.Formatter):
    width = 24

    def format(self, record):
        max_filename_width = self.width - 1 - len(str(record.lineno))
        filename = record.filename
        if len(record.filename) > max_filename_width:
            filename = record.filename[:max_filename_width]
        a = "%s:%s" % (filename, record.lineno)

        return "%s[%s] %s\t%s" % (a.rjust(self.width), datetime.now().strftime("%H:%M:%S"), record.levelname[0], record.getMessage())


def initColorLog(log_level="DEBUG", log_filename=None):
    '''
    if log_filename == None:
        log_filename = "log%d.txt" % (int(time.time()))
    '''

    # formatter = logging.Formatter(FORMAT)
    formatter = MyFormatter()

    stmhdlr = logging.StreamHandler(sys.stdout)
    stmhdlr.setFormatter(formatter)

    logger = logging.getLogger()
    # print 'stmhdlr =',stmhdlr

    handlers = logger.handlers
    for handler in handlers:
        logger.removeHandler(handler)

    logger.addHandler(stmhdlr)

    if log_filename is not None:
        LOGFILE = os.path.join(os.getcwd(), log_filename)
        MAXLOGSIZE = 100 * 1024 * 1024  # Bytes
        BACKUPCOUNT = 5
        FORMAT = \
            "%(message)-72s %(asctime)s %(levelname)-8s[%(filename)s:%(lineno)d(%(funcName)s)]"
        hdlr = RotatingFileHandler(LOGFILE,
                                   mode='a',
                                   maxBytes=MAXLOGSIZE,
                                   backupCount=BACKUPCOUNT)

        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

    # print 'log_level =',log_level

    if "DEBUG" == log_level.upper():
        logger.setLevel(logging.DEBUG)
    elif "INFO" == log_level.upper():
        logger.setLevel(logging.INFO)
    elif "WARNING" == log_level.upper():
        logger.setLevel(logging.WARNING)
    elif "ERROR" == log_level.upper():
        logger.setLevel(logging.ERROR)
    elif "CRITICAL" == log_level.upper():
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logging.ERROR)
    return logger


#   日志输出
uzwlogger = None


def getUZWLogger(level="DEBUG", savename=None):
    global uzwlogger
    if uzwlogger is not None:
        return uzwlogger

    uzwlogger = initColorLog(level, savename)
    return uzwlogger
