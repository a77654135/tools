# -*- coding: utf-8 -*-

"""
bmfont工具生成的.fnt文件转换成egret使用的fnt格式文件.

双击bmfnt2egret.exe可以修改当前文件夹下的所有.fnt文件
可以指定-f参数，可以指定文件夹或者具体的文件
"""

import sys

reload(sys)
sys.setdefaultencoding("utf-8")

import os
import re
import json
import getopt

fname = ""


def findArg(line, key):
    ret = re.findall('{}=(-?\d+)'.format(key), line)
    return ret[0]

def parseFile(filename):
    if os.path.splitext(filename)[-1] != ".fnt":
        return
    with open(filename, "r") as f:
        lines = f.readlines()
        if not lines[0].startswith("info face"):
            return

    print "parse file:   {}".format(filename)

    fn = re.findall('file="(.*?)"', lines[2])[0]

    frames = {}
    for line in lines:
        if line.startswith("char id"):
            id = findArg(line, "id")
            x = findArg(line, "x")
            y = findArg(line, "y")
            width = findArg(line, "width")
            height = findArg(line, "height")
            xoffset = findArg(line, "xoffset")
            yoffset = findArg(line, "yoffset")
            string = ascii2Unicode(id)
            frames[string] = {}
            frames[string]["x"] = int(x)
            frames[string]["y"] = int(y)
            frames[string]["w"] = int(width)
            frames[string]["h"] = int(height)
            frames[string]["sourceW"] = int(width)
            frames[string]["sourceH"] = int(height)
            frames[string]["offX"] = int(xoffset)
            frames[string]["offY"] = int(yoffset)


        ret = {}
        ret["file"] = fn
        ret["frames"] = frames

    with open(filename, "w") as f:
        json.dump(ret, f, ensure_ascii=False, indent=4, encoding="utf-8")



def ascii2Unicode(ascii_code):
    try:
        return unichr(int(ascii_code))
    except:
        print "cannot convert ascci_code:   {}".format(ascii_code)
        return "{}".format(ascii_code)

def parse():
    global fname
    print "fname:   {}".format(fname)
    if not fname:
        fname = os.path.dirname(os.path.abspath(__file__))

    if os.path.isdir(fname):
        for p, d, fs in os.walk(fname):
            for f in fs:
                if os.path.splitext(f)[-1] == ".fnt":
                    parseFile(os.path.join(p, f))

    elif os.path.isfile(fname):
        parseFile(fname)


def main(argv):
    global fname

    try:
        opts, args = getopt.getopt(argv, "f:")
    except getopt.GetoptError:
        print "--------------------------------------------"
        print 'bmfnt2egret -f <filename> '
        print "--------------------------------------------"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "--------------------------------------------"
            print 'bmfnt2egret -f <filename> '
            print "--------------------------------------------"
            sys.exit(2)
        elif opt in ("-f",):
            fname = os.path.abspath(arg)

    parse()


if __name__ == "__main__":
    main(sys.argv[1:])