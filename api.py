from flask import make_response, session, Response, request, g, url_for, render_template
from flask_mail import Message
import random
import string
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import os, datetime

from . import mail

#验证码类
class ImageCode():
    #生成随机颜色
    def __randomColor(self):
        return (random.randint(32, 127), random.randint(32, 127), random.randint(32, 127))

    #随机划线
    def __drawLine(self, draw, num, width, height):
        for num in range(num):
            x1 = random.randint(0, width / 2)
            y1 = random.randint(0, height / 2)
            x2 = random.randint(0, width)
            y2 = random.randint(height / 2, height)
            draw.line(((x1, y1), (x2, y2)), fill='black', width=1)
    
    #生成验证码图片
    def __getVerifyCode(self):
        code = generateCode()
        width, height = 120, 50
        image = Image.new('RGB', (width, height), 'white')
        font = ImageFont.truetype('app/static/arial.ttf', 40)
        draw = ImageDraw.Draw(image)

        for item in range(4):
            draw.text((5+random.randint(-3,3)+23*item, 5+random.randint(-3,3)),
                  text=code[item], fill=self.__randomColor(), font=font)
        
        self.__drawLine(draw, 2, width, height)
        image = image.filter(ImageFilter.GaussianBlur(radius=1.5))
        return image, code

    #生成向前端的反馈
    def getImageCode(self):
        image, code = self.__getVerifyCode()
        buffer = BytesIO()
        image.save(buffer, 'jpeg')
        bufferStr = buffer.getvalue()
        response = make_response(bufferStr)
        response.headers['Content-Type'] = 'image/gif'
        session['imageCode'] = code
        return response

#生成随机字母数字
def generateCode() -> str:
    return ''.join(random.sample(string.ascii_letters + string.digits, 4))

#发送邮件
def sendMail(app, desemail, captcha):
    with app.app_context():
        message = Message(subject = 'XXBBS注册验证码', recipients=[desemail])
        message.html = render_template('auth/emailcode.html', code=captcha)
        mail.send(message)

#上传图片
def uploadImg(uuid, name, file):
    if not file:
        return False
    else:
        if name == "avatar":
            im = Image.open(file)
            if im.size[0] > im.size[1]:
                x = 0.5*(im.size[0] - im.size[1])
                y = 0
                w = im.size[1]
                h = im.size[1]
            else:
                x = 0
                y = 0.5*(im.size[1] - im.size[0])
                w = im.size[0]
                h = im.size[0]
            _file = im.crop((x, y, x+w, y+h))
        else:
            _file = file
        ext = os.path.splitext(file.filename)[1]
        filename = name + ext
        current_path = os.path.abspath(os.path.dirname(__file__))       #获取当前文件夹绝对路径
        filedir = os.path.join(current_path, 'data/img')                #获取保存图片的路径
        filepath = os.path.join(filedir, str(uuid))                     #获取当前用户保存图片的路径
        if not os.path.exists(filepath):
            os.mkdir(filepath)
        _file.save(os.path.join(filepath, filename))
        return True

#读取图片，包括帖子中的图片和用户头像
def readImg(uuid, name):                                                    #uuid区分不同用户的id，name区分图片名称
    current_path = os.path.abspath(os.path.dirname(__file__))
    filedir = os.path.join(current_path, 'data/img')
    filepath = os.path.join(filedir, str(uuid))                             #获取图片文件路径

    if os.path.exists(os.path.join(filepath, name)):
        with open(os.path.join(filepath, name), 'rb') as f:
            res = Response(f.read(), mimetype="image/jpeg")
    else:
        with open(os.path.join(current_path, 'static/img/avatar.jpg'), 'rb') as f:
            res = Response(f.read(), mimetype="image/jpeg")
        
    return res                                                              #返回图片

#获取表内的一行数据
def getData(cursor, table, key, value):
    cursor.execute(
        'SELECT * FROM '+table+' WHERE '+key+'=%s;', (value,)
    )
    return cursor.fetchone()

#获取表内一行数据的部分列
def getPartData(cursor, table, key, value, *data):
    cursor.execute(
        'SELECT '+(','.join(data))+' FROM '+table+' WHERE '+key+'=%s;', (value,)
    )
    return cursor.fetchone()

#获取用户名字
def getUserName(cursor, uuid):
    cursor.execute(
        'SELECT name FROM user WHERE uuid=%s;', (uuid,)
    )
    user = cursor.fetchone()
    return user[0] if user is not None else None

#获取用户组名字
def getGroupName(name):
    groupdic = {
        'admin': '管理员',
        'normal': '普通会员',
        'ban': '禁言状态',
        'part1': '技术分享 版主',
        'part2': '学习生活 版主',
        'part3': '休闲娱乐 版主',
        'part4': '摸鱼灌水 版主'
    }
    return groupdic[name]