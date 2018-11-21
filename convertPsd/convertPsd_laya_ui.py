# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
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

#当前文件的文件夹深度
currentDepth = []
# 图片的缓存
imgMap = {}

compId = 0;

def getPropValue(obj, keys, defaultValue):
    """
    获取一个dict中的key对应的值
    :param keys:
    :param defaultValue:
    :return:
    """
    if obj is None or (type(obj) != dict and type(obj) != OrderedDict):
        return defaultValue

    data = obj
    for key in keys.split("."):
        if type(data) == dict or type(obj) == OrderedDict:
            data = data.get(key, None)
            if data is None:
                return defaultValue
        elif type(data) == list:
            try:
                key = int(key)
                data = data[key]
            except:
                return defaultValue
        else:
            return defaultValue
    return data

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

    ret = OrderedDict()
    # 获取自定义属性
    customProp = getLayerCustomProp(layer)
    x, y, w, h = getLayerSize(layer)
    ret["x"] = x
    ret["y"] = y
    ret["width"] = w
    ret["height"] = h

    if customProp.has_key("id"):
        ret["var"] = customProp["id"]
        del customProp["id"]

    visible = getLayerVisible(layer)
    if not visible:
        ret["visible"] = False
    alpha = getLayerAlpha(layer)
    if alpha != 1:
        ret["alpha"] = alpha

    if isLabel(layer):
        ret["font"] = "Aria"
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
        global imgMap
        if name in imgMap:
            # 资源中有图片
            ret["skin"] = imgMap[name]
        else:
            # 导出图片
            dirList= imgDir.split("/")
            dirList.extend(currentDepth)
            dirList.append(curPsdName.split(".")[0].lower())
            absImgDir = os.path.join(os.path.abspath(imgRoot), *dirList)
            if not os.path.exists(absImgDir):
                os.makedirs(absImgDir)
            imgFile = os.path.join(absImgDir, "{}.png".format(name))
            if not os.path.exists(imgFile):
                layer_image = layer.as_PIL()
                layer_image.save(imgFile)
                print u"生成图片：{}".format(imgFile)
            if len(dirList):
                ret["skin"] = "{}/{}.png".format("/".join(dirList), name)
            else:
                ret["skin"] = "{}.png".format(name)
    elif isButton:
        layer = layer.layers[0]
        name = getLayerName(layer)
        x, y, w, h = getLayerSize(layer)
        ret["width"] = w
        ret["height"] = h
        ret["stateNum"] = 1

        if name in imgMap:
            # 资源中有图片
            ret["skin"] = imgMap[name]
        else:
            # 导出图片
            dirList = imgDir.split("/")
            dirList.extend(currentDepth)
            dirList.append(curPsdName.split(".")[0].lower())
            absImgDir = os.path.join(os.path.abspath(imgRoot), *dirList)
            if not os.path.exists(absImgDir):
                os.makedirs(absImgDir)
            imgFile = os.path.join(absImgDir, "{}.png".format(name))
            if not os.path.exists(imgFile):
                layer_image = layer.as_PIL()
                layer_image.save(imgFile)
                print u"生成图片：{}".format(imgFile)
            if len(dirList):
                ret["skin"] = "{}/{}.png".format("/".join(dirList), name)
            else:
                ret["skin"] = "{}.png".format(name)


    for k in customProp:
        ret[k] = customProp[k]

    result = OrderedDict()

    if isGroup(layer):
        tp = "Box"
    elif isLabel(layer):
        tp = "Label"
    elif isButton:
        tp = "Button"
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
    result["compId"] = getCompId()

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
    configFile = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.ini"))
    parser.read(configFile, encoding="utf-8")

    psdDir = os.path.abspath(parser.get("laya", "psdDir"))

    generateUi = parser.getboolean("laya","generateUi")
    uiDir = os.path.abspath(parser.get("laya", "uiDir"))
    replaceFile = parser.getboolean("laya","replaceFile")

    generateImg = parser.getboolean("laya","generateImg")
    generateLabelImg = parser.getboolean("laya","generateLabelImg")
    imgDir = parser.get("laya", "imgDir")
    imgRoot = os.path.abspath(parser.get("laya", "imgRoot"))

    # temp data
    psdDir = r"D:\study\work\game_framework\art\psd\love"
    generateUi = True
    uiDir = r"D:\study\work\game_framework\client_laya\client_laya_2\laya\pages\panel\love"
    replaceFile = True
    generateImg = True
    generateLabelImg = False
    imgDir = r"panel"
    imgRoot = r"D:\study\work\game_framework\client_laya\client_laya_2\laya\assets"


def walkImgDir(path, depth=[]):
    """
    缓存所有图片
    :return:
    """
    global imgMap
    for f in os.listdir(path):
        filename = os.path.join(path, f)
        if os.path.isfile(filename):
            ext = os.path.splitext(filename)[-1]
            if ext in [".png", ".jpg"]:
                imgMap[os.path.splitext(f)[0]] = r"{}/{}".format(r"/".join(depth), f)
        elif os.path.isdir(filename):
            d = depth[:]
            d.append(f)
            walkImgDir(filename, d)


def walkPsdDir(depth=[]):
    """
    遍历psd的目录，解析psd
    :param depth:
    :return:
    """
    global psdDir
    global uiDir
    global replaceFile

    fromDir = os.path.join(psdDir, *depth)

    for f in os.listdir(fromDir):
        if f.startswith("unuse"):
            continue

        fromFile = os.path.join(fromDir, f)
        if os.path.isdir(fromFile):
            dp = depth[:]
            dp.append(f)
            walkPsdDir(dp)
        else:
            ext = os.path.splitext(f)[-1]
            if ext != ".psd":
                continue

            parsePsd(fromFile, depth)


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

    if generateUi:
        psdToUi(fromFile,depth)
    # if generateImg:
    #     psdToImg(fromFile,depth)

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

    psdName = os.path.split(fromFile)[1]
    name = psdName.split(r".")[0]

    toFile = os.path.join(uiDir, *depth)
    if not os.path.exists(toFile):
        os.makedirs(toFile)
    toFile = os.path.join(toFile, psdName)
    toFile = toFile.replace(r".psd", r".ui")

    if os.path.exists(toFile) and not replaceFile:
        return

    psd = PSDImage.load(fromFile)
    jsonContent = OrderedDict()
    curContent = jsonContent

    curContent["x"] = 0
    curContent["type"] = "BasePanel"
    curContent["selectedBox"] = 1
    curContent["selecteID"] = 2
    curContent["searchKey"] = "BasePanel"
    curContent["props"] = OrderedDict()
    curContent["props"]["width"] = psd.header.width
    curContent["props"]["height"] = psd.header.height
    curContent["props"]["sceneColor"] = "#000000"
    curContent["nodeParent"] = -1
    curContent["label"] = "BasePanel"
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


    cameraObj = OrderedDict()
    cameraObj["rotation"] = [0, 1, 0, 0]
    cameraObj["position"] = [0, 0, 0]
    curContent["cameraInfo"] = cameraObj

    animObj = OrderedDict()
    animObj["nodes"] = []
    animObj["name"] = "ani1"
    animObj["id"] = 1
    animObj["frameRate"] = 24
    animObj["action"] = 0
    curContent["animations"] = []
    curContent["animations"].append(animObj)

    if os.path.exists(toFile):
        os.unlink(toFile)

    try:
        with open(toFile, mode="w") as f:
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
    # 目前只有Button
    if name.startswith("Button"):
        ButtonGroupToJson(layer, content)
    # elif name.startswith("Bone"):
    #     BoneGroupToJson(layer, content)
    # elif name.startswith("Skin"):
    #     SkinGroupToJson(layer, content)
    # elif name.startswith("e_") or name.startswith("n_"):
    #     CommonGroupToJson(layer, content)


def ButtonGroupToJson(layer,content):
    """
    Button组
    :param layer:
    :param depth:
    :return:
    """

    prop = getLayerProp_laya(layer,True)
    prop["props"]["x"] -= getPropValue(content, "props.x", 0)
    prop["props"]["y"] -= getPropValue(content, "props.y", 0)
    prop["props"]["x"] += int(prop["props"]["width"]/2)
    prop["props"]["y"] += int(prop["props"]["height"]/2)
    prop["props"]["anchorX"] = prop["props"]["anchorY"] = 0.5
    prop["child"] = [
                {
                    "type":"Script",
                    "switchAble":True,
                    "source":"src/common/component/ScaleButton.ts",
                    "searchKey":"Script,ScaleButton",
                    "removeAble":True,
                    "props":{},
                    "nodeParent":prop["compId"],
                    "label":"ScaleButton",
                    "isDirectory":False,
                    "isAniNode":True,
                    "hasChild":False,
                    "compId":getCompId(),
                    "child":[
                        ]
                }]
    # propProcess(prop)
    content["child"].append(prop)

    # layers = layer.layers
    # layers.reverse()

    # for l in layers:
    #     if isLayerLocked(l):
    #         # 如果锁定了，不解析
    #         continue
    #     if isGroup(l):
    #         name = getLayerName(l)
    #         if name.startswith(r"$"):
    #             specialGroupToJson(l,prop)
    #         else:
    #             normalGroupToJson(l,prop)
    #     else:
    #         layerToJson(l, prop)


def normalGroupToJson(group, content):
    prop = getLayerProp_laya(group)

    prop["props"]["x"] -= getPropValue(content, "props.x", 0)
    prop["props"]["y"] -= getPropValue(content, "props.y", 0)

    prop["nodeParent"] = curContent["compId"]
    prop["isOpen"] = True
    prop["isDirectory"] = True
    prop["isAniNode"] = True
    prop["hasChild"] = True
    prop["compId"] = getCompId()
    prop["child"] = []

    content["child"].append(prop)

    layers = group.layers
    layers.reverse()
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


def layerToJson(layer, content):
    """
    图层转换成json对象
    :param layer:
    :param curContent:
    :return:
    """
    prop = getLayerProp_laya(layer)

    prop["props"]["x"] -= getPropValue(content, "props.x", 0)
    prop["props"]["y"] -= getPropValue(content, "props.y", 0)

    prop["nodeParent"] = curContent["compId"]
    prop["isOpen"] = True
    prop["isDirectory"] = False
    prop["isAniNode"] = True
    prop["hasChild"] = False
    prop["compId"] = getCompId()
    prop["child"] = []

    content["child"].append(prop)



def main():
    try:
        global imgRoot
        global imgMap
        configParser()
        walkImgDir(imgRoot, [])
        # print imgMap
        walkPsdDir([])
        # walkDir([])
    except Exception,e:
        print_call_stack()


if __name__ == "__main__":
    main()