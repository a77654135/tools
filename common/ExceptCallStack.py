# coding:utf-8

import traceback, sys, os.path, StringIO

'''

    打印异常时的callstack

'''


def print_call_stack(logger=None):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    output = "---------------------------Exception Begin------------------------------------\n"
    # err_desc    =   str(exc_obj)
    output += ("[Exception Desc]" + str(exc_obj) + "\n")
    stackarr = []
    for frame in traceback.extract_tb(exc_tb):
        # print frame
        fname, lineno, fn, text = frame
        line = "[stack trace] %s , line %d -> %s" % (os.path.split(fname)[1], lineno, text)
        stackarr.insert(0, line)

    for line in stackarr:
        output += (line + "\n")

    output += "-------------------------------------------------------------------------------"

    if logger is None:
        print output
    else:
        strio = StringIO.StringIO(output)
        while True:
            _line = strio.readline()
            if _line == '' or _line is None:
                break
            _line = _line.strip()
            logger.warning(_line)

        #

    return output


def print_error(func):
    def desc(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            print traceback.print_exc()
    return desc
