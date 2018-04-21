# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     publish_n5
   Author :       talus
   date：          2018/3/23 0023
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
import datetime
import time
import hashlib
import string
import random

from common.ExceptCallStack import print_call_stack
from slimit import minify

projectDir = ""
testDir = ""
publishDir = ""
configDir = ""
releaseDir = ""

updateAll = True
updateConfig = True
updateSkin = True
updateProgram = True
updateRes = True

version = ""

mainVer = ""
skinVer = ""



def configParser():
    """
    解析配置文件
    :return:
    """
    global projectDir
    global testDir
    global publishDir
    global configDir
    global releaseDir

    global updateAll
    global updateConfig
    global updateSkin
    global updateProgram
    global updateRes


    parser = configparser.ConfigParser()
    parser.read("config.ini",encoding="utf-8")

    projectDir = os.path.abspath(parser.get("default", "projectDir"))
    publishDir = os.path.abspath(parser.get("default", "publishDir"))
    testDir = os.path.abspath(parser.get("default", "testDir"))
    configDir = os.path.abspath(parser.get("default", "configDir"))
    testOrPublish = parser.get("default", "testOrPublish")

    updateAll = parser.getboolean("default","updateAll")
    updateConfig = parser.getboolean("default","updateConfig")
    updateSkin = parser.getboolean("default","updateSkin")
    updateProgram = parser.getboolean("default","updateProgram")
    updateRes = parser.getboolean("default","updateRes")

    if testOrPublish == "test":
        releaseDir = testDir
    else:
        releaseDir = publishDir


def minJson(jsonFile):
    '''
    压缩json文件
    :param jsonFile:
    :return:
    '''
    with open(jsonFile,"r") as f:
        content = json.load(f)
    with open(jsonFile,"w") as f:
        json.dump(content,f)

def updateReleaseCode():
    '''
    把发布目录代码更新到最新，防止提交时冲突
    然后删除所有文件，方便提交最新的文件
    :return:
    '''
    global releaseDir
    global configData

    os.system(r"svn revert -R {}".format(releaseDir))
    os.system(r"svn update {}".format(releaseDir))
    print u"目录更新成功"

def updateCode():
    global projectDir

    os.system(r"svn update {}".format(projectDir))

def updateConfigOnly():
    """
    只更新配置
    :return:
    """
    global updateConfig
    global updateAll
    global projectDir
    global configDir
    global releaseDir

    if updateConfig or updateAll:
        os.chdir(projectDir)
        if not updateConfig:
            return
        os.system(r"svn update {}".format(configDir))
        os.system(r"gulp json-zip")

        time.sleep(1)

        fromFile = os.path.join(projectDir,*["resource","blank.png"])
        toFile = os.path.join(releaseDir,*["resource","blank.png"])
        if not os.path.exists(os.path.dirname(toFile)):
            os.makedirs(os.path.dirname(toFile))

        shutil.copyfile(fromFile,toFile)


def updateResOnly():
    """
    只更新资源
    :return:
    """
    global projectDir
    global releaseDir

    fromDir = os.path.join(projectDir,"resource")
    assets = ["assets","notice","web"]

    toDir = os.path.join(releaseDir,"resource")

    for asset in assets:
        toPath = os.path.join(toDir,asset)
        if os.path.exists(toPath):
            if os.path.isdir(toPath):
                shutil.rmtree(toPath)
            else:
                os.unlink(toPath)
    time.sleep(2)

    for asset in assets:
        fromPath = os.path.join(fromDir, asset)
        toPath = os.path.join(toDir, asset)
        shutil.copytree(fromPath,toPath)
    time.sleep(2)

    jsonFrom = os.path.join(fromDir,"default.res.json")
    jsonTo = os.path.join(toDir,"default.res.json")
    if os.path.exists(jsonTo):
        os.unlink(jsonTo)
    time.sleep(1)

    shutil.copyfile(jsonFrom,jsonTo)
    time.sleep(1)

    minJson(jsonTo)

def getVersion():
    ver = ""
    for i in range(0,3):
        ver += str(random.choice(string.digits))
    return ver

def updateSkinOnly():
    """
    只更新skin
    :return:
    """
    global projectDir
    global releaseDir
    global version
    global skinVer

    thmJson = os.path.join(projectDir,*["bin-release","web",version,"resource","default.thm.json"])

    with open(thmJson, "r") as f:
        content = json.load(f)

    output = ""
    exmls = content.get("exmls", [])
    for item in exmls:
        className = item.get("className", "")
        gjs = item.get("gjs", "")
        if className and gjs:
            if re.match(r"City_.*Skin", className):
                continue
            output += u"var {} = {}".format(className, gjs)
            output += os.linesep

    # skinVer = hashlib.md5(output).hexdigest()[:3]
    skinVer = getVersion()
    skinMinJs = os.path.join(releaseDir, *["resource", "skin{}.min.js".format(skinVer)])
    while os.path.exists(skinMinJs):
        skinVer = getVersion()
        skinMinJs = os.path.join(releaseDir, *["resource", "skin{}.min.js".format(skinVer)])

    skinJs = os.path.join(releaseDir, *["resource", "skin.js".format(skinVer)])

    with open(skinJs, "w") as f:
        f.write(output)

    try:
        with open(skinMinJs, "w") as f:
            f.write(minify(output, mangle=False, mangle_toplevel=True))
    except:
        with open(skinMinJs, "w") as f:
            f.write(output)

    #拷贝skins过去
    skinFrom = os.path.join(projectDir,*["resource","skins"])
    skinTo = os.path.join(releaseDir,*["resource","skins"])

    if os.path.exists(skinTo):
        shutil.rmtree(skinTo)
        time.sleep(2)
    shutil.copytree(skinFrom,skinTo)
    time.sleep(2)


def updateProgramOnly():
    """
    更新代码
    :return:
    """
    global projectDir
    global releaseDir
    global version
    global mainVer

    mainJs = os.path.join(projectDir, *["bin-release", "web", version, "main.min.js"])

    with open(mainJs,"r") as f:
        content = "".join(f.readlines())

    ver = hashlib.md5(content).hexdigest()
    mainVer = ver[:5]

    # mainName = "main.{}.min.js".format(mainVer)
    mainName = "main.min.js"
    toJs = os.path.join(releaseDir, mainName)
    shutil.copy(mainJs,toJs)


def runPublish():
    '''
    egret publish
    :return:
    '''
    global projectDir
    global releaseDir
    global version

    os.chdir(projectDir)
    version = str(datetime.datetime.now())[:10]

    tempDir = os.path.join(projectDir,*[r"bin-release",r"web",version])
    # if os.path.exists(tempDir):
    #     shutil.rmtree(tempDir)
    #     time.sleep(2)

    os.system(r"egret publish --version {}".format(version))


def parseIndexHtml():
    '''
    替换html中的信息
    :return:
    '''
    global projectDir
    global releaseDir
    global mainVer
    global skinVer

    indexFile = os.path.join(releaseDir,"index.html")

    with open(indexFile,"r") as f:
        lines = f.readlines()

    # 替换版本号
    version = str(datetime.datetime.now())[0:16]
    newlines = []
    for line in lines:
        if re.match(r"<script>var game_version",line):
            l = r'<script>var game_version = "{}";</script>'.format(version)
            l += '\n'
        else:
            # l = line.replace("main.min.js","main.{}.min.js".format(mainVer))
            l = line
        newlines.append(l)

    with open(indexFile,"w") as f:
        f.writelines(newlines)

    # mainJs = os.path.join(releaseDir, "main.{}.min.js".format(mainVer))
    mainJs = os.path.join(releaseDir, "main.min.js")
    with open(mainJs,"r") as f:
        lines = f.readlines()

    newlines = []
    for line in lines:
        l = line.replace("skin.min.js","skin{}.min.js".format(skinVer))
        newlines.append(l)

    with open(mainJs,"w") as f:
        f.writelines(newlines)


def parseConfigVersion():
    global releaseDir
    global updateProgram
    global updateSkin
    global updateRes
    global updateConfig
    global updateAll

    versionFile = os.path.join(releaseDir,*["resource","config_vutimes.json"])

    with open(versionFile,"r") as f:
        content = json.load(f)
    # "xml_ver":45, "notice_ver":338, "json_ver":44, "res_ver":47

    if content.has_key("xml_ver") and (updateSkin or updateAll):
        content["xml_ver"] += 1
    if content.has_key("json_ver") and (updateConfig or updateAll):
        content["json_ver"] += 1
    if content.has_key("res_ver") and (updateRes or updateAll):
        content["res_ver"] += 1

    with open(versionFile,"w") as f:
        json.dump(content,f)



def main():

    global updateAll
    global updateConfig
    global updateProgram
    global updateRes
    global updateSkin

    try:
        configParser()
        updateCode()
        print u"更新代码成功"
        updateReleaseCode()
        print u"更新发布目录成功"

        if updateAll:
            pass
        else:
            if updateConfig:
                updateConfigOnly()
                print u"更新配置成功"
            if updateRes:
                updateResOnly()
                print u"更新资源成功"

            if updateProgram or updateSkin:
                runPublish()
                print u"编译成功"

                if updateSkin:
                    updateSkinOnly()
                    print u"更新皮肤成功"
                if updateProgram:
                    updateProgramOnly()
                    print u"更新代码成功"

        parseIndexHtml()
        parseConfigVersion()
        print u"替换版本号成功"





    except Exception,e:
        print_call_stack()


if __name__ == "__main__":
    main()