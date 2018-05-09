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

from collections import OrderedDict
from psdTools import *
from psd_tools import PSDImage,Layer,Group
from common.ExceptCallStack import print_call_stack




curPsdName = ""

psdDir = ""
uiDir = ""
generateUi = True
replaceFile = False

imgDir = ""
imgRoot = ""
generateImg = False
generateLabelImg = False

exportJson = False
minJson = False
jsonDir = ""
jsonContent = {}
curContent = None

compId = 0

currentDepth = None

def getCompId():
    global compId
    compId += 1
    return compId


def getLayerProp_laya(layer,isButton=False):
    """
    获得图层属性
    自定义属性权重高于原始属性
    这个格式是ui方便使用
    :param layer:
    :return:
    """
    global imgDir
    global imgRoot
    global currentDepth
    global curPsdName

    absImgDir = os.path.join(os.path.abspath(imgDir),*currentDepth)
    absImgRoot = os.path.abspath(imgRoot)

    relative = absImgDir.replace(absImgRoot,"")
    relative = "/".join(relative.split("\\"))
    if relative.startswith("/"):
        relative = relative[1:]

    ret = OrderedDict()
    customProp = getLayerCustomProp(layer)
    x, y, w, h = getLayerSize(layer)
    ret["x"] = x
    ret["y"] = y
    ret["width"] = w
    ret["height"] = h

    if customProp.has_key("id"):
        ret["var"] = customProp["id"]
        if isButton:
            ret["name"] = customProp["id"]
        del customProp["id"]
    if customProp.has_key("name"):
        if not isButton:
            ret["name"] = customProp["name"]
        del customProp["name"]


    visible = getLayerVisible(layer)
    if not visible:
        ret["visible"] = False
    alpha = getLayerAlpha(layer)
    if alpha != 1:
        ret["alpha"] = alpha

    if isButton:
        ret["mouseEnabled"] = True
    else:
        ret["mouseEnabled"] = False

    if isGroup(layer):
        ret["mouseEnabled"] = True

    if isLabel(layer):
        ret["font"] = "Microsoft YaHei"
        ret["text"] = getLabelText(layer)
        se, sz, sc = getLabelStrokeInfo(layer)
        if se:
            ret["stroke"] = int(sz)
            ret["strokeColor"] = sc
        ret["fontSize"] = getLabelSize(layer)
        color, alpha = getLabelColor(layer)
        ret["color"] = color
        if float(alpha) != float(1):
            ret["alpha"] = alpha
    elif isLayer(layer):
        name = getLayerName(layer)
        ret["skin"] = "{}/{}/{}.png".format(relative, curPsdName.split(".")[0], name)

    for k in customProp:
        ret[k] = customProp[k]

    result = OrderedDict()

    if isGroup(layer):
        tp = "Box"
    elif isLabel(layer):
        tp = "Label"
    else:
        tp = "Image"

    label = tp
    if ret.has_key("var"):
        label += "({})".format(ret["var"])
    elif ret.has_key("name"):
        label += "({})".format(ret["name"])

    result["x"] = 15
    result["type"] = tp
    result["props"] = ret
    result["label"] = label

    return result


def configParser():
    """
    解析配置文件
    :return:
    """
    global psdDir
    global uiDir
    global imgDir
    global imgRoot
    global generateUi
    global generateImg
    global generateLabelImg
    global replaceFile

    parser = configparser.ConfigParser()
    parser.read("config.ini",encoding="utf-8")

    psdDir = os.path.abspath(parser.get("laya", "psdDir"))

    generateUi = parser.getboolean("laya","generateUi")
    uiDir = os.path.abspath(parser.get("laya", "uiDir"))
    replaceFile = parser.getboolean("laya","replaceFile")

    generateImg = parser.getboolean("laya","generateImg")
    generateLabelImg = parser.getboolean("laya","generateLabelImg")
    imgDir = os.path.abspath(parser.get("laya", "imgDir"))
    imgRoot = os.path.abspath(parser.get("laya", "imgRoot"))


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
    global uiDir
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
    global currentDepth
    currentDepth = depth
    curPsdName = os.path.split(fromFile)[1]

    #print u"开始解析psd: {}".format(curPsdName)

    global generateUi
    global generateImg
    global exportJson

    if generateUi:
        psdToUi(fromFile,depth)
    if generateImg:
        psdToImg(fromFile,depth)

def psdToUi(fromFile,depth):
    """
    psd转换成json格式
    :param fromFile:
    :param depth:
    :return:
    """
    global uiDir
    global replaceFile
    global jsonContent
    global curContent
    global minJson

    psdName = os.path.split(fromFile)[1]
    name = psdName.split(r".")[0]

    toFile = os.path.join(uiDir, *depth)
    if not os.path.exists(toFile):
        print toFile
        os.makedirs(toFile)
    toFile = os.path.join(toFile, psdName)
    toFile = toFile.replace(r".psd", r".ui")

    if os.path.exists(toFile) and not replaceFile:
        return

    psd = PSDImage.load(fromFile)
    jsonContent = OrderedDict()
    curContent = jsonContent

    curContent["x"] = 0
    curContent["type"] = "View"
    curContent["selectedBox"] = 1
    curContent["selecteID"] = 2
    curContent["props"] = OrderedDict()
    curContent["props"]["width"] = psd.header.width
    curContent["props"]["height"] = psd.header.height
    curContent["props"]["sceneColor"] = "#ffffff"
    curContent["nodeParent"] = -1
    curContent["label"] = "View"
    curContent["isOpen"] = True
    curContent["isDirectory"] = True
    curContent["isAniNode"] = True
    curContent["hasChild"] = True
    curContent["compId"] = getCompId()
    curContent["child"] = []

    layers = psd.layers
    layers.reverse()

    for layer in layers:
        if isLayerLocked(layer):
            continue
        if isGroup(layer):
            groupToJson(layer,curContent)
        else:
            layerToJson(layer,curContent)


    if os.path.exists(toFile):
        os.unlink(toFile)

    try:
        with open(toFile, mode="w") as f:
            if minJson:
                json.dump(jsonContent, f)
            else:
                json.dump(jsonContent, f, indent=4)
        print u"生成 json 成功：  " + toFile
    except Exception, e:
        print u"生成 json 失败：  " + toFile


def groupToJson(layer,content):
    """
    图层组转换成json对象
    :param layer:
    :param curContent:
    :return:
    """
    name = getLayerName(layer)
    if name.startswith(r"$"):
        specialGroupToJson(layer, content)
    else:
        normalGroupToJson(layer, content)


def specialGroupToJson(layer, content):
    name = layer.name.strip()[1:]
    if name.startswith("Button"):
        ButtonGroupToJson(layer, content)
    elif name.startswith("Bone"):
        BoneGroupToJson(layer, content)
    elif name.startswith("Skin"):
        SkinGroupToJson(layer, content)
    elif name.startswith("e_") or name.startswith("n_"):
        CommonGroupToJson(layer, content)


def ButtonGroupToJson(layer,content):
    """
    Button组
    :param layer:
    :param depth:
    :return:
    """

    prop = getLayerProp_laya(layer,True)
    prop["cls"] = "n:BaseButton"
    prop["children"] = []
    propProcess(prop)
    content["children"].append(prop)

    layers = layer.layers
    layers.reverse()

    for l in layers:
        if isLayerLocked(l):
            # 如果锁定了，不解析
            continue
        if isGroup(l):
            name = getLayerName(l)
            if name.startswith(r"$"):
                specialGroupToJson(l,prop)
            else:
                normalGroupToJson(l,prop)
        else:
            layerToJson(l, prop)


def BoneGroupToJson(layer,content):
    """
    龙骨组
    :param layer:
    :param depth:
    :return:
    """

    prop = getLayerProp_laya(layer)
    prop["x"] = 0
    prop["y"] = 0
    prop["width"] = "100%"
    prop["height"] = "100%"
    prop["cls"] = "e:Group"
    prop["children"] = []
    propProcess(prop)
    content["children"].append(prop)

    layers = layer.layers
    layers.reverse()

    for l in layers:
        name = getLayerName(l)
        name = name.replace(r"_tex","")
        attr = getLayerCustomProp(l)
        x,y,_,__ = getLayerSize(l)
        attr["x"] = x
        attr["y"] = y
        attr["name"] = name
        attr["cls"] = "n:BaseBone"
        propProcess(attr)
        prop["children"].append(attr)



def SkinGroupToJson(layer,content):
    """
    psd层
    :param layer:
    :param depth:
    :return:
    """
    layers = layer.layers
    layers.reverse()

    for l in layers:
        name = getLayerName(l)
        name += "Skin"
        prop = getLayerProp_laya(l)
        if prop.has_key("source"):
            del prop["source"]

        prop["cls"] = "e:Panel"
        prop["skinName"] = name
        propProcess(prop)
        content["children"].append(prop)


def CommonGroupToJson(layer,content):
    """
    自定义层
    :param layer:
    :param depth:
    :return:
    """

    name = getLayerName(layer)
    prop = getLayerCustomProp(layer)

    if name.startswith("$e_"):
        name = name.replace(r"$e_","")
        prop["cls"] = "e:{}".format(name)
    else:
        name = name.replace(r"$n_","")
        prop["cls"] = "n:{}".format(name)

    propProcess(prop)
    content["children"].append(prop)


def normalGroupToJson(group, content):
    prop = getLayerProp_laya(group)

    prop["props"]["x"] = 0
    prop["props"]["y"] = 0
    prop["props"]["width"] = curContent["props"]["width"]
    prop["props"]["height"] = curContent["props"]["height"]
    prop["nodeParent"] = curContent["compId"]
    prop["isOpen"] = True
    prop["isDirectory"] = True
    prop["isAniNode"] = True
    prop["hasChild"] = True
    prop["compId"] = getCompId()
    prop["child"] = []

    content["child"].append(prop)

    layers = group.layers
    if len(layers):
        for layer in layers:
            if isLayerLocked(layer):
                continue
            if isGroup(layer):
                groupToJson(layer, prop)
            else:
                layerToJson(layer, prop)
    else:
        prop["hasChild"] = False


def layerToJson(layer,content):
    """
    图层转换成json对象
    :param layer:
    :param curContent:
    :return:
    """
    prop = getLayerProp_laya(layer)

    prop["nodeParent"] = curContent["compId"]
    prop["isOpen"] = True
    prop["isDirectory"] = False
    prop["isAniNode"] = True
    prop["hasChild"] = False
    prop["compId"] = getCompId()
    prop["child"] = []

    content["child"].append(prop)


def propProcess(prop):
    """
    属性处理
    :param prop:
    :return:
    """
    for k, v in prop.iteritems():
        if v == "true":
            prop[k] = True
        if v == "false":
            prop[k] = False
        if k == "x":
            prop[k] = int(v)
        if k == "y":
            prop[k] = int(v)
        if k == "width":
            val = v
            if isinstance(val,str) and val.endswith("%"):
                del prop[k]
                val = val.replace("%","")
                prop["percentWidth"] = int(val)
            else:
                prop[k] = int(val)
        if k == "height":
            val = v
            if isinstance(val, str) and val.endswith("%"):
                del prop[k]
                val = val.replace("%","")
                prop["percentHeight"] = int(val)
            else:
                prop[k] = int(val)



def psdToUi1(fromFile,depth):
    """
    psd转换成Ui
    :param fromFile:
    :param depth:
    :return:
    """

    global uiDir
    global replaceFile

    psdName = os.path.split(fromFile)[1]
    name = psdName.split(r".")[0]

    toFile = os.path.join(uiDir,*depth)
    if not os.path.exists(toFile):
        os.makedirs(toFile)
    toFile = os.path.join(toFile,psdName)
    toFile = toFile.replace(r".psd",r".ui")

    if os.path.exists(toFile) and not replaceFile:
        return

    psd = PSDImage.load(fromFile)

    content = u""
    content += u"<?xml version='1.0' encoding='utf-8'?>"
    content += u'\n'
    content += u'<e:Skin class="{}" width="{}" height="{}" xmlns:e="http://ns.egret.com/eui" xmlns:w="http://ns.egret.com/wing" xmlns:n="*">'.format(
        name + "Skin", psd.header.width, psd.header.height)
    content += u'\n'
    content += groupToUi(psd, 0)
    content += u'</e:Skin>'

    if os.path.exists(toFile):
        os.unlink(toFile)

    try:
        with open(toFile, mode="w+") as f:
            f.write(content)
        print u"生成 Ui 成功：  " + toFile
    except Exception, e:
        print u"生成 Ui 失败：  " + toFile

def groupToUi(group, depth):
    """
    把图层组转成Ui字符串
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
                content += specialGroupToUi(layer,depth+1)
            else:
                content += normalGroupToUi(layer,depth+1)
        else:
            if isLabel(layer):
                content += labelToUi(layer, depth+1)
            else:
                content += layerToUi(layer, depth+1)
    return content

def labelToUi(layer,depth):
    """
    layer转成Ui字符串
    :param layer:
    :return:
    """

    prefix = depth * "    "
    content = ""
    content += u'{}<e:Label '.format(prefix)

    prop = getLayerProp_laya(layer)
    for k, v in prop.iteritems():
        content += u'{0}="{1}" '.format(k, v)
    content += u'/>'
    content += u'\n'

    return content

def layerToUi(layer,depth):
    """
    layer转成Ui字符串
    :param layer:
    :return:
    """

    global s9Map
    global smartSource

    prefix = depth * "    "
    content = ""
    content += u'{}<e:Image '.format(prefix)

    prop = getLayerProp_laya(layer)

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

def specialGroupToUi(layer,depth):
    """
    特殊组转成Ui字符串
    :param layer:
    :return:
    """
    name = layer.name.strip()[1:]
    if name.startswith("Button"):
        return ButtonGroupToUi(layer,depth)
    elif name.startswith("Bone"):
        return BoneGroupToUi(layer,depth)
    elif name.startswith("Skin"):
        return SkinGroupToUi(layer,depth)
    elif name.startswith("e_") or name.startswith("n_"):
        return CommonGroupToUi(layer,depth)

    return ""

def ButtonGroupToUi(layer,depth):
    """
    Button组
    :param layer:
    :param depth:
    :return:
    """

    prefix = depth * "    "
    content = ""
    content += u'{}<n:BaseButton '.format(prefix)

    prop = getLayerProp_laya(layer,True)

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
                content += specialGroupToUi(l,depth+1)
            else:
                content += normalGroupToUi(l,depth+1)
        else:
            if isLabel(l):
                content += labelToUi(l, depth+1)
            else:
                content += layerToUi(l, depth+1)

    content += u'{}</n:BaseButton>'.format(prefix)
    content += u'\n'

    return content

def BoneGroupToUi(layer,depth):
    """
    龙骨组
    :param layer:
    :param depth:
    :return:
    """

    prefix = depth * "    "
    content = ""

    content += u'{}<e:Group '.format(prefix)
    prop = getLayerProp_laya(layer)
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
        name = name.replace(r"_tex","")
        attr = getLayerCustomProp(l)
        x,y,_,__ = getLayerSize(l)

        content += u'{}<n:BaseBone x="{}" y="{}" name="{}" '.format(prefix2,x,y,name)
        for k, v in attr.iteritems():
            content += u'{0}="{1}" '.format(k, v)
        content += u'/>\n'

    content += u'{}</e:Group>\n'.format(depth * u"    ")

    return content


def SkinGroupToUi(layer,depth):
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
        prop = getLayerProp_laya(l)
        if prop.has_key("source"):
            del prop["source"]

        content += u'{}<e:Panel '.format(prefix)
        for k, v in prop.iteritems():
            content += u'{0}="{1}" '.format(k, v)
        content += u'skinName="{}" '.format(name)
        content += u'/>\n'

    return content


def CommonGroupToUi(layer,depth):
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


def normalGroupToUi(group,depth):
    """
    普通组转成Ui字符串
    :param layer:
    :return:
    """
    prefix = depth * "    "
    content = ""

    content += u'{}<e:Group '.format(prefix)
    prop = getLayerProp_laya(group)
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
                content += specialGroupToUi(group, depth + 1)
            else:
                content += normalGroupToUi(group, depth + 1)
        else:
            if isLabel(layer):
                content += labelToUi(layer, depth + 1)
            else:
                content += layerToUi(layer, depth + 1)

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
    print u"生成图片：{}".format(imgFile)


def main():
    try:
        configParser()
        walkDir([])
    except Exception,e:
        print_call_stack()


if __name__ == "__main__":
    main()