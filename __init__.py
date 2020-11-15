import os

from flask import Flask
from flask_mail import Mail

mail = None         #邮件发送对象

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(  #默认配置
        HOST="127.0.0.1",
        PORT=3306,
        USER="root",
        PASSWORD="root",
        DATABASE="bbs",

        MAIL_SERVER='smtp.qq.com',
        EMAIL_USERNAME="null",
        EMAIL_PASSWORD="null",
        MAIL_DEFAULT_SENDER="null",
        MAIL_USE_TLS=True,
        MAIL_PORT=587
    )
    app.config.from_pyfile('config.py', silent=True)  #载入配置文件
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    global mail
    mail = Mail(app)

    from BBS import database
    database.init_app(app)       #注册数据库初始化命令

    @app.route('/test')
    def hello():
        return "这是一个测试网站"
    
    return app