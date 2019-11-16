import turtle as te
from bs4 import BeautifulSoup
import argparse
import sys
import numpy as np
import cv2
import os
import lxml
from win32.win32api import GetSystemMetrics
from PIL import Image
import imageio

WriteStep = 15  # 贝塞尔函数的取样次数
Width = 600  # 界面宽度
Height = 600  # 界面高度
scale = (1, 1)
first = True
K = 32

def Bezier(p1, p2, t):  # 一阶贝塞尔函数
    return p1 * (1 - t) + p2 * t

def Bezier_3(x1, y1, x2, y2, x3, y3, x4, y4):  # 三阶贝塞尔函数
    x1 = -Width / 2 + x1
    y1 = Height / 2 - y1
    x2 = -Width / 2 + x2
    y2 = Height / 2 - y2
    x3 = -Width / 2 + x3
    y3 = Height / 2 - y3
    x4 = -Width / 2 + x4
    y4 = Height / 2 - y4  # 坐标变换
    te.goto(x1, y1)
    te.pendown()
    for t in range(0, WriteStep + 1):
        x = Bezier(Bezier(Bezier(x1, x2, t / WriteStep),
                          Bezier(x2, x3, t / WriteStep),
                          t / WriteStep),
                   Bezier(Bezier(x2, x3, t / WriteStep),
                          Bezier(x3, x4, t / WriteStep),
                          t / WriteStep), t / WriteStep)
        y = Bezier(Bezier(Bezier(y1, y2, t / WriteStep),
                          Bezier(y2, y3, t / WriteStep),
                          t / WriteStep),
                   Bezier(Bezier(y2, y3, t / WriteStep),
                          Bezier(y3, y4, t / WriteStep),
                          t / WriteStep), t / WriteStep)
        te.goto(x, y)
    te.penup()


def Moveto(x, y, idt):  
    te.penup()
    if idt == 'M':
        te.goto(-Width / 2 + x, Height / 2 - y)
    else:
        te.goto(te.xcor() + x, te.ycor() - y)
    te.pendown()

def Lineto(x, y, idt):  
    te.pendown()
    if idt == 'L':
        te.goto(-Width / 2 + x, Height / 2 - y)
    else:
        te.goto(te.xcor() + x, te.ycor() - y)
    te.penup()


def Curveto(x1, y1, x2, y2, x, y, idt):  # 三阶贝塞尔曲线到（x，y）
    te.penup()
    X_now = te.xcor() + Width / 2
    Y_now = Height / 2 - te.ycor()
    if idt == 'C':
        Bezier_3(X_now, Y_now, x1, y1, x2, y2, x, y)
    else:
        Bezier_3(X_now, Y_now, X_now + x1, Y_now + y1,
             X_now + x2, Y_now + y2, X_now + x, Y_now + y)

def transform(w_attr):
    funcs = w_attr.split(' ')
    for func in funcs:
        func_name = func[0: func.find('(')]
        if func_name == 'scale':
            global scale
            scale = (float(func[func.find('(') + 1: -1].split(',')[0]),
                     -float(func[func.find('(') + 1: -1].split(',')[1]))

def readPathAttrD(w_attr):
    ulist = w_attr.split(' ')
    for i in ulist:
        # print("now cmd:", i)
        if i.isdigit() or i.isalpha():
            yield float(i)
        elif i[0].isalpha():
            yield i[0]
            yield float(i[1:])
        elif i[-1].isalpha():
            yield float(i[0: -1])
        elif i[0] == '-':
            yield float(i)

def drawSVG(filename, w_color):
    global first
    SVGFile = open(filename, 'r')
    SVG = BeautifulSoup(SVGFile.read(), 'lxml')
    Height = float(SVG.svg.attrs['height'][0: -2])
    Width = float(SVG.svg.attrs['width'][0: -2])
    transform(SVG.g.attrs['transform'])
    if first:
        te.setup(height=Height, width=Width)
        te.setworldcoordinates(-Width / 2, 300, Width / 2, -Height + 300)
        first = False
    te.speed(1000)
    te.pensize(2)
    te.tracer(100)
    te.hideturtle()
    te.penup()
    te.color(w_color)
    for i in SVG.find_all('path'):
        attr = i.attrs['d'].replace('\n', ' ')
        f = readPathAttrD(attr)
        last = ' '
        for j in f:
            if str(j).isalpha():
                last = j
                if j == 'M' or j=='m':
                    te.end_fill()
                    Moveto(next(f) * scale[0], next(f) * scale[1],j)
                    te.begin_fill()
                elif j == 'C' or j=='c':
                    Curveto(next(f) * scale[0], next(f) * scale[1],
                            next(f) * scale[0], next(f) * scale[1],
                            next(f) * scale[0], next(f) * scale[1],j)
                elif j == 'L' or j=='l':
                    Lineto(next(f) * scale[0], next(f) * scale[1],j)
            elif last == 'C' or last == 'c':
                Curveto(j * scale[0], next(f) * scale[1],
                            next(f) * scale[0], next(f) * scale[1],
                            next(f) * scale[0], next(f) * scale[1],last)
            elif last == 'L' or last == 'l':
                Lineto(j * scale[0], next(f) * scale[1],last)
    te.penup()
    te.update()
    SVGFile.close()

def drawBitmap(w_image):
    print('Reducing the colors...')
    Z = w_image.reshape((-1, 3))
    Z = np.float32(Z)
    criteria = (cv2.TERM_CRITERIA_EPS, 10, 1.0)
    global K
    ret, label, center = cv2.kmeans(
        Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    te.hideturtle()
    center = np.uint8(center)
    res = center[label.flatten()].reshape(w_image.shape)
    for j in range(K-1,-1,-1):
        i = center[j]
        os.system("cls")
        print("color:[R G B] -> ",i)
        if i[0]==i[1]==i[2]==255 :
            continue
        print('\rDrawing: %.2f%% ['%((K-j)/K*100)+'#'*(K-j)+' '*j+']\n')
        res2 = cv2.bitwise_not(cv2.inRange(res, i, i))
        bmpname = './tmp/'+str(j)+'.bmp'
        svgname = './tmp/'+str(j)+'.svg'
        cv2.imwrite(bmpname, res2)
        os.system('potrace.exe '+bmpname+' -s --flat')
        #print(i)
        drawSVG(svgname, '#%02x%02x%02x' % (i[2], i[1], i[0]))
    print('\n\rFinished')
    te.done()
    te.mainloop()
    
filename = input("请输入原图地址")
bitmapFile = open(filename, mode='r')
bitmap = cv2.imread(filename)
drawBitmap(bitmap)
