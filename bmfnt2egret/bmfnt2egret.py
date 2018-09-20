# -*- coding: utf-8 -*-

"""
用法：
step1:   /your_path/dirname/bmfnt2egret.exe -f  /your_path/dirname/filename.fnt
step2:   windows记事本打开/your_path/dirname/filename.fnt   另存为:/your_path/dirname/filename.fnt   格式改成utf8

ascii.txt是中文ascii表，没有中文字符的ascii，如果表中没有的字符，在ascii.txt中增加这个字符对应的ascii码，就可以正常解析
egret只识别utf8编码格式的文件，工具暂不支持自动转换，所以需要手动转换一下，转换成utf8就可以在egret中正常使用。
"""

import sys

reload(sys)
sys.setdefaultencoding("utf-8")

import os
import re
import json
import getopt

fname = ""
codeMap = {}


def findArg(line, key):
    ret = re.findall('{}=(\d+)'.format(key), line)
    return ret[0]

def parseFile(filename):
    with open(filename, "r") as f:
        lines = f.readlines()

    fn = re.findall('file="(.*?)"', lines[2])[0]

    frames = {}
    for line in lines:
        if line.startswith("char id"):
            id = findArg(line, "id")
            x = findArg(line, "x")
            y = findArg(line, "y")
            width = findArg(line, "width")
            height = findArg(line, "height")
            xoffset = findArg(line, "xoffset")
            yoffset = findArg(line, "yoffset")
            string = ascii2Unicode(id)
            frames[string] = {}
            frames[string]["x"] = int(x)
            frames[string]["y"] = int(y)
            frames[string]["w"] = int(width)
            frames[string]["h"] = int(height)
            frames[string]["sourceW"] = int(width)
            frames[string]["sourceH"] = int(height)
            frames[string]["offX"] = int(xoffset)
            frames[string]["offY"] = int(yoffset)


        ret = {}
        ret["file"] = fn
        ret["frames"] = frames

    print filename
    with open(filename, "w") as f:
        json.dump(ret, f, ensure_ascii=False, indent=4, encoding="utf-8")



def parseAscii():
    ascii_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ascii.txt")
    if not os.path.exists((ascii_file)):
        print "not fonnd file:  {}".format("ascii.txt")
        sys.exit(2)

    with open(ascii_file, "r") as f:
        content = f.read()

    line_list = content.split("\n")
    for line in line_list:
        str_list = line.split(" ")
        for s in str_list:
            sc_list = s.split(":")
            if len(sc_list) == 2:
                codeMap[sc_list[1]] = sc_list[0]
            elif len(sc_list) == 3:
                num = re.findall("(\d+)", sc_list[1])[0]
                codeMap[num] = sc_list[0]
                codeMap[sc_list[2]] = sc_list[1].replace(num, "")


def ascii2Unicode(ascii_code):
    if "{}".format(ascii_code) in codeMap:
        return codeMap["{}".format(ascii_code)]
    else:
        try:
            return chr(int(ascii_code))
        except:
            print "cannot find ascii:   {}".format(ascii_code)
            return "{}".format(ascii_code)

def main(argv):
    global fname

    try:
        opts, args = getopt.getopt(argv, "f:", ["filename=", ])
    except getopt.GetoptError:
        print "--------------------------------------------"
        print 'bmfnt2egret -f <filename> '
        print "--------------------------------------------"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "--------------------------------------------"
            print 'bmfnt2egret -f <filename> '
            print "--------------------------------------------"
            sys.exit(2)
        elif opt in ("-f", "--filename"):
            fname = os.path.abspath(arg)

    if not os.path.exists(fname):
        print "not found any .fnt file!"
        print "exit!"
        sys.exit(2)

    parseAscii()
    parseFile(fname)


if __name__ == "__main__":
    main(sys.argv[1:])