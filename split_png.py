# -*- coding: UTF-8 -*-

import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import getopt
import xml.sax
import re
import json
import datetime
import traceback
from PIL import Image
from ToolFunctions import GetRects

dir = ""
recursive = False


def parse():
    global dir
    walkDir(dir)

def walkDir(dir):
    for f in os.listdir(dir):
        path = os.path.join(dir,f)
        if os.path.isdir(path):
            # walkDir(dir)
            continue
        elif os.path.splitext(f)[1] == ".png":
            parsePng(path)

def parsePng(pngFile):
    pngPath,pngName = os.path.split(pngFile)
    dirname = os.path.join(pngPath,os.path.splitext(pngName)[0])
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    img = Image.open(pngFile)

    rects = GetRects(img)
    for idx, rect in enumerate(rects):
        im = img.crop((rect.left, rect.top, rect.left + rect.width, rect.top + rect.height))
        im.save(os.path.join(dirname, "{}_{}.png".format(pngName.split(".")[0],idx)))


def main(argv):
    global dir

    try:
        opts, args = getopt.getopt(argv, "d:", ["dir=",])
    except getopt.GetoptError:
        print "--------------------------------------------"
        print 'split_png -d <dir>'
        print "--------------------------------------------"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "--------------------------------------------"
            print 'split_png -d <dir>'
            print "--------------------------------------------"
            sys.exit(2)
        elif opt in ("-d", "--dir"):
            dir = os.path.abspath(arg)

    # dir = os.path.abspath(r"C:\Users\talus\work\moni\sheep\0")

    try:
        parse()
    except Exception,e:
        print traceback.print_exc()


def ttt():
    path = os.path.abspath(r"C:\Users\talus\work\moni\sheep\0\aaa.png")
    dirname = os.path.dirname(path)
    img = Image.open(path)

    rects = GetRects(img)
    for idx,rect in enumerate(rects):
        im = img.crop((rect.left, rect.top, rect.left + rect.width, rect.top + rect.height))
        im.save(os.path.join(dirname, "{}.png".format(idx)))


if __name__ == '__main__':

    # ttt()
    main(sys.argv[1:])