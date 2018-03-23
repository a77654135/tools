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
import xml.sax
import collections

from common.ExceptCallStack import print_call_stack
from PIL import Image

fromDir = ""
toDir = ""




class ExmlHandler( xml.sax.ContentHandler):

    def __init__(self):
        self.data = collections.OrderedDict()
        #当前正在解析的节点
        self.curNode = None
        #当前解析的借点的父节点
        self.parentNode = None

        self.depth = []


    def characters(self, content):
        print "characters:  " + content


    # 元素开始事件处理
    def startElement(self, tag, attributes):
        print "startElement:  " + tag

        for k in dict(attributes):
            print k,attributes[k]

        # attr = dict(attributes)
        # if tag.strip() == "e:Skin":
        #     self.curNode = self.data
        #     if attr.has_key("width"):
        #         self.curNode["width"] = int(attr["width"])
        #     if attr.has_key("height"):
        #         self.curNode["height"] = int(attr["height"])
        #     self.curNode["children"] = []
        #     self.depth.append(self.curNode)
        # else:
        #     self.parentNode = self.curNode
        #     self.curNode = collections.OrderedDict()
        #     self.parentNode["children"].append(self.curNode)
        #
        #     tagList = tag.split(":")
        #     self.curNode["class"] = tagList[-1]
        #     if tagList[-1] == "Group":
        #         self.curNode["children"] = []
        #         self.depth.append(self.curNode)
        #     # self.curNode["children"] = []
        #
        #     for k in attr:
        #         if k == "touchEnabled":
        #             self.curNode["touchEnabled"] = attr[k] == "true"
        #         elif k == "touchChildren":
        #             self.curNode["touchChildren"] = attr[k] == "true"
        #         elif k == "width":
        #             prop = attr[k]
        #             if prop.endswith(r"%"):
        #                 self.curNode["percentWidth"] = int(prop.replace(r"%",""))
        #             else:
        #                 self.curNode["width"] = int(prop)
        #         elif k == "height":
        #             prop = attr[k]
        #             if prop.endswith(r"%"):
        #                 self.curNode["percentHeight"] = int(prop.replace(r"%", ""))
        #             else:
        #                 self.curNode["height"] = int(prop)
        #         elif k == "source":
        #             prop = attr[k]
        #             # propList = prop.split(r".")
        #             # if len(propList) > 1:
        #             #     self.curNode["source"] = propList[-1]
        #             # else:
        #             #     self.curNode["source"] = prop
        #             self.curNode["source"] = prop
        #         elif k == "x":
        #             self.curNode["x"] = int(attr[k])
        #         elif k == "y":
        #             self.curNode["y"] = int(attr[k])
        #         elif k == "alpha":
        #             self.curNode["alpha"] = float(attr[k])
        #         else:
        #             self.curNode[k] = attr[k]




    # 元素结束事件处理
    def endElement(self, tag):
        print "endElement..........." + tag
        # if(tag.strip() == "e:Group"):
        #     if len(self.depth):
        #         self.depth.pop()
        #     else:
        #         print "1111111111"
        #     if len(self.depth):
        #         self.curNode = self.depth[-1]
        #     else:
        #         print "2222222222"
        # else:
        #     self.curNode = self.parentNode


    def endDocument(self):
        print "endDocument"
        print self.data
        # global currentFile
        # path, filename = os.path.split(currentFile)
        # fname = os.path.join(path,filename.replace(r".exml",r".json"))
        #
        # with open(fname,"w") as f:
        #     json.dump(self.data,f)



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
                # elif ext == ".plist":
                #     plistUnpacker(f, depth)
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

    print "plistUnpacker:  {}".format(f)
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    Handler = ExmlHandler()
    parser.setContentHandler(Handler)

    fDir = os.path.join(fromDir, *depth)
    plistFile = os.path.join(fDir, f)

    parser.parse(plistFile)



def main():
    try:
        parseConfig()
        walkDir([])
    except:
        print_call_stack()

if __name__ == '__main__':
    main()