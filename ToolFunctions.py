# encoding: utf-8
"""
-------------------------------------------------
   File Name：     ToolFunctions
   @time: 2018/2/4 21:47
   @author: talus
   @desc: 图片处理工具
-------------------------------------------------
"""

import os
from PIL import Image


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


def getColors(img):
    """
    判断所有像素点是否存在非透明像素
    :param img:
    :return: 二维数组，存储像素是否为非透明像素
    """
    width,height = img.size

    has = []
    for i in range(0,width):
        has.append([])
        for j in range(0,height):
            has[i].append([])
            has[i][j] = img.getpixel((i,j)) != 0

    return has

def Exist(colors,x,y):
    """
    判断坐标处是否存在非透明像素值
    :param colors:
    :param x:
    :param y:
    :return:
    """
    if x < 0 or y < 0 or x >= len(colors) or y >= len(colors[0]):
        return False
    else:
        return colors[x][y]

def L_Exist(colors,rect):
    """
    判定区域Rect右侧是否存在像素点
    :param colors:
    :param rect:
    :return:
    """
    if rect.right >= len(colors )or rect.left < 0:
        return False
    for i in range(0,rect.height):
        if Exist(colors,rect.left - 1, rect.top + i):
            return True
    return False

def R_Exist(colors,rect):
    """
    判定区域Rect右侧是否存在像素点
    :param colors:
    :param rect:
    :return:
    """
    if rect.right >= len(colors)or rect.left < 0:
        return False
    for i in range(0,rect.height):
        if Exist(colors,rect.right + 1,rect.top + i):
            return True
    return False

def D_Exist(colors,rect):
    """
    判定区域Rect下侧是否存在像素点
    :param colors:
    :param rect:
    :return:
    """
    if rect.bottom >= len(colors[0]) or rect.top < 0:
        return False
    for i in range(0,rect.width):
        if Exist(colors, rect.left + i,rect.bottom + 1):
            return True
    return False

def U_Exist(colors,rect):
    """
    判定区域Rect上侧是否存在像素点
    :param colors:
    :param rect:
    :return:
    """
    if rect.bottom >= len(colors[0]) or rect.top < 0:
        return False
    for i in range(0,rect.width):
        if Exist(colors, rect.left + i,rect.top - 1):
            return True
    return False

def clearRect(colors,rect):
    """
    清空区域内的像素非透明标记
    :param colors:
    :param rect:
    :return:
    """
    for i in range(rect.left,rect.right+1):
        for j in range(rect.top,rect.bottom+1):
            colors[i][j] = False

def getRect(colors,x,y):
    """
    获取坐标所在图块的区域范围
    :param colors:
    :param x:
    :param y:
    :return:
    """
    rect = Rectangle(x,y,1,1)
    flag = True
    while flag:
        flag = False
        while R_Exist(colors,rect):
            rect.width += 1
            flag = True
        while D_Exist(colors,rect):
            rect.height += 1
            flag = True
        while L_Exist(colors,rect):
            rect.width += 1
            rect.left -= 1
            flag = True
        while U_Exist(colors,rect):
            rect.height += 1
            rect.top -= 1
            flag = True

    clearRect(colors,rect)
    return rect

def GetRects(img):
    """
    对图像pic进行图块分割，分割为一个个的矩形子图块区域
    分割原理： 相邻的连续区域构成一个图块，透明区域为分割点
    :param img:
    :return:
    """

    rects = []
    colors = getColors(img)
    width,height = img.size
    for i in range(0,width):
        for j in range(0,height):
            if Exist(colors,i,j):
                rect = getRect(colors,i,j)
                rects.append(rect)
                # if rect.width > 10 and rect.height > 10:
                #     rects.append(rect)

    return rects

if __name__ == "__main__":
    path = os.path.abspath(r"C:\Users\talus\work\moni\sheep\0\103.png")
    dirname = os.path.dirname(path)
    img = Image.open(path)

    rects = GetRects(img)
    for idx, rect in enumerate(rects):
        im = img.crop((rect.left, rect.top, rect.left + rect.width, rect.top + rect.height))
        print rect
        im.save(os.path.join(dirname, "{}.png".format(idx)))


