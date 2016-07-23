# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 18:28:11 2016

@author: Administrator
"""
import traceback
import os
import codecs

from datetime import datetime
from markdown import markdown
import bleach
from flask import url_for, current_app
from app.exceptions import ValidationError

from . import db
from email import send_email


class Follower(db.Model):
    __tablename__ = 'followers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True, index=True)
    subsribed = db.Column(db.Boolean, default=True)
    subsribed_since = db.Column(db.DateTime(), default=datetime.utcnow)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy='dynamic',
                               cascade="all, delete-orphan")

    #为每一篇博文设置默认的一个评论，所有其他无实际回复的评论则将会视为回复该评论
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        default_comment = Comment()
        default_comment.disabled = True
        default_comment.post = self
        db.session.add(default_comment)
        db.session.commit()

    @staticmethod
    def generate_fake(count=10):
        from random import seed, randint
        import forgery_py

        seed()
        for i in range(count):
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True))
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))
            
    @staticmethod
    def add_post():
        blog_dir = current_app.config['BLOG_POSTS_DIR']
        get_id = lambda x: int(os.path.splitext(x)[0].split("-")[0])
        posts = [post for post in os.listdir(blog_dir)\
                if not Post.query.get(get_id(post))]
        new_posts = []
        for post in posts:
            with codecs.open(os.path.join(blog_dir, post), encoding='utf-8') as f:
                file_name = os.path.splitext(post)[0].split("-")
                id = int(file_name[0])
                title = file_name[1].decode('gb2312').encode('utf-8')
                new_posts.append(id)
                body = f.read()
#                print chardet.detect(title)
                db.session.add(Post(id=id, title=title, body=body))
        db.session.commit()
        #邮件通知关注者有更新
        for follower in Follower.query.all():
            send_email(follower.email, u"您关注的博客有新更新啦！", 
                       'email/new_posts', posts=[Post.query.get(id) for id in new_posts],
                       name=follower.name,
                       follower_id=follower.id)
                       
    @staticmethod
    def add_post_secured():
        try:
            Post.add_post()
        except:
            db.session.rollback()
            traceback.print_exc()
    

db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_name = db.Column(db.String(64))
    email = db.Column(db.String(64), index=True)
    comment_index = db.Column(db.Integer)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    replies = db.relationship('Comment', 
                              backref=db.backref("reply_to", remote_side=id),
                              lazy='dynamic')
    reply_to_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    email_remind = db.Column(db.Boolean, default=True)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Message(db.Model):
    __tablename__ = 'main_page_comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    email = db.Column(db.String(64), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_name = db.Column(db.String(64))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)


db.event.listen(Message.body, 'set', Message.on_changed_body)