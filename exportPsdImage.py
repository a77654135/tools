#-.-coding:utf-8

"""
导出PSD的图层，参数-p如果是dir，就导出dir下的所有psd，也可以指定为特定的psd文件
"""

import os
import getopt
import sys
import traceback
import json
import shutil
import re
from psd_tools import PSDImage,Layer,Group

psdDir = ""
imgDir = ""
data = {}

curPsd = ""


'''
layer_image = layer.as_PIL()
layer_image.save(pngFile)
'''

idx = 0
def getName():
    global idx
    idx += 1
    return "img_name_{}".format(idx)

#获得图层或图层组的尺寸信息
def getDimension(layer):
    #"".strip()
    assert isinstance(layer, Group) or isinstance(layer, Layer)
    try:
        if isinstance(layer,Group):
            box = layer.bbox
            return int(box.x1), int(box.y1), int(box.width), int(box.height)
        elif isinstance(layer,Layer):
            #box = layer.transform_bbox if layer.transform_bbox is not None else layer.bbox
            box = layer.bbox
            return int(box.x1), int(box.y1), int(box.width), int(box.height)
        return 0,0,0,0
    except Exception,e:
        # print "--------------------------------------------"
        # print u"解析图层组[ " + layer.name.strip() + u" ]错误：  " + e.message
        # print "--------------------------------------------"
        return 0,0,0,0

def isLayerLocked(layer):
    assert isinstance(layer,Layer) or isinstance(layer,Group)
    locked = False
    try:
        locked = layer._info[9][0]
    except:
        pass
    return locked

def parseLayer(layer,dir):
    assert isinstance(layer,Layer)
    if isLayerLocked(layer):
        return
    global data
    try:
        name = layer.name.strip().split(":")[0].strip().split(" ")[0].strip()
        if not re.match(r'[0-9a-zA-Z_]+',name):
            name = getName()
        _,__,w,h = getDimension(layer)
        if data.has_key(name):
            attr = data[name]
            if w > attr["w"] or h > attr["h"]:
                d = {}
                d["w"] = w
                d["h"] = h
                data[name] = d
                layer_image = layer.as_PIL()
                imgName = os.path.join(dir, "{}.png".format(name))
                layer_image.save(imgName)
                print "export png successfully.  " + (imgName)
        else:
            d = {}
            d["w"] = w
            d["h"] = h
            data[name] = d
            layer_image = layer.as_PIL()
            imgName = os.path.join(dir, "{}.png".format(name))
            layer_image.save(imgName)

            print "export png successfully.  " + (imgName)
    except Exception,e:
        pass


def parseGroup(group,dir):
    for layer in group.layers:
        if isLayerLocked(layer):
            continue
        if isinstance(layer,Layer):
            parseLayer(layer,dir)
        elif isinstance(layer,Group):
            if layer.name.strip() == "$Bone":
                continue
            parseGroup(layer,dir)

def parseFile(file,depth,fileName):
    ext = os.path.splitext(file)[-1]
    if ext != ".psd":
        return
    if fileName.startswith("unuse"):
        return
    global imgDir
    global data
    psdImgDir = os.path.join(os.path.abspath(imgDir),*depth)
    if not os.path.exists(psdImgDir):
        os.makedirs(psdImgDir)
    psd = PSDImage.load(file)
    parseGroup(psd,psdImgDir)

    global curPsd
    curPsd = file

def walkDir(dir,depth):
    global data
    data = {}
    for f in os.listdir(dir):
        path = os.path.join(dir,f)
        dph = depth[:]
        if os.path.isfile(path):
            parseFile(path,dph,f)
        elif os.path.isdir(path):
            dph.append(f)
            walkDir(path,dph)

def parse():
    global psdDir

    psdDir = os.path.abspath(psdDir)
    if os.path.isdir(psdDir):
        walkDir(os.path.abspath(psdDir),[])
    elif os.path.isfile(psdDir):
        parseFile(psdDir,[], "")


def main(argv):
    global psdDir
    global imgDir
    try:
        opts, args = getopt.getopt(argv, "p:i:", ["psdDir=", "imgDir="])
    except getopt.GetoptError:
        print "--------------------------------------------"
        print 'exportPsdImage -p <psdDir> -i <imgDir>'
        print "--------------------------------------------"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "--------------------------------------------"
            print 'exportPsdImage -p <psdDir> -is <imgDir>'
            print "--------------------------------------------"
            sys.exit(2)
        elif opt in ("-p", "--psdDir"):
            psdDir = arg
        elif opt in ("-i", "--imgDir"):
            imgDir = arg

    try:
        parse()
    except:
        print traceback.print_exc()


if __name__ == '__main__':
    main(sys.argv[1:])