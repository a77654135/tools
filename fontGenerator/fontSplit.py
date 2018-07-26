# encoding: utf-8
"""
-------------------------------------------------
   File Name：     fontSplit
   @time: 2018/2/15 9:41
   @author: talus
   @desc: 分割字符图片，要求所有字符在一行上(暂时只支持一行上的字体)，以保证分割之后字符高度对齐，字体四周要留空白像素
          图片要保存为PNG-24格式
          图片命名为：fntname_abcdefg.png，用名字做字体区分，名字长度必须和图片里面字符的个数一致   fnt代表字体名字，后面代表每个字符的名字
          读取config.json文件，替换windows不能命名的字符
-------------------------------------------------
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import getopt
import traceback
import shutil
import json
from PIL import Image



fromDir = ""
toDir = ""
globalData = {}

class Rectangle():
    def __init__(self, l=0, t=0, w=1, h=1):
        self.left = l
        self.top = t
        self.width = w
        self.height = h

    @property
    def right(self):
        return self.left + self.width - 1

    @property
    def bottom(self):
        return self.top + self.height - 1

    def __str__(self):
        return "{} {} {} {}".format(self.left,self.top,self.width,self.height)

    def __unicode__(self):
        return "{} {} {} {}".format(self.left,self.top,self.width,self.height)


def Exist(img,x,y):
    w,h = img.size
    if x < 0 or x >= w or y < 0 or y >= h:
        return False
    pix = img.getpixel((x, y))

    # print "x:{} y:{} pix:{}  ".format(x, y, pix)

    if isinstance(pix,tuple):
        return pix[-1] != 0
    return pix != 0

def hExist(img,y):
    w,h = img.size

    for i in range(0,w):
        if Exist(img,i,y):
            return True
    return False

def vExist(img,x):
    w,h = img.size
    for i in range(0,h):
        if Exist(img,x,i):
            return True
    return False

def getLineRect(img):
    w,h = img.size

    start = 0
    end = 0
    step = 0
    for i in range(0,h):
        if hExist(img,i):
            if step == 0:
                start = i - 1
                step += 1
        else:
            if step == 1:
                end = i
                step += 1

    assert start != 0 and end != 0

    return Rectangle(0,start,w,end - start)

def getRects(img):
    lineRect = getLineRect(img)
    rects = []

    w,h = img.size
    x_list = []
    for i in range(0,w):
        if i == 0 or i == w-1:
            continue
        if vExist(img,i-1) and not vExist(img,i):
            x_list.append(i)
        elif not vExist(img,i-1) and vExist(img,i):
            x_list.append(i)
    length = len(x_list)
    # print u"length:  {}".format(length)

    if length:
        for i in range(0,length,2):
            if i + 1 > length - 1:
                continue
            rect = Rectangle(x_list[i],lineRect.top,x_list[i+1]-x_list[i],lineRect.height)
            rects.append(rect)
    return rects


def parsePng(pngFile,filename):

    global toDir
    global globalData

    filename = filename.split(r".")[0]
    img = Image.open(pngFile)
    #得到每个字符的位置
    rects = getRects(img)

    name,chars = filename.split("_")
    if len(chars) != len(rects):
        raise Exception(u"字符的个数和图片名字个数不一致！")

    dirname = os.path.join(toDir, "font", name)
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # 分割每个字符
    for idx, rect in enumerate(rects):
        im = img.crop((rect.left, rect.top, rect.left + rect.width, rect.top + rect.height))
        im.save(os.path.join(dirname, "{}.png".format(chars[idx])))

    #打包成字体文件
    os.system('TextureMerger.exe -p {0} -o {0}.fnt'.format(dirname))
    #删除临时文件
    shutil.rmtree(dirname)
    #替换fnt文件中的字符
    fnt_file = os.path.join(toDir, "font", "{}.fnt".format(name))
    with open(fnt_file, "r") as f:
        content = json.load(f)

    frames = content.get("frames", {})
    newFrames = {}
    for key in frames:
        value = frames[key]
        key = key.replace("_png", "")
        if key in globalData:
            key = globalData[key]
        newFrames[key] = value
    content["frames"] = newFrames

    with open(fnt_file, "w") as f:
        json.dump(content, f, indent=4)



def parse():
    global fromDir
    global toDir
    global globalData

    with open(os.path.join(os.path.dirname(__file__),'config.json'), "r") as f:
        globalData = json.load(f)

    for f in os.listdir(fromDir):
        if os.path.splitext(f)[1] == ".png":
            toPath = os.path.join(toDir,f.split(r".")[0])
            if os.path.exists(toPath):
                continue
            path = os.path.join(fromDir,f)
            parsePng(path,f)



def main(argv):
    global fromDir
    global toDir

    try:
        opts, args = getopt.getopt(argv, "f:t:", ["fromDir=","toDir=",])
    except getopt.GetoptError:
        print "--------------------------------------------"
        print 'fontSplit -f <fromDir> -t <toDir>'
        print "--------------------------------------------"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "--------------------------------------------"
            print 'fontSplit -f <fromDir> -t <toDir>'
            print "--------------------------------------------"
            sys.exit(2)
        elif opt in ("-f", "--fromDir"):
            fromDir = os.path.abspath(arg)
        elif opt in ("-t", "--toDir"):
            toDir = os.path.abspath(arg)

    # fromDir = os.path.abspath(r"C:\Users\talus\Desktop\aaa")

    if not toDir:
        toDir = fromDir

    try:
        parse()
    except Exception,e:
        print traceback.print_exc()



if __name__ == '__main__':

    main(sys.argv[1:])

# if __name__ == "__main__":
#
#     main()
#
#     path = os.path.abspath(r"C:\Users\talus\Desktop\text.png")
#     dirname = os.path.dirname(path)
#     img = Image.open(path)
#
#     rects = GetRects(img)
#     for idx, rect in enumerate(rects):
#         im = img.crop((rect.left, rect.top, rect.left + rect.width, rect.top + rect.height))
#         print rect
#         im.save(os.path.join(dirname, "{}.png".format(idx)))