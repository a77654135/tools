# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

"""
把排行榜的itemRender.exml转成微信开放数据域的坐标，大小数据，在开放数据域中，用一个方法直接生成排行榜数据
生成的排行榜数据可以在主域中进行显示
"""

import os
import getopt
import xml.sax
import re
import json
import traceback
import collections

exmlFile = ""

assetsUrl = {
    # 底部区域
    "rank_bg_1": "openDataContext/assets/rank_bg_1.png",
    "rank_bg_2": "openDataContext/assets/rank_bg_2.png",
    # 排名图标
    "rank_item_1": "openDataContext/assets/rank_item_1.png",
    "rank_item_2": "openDataContext/assets/rank_item_2.png",
    "rank_item_3": "openDataContext/assets/rank_item_3.png"
}
assetsConf = []



class ExmlHandler( xml.sax.ContentHandler):
    """
    <e:Image width="684" height="107" touchEnabled="false" source="rank_bg_1_png" />
    <e:Image x="17" y="10" width="63" height="83" id="rankImg" touchEnabled="false" source="rank_bg_8_png" />
    <e:Image x="509" y="31" width="40" height="48" touchEnabled="false" source="main_icon_fraction_png" />
    <e:Image x="108" y="18" width="77" height="77" id="headImg" touchEnabled="false" source="main_head_png" />
    <e:Image x="103" y="13" width="88" height="87" touchEnabled="false" source="main_head_box_png" />
	<e:Label x="215" y="45" width="57" height="20" id="nameLbl" touchEnabled="false" fontFamily="Microsoft YaHei" text="BinZ" stroke="3" strokeColor="0x0e6f9c" size="18" textColor="0xffffff"/>
	<e:Label x="562" y="45" width="98" height="21" id="scoreLbl" touchEnabled="false" fontFamily="Microsoft YaHei" text="32445" size="18" textColor="0x0e6f9c" bold="true" anchorOffsetX="0"/>
    <e:Label x="36" y="42" width="27" height="33" id="rankLbl" touchEnabled="false" fontFamily="Microsoft YaHei" text="4" size="30" textColor="0x0e6f9c"  anchorOffsetX="0" anchorOffsetY="0"/>
    """

    # 元素开始事件处理
    def startElement(self, tag, attributes):
        # print "startElement:  " + tag
        #
        # for k in dict(attributes):
        #     print k,attributes[k]
        global assetsConf
        global assetsUrl

        attr = dict(attributes)
        if tag.strip() == "e:Image":
            conf = {}
            conf["type"] = "image"
            source = attr["source"].replace("_png", "")
            assetsConf.append(conf)
            id = attr.get("id", "")
            if not id:
                conf["image"] = "{}".format(source)
                assetsUrl[source] = "openDataContext/assets/{}.png".format(source)
            else:
                conf["id"] = attr["id"]
            conf["x"] = int(attr.get("x", 0))
            conf["y"] = int(attr.get("y", 0))
            if attr.has_key("width"):
                conf["width"] = int(attr["width"])
            if attr.has_key("height"):
                conf["height"] = int(attr["height"])
        elif tag.strip() == "e:Label":
            id = attr.get("id", "")
            # label必须有id
            assert id
            conf = {}
            conf["type"] = "label"
            assetsConf.append(conf)

            conf["x"] = int(attr.get("x", 0))
            conf["y"] = int(attr.get("y", 0))
            if attr.has_key("width"):
                conf["width"] = int(attr["width"])
            if attr.has_key("height"):
                conf["height"] = int(attr["height"])
            if attr.has_key("stroke"):
                conf["stroke"] = int(attr["stroke"])
                conf["strokeColor"] = attr["strokeColor"].replace("0x", "#")
            if attr.has_key("id"):
                conf["id"] = attr["id"]
            if attr.has_key("textColor"):
                conf["textColor"] = attr["textColor"]
            if attr.has_key("size"):
                conf["textSize"] = int(attr["size"])


    # 元素结束事件处理
    def endElement(self, tag):
        # print "endElement..........." + tag
        pass


    def endDocument(self):
        # print "endDocument"
        # print self.data
        global assetsConf
        global assetsUrl

        print assetsConf
        print assetsUrl



def parseFile(filename):
    '''
    解析单个文件
    :param filename:
    :return:
    '''
    if os.path.splitext(filename)[1] != ".exml":
        return

    print "parseFile:  {}".format(filename)
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    Handler = ExmlHandler()
    parser.setContentHandler(Handler)

    parser.parse(filename)

def main(argv):
    global exmlFile
    try:
        opts, args = getopt.getopt(argv, "e:", ["exmlFile=", ])
    except getopt.GetoptError:
        print "--------------------------------------------"
        print 'exml2openDataContext -e <exmlFile> '
        print "--------------------------------------------"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "--------------------------------------------"
            print 'exml2openDataContext -e <exmlFile> '
            print "--------------------------------------------"
            sys.exit(2)
        elif opt in ("-e", "--exmlFile"):
            exmlFile = os.path.abspath(arg)

    global assetsUrl
    global assetsConf
    try:
        exmlFile = os.path.abspath(r"D:\study\work\game_framework\client\resource\skins\game\panel\RankItemRenderSkin.exml")
        parseFile(exmlFile)
        with open(os.path.join(os.path.dirname(exmlFile), "index.js"), "w") as f:

            s = ""
            s += "const assetsUrl = { \n"

            for key in assetsUrl:
                s += '    {}: "{}",\n'.format(key, assetsUrl[key])
            s = s[0:-2]
            s += "\n"
            s += "};"
            s += "\n"
            f.write(s)

            c = ""
            c += "const assetsConf = "
            c += json.dumps(assetsConf)
            c += "; \n"
            f.write(c)
    except Exception,e:
        print traceback.print_exc()

def ttt():
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    Handler = ExmlHandler()
    parser.setContentHandler(Handler)

    parser.parse(r"")

if __name__ == '__main__':

    # parseFile(r"F:\work\n5\roll\client\stable_client\resource\skins\city\City_huoguo\City_huoguo_5Skin.exml")

    main(sys.argv[1:])