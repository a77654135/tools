# encoding: utf-8
"""
-------------------------------------------------
   File Name：     fontSplit
   @time: 2018/2/15 9:41
   @author: talus
   @desc: 分割字符图片，要求所有字符在一行上，以保证分割之后字符高度对齐，字体四周要留空白像素
-------------------------------------------------
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import getopt
import traceback
import shutil
from PIL import Image



fromDir = ""
toDir = ""

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

    img = Image.open(pngFile)
    rects = getRects(img)

    dirname = os.path.join(toDir,filename.split(r".")[0])
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    for idx, rect in enumerate(rects):
        im = img.crop((rect.left, rect.top, rect.left + rect.width, rect.top + rect.height))
        im.save(os.path.join(dirname, "{}.png".format(idx)))


def parse():
    global fromDir
    global toDir

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

    fromDir = os.path.abspath(r"C:\Users\talus\study\ttt")

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