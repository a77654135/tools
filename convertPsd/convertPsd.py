# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     convertPsd
   Author :       talus
   date：          2018/2/8 0008
   Description :
-------------------------------------------------

"""
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import json
import re
import logging
import shutil
import configparser

from psdTools import *
from psd_tools import PSDImage,Layer,Group
from common.ExceptCallStack import print_call_stack




curPsdName = ""

psdDir = ""
exmlDir = ""
generateExml = True
replaceFile = False

imgDir = ""
generateImg = False
generateLabelImg = False

s9File = ""
s9Map = {}

smartSource = False
defResFile = ""
resNameMap = {}



def configParser():
    """
    解析配置文件
    :return:
    """
    global psdDir
    global exmlDir
    global imgDir
    global generateExml
    global generateImg
    global generateLabelImg
    global replaceFile
    global s9File
    global smartSource
    global defResFile

    parser = configparser.ConfigParser()
    parser.read("config.ini",encoding="utf-8")

    psdDir = os.path.abspath(parser.get("default", "psdDir"))
    exmlDir = os.path.abspath(parser.get("default", "exmlDir"))
    imgDir = os.path.abspath(parser.get("default", "imgDir"))
    s9File = os.path.abspath(parser.get("default", "s9File"))
    defResFile = os.path.abspath(parser.get("default", "defResFile"))

    generateImg = parser.getboolean("default","generateImg")
    generateLabelImg = parser.getboolean("default","generateLabelImg")
    replaceFile = parser.getboolean("default","replaceFile")
    generateExml = parser.getboolean("default","generateExml")
    smartSource = parser.getboolean("default","smartSource")


def readS9Info():
    """
    读取九宫格信息
    :return:
    """
    global s9File
    global s9Map
    if os.path.exists(s9File):
        with open(s9File, mode='r') as f:
            s9Map = json.load(f, encoding="utf-8")

def readResFile():
    """
    读取default.res.json
    :return:
    """
    global smartSource
    if not smartSource:
        return

    global defResFile
    if not os.path.exists(defResFile):
        return

    with open(defResFile, mode='r') as f:
        content = json.load(f, encoding="utf-8")
        if content["resources"] is not None:
            for res in content["resources"]:
                parseSingleResource(res)


def parseSingleResource(res):
    """
    解析组员组中的一个资源
    :param res:
    :return:
    """
    global resNameMap
    if res["type"] == "sheet":
        if res["subkeys"]:
            for name in res["subkeys"].split(r","):
                if resNameMap.has_key(name):
                   resNameMap[name].append(res["name"])
                else:
                    resNameMap[name] = []
                    resNameMap[name].append(res["name"])
    elif res["type"] == "image":
        if resNameMap.has_key(res["name"]):
            resNameMap[res["name"]].append(None)
        else:
            resNameMap[res["name"]] = []
            resNameMap[res["name"]].append(None)

def walkDir(depth):
    """
    遍历文件夹
    :param depth:
    :return:
    """
    global psdDir
    global exmlDir
    global replaceFile

    fromDir = os.path.join(psdDir,*depth)

    for f in os.listdir(fromDir):
        if f.startswith("unuse"):
            continue

        fromFile = os.path.join(fromDir,f)
        if os.path.isdir(fromFile):
            dp = depth[:]
            dp.append(f)
            walkDir(dp)
        else:
            ext = os.path.splitext(f)[-1]
            if ext != ".psd":
                continue

            parsePsd(fromFile,depth)

def parsePsd(fromFile,depth):
    """
    解析psd
    :param fromFile:
    :param toFile:
    :return:
    """

    global curPsdName
    curPsdName = os.path.split(fromFile)[1]

    #print u"开始解析psd: {}".format(curPsdName)

    global generateExml
    global generateImg
    if generateExml:
        psdToExml(fromFile,depth)
    if generateImg:
        psdToImg(fromFile,depth)

def psdToExml(fromFile,depth):
    """
    psd转换成exml
    :param fromFile:
    :param depth:
    :return:
    """

    global exmlDir
    global replaceFile

    psdName = os.path.split(fromFile)[1]
    name = psdName.split(r".")[0]

    toFile = os.path.join(exmlDir,*depth)
    if not os.path.exists(toFile):
        os.makedirs(toFile)
    toFile = os.path.join(toFile,psdName)
    toFile = toFile.replace(r".psd",r"Skin.exml")

    if os.path.exists(toFile) and not replaceFile:
        return

    psd = PSDImage.load(fromFile)

    content = u""
    content += u"<?xml version='1.0' encoding='utf-8'?>"
    content += u'\n'
    content += u'<e:Skin class="{}" width="{}" height="{}" xmlns:e="http://ns.egret.com/eui" xmlns:w="http://ns.egret.com/wing" xmlns:n="*">'.format(
        name + "Skin", psd.header.width, psd.header.height)
    content += u'\n'
    content += groupToExml(psd, 0)
    content += u'</e:Skin>'

    if os.path.exists(toFile):
        os.unlink(toFile)

    try:
        with open(toFile, mode="w+") as f:
            f.write(content)
        print u"生成 exml 成功：  " + toFile
    except Exception, e:
        print u"生成 exml 失败：  " + toFile

def groupToExml(group, depth):
    """
    把图层组转成exml字符串
    :param layer:
    :param isRoot:
    :return:
    """
    layers = group.layers
    layers.reverse()

    content = ""
    for layer in layers:
        if isLayerLocked(layer):
            # 如果锁定了，不解析
            continue
        if isGroup(layer):
            name = getLayerName(layer)
            if name.startswith(r"$"):
                content += specialGroupToExml(layer,depth+1)
            else:
                content += normalGroupToExml(layer,depth+1)
        else:
            if isLabel(layer):
                content += labelToExml(layer, depth+1)
            else:
                content += layerToExml(layer, depth+1)
    return content

def labelToExml(layer,depth):
    """
    layer转成exml字符串
    :param layer:
    :return:
    """

    prefix = depth * "    "
    content = ""
    content += u'{}<e:Label '.format(prefix)

    prop = getLayerProp(layer)
    for k, v in prop.iteritems():
        content += u'{0}="{1}" '.format(k, v)
    content += u'/>'
    content += u'\n'

    return content

def layerToExml(layer,depth):
    """
    layer转成exml字符串
    :param layer:
    :return:
    """

    global s9Map
    global smartSource

    prefix = depth * "    "
    content = ""
    content += u'{}<e:Image '.format(prefix)

    prop = getLayerProp(layer)

    #智能选择资源
    src = prop.get("source","")
    if src and smartSource:
        src = getLayerSmartSrc(src)
        prop["source"] = src

    for k, v in prop.iteritems():
        content += u'{0}="{1}" '.format(k, v)

    name = getLayerName(layer)
    s9Info = s9Map.get(name,None)
    if s9Info:
        content += u'scale9Grid="{}" '.format(s9Info)

    content += u'/>'
    content += u'\n'

    return content

def getLayerSmartSrc(sourceName):
    """
    获得智能资源名
    :param src:
    :return:
    """
    global curPsdName

    currentPsdFile = curPsdName.split(r".")[0]

    if resNameMap.has_key(sourceName):
        folders = resNameMap[sourceName]
        if currentPsdFile + "_json" in folders:
            return currentPsdFile + r"_json." + sourceName
        if "common_json" in folders:
            return r"common_json." + sourceName
        return sourceName

    return sourceName

def specialGroupToExml(layer,depth):
    """
    特殊组转成exml字符串
    :param layer:
    :return:
    """
    name = layer.name.strip()[1:]
    if name.startswith("Button"):
        return ButtonGroupToExml(layer,depth)
    elif name.startswith("Bone"):
        return BoneGroupToExml(layer,depth)
    elif name.startswith("Skin"):
        return SkinGroupToExml(layer,depth)
    elif name.startswith("e_") or name.startswith("n_"):
        return CommonGroupToExml(layer,depth)

    return ""

def ButtonGroupToExml(layer,depth):
    """
    Button组
    :param layer:
    :param depth:
    :return:
    """

    prefix = depth * "    "
    content = ""
    content += u'{}<n:BaseButton '.format(prefix)

    prop = getLayerProp(layer,True)

    for k, v in prop.iteritems():
        content += u'{0}="{1}" '.format(k, v)

    content += u'>'
    content += u'\n'

    layers = layer.layers
    layers.reverse()

    for l in layers:
        if isLayerLocked(l):
            # 如果锁定了，不解析
            continue
        if isGroup(l):
            name = getLayerName(l)
            if name.startswith(r"$"):
                content += specialGroupToExml(l,depth+1)
            else:
                content += normalGroupToExml(l,depth+1)
        else:
            if isLabel(l):
                content += labelToExml(l, depth+1)
            else:
                content += layerToExml(l, depth+1)

    content += u'{}</n:BaseButton>'.format(prefix)
    content += u'\n'

    return content

def BoneGroupToExml(layer,depth):
    """
    龙骨组
    :param layer:
    :param depth:
    :return:
    """

    prefix = depth * "    "
    content = ""

    content += u'{}<e:Group '.format(prefix)
    prop = getLayerProp(layer)
    prop["x"] = 0
    prop["y"] = 0
    prop["width"] = "100%"
    prop["height"] = "100%"

    for k, v in prop.iteritems():
        content += u'{0}="{1}" '.format(k, v)
    content += u'>'
    content += u'\n'

    layers = layer.layers
    layers.reverse()

    prefix2 = (depth + 1) * "    "
    for l in layers:
        name = getLayerName(l)
        name = name.replace(r"_ske","")
        attr = getLayerCustomProp(l)
        x,y,_,__ = getLayerSize(l)

        content += u'{}<n:BaseBone x="{}" y="{}" name="{}" '.format(prefix2,x,y,name)
        for k, v in attr.iteritems():
            content += u'{0}="{1}" '.format(k, v)
        content += u'/>\n'

    content += u'{}</e:Group>\n'.format(depth * u"    ")

    return content


def SkinGroupToExml(layer,depth):
    """
    psd层
    :param layer:
    :param depth:
    :return:
    """

    prefix = depth * "    "
    content = ""

    layers = layer.layers
    layers.reverse()

    for l in layers:
        name = getLayerName(l)
        name += "Skin"
        prop = getLayerProp(l)
        if prop.has_key("source"):
            del prop["source"]

        content += u'{}<e:Panel '.format(prefix)
        for k, v in prop.iteritems():
            content += u'{0}="{1}" '.format(k, v)
        content += u'skinName="{}" '.format(name)
        content += u'/>\n'

    return content


def CommonGroupToExml(layer,depth):
    """
    自定义层
    :param layer:
    :param depth:
    :return:
    """

    prefix = depth * "    "
    content = ""

    name = getLayerName(layer)
    prop = getLayerCustomProp(layer)

    if name.startswith("$e_"):
        name = name.replace(r"$e_","")
        content += u'{}<e:{} '.format(prefix,name)
    else:
        name = name.replace(r"$n_","")
        content += u'{}<n:{} '.format(prefix,name)

    for k, v in prop.iteritems():
        content += u'{0}="{1}" '.format(k, v)
    content += u'/>\n'

    return content


def normalGroupToExml(group,depth):
    """
    普通组转成exml字符串
    :param layer:
    :return:
    """
    prefix = depth * "    "
    content = ""

    content += u'{}<e:Group '.format(prefix)
    prop = getLayerProp(group)
    prop["x"] = 0
    prop["y"] = 0
    prop["width"] = "100%"
    prop["height"] = "100%"

    for k, v in prop.iteritems():
        content += u'{0}="{1}" '.format(k, v)
    content += u'>'

    layers = group.layers
    layers.reverse()

    for layer in layers:
        if isLayerLocked(layer):
            # 如果锁定了，不解析
            continue
        if isGroup(layer):
            name = getLayerName(layer)
            if name.startswith(r"$"):
                content += specialGroupToExml(group, depth + 1)
            else:
                content += normalGroupToExml(group, depth + 1)
        else:
            if isLabel(layer):
                content += labelToExml(layer, depth + 1)
            else:
                content += layerToExml(layer, depth + 1)

    content += u'{}</e:Group>'.format(prefix)
    content += u'\n'
    return content


def psdToImg(fromFile,depth):
    """
    psd导出img
    必须保证同名的图层是同一张图片
    :param fromFile:
    :param depth:
    :return:
    """
    global imgDir

    psdName = os.path.split(fromFile)[1]
    name = psdName.split(r".")[0]

    toFile = os.path.join(imgDir, *depth)
    toFile = os.path.join(toFile,name)

    if os.path.exists(toFile):
        shutil.rmtree(toFile)
    if not os.path.exists(toFile):
        os.makedirs(toFile)

    psd = PSDImage.load(fromFile)

    groupToImg(psd,toFile)


def groupToImg(group,imgDir):
    """
    把一个图层下面的
    :param layer:
    :return:
    """
    global generateLabelImg
    for l in group.layers:
        if isLayerLocked(l):
            continue
        if isGroup(l):
            groupToImg(l,imgDir)
        elif isLabel(l):
            if generateLabelImg:
                layerToImg(l,imgDir)
        else:
            layerToImg(l,imgDir)


def layerToImg(layer,imgDir):
    """
    图层保存为png
    :param layer:
    :param imgDir:
    :return:
    """
    idx = 1
    if isLabel(layer):
        name = "label_{}.png".format(idx)
        while os.path.exists(os.path.join(imgDir,name)):
            idx += 1
            name = "label_{}.png".format(idx)
    else:
        name = getLayerName(layer) + ".png"

    imgFile = os.path.join(imgDir,name)

    if os.path.exists(imgFile):
        return

    layer_image = layer.as_PIL()
    layer_image.save(imgFile)


def main():
    try:
        configParser()
        readS9Info()
        readResFile()
        walkDir([])
    except Exception,e:
        print_call_stack()


if __name__ == "__main__":
    main()