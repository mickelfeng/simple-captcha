# -*- coding:utf-8 -*-
import tkinter as tk
import threading
from tkinter import filedialog, font
from PIL import Image, ImageTk
import imgRe
import download

im = None
imDeal = None
pieces = []
res = []
low = 0
high = 0

getCon = threading.Condition()
reCon = threading.Condition()
dwnCon = threading.Condition()


def drawHelp(master=None, width=400, height=500):
    '''
    绘制使用说明窗口
    '''
    usageText = '''快捷用法：
    依次点击“选取图片”→“自动识别”

    识别结果可复制至剪切板。程序自带若干验证码图片，保存在“简单验证码”文件夹中，可点击“下载图片”下载更多，目前的算法只能识别这种简单验证码，对于干扰较多、扭曲、形变等验证码，可自行点击“调整门限”改变降噪门限，但效果欠佳，尚待优化。
    '''
    usage = tk.Toplevel(master, width=width, height=height)
    usage.resizable(False, False)
    usage.title('使用简介')
    usage.wm_attributes('-topmost', 1)

    ft = font.Font(family='微软雅黑', size=13)
    l = tk.Label(usage, text=usageText,  font=ft, justify='left', wraplength=width*0.8)
    l.place(
        in_=usage, relwidth=1, relheight=1, relx=0.5, rely=0.55, anchor='center')


def start():
    '''
    自动识别验证码，对应“自动识别”按钮
    '''
    global res

    reCon.acquire()
    if len(pieces) > 0:
        reCon.notifyAll()  # 取到图片且分割成功，通知展示栏
        res = imgRe.Recognize().recognize(pieces)
    else:
        text = '识别未成功，未选取图片或识别未完成\n请稍作等待或重新选取图片\n选取简单验证码可直接点击自动识别'
        Dialog(root, text)
    reCon.release()


def _chooseImg():
    '''
    读取图片，对应“选取图片”按钮
    '''
    global im
    global imDeal
    global pieces

    imgFile = filedialog.askopenfile()
    if imgFile is not None:
        try:
            getCon.acquire()
            fileName = imgFile.name
            im = Image.open(fileName)  # 原图
            imDeal = imgRe.Div(im)  # 经过等待处理的图
            pieces = imDeal.imDiv()  # 切割之后的四个验证码碎片
            getCon.notifyAll()  # 取到图片，通知展示栏
            getCon.release()
        except Exception as e:
            print(e)
    pass


def _downloadImg(num):
    '''
    下载图片，对应“下载图片”按钮
    '''
    do = '自动下载%s张验证码\n现在自动下载中\n保存至文件夹“简单验证码”中' % num
    dia = Dialog(root, do)
    dia.resizable(False, False)
    dia.geometry('300x150-512-384')

    t = threading.Thread(target=download.main, args=[num])
    t.setDaemon(True)
    t.start()
    # done = '下载完成！保存在文件夹“简单验证码”中'
    # Dialog(root, done)


def _changeThreshold():
    global imDeal
    global pieces

    getCon.acquire()
    if imDeal is not None:
        imDeal.reDenoise(low, high)
        pieces = imDeal.imDiv()
        getCon.notifyAll()
    else:
        text = '请先选取图片!\n选取简单验证码可直接点击自动识别'
        dia = Dialog(root, text)
        dia. resizable(False, False)
        dia.geometry('300x150-512-384')
        print(text)
        pass
    getCon.release()


class Root(tk.Tk):

    """
    主框架
    实现展示栏处可变化大小的窗口
    """

    def __init__(self, width=900, height=500):
        tk.Tk.__init__(self)
        self.minsize(width, height)  # 最小尺寸
        self.attributes('-alpha', 0.95)
        self.topH = 100  # 顶部栏高度
        self.optH = 50  # 选项栏高度
        self.drawTop()
        self.drawOpt()
        self.drawDisplay()

    def _mainResize(self, event):
        '''
        动态调节展示栏高度
        '''
        height = self.winfo_height()  # 获得主窗口的高度
        relheight = (height - (self.topH + self.optH))  # 窗口高度减去上两栏高度即展示栏的真实高度
        self.display.configure(height=relheight)

    def drawTop(self):
        '''
        画出顶部栏
        '''
        self.top = Top(master=self, bg='#99CCFF', height=self.topH)
        self.top.place(in_=self, relwidth=1, y=0)

    def drawOpt(self):
        '''
        画出选项栏
        '''
        self.opt = Option(self, bg='#EEDFCC', height=self.optH)
        self.opt.place(in_=self, relwidth=1, y=self.topH)

    def drawDisplay(self):
        '''
        画出用于展示的主界面：展示栏
        '''
        self.display = Display(self, bg='#CCFFFF')
        self.bind('<Configure>', self._mainResize)  # 通过事件实时监控、动态调节其高度
        self.display.place(in_=self, relwidth=1, y=(self.topH + self.optH))


class Top(tk.Frame):

    """顶部栏"""

    def __init__(self, master=None, height=None, bg=None):
        tk.Frame.__init__(self, master, bg=bg, height=height)
        self.bg = bg
        self.ft = font.Font(family='微软雅黑', size=23)
        self.drawLabe()

    def drawLabe(self):
        btn = tk.Button(self, command=start, fg='white', text='自动识别', font=self.ft,
                        activeforeground='#EEDFCC', activebackground=self.bg, bg=self.bg, bd=0)
        btn.place(in_=self, relx=0.8, rely=0.5, anchor='center')


class Option(tk.Frame):

    """选项栏"""

    def __init__(self, master=None, height=None, bg=None):
        tk.Frame.__init__(self, master, bg=bg, height=height)
        self.bg = bg
        self.options = ['选取图片', '下载图片', '调节门限']  # 功能集中在这里，长度改变时各按钮长度可动态更改
        self.ft = font.Font(family='微软雅黑', size=17)
        self.num = len(self.options)
        self.Min = tk.StringVar()
        self.Max = tk.StringVar()
        self.imgNum = tk.StringVar()
        self.chooseImg()
        self.downloadImg()
        self.changeThreshold()

    def chooseImg(self):
        '''
        绘制“选择图片”的按钮
        '''
        begin = 0  # 该option的起点
        end = begin + 1 / self.num  # 该option的终点
        location = 0.5 * (begin + end)  # 中点，即该option应该放置的坐标
        btn = tk.Button(self, command=_chooseImg, fg='#474747', text=self.options[0], font=self.ft,
                        activeforeground='#ADADAD', activebackground=self.bg, bg=self.bg, bd=0)
        btn.place(in_=self, relx=location, rely=0.5, anchor='center')

    def downloadImg(self):
        '''
        绘制“下载图片”的按钮
        '''
        begin = 1 / self.num  # 该option的起点
        end = begin + 1 / self.num  # 该option的终点
        location = 0.5 * (begin + end)  # 中点，即该option应该放置的坐标
        btn = tk.Button(self, command=self.topDwn, fg='#474747', text=self.options[1], font=self.ft,
                        activeforeground='#ADADAD', activebackground=self.bg, bg=self.bg, bd=0)
        btn.place(in_=self, relx=location, rely=0.5, anchor='center')

    def changeThreshold(self):
        '''
        绘制“调节门限”的按钮
        '''
        begin = 2 / self.num  # 该option的起点
        end = begin + 1 / self.num  # 该option的终点
        location = 0.5 * (begin + end)  # 中点，即该option应该放置的坐标
        btn = tk.Button(self, command=self.getMin, fg='#474747', text=self.options[2], font=self.ft,
                        activeforeground='#ADADAD', activebackground=self.bg, bg=self.bg, bd=0)
        btn.place(in_=self, relx=location, rely=0.5, anchor='center')

    def topDwn(self):
        '''
        绘制选择下载张数的对话窗口
        '''
        ft = font.Font(family='微软雅黑', size=10)
        self.dwnWin = tk.Toplevel(self)
        self.dwnWin.title('验证码自动下载')
        self.dwnWin.geometry('300x150-512-384')
        self.dwnWin.resizable(False, False)
        self.dwnNum = tk.Scale(self.dwnWin,
                               from_=0,
                               to=500,
                               resolution=5,  # 设置步距值
                               orient='horizontal',  # 设置水平方向
                               variable=self.imgNum,
                               )
        self.btnDwn = tk.Button(
            self.dwnWin, command=self.getNum, text='确定', font=ft)

        self.dwnNum.place(
            in_=self.dwnWin, relx=0.5, rely=0.35, width=200, height=50, anchor='center')
        self.btnDwn.place(
            in_=self.dwnWin, relx=0.5, rely=0.8, width=80, height=35, anchor='center')

    def getNum(self):
        num = int(self.imgNum.get())
        _downloadImg(num)
        self.dwnWin.destroy()

    def topLevel(self):
        '''
        绘制“调节门限”的对话窗口
        '''
        ft = font.Font(family='微软雅黑', size=10)
        self.win = tk.Toplevel(self)
        self.win.geometry('300x150-512-384')
        self.win.resizable(False, False)
        self.theMin = tk.Scale(self.win,
                               from_=0,
                               to=256,
                               resolution=1,  # 设置步距值
                               orient='horizontal',  # 设置水平方向
                               variable=self.Min,
                               )
        self.theMax = tk.Scale(self.win,
                               from_=0,
                               to=256,
                               resolution=1,  # 设置步距值
                               orient='horizontal',  # 设置水平方向
                               variable=self.Max,
                               )
        self.btn1 = tk.Button(
            self.win, command=self.getMax, text='确定', font=ft)
        self.btn2 = tk.Button(
            self.win, command=self.geThreshold, text='确定', font=ft)

    def getMin(self):
        '''
        获得门限的最小值
        '''
        global low

        self.topLevel()
        self.win.title('请确定门限的最小值')
        self.theMin.place(in_=self.win, relx=0.5, rely=0.35, width=200, height=50, anchor='center')
        self.btn1.place(in_=self.win, relx=0.5, rely=0.8, width=80, height=35, anchor='center')

    def getMax(self):
        '''
        销毁“确定最小值”的对话窗，
        同时创建“确定最大值”的对话窗
        '''
        global low

        low = self.Min.get()
        self.win.destroy()

        self.topLevel()
        self.win.title('请确定门限的最大值')
        self.theMax.configure(from_=low)
        self.theMax.place(in_=self.win, relx=0.5, rely=0.35, width=200, height=50, anchor='center')
        self.btn2.place(in_=self.win, relx=0.5, rely=0.8, width=80, height=35, anchor='center')

    def geThreshold(self):
        '''
        确定最大值并销毁窗口
        '''
        global high

        high = self.Max.get()
        _changeThreshold()
        self.win.destroy()


class Display(tk.Frame):

    """主体展示栏"""

    def __init__(self, master=None, bg=None):
        tk.Frame.__init__(self, master, bg=bg)
        self.bg = bg
        self.ftL = font.Font(family='微软雅黑', size=13)  # 左侧展示框的字体
        self.ftR = font.Font(family='微软雅黑', size=15)  # 右侧展示结果的字体
        self.pieces = []  # 存放经过格式、大小转换后的验证码碎片图
        self.resultStr = ' '  # 最终结果，以字符形式存储
        self.width = 0.4  # 展示栏左侧展示图片的宽度
        self.height = 0.25  # 展示栏左侧展示图片的高度
        self.leftImgX = 0.25  # 展示栏左侧展示图片的中心点，默认为坐边区域的中点即四分之一处
        self.leftY = 5  # 展示栏左侧展示图片的留白高度
        self.rightImgX = 0.1  # 展示栏右侧，验证码碎片左右的两边的留白
        self.size = 50  # 每张piece的绝对大小(默认为正方形)
        self.finalShow = tk.StringVar()  # 展示最后结果的文本框
        self.showText()
        self.showOrigin()
        self.showPure()
        self.showHist()
        self.__author__()
        t1 = threading.Thread(target=self.showImg)  # 子线程，等待读取图片的命令
        t1.start()
        t2 = threading.Thread(target=self.showRes)  # 子线程，等待自动识别
        t2.start()

    def showOrigin(self):
        '''
        绘制展示原图的框架
        '''
        location = 1 / 6  # 图片中心位置
        self.origin = tk.Label(
            self, text='原图', font=self.ftL, fg='#ADADAD', bg='#E0FFFF', bd=0)
        self.origin.place(in_=self, relwidth=self.width, relheight=self.height,
                          relx=self.leftImgX, rely=location, y=self.leftY, anchor='center')

    def showPure(self):
        '''
        绘制展示降噪位图的框架
        '''
        location = 1 / 2  # 图片中心位置
        self.pureFrame = tk.Label(
            self, text='降噪后的二值化图', font=self.ftL, fg='#ADADAD', bg='#E0FFFF', bd=0)
        self.pureFrame.place(in_=self, relwidth=self.width, relheight=self.height,
                             relx=self.leftImgX, rely=location, y=self.leftY, anchor='center')

    def showHist(self):
        '''
        绘制展示灰度直方图的框架
        '''
        location = 5 / 6  # 图片中心位置
        self.histFrame = tk.Label(
            self, text='灰度直方图', font=self.ftL, fg='#ADADAD', bg='#E0FFFF', bd=0)
        self.histFrame.place(in_=self, relwidth=self.width, relheight=self.height,
                             relx=self.leftImgX, rely=location, y=self.leftY, anchor='center')

    def showImg(self):
        '''
        给以上三个框架填充相应的图
        '''
        global imDeal
        global pieces

        while True:
            getCon.acquire()
            getCon.wait()  # 等待选取图片成功的命令

            ratio = im.size[0] / im.size[1]  # 原图的横纵比
            widthF = self.origin.winfo_width()  # 获得这个框架的宽度
            height = self.origin.winfo_height()  # 获得这个框架的高度
            width = int(height * ratio)  # 跟原图相同横纵比的宽度

            ori = im.resize((width, height))  # 经过比例放大后的原图
            imgOri = ImageTk.PhotoImage(ori)

            pure = imDeal.imgPure.resize((width, height))  # 经过比例放大后的位图
            pure = pure.convert('RGB')  # 从位图转换为rgb模式
            imgPure = ImageTk.PhotoImage(pure)

            imHistOri = imDeal.showHist()  # 灰度直方图
            imHist = imHistOri.resize((widthF, height))  # 经过拉伸后的灰度直方图
            imHist = ImageTk.PhotoImage(imHist)

            showOri = tk.Label(self.origin, image=imgOri)
            showPure = tk.Label(self.pureFrame, image=imgPure)
            showHist = tk.Label(self.histFrame, image=imHist)

            showOri.place(
                in_=self.origin, relx=0.5, rely=0.5, anchor='center')
            showPure.place(
                in_=self.pureFrame, relx=0.5, rely=0.5, anchor='center')
            showHist.place(
                in_=self.histFrame, relx=0.5, rely=0.5, anchor='center')

            getCon.release()

    def showText(self):
        '''
        展示栏右侧的文字
        '''
        pieceText = tk.Label(
            self, text='切割效果:', font=self.ftR, fg='#474747', bg=self.bg, bd=0)
        pieceText.place(in_=self, relx=0.6, rely=0.25, anchor='center')

        resText = tk.Label(
            self, text='识别结果:', font=self.ftR, fg='#474747', bg=self.bg, bd=0)
        resText.place(in_=self, relx=0.6, rely=0.65, anchor='center')

        self.finalShow.set('_____________')
        self.finalFrame = tk.Entry(
            bd=0, state='readonly', font=self.ftR, fg='#474747', justify='center',bg='#E0FFFF', readonlybackground='#E0FFFF')
        self.finalFrame.place(
            in_=self, relx=0.75, rely=0.65, width=120, height=30, anchor='center')
        self.finalFrame['textvariable'] = self.finalShow

    def showRes(self):
        '''
        接到“开始识图”命令后线程启动，展示结果
        '''
        while True:
            reCon.acquire()
            reCon.wait()  # 等待命令
            num = len(pieces)  # 创建与碎片数量相对应个框架
            self.pieces = []  # 清零，除掉上次剩余的验证码碎片
            self.resultStr = ' '  # 清零，除掉上次的验证码识别结果
            for i in range(num):  # 将各个验证码碎片图转换格式和大小后存为这个类的属性
                piece = pieces[i]
                piece = piece.resize((self.size, self.size))  # 拉伸
                piece = piece.convert('RGB')
                pieImg = ImageTk.PhotoImage(piece)  # 转换成可用于展示在tk上的图片
                self.pieces.append(pieImg)

            for i in range(num):  # 开始画图
                width = (1 - 2 * self.rightImgX) / num  # 去掉左右两个留白后每张piece间的宽度
                begin = 0.5 * (self.rightImgX + i * width)  # 每张piece的最左边的开始坐标
                end = 0.5 * (self.rightImgX + (i + 1) * width)  # 同上，最右边的结束坐标
                location = 0.5 + 0.5 * (begin + end)  # 中点，即该piece应该放置的坐标

                img = tk.Label(self, image=self.pieces[i], bg=self.bg, bd=0)
                img.place(
                    in_=self, width=self.size, height=self.size, relx=location, rely=0.45, anchor='center')

            for pie in res:
                self.resultStr = self.resultStr + pie + ' '
            self.finalShow.set(self.resultStr)

            reCon.release()

    def __author__(self):
        text = '作者：文鹏程  梁智戈\n华农12光信1班'
        ft = font.Font(family='微软雅黑', size=10)
        l = tk.Label(
            self, text=text, font=ft, fg='#474747', bg=self.bg, bd=0, justify='center')
        l.place(in_=self, relx=0.98, rely=0.98, anchor='se')


class Dialog(tk.Toplevel):

    """对话框"""

    def __init__(self, master=None, content=None):
        tk.Toplevel.__init__(self, master)
        self.geometry('300x150')
        self.attributes('-alpha', 0.95)
        self.content = content
        self.ft = font.Font(family='微软雅黑', size=15)
        self.resizable(False, False)
        self.show()
        self.quit()

    def show(self):
        ft = font.Font(family='微软雅黑', size=12)
        text = tk.Label(self, text=self.content, font=ft)
        text.place(in_=self, relwidth=1, relheight=0.6)

    def quit(self):
        ft = font.Font(family='微软雅黑', size=15)
        btn = tk.Button(self, command=self.destroy, text='确定', font=ft)
        btn.place(
            in_=self, relx=0.5, rely=0.8, width=80, height=35, anchor='center')


root = Root()
root.title('简单验证码识别')
drawHelp(root, 500, 250)
root.mainloop()
