# -*- coding: utf-8 -*-
"""
从一堆资源里面,找出exml中需要的资源
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os, getopt, traceback, shutil, re


imgDir = ''
exmlDir = ''
toDir = ''
allData = {}
allNeed = []


def getAllImg():
    """
    扫描所有的资源
    :return:
    """
    global imgDir
    global allData

    for parent, dirs, files in os.walk(imgDir):
        for f in files:
            ext = os.path.splitext(f)[-1]
            if ext == ".png" or ext == ".jpg":
                absPath = os.path.join(parent, f)
                name = f.replace(r".png", r"_png")
                name = name.replace(r".jpg", r"_jpg")
                allData[name] = absPath

def getAllNeed():
    """
    寻找exml中所有需要的资源
    :return:
    """
    global exmlDir
    global allNeed
    for parent, dirs, files in os.walk(exmlDir):
        for f in files:
            if f.endswith(r".exml"):
                with open(os.path.join(parent, f), "r") as ef:
                    allNeed.extend(re.findall(r'source="(.*?)"', ef.read()))

def copyResource():
    """
    拷贝资源到目标文件夹
    :return:
    """
    global toDir
    global allData
    global allNeed

    if not os.path.exists(toDir):
        os.makedirs(toDir)

    for f in allNeed:
        if not f.startswith(r"animal") and f in allData:
            path = allData[f]
            parent, filename = os.path.split(path)
            toFile = os.path.join(toDir, filename)
            shutil.copy(path, toFile)



def parse():
    getAllImg()
    getAllNeed()
    copyResource()


def main(argv):
    global exmlDir
    global imgDir
    global toDir
    try:
        opts, args = getopt.getopt(argv, "e:i:t:", ["exmlDir=", "imgDir=", "toDir="])
    except getopt.GetoptError:
        print "--------------------------------------------"
        print 'findResource -i <imgDir> -e <exmlDir> -t <toDir>'
        print "--------------------------------------------"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "--------------------------------------------"
            print 'findResource -i <imgDir> -e <exmlDir> -t <toDir>'
            print "--------------------------------------------"
            sys.exit(2)
        elif opt in ("-i", "--imgDir"):
            imgDir = os.path.abspath(arg)
        elif opt in ("-e", "--exmlDir"):
            exmlDir = os.path.abspath(arg)
        elif opt in ("-t", "--toDir"):
            toDir = os.path.abspath(arg)

    imgDir = os.path.abspath(r"F:\work\n5\roll\art\resources")
    exmlDir = os.path.abspath(r"D:\study\work\egret_framework\resource\skins\animal")
    toDir = os.path.abspath(r"D:\study\work\egret_framework\resource\assets\game\animal\animal_other")

    try:
        parse()
    except:
        print traceback.print_exc()


if __name__ == '__main__':
    main(sys.argv[1:])

