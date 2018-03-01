# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     texturepackerUnpack
   Author :       talus
   date：          2018/3/1 0001
   Description :
-------------------------------------------------

"""
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import configparser
import os
import shutil
import json

from common.ExceptCallStack import print_call_stack
from PIL import Image

fromDir = ""
toDir = ""






def parseConfig():

    global fromDir
    global toDir

    parser = configparser.ConfigParser()
    parser.read('config.ini',encoding="utf-8")

    fromDir = os.path.abspath(parser.get('default',"fromDir"))
    toDir = os.path.abspath(parser.get('default',"toDir"))


def walkDir(depth):
    """
    遍历文件夹
    :param depth:
    :return:
    """

    global fromDir

    fdir = os.path.join(fromDir,*depth)

    for f in os.listdir(fdir):
        path = os.path.join(fdir,f)
        if os.path.isdir(path):
            dp = depth[:]
            dp.append(f)
            walkDir(dp)
        else:
            ext = os.path.splitext(f)[1]
            try:
                if ext == ".json":
                    jsonUnpacker(f,depth)
                elif ext == ".plist":
                    plistUnpacker(f, depth)
            except Exception,e:
                print "unpacker error:  " + f
                raise e


def jsonUnpacker(f,depth):
    """
    解析json
    :param f:
    :param depth:
    :return:
    """
    global fromDir
    global toDir

    print "jsonUnpacker:  " + f

    fDir = os.path.join(fromDir,*depth)
    jsonFile = os.path.join(fDir,f)

    with open(jsonFile,"r") as f:
        content = json.load(f,encoding="utf-8")

    if not content:
        return
    meta = content.get("meta",None)
    if not meta:
        return
    image = meta.get("image",None)
    if not image:
        return

    pngFile = os.path.join(fDir,image)
    if not os.path.exists(pngFile):
        return

    img = Image.open(pngFile)

    pngDir = os.path.join(toDir,*depth)
    pngDir = os.path.join(pngDir,image.split(".")[0])
    if os.path.exists(pngDir):
        shutil.rmtree(pngDir)
    if not os.path.exists(pngDir):
        os.makedirs(pngDir)


    frames = content.get("frames",[])
    if not len(frames):
        return


    for item in frames:
        filename = item.get("filename","")
        frame = item.get("frame",{})
        rotated = item.get("rotated",False)
        trimmed = item.get("trimmed",False)
        spriteSourceSize = item.get("spriteSourceSize",{})
        sourceSize = item.get("sourceSize",{})

        if not trimmed:
            if rotated:
                im = img.crop((frame["x"],frame["y"],frame["x"] + frame["h"],frame["y"] + frame["w"]))
                im = im.transpose(Image.ROTATE_90)
            else:
                im = img.crop((frame["x"], frame["y"], frame["x"] + frame["w"], frame["y"] + frame["h"]))
            im.save(os.path.join(pngDir, filename))
        else:
            if not rotated:

                im = img.crop((frame["x"], frame["y"], frame["x"] + frame["w"], frame["y"] + frame["h"]))
                im1 = Image.new("RGBA",(sourceSize["w"],sourceSize["h"]),(255,255,255,0))
                im1.paste(im,(spriteSourceSize["x"],spriteSourceSize["y"]))
                im1.save(os.path.join(pngDir, filename))

            else:
                """
                不知道会不会有同时存在rotated和trimmed的情况，先打印
                """
                print "----------------------------"




def plistUnpacker(f, depth):
    """
    解析plist
    :param f:
    :param depth:
    :return:
    """


def main():
    try:
        parseConfig()
        walkDir([])
    except:
        print_call_stack()

if __name__ == '__main__':
    main()