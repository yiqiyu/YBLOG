# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 22:57:41 2016

@author: Administrator
"""

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import Required, Length, Email, Regexp

class SubscribeForm(Form):
    name = StringField(u'昵称', validators=[
        Length(1, 64), Regexp(u'^[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9_.]*$', 0,
                                          u'名称只允许包含汉字，字母，数字和下划线！')])
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField(u'提交')


class BasicForm(Form):
    name = StringField(u'昵称(必须)', validators=[
        Required(), Length(1, 64), Regexp(u'^[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9_.]*$', 0,
                                          u'名称只允许包含汉字，字母，数字和下划线！')])
    email = StringField(u'Email(必须)', validators=[Required(), Length(1, 64),
                                             Email()])
    body = TextAreaField(u'评论内容', validators=[Required()], render_kw={'placeholder': u'说点什么吧...'})


class CommentForm(BasicForm):
    email_remind = BooleanField(u'有人回复时邮件通知我', default="checked")
    submit = SubmitField(u'提交')
    

class ReplyForm(CommentForm):
    body = TextAreaField(u'回复内容', validators=[Required()], render_kw={'placeholder': u'说点什么吧...'})
    email_remind = BooleanField(u'有人回复时邮件通知我', default="checked")
    submit = SubmitField(u'提交')


class MessageForm(BasicForm):
    body = TextAreaField(u'留言内容', validators=[Required()], render_kw={'placeholder': u'说点什么吧...'})
    submit = SubmitField(u'提交')