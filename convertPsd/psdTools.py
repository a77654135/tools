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
import re
from collections import OrderedDict


from common.ColorLogger import getUZWLogger
from psd_tools import PSDImage,Layer,Group

logger = getUZWLogger()


def rgbToHex(r,g,b):
    """
    rgb转十六进制
    :param r:
    :param g:
    :param b:
    :return:
    """
    r = hex(int(r))[2:]
    g = hex(int(g))[2:]
    b = hex(int(b))[2:]
    r = "0" + r if len(r) < 2 else "" + r
    g = "0" + g if len(g) < 2 else "" + g
    b = "0" + b if len(b) < 2 else "" + b
    return r"0x{}{}{}".format(r, g, b)

def isLayer(layer):
    """
    是否是图层
    :param layer:
    :return:
    """
    return isinstance(layer, Layer) and layer.text_data is None

def isLabel(layer):
    """
    是否是label
    :param layer:
    :return:
    """
    return isinstance(layer, Layer) and layer.text_data is not None

def isGroup(layer):
    """
    是否是图层组
    :param layer:
    :return:
    """
    return isinstance(layer,Group)

def getPsdSize(psd):
    """
    获得PSD的宽高
    :param psd:
    :return:
    """
    return int(psd.header.width),int(psd.header.height)

def getLayerName(layer):
    """
    获得layer的名字
    name 副本 :k=v;k=v;
    :param layer:
    :return:
    """
    return layer.name.split(r":")[0].split(r" ")[0].strip()

def getLayerVisible(layer):
    """
    图层是否可见
    :param layer:
    :return:
    """
    return layer.visible

def getLayerAlpha(layer):
    """
    获取alpha
    :param layer:
    :return:
    """
    try:
        opacity = layer.opacity
        if opacity == 255:
            return 1
        else:
            return round(opacity/255.0,2)
    except:
        return 1

def getLayerSize(layer):
    """
    获取图层位置大小
    :param layer:
    :return:
    """
    try:
        box = layer.bbox
        return int(box.x1), int(box.y1), int(box.width), int(box.height)
    except Exception, e:
        return 0, 0, 0, 0

def isLayerLocked(layer):
    """
    图层是否锁定
    :param layer:
    :return:
    """
    assert isinstance(layer,Layer) or isinstance(layer,Group)
    locked = False
    try:
        locked = layer._info[9][0]
    except:
        pass
    return locked

def parseList(lst):
    hasKh = False
    for l in lst:
        if l.strip() == r"[" or l.strip() == r"]":
            hasKh = True
            break
    if hasKh:
        nl = []
        inKh = False
        for l in lst:
            if l.strip() == r"[" and inKh == False:
                inKh = True
                continue
            if inKh and l.strip() == r"]":
                inKh = False
                break
            if inKh:
                nl.append(l)
        return nl
    else:
        return " ".join(lst)

def parseEngineData(layer):
    """
    解析图层原始数据
    :param layer:
    :return:
    """
    try:
        TySh = layer._tagged_blocks["TySh"][9][2]
        for tp in TySh:
            if tp[0] == "EngineData":
                engineData = tp[1][0]
                break
        if isinstance(engineData,str) and engineData != "":
            lines = engineData.splitlines()
            newLines = []
            for line in lines:
                ln = line.strip()
                if ln == "":
                    continue
                newLines.append(ln)

            ed = {}
            stack = [ed]
            for idx, ln in enumerate(newLines):
                stackLen = len(stack)
                if stackLen <= 0:
                    break
                lastData = stack[stackLen - 1]

                if ln == "<<":
                    continue
                if ln.startswith(r"/") and len(ln.split(r" ")) == 1 and newLines[idx + 1] == "<<":
                    key = ln.lstrip(r"/")
                    data = {}
                    lastData[key] = data
                    stack.append(data)
                if ln.startswith(r"/") and len(ln.split(r" ")) > 1:
                    lnlen = len(ln)
                    if ln[lnlen - 1] == r"[":
                        key = ln.lstrip(r"/")
                        key = key.rstrip(r" [")
                        data = {}
                        lastData[key] = data
                        stack.append(data)
                        continue
                    attrs = ln.split(r" ")
                    key = attrs[0].lstrip(r"/")
                    value = parseList(attrs[1:])
                    lastData[key] = value
                if ln == ">>":
                    stack = stack[0:stackLen - 1]
            return ed
        else:
            return None
    except Exception,e:
        #print "parseEngineData error: " + e.message
        return None

def getLabelSize(layer):
    assert isLabel(layer)
    try:
        ed = parseEngineData(layer)
        if ed is None:
            return 18
        else:
            return int(ed["EngineDict"]["StyleRun"]["RunArray"]["StyleSheet"]["StyleSheetData"]["FontSize"])
    except Exception,e:
        return 18

def getLabelColor(label):
    assert isinstance(label,Layer) and label.text_data is not None
    try:
        ed = parseEngineData(label)
        if ed is None:
            return "0xffffff", 1
        else:
            colorInfo = ed["EngineDict"]["StyleRun"]["RunArray"]["StyleSheet"]["StyleSheetData"]["FillColor"]["Values"]
            a, r, g, b = colorInfo[0], colorInfo[1], colorInfo[2], colorInfo[3]
            return rgbToHex(round(float(r) * 255), round(float(g) * 255), round(float(b) * 255)), a
    except Exception,e:
        return "0xffffff", 1

def getListTupleAttr(lst,key):
    for l in lst:
        if l[0].strip() == key:
            return l[1]
    return None

def getLabelStrokeInfo(label):
    assert isinstance(label,Layer) and label.text_data is not None
    try:
        #家里ps的版本

        # info = label._tagged_blocks["lfx2"][2][2]
        # for item in info:
        #     if item[0] == "FrFX":
        #         strokeInfo = item[1][2]
        #         enabled = strokeInfo[0][1][0]
        #         size = strokeInfo[5][1][1]
        #         clr = strokeInfo[6][1][2]
        #         r,g,b = clr[0][1][0],clr[1][1][0],clr[2][1][0]
        #         #print enabled,size,r
        #         return enabled,size,rgbToHex(round(r),round(g),round(b))
        # return False,0,"0xffffff"

        #公司的ps版本
        info = label._tagged_blocks["lfx2"][2][2]
        for item in info:
            if item[0] == "FrFX":
                frfx = item[1][2]
                enabled = getListTupleAttr(frfx,"enab")[0] if getListTupleAttr(frfx,"enab") is not None else False
                size = getListTupleAttr(frfx,"Sz")[1] if getListTupleAttr(frfx,"Sz") is not None else 0
                clr = getListTupleAttr(frfx,"Clr")[2]
                if clr is not None:
                    r, g, b = clr[0][1][0], clr[1][1][0], clr[2][1][0]
                else:
                    r,g,b, = 0,0,0
                return enabled, size, rgbToHex(round(r), round(g), round(b))
        return False, 0, "0xffffff"

    except Exception,e:
        return False,0,"0xffffff"

def getLabelText(layer):
    """
    获取label文字
    :param layer:
    :return:
    """
    if not isLabel(layer):
        return ""
    try:
        tex = layer.text_data.text
        # tex = tex.replace("\n","")
        return tex
    except:
        return "unknown"

def getLayerCustomProp(layer):
    """
    获取图层自定义属性
    name 副本 :k=v;k=v;
    :param layer:
    :return:
    """
    ret = {}

    names = layer.name.split(r":")
    if len(names) > 1:
        attrStr = names[-1]
        if not re.search(r"=", attrStr):
            return ret
        kvList = attrStr.split(";")
        for item in kvList:
            k,v = item.strip().split(r"=")
            ret[k.strip()] = v.strip()

    return ret

def getLayerProp(layer,isButton=False):
    """
    获得图层属性
    自定义属性权重高于原始属性
    :param layer:
    :return:
    """
    ret = OrderedDict()
    customProp = getLayerCustomProp(layer)
    x, y, w, h = getLayerSize(layer)
    ret["x"] = x
    ret["y"] = y
    ret["width"] = w
    ret["height"] = h

    if customProp.has_key("id"):
        ret["id"] = customProp["id"]
        del customProp["id"]
    if customProp.has_key("name"):
        ret["name"] = customProp["name"]
        del customProp["name"]
    if isButton and customProp.has_key("id"):
        customProp["name"] = customProp["id"]

    visible = getLayerVisible(layer)
    if not visible:
        ret["visible"] = "false"
    alpha = getLayerAlpha(layer)
    if alpha != 1:
        ret["alpha"] = alpha

    if isButton:
        ret["touchEnabled"] = "true"
    else:
        ret["touchEnabled"] = "false"

    if isGroup(layer):
        ret["touchChildren"] = "false"

    if isLabel(layer):
        ret["fontFamily"] = "Microsoft YaHei"
        ret["text"] = getLabelText(layer)
        se, sz, sc = getLabelStrokeInfo(layer)
        if se:
            ret["stroke"] = int(sz)
            ret["strokeColor"] = sc
        ret["size"] = getLabelSize(layer)
        color, alpha = getLabelColor(layer)
        ret["textColor"] = color
        if float(alpha) != float(1):
            ret["alpha"] = alpha
    elif isLayer(layer):
        name = getLayerName(layer)
        ret["source"] = "{}_png".format(name)

    for k in customProp:
        ret[k] = customProp[k]

    return ret





def main(argv):
    p = r"F:\work\n5\roll\art\psd\panel\mailPanel\MailContent.psd"
    psd = PSDImage.load(p)
    print ""


if __name__ == '__main__':
    main(sys.argv[1:])


