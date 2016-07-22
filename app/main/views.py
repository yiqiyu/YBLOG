# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 21:43:00 2016

@author: Administrator
"""
import traceback
#import logging

from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, g
from flask.ext.sqlalchemy import get_debug_queries
import flask_sijax
from pyquery import PyQuery as pq

from . import main
from .forms import SubscribeForm, CommentForm, ReplyForm, MessageForm
from .. import db
from ..email import send_email
from ..models import Follower, Comment, Post, Message


DEFAULT_REPLY_TO_ID = 1
#logging.basicConfig(level=logging.INFO,  
#                    filename='./log/test.log',  
#                    filemode='w')  


def add_otherwise_rollback(entity, message):
    try:
        db.session.add(entity)
        db.session.commit()
        flag = True
        category = 'info'
    except:
        db.session.rollback()
        message = u'Oops...我们的服务器貌似出了点问题，请重试'
        category = 'error'
        flag = False
        if current_app.debug is True or current_app.testing is True:
            with open("./log/log.txt",'a') as f:
                traceback.print_exc(file=f)
                f.flush()
    finally:
        flash(message, category)
        return flag


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['BLOG_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response
    

@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/', methods=['GET', 'POST'])
def index():
    subscribeForm = SubscribeForm()
    if subscribeForm.validate_on_submit():
        if Follower.query.filter_by(email=subscribeForm.email.data).count():
            flash(u'您已经关注过本博客了~')
        else:
            follower = Follower(name=subscribeForm.name.data,
                                email=subscribeForm.email.data)
            add_otherwise_rollback(follower, u'你已成功关注我的博客！谢谢！')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['BLOG_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', subscribeForm=subscribeForm, 
                           posts=posts, pagination=pagination)


@main.route('/unsubscribe/<int:id>')
def unsubscribe(id):
    if request.args.get('unsubscribe'):
        follower = Follower.query.get_or_404(id)
        follower.subscribed = False
        add_otherwise_rollback(follower, u'你已取消关注！感恩我们曾在一起的日子~')
        return redirect(url_for('.index'))
    return render_template('unsubscribe.html', id=id)
    
    
@main.route('/reply_notice_cancel/<int:id>')
def reply_notice_cancel(id):
    if request.args.get('notice_cancel'):
        comment = Comment.query.get_or_404(id)
        comment.email_remind = False
        add_otherwise_rollback(comment, u'你已取消回复提醒！')
        return redirect(url_for('.index'))
    return render_template('reply_notice_cancel.html', id=id)


@main.route('/message_board', methods=['GET', 'POST'])
def message_board():    
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(body=form.body.data,
                          email=form.email.data,
                          author_name=form.name.data)
        add_otherwise_rollback(message, u'感谢您的留言让我能做的更好！')
        return redirect(url_for('.message_board'))
    page = request.args.get('page', 1, type=int)
    query = Message.query
    if page == -1:
        page = (query.count() - 1) // \
            current_app.config['BLOG_COMMENTS_PER_PAGE'] + 1
    pagination = query.order_by(Message.timestamp.asc()).paginate(
        page, per_page=current_app.config['BLOG_COMMENTS_PER_PAGE'],
        error_out=False)
    messages = pagination.items
    return render_template('message_board.html', form=form,
                           messages=messages, pagination=pagination)


@flask_sijax.route(main, '/post/<int:id>', methods=['GET', 'POST'])                          
#@main.route('/post/<int:id>', methods=['GET', 'POST'])
def blog_post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        default_reply_to = post.comments.order_by(Comment.timestamp.asc()).first()
        comment_index = post.comments.count()
        comment = Comment(body=form.body.data,
                          post=post,
                          email=form.email.data,
                          reply_to=default_reply_to,
                          comment_index=comment_index,
                          author_name=form.name.data,
                          email_remind=form.email_remind.data)
        add_otherwise_rollback(comment, u'你的评论已被提交。')
        return redirect(url_for('.blog_post', id=post.id, page=-1))
        
    if g.sijax.is_sijax_request:
        g.sijax.register_callback('ajax_reply', ajax_reply)
        return g.sijax.process_request()
        
    page = request.args.get('page', 1, type=int)
    if page == -1:
        #若是回复后的跳转，则计算最后一页的页码
        page = (post.comments.count() - 2) // \
            current_app.config['BLOG_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['BLOG_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)
                           

@main.route('/reply/<int:id>', methods=['GET', 'POST'])
def reply(id):
    reply_to = Comment.query.get_or_404(id) 
    form = ReplyForm()
    if form.validate_on_submit():
        post = reply_to.post
        comment_index = post.comments.count()
        comment = Comment(post=post,
                          comment_index=comment_index,
                          reply_to=reply_to,
                          body=form.body.data,
                          email=form.email.data,
                          author_name=form.name.data,
                          email_remind=form.email_remind.data)
        if add_otherwise_rollback(comment, u'您的回复已被提交。') and \
            reply_to.email_remind:
            page = (post.comments.count() - 2) // \
                    current_app.config['BLOG_COMMENTS_PER_PAGE'] + 1
            send_email(reply_to.email, u'您的评论有一个新回复！',
                       'email/new_reply', name = reply_to.author_name, 
                       page=page,  
                       post_id = post.id,
                       comment_index=str(comment_index),
                       reply_to_id=reply_to.id)
        return redirect(url_for('.blog_post', id=post.id, page=-1))
    return render_template('reply.html', form=form, reply_to=reply_to)
    

def ajax_reply(obj_response, id):
    reply_to = Comment.query.get_or_404(id)
    form = ReplyForm()
    template = render_template('reply.html', form=form, reply_to=reply_to)
    renderedForm = pq(template)
    obj_response.html_append("div.replyToggle", renderedForm(".ajax-reply").html())