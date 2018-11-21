# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os, time, getopt, re, traceback

"""
发布微信小游戏版本
"""

# 项目目录
project_dir = ""

ignore_js = [
    "netWorker",
    "sdk",
]




def parse():
    os.chdir(project_dir)
    os.system("egret publish --target wxgame")
    time.sleep(1)

    path, name = os.path.split(project_dir)
    newPath = os.path.join(path, "{}_wxgame".format(name))
    manifest_js = os.path.join(newPath, "manifest.js")

    for js in ignore_js:
        ijs = os.path.join(newPath, "js", "{}.js".format(js))
        if os.path.exists(ijs):
            os.unlink(ijs)

    if os.path.exists(manifest_js):
        newContent = ""
        with open(manifest_js, "r") as f:
            lines = f.readlines()
            for line in lines:
                w = True
                for js in ignore_js:
                    if re.search(".*/{}.*".format(js), line):
                        w = False
                        break
                if w:
                    newContent += line

        with open(manifest_js, "w") as f:
            f.write(newContent)





def main(argv):
    global project_dir
    try:
        opts, args = getopt.getopt(argv, "p:", ["projectDir=",])
    except getopt.GetoptError:
        print "--------------------------------------------"
        print 'publishWxgame -p <projectDir> '
        print "--------------------------------------------"
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "--------------------------------------------"
            print 'publishWxgame -p <projectDir> '
            print "--------------------------------------------"
            sys.exit(2)
        elif opt in ("-p", "--projectDir"):
            project_dir = os.path.abspath(arg)

    # project_dir = os.path.abspath("D:\study\work\game_framework\client")

    try:
        parse()
    except:
        print traceback.print_exc()


if __name__ == '__main__':
    main(sys.argv[1:])