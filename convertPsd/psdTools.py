# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     psdTools
   Author :       talus
   date：          2018/2/8 0008
   Description :
-------------------------------------------------

"""

"""
methods to get psd property
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import json


from common.ColorLogger import getUZWLogger
from psd_tools import PSDImage,Layer,Group

logger = getUZWLogger()










def main(argv):
    global psdDir
    global imgDir
    global skinDir
    global resFile
    global genImg
    global intelligent
    global force
    global genFontImg
    global currentPsdFile
    global s9gFile
    try:
        opts, args = getopt.getopt(argv, "p:i:s:r:", ["psdDir=", "imgDir=","skinDir=","genImg","genFontImg","resFile=","s9=","intelligent","force"])
    except getopt.GetoptError:
        print "--------------------------------------------"
        #print 'convertPsd -p <psdDir> -s <skinDir>    -i <imgDir> --genImg --genFontImg   -r resFile --intelligent --force'
        print 'convertPsd -p <psdDir> -s <skinDir>'
        print "--------------------------------------------"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "--------------------------------------------"
            print 'convertPsd -p <psdDir> -s <skinDir>'
            #print 'convertPsd -p <psdDir> -s <skinDir>    -i <imgDir> --genImg --genFontImg   -r resFile --intelligent --force'
            print "--------------------------------------------"
            sys.exit(2)
        elif opt in ("-p", "--psdDir"):
            psdDir = arg
        elif opt in ("-i", "--imgDir"):
            imgDir = arg
        elif opt in ("-s", "--skinDir"):
            skinDir = arg
        elif opt in ("-r", "--resFile"):
            resFile = arg
        elif opt in ("--genImg",):
            genImg = True
        elif opt in ("--intelligent",):
            intelligent = True
        elif opt in ("--force",):
            force = True
        elif opt in ("--genFontImg",):
            genFontImg = True
        elif opt in ("--s9",):
            s9gFile = arg

    #psdDir = r"C:\work\N5\roll\psd"
    if intelligent:
        parseResourceFile()
    if s9gFile != "":
        parseS9File()

    try:
        parse()
    except Exception,e:
        print u"解析psd失败：" + currentPsdFile
        print e.message
        print traceback.print_exc()



if __name__ == '__main__':
    main(sys.argv[1:])


