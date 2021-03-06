from flask import(
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Response
)
import os, datetime
from PIL import Image

from .auth import loginRequired
from .database import getDatabase
from .api import readImg, uploadImg, getData, getPartData

editbp = Blueprint('edit', __name__, url_prefix='/edit')

@editbp.route('/<int:part>/create', methods=('GET','POST'))
@loginRequired
def create(part):
    if part < 1 or part > 4 or g.userinfo[2] == 'ban':
        return render_template('404.html')
    database = getDatabase()
    cursor = database.cursor()

    if request.method == 'POST':
        title = request.form['title']       #标题
        content = request.form['content']   #内容
        _type = request.form['type']        #发往的版块
        dtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #创建新主题
        cursor.execute(
                    'INSERT INTO post(id, title, type, content, userid, posttime, updatetime, reply, visit, collect)'
                    'VALUES(null, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
                    , (title, _type, content, g.user[0], dtime, dtime, '', 1, 0)
                )
        cursor.execute(
            'UPDATE userinfo SET point=point+3 WHERE uuid=%s;', (g.user[0],)        #发表主题获得积分
        )
        return redirect(url_for('index.index'))
    return render_template('post/edit.html', post=[0, 0, part])

@editbp.route('/<int:id>/post', methods=('GET', 'POST'))
@loginRequired
def edit(id):
    database = getDatabase()
    cursor = database.cursor()
    post = getData(cursor, 'post', 'id', id)
    if post is None or not hasPermission(post[4], post[2]):         #检查是否有权限
        return render_template('404.html')          #返回404

    if request.method == 'POST':
        title = request.form['title']       #标题
        content = request.form['content']   #内容
        _type = None
        dtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if 'type' in request.form:
            _type = request.form['type']        #发往的版块
            cursor.execute(
                        'UPDATE post SET title=%s, type=%s, content=%s, updatetime=%s WHERE id=%s;'
                        , (title, _type , content, dtime, id,)
                    )
        else:
            cursor.execute(
                        'UPDATE post SET title=%s, content=%s, updatetime=%s WHERE id=%s;'
                        , (title, content, dtime, id,)
                    )
        return redirect(url_for('posts.posts', postid=id, page=1))
    
    return render_template('post/edit.html', post=post)

@editbp.route('/<int:id>/delete')
@loginRequired
def delete(id):
    database = getDatabase()
    cursor = database.cursor()
    post = getPartData(cursor, 'post', 'id', id, 'userid', 'type', 'reply')     #获取帖子信息
    if post is None or not hasPermission(post[0], post[1]):                     #检查是否有权限
        return render_template('404.html')          #返回404

    replys = post[2].split(' ')
    for reply in replys:                            #删除该帖子的所有回复
        if reply != '':
            cursor.execute(
                'DELETE FROM reply WHERE id=%s;', (reply,)
            )

    cursor.execute(
        'DELETE FROM post WHERE id=%s;', (id,)
    )
    return redirect(url_for('parts.parts', type = post[1], page = 1))

@editbp.route('/<int:id>/delreply/<int:replyid>')
@loginRequired
def delreply(id, replyid):          #删除回复
    database = getDatabase()
    cursor = database.cursor()
    post = getPartData(cursor, 'post', 'id', id, 'userid', 'type', 'reply')              #获取帖子信息
    reply = getPartData(cursor, 'reply', 'id', replyid, 'id')
    if reply is None or post is None or not hasPermission(post[0], post[1]):    #检查是否有权限
        return render_template('404.html')          #返回404

    cursor.execute(
        'DELETE FROM reply WHERE id=%s;', (replyid,)    #删除回复
    )
    replylist = post[2].split(' ')
    if '' in replylist:
        replylist.remove('')
    replylist.remove(str(replyid))
    cursor.execute(
        'UPDATE post SET reply=%s WHERE id=%s;', (' '.join(replylist), id,)     #从帖子中删除回复
    )

    return redirect(url_for('posts.posts', postid = id, page = 1))

@editbp.route('/upload', methods=('GET', 'POST'))
@loginRequired
def upload():
    if request.method == 'POST':
        file = request.files.get('editormd-image-file')     #获取上传的图片
        if not file:
            result = {
                'success':0,
                'message':'上传失败'
            }
        else:
            ext = os.path.splitext(file.filename)[1]
            filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            uploadImg(g.user[0], filename, file)
            result = {
                'success':1,
                'message':'上传成功',
                'url':url_for('edit.image', id=g.user[0], name=filename + ext)
            }
        return result

@editbp.route('/image/<int:id>/<name>')
def image(id, name):
    return readImg(id, name)

#检查用户是否有对帖子的操作权限
def hasPermission(userid, typep):
    if g.userinfo[2] == 'ban':
        return False
    if userid != g.user[0] and g.userinfo[2] != 'admin' and g.userinfo[2] != 'part' + str(typep):
        return False
    return True


