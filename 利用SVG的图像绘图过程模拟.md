# 利用SVG的图像绘图过程模拟

## 1 - 项目介绍

`Python` 强大之处在于其拥有很多功能强大的库，其中 `turtle` 库是其自带的简单又强大的绘图库， 配合其他库使用将可以完成许多有趣的功能。

我们想利用 `turtle` 完成对图片的绘画过程模拟，模拟现实情况下的绘图过程，因此有了这个项目。此项目功能：输入用户图片，输出`turtle`绘图过程。

如果只是单纯的读取像素值进行绘图不符合我们的要求。现实生活下的绘图是按颜色按区域进行绘制，而且绘图中不是绘制“点阵”，而是有运笔痕迹，所以使用矢量图将可以解决问题。

### 1.1 - SVG 图像格式

`SVG` 全称 `Scalable Vector Graphics`, 可缩放的矢量图形 .  其是一种用XML定义的语言，用来描述二维矢量及矢量/栅格图形。可以插入到HTML并用浏览器观看，也可以用任何文字处理软件打开进行编辑。

`SVG` 文件由许多 `Path` 构成，可以直接理解成路径绘制，后面跟命令，一般构成为 命令代码+坐标 形式。常见命令如下表格：


|命令 |	名称| 	参数|
|--|--|---|
|M |	moveto 移动到 	|(x y)+|
|Z |	closepath 关闭路径 |	(none)|
|L |	lineto 画线到 |	(x y)+|
|H |	horizontal lineto 水平线到 |	x+|
|V |	vertical lineto  垂直线到 |	y+|
|C |	curveto  三次贝塞尔曲线到 |	(x1 y1 x2 y2 x y)+|

读取一个`SVG`图像，分析每一个`Path`，并调用`turtle`中的相应函数，即可完成画笔痕迹模拟。

### 1.2 - Potrace 位图矢量化算法

常见图片输入格式`bmp`，`jpg`,`jpeg`,`png`等等都属于位图（即`bitmap`,点阵图，栅格图），需要转化成矢量图，即引入位图矢量化算法。

`potrace`算法过程：
1. 位图被分解为一些路径，他们构成了黑白区域之间的边界。（默认前提是二值化的位图）
2. 每条路径都被近似为一个最优多边形，并转化为光滑的轮廓。
3. 曲线通过链接连续的 贝塞尔曲线 片段来进行优化。
4. 产生需要的格式输出。

### 1.2.1 - 图像二值化
图像二值化即把图片上的像素设置为黑`(0,0,0)`或白`(255,255,255)`，可以利用`python-opencv`处理。

### 1.2.2 - potrace.exe
使用方法： `potrace.exe filename -s --flat` ,可在同目录下生成对应的`.svg`

### 1.3 - 高阶贝塞尔曲线

贝塞尔曲线（`Bézier curve`）是应用于二维图形应用程序的数学曲线。一般的矢量图形软件通过它来精确画出曲线。一阶曲线就是直线，两点确定位置。N阶（高阶）即N+1个点N条线来确定一段曲线，具体实现过程利用递推解决。

（https://www.jianshu.com/p/0c9b4b681724）

### 1.4 - 颜色量化算法

利用人眼惰性，将图片中相似的颜色合并，而前后人眼认识差最小。这里使用K-means聚类进行颜色量化，利用`python-opencv`中的`cv2.kmeans`可以完成。

## 2 - Code

### 2.1 - Bezier
```Python
def Bezier(p1, p2, t):  # 一阶贝塞尔函数
    return p1 * (1 - t) + p2 * t
```
p1,p2是两个点，理解成向量即可。在向量p1p2上按比例的点。

```Python

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
```
高阶贝塞尔曲线是递归定义的，调用相应函数即可。

### 2.2 - drawSVG
读取图像中所有的`path`,依次绘图。
```Python
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
```
在SVG图像中，相同字母对应的操作相似，其中大写表示绝对坐标，小写表示相对坐标。

### 2.2.1 - Moveto/Move
``` Python
def Moveto(x, y, idt):  
    te.penup()
    if idt == 'M':
        te.goto(-Width / 2 + x, Height / 2 - y)
    else:
        te.goto(te.xcor() + x, te.ycor() - y)
    te.pendown()
```
由于图像坐标系统和turtle画图系统的坐标系不同，需要重新转换，方式如程序所示。

### 2.2.2 -  Curveto/Curve
```Python
def Curveto(x1, y1, x2, y2, x, y, idt):  # 三阶贝塞尔曲线到（x，y）
    te.penup()
    X_now = te.xcor() + Width / 2
    Y_now = Height / 2 - te.ycor()
    if idt == 'C':
        Bezier_3(X_now, Y_now, x1, y1, x2, y2, x, y)
    else:
        Bezier_3(X_now, Y_now, X_now + x1, Y_now + y1,
             X_now + x2, Y_now + y2, X_now + x, Y_now + y)
```

### 2.2.3 -  Lineto/Line
```Python
def Lineto(x, y, idt):  
    te.pendown()
    if idt == 'L':
        te.goto(-Width / 2 + x, Height / 2 - y)
    else:
        te.goto(te.xcor() + x, te.ycor() - y)
    te.penup()
```

### 2.2.4 - transform
```Python
def transform(w_attr):
    funcs = w_attr.split(' ')
    for func in funcs:
        func_name = func[0: func.find('(')]
        if func_name == 'scale':
            global scale
            scale = (float(func[func.find('(') + 1: -1].split(',')[0]),
                     -float(func[func.find('(') + 1: -1].split(',')[1]))
```
直接转换往往会使得图片过大无法在Graphics画出，需要transform改变放缩比例。

### 2.3 - drawBitmap

### 2.3.1 - K-means颜色量化
```Python
ret, label, center = cv2.kmeans(
	Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)  
center = np.uint8(center)
```
`cv2.kmeans`返回的三个参数分别为：密实度，标签，中心。由于我们想要颜色量化，被聚拢的中心`center`保存的就是量化后的颜色。center中每一个元素都是[R,G,B]。但不一定是整数，所i需要向下取整保证都为在[0,255]的整数。

### 2.3.2 - 二值化
```Python
res2 = cv2.bitwise_not(cv2.inRange(res, i, i))
bmpname = './tmp/'+str(j)+'.bmp'
svgname = './tmp/'+str(j)+'.svg'
cv2.imwrite(bmpname, res2)
os.system('potrace.exe '+bmpname+' -s --flat')
```
利用`python-opencv`中的`cv2.inRange`函数, `cv2.inRange(res, lower, upper)`将图像中高于upper的和低于lower颜色的像素点全部去除。我们可以将颜色量化后的颜色带入其中，就可以得到每一种颜色对应在图中的位置。
`cv2.imwrite(bmpname, res2)`将res2写入到bmpname中，调用`os.system`,使用potrace将位图图像`.bmp`转化为`.svg`图像。将`.svg`传入到`drawSVG`即可。

### 2.4 - turtle设置
```Python
te.setup(height=Height, width=Width)
te.setworldcoordinates(-Width / 2, 300, Width / 2, -Height + 300)
te.speed(1000)
te.tracer(100)
```
图片坐标系和绘图坐标系不同，需要重新设置。利用`setworldcoordinates`可以定义“Graphics窗口”的左下角和右上角坐标对应的绘图坐标。如果不设置会导致绘图图片产生 压缩/拉伸/反向 等问题。

为了使动画效果明显，我们使用了`tracer`.如果`tracer`设置为 0，那么将导致整个颜色区块完全绘制完成后直接刷新到Graphics里，演示效果不佳。包括使用`delay`,由于图像绘画时间较长，后续会产生卡顿，也因此舍弃。

## 3 - Demo
演示视频：https://www.bilibili.com/video/av75727076