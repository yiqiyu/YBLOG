# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 22:57:41 2016

@author: Administrator
"""

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp

class SubscribeForm(Form):
    name = StringField(u'昵称', validators=[
        Length(1, 64), Regexp(u'^[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9_.]*$', 0,
                                          u'名称只允许包含汉字，字母，数字和下划线！')])
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField(u'提交')


class CommentForm(Form):
    name = StringField(u'昵称', validators=[
        Required(), Length(1, 64), Regexp(u'^[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z0-9_.]*$', 0,
                                          u'名称只允许包含汉字，字母，数字和下划线！')])
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    body = StringField(u'评论内容', validators=[Required()])
    submit = SubmitField(u'提交')
    

class ReplyForm(CommentForm):
    body = StringField(u'回复内容', validators=[Required()])
    submit = SubmitField(u'提交')


class MessageForm(CommentForm):
    body = StringField(u'留言内容', validators=[Required()])
    submit = SubmitField(u'提交')