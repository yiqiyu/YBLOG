# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 21:43:00 2016

@author: Administrator
"""
#import logging

from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, g
from flask.ext.sqlalchemy import get_debug_queries
import flask_sijax
from flask.ext.login import current_user
from pyquery import PyQuery as pq

from . import main
from ..functions import add_otherwise_rollback
from .forms import SubscribeForm, CommentForm, ReplyForm, MessageForm, AdminForm
from ..email import send_email
from ..models import Follower, Comment, Post, Message


DEFAULT_REPLY_TO_ID = 1
#logging.basicConfig(level=logging.INFO,  
#                    filename='./log/test.log',  
#                    filemode='w')  


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
        send_email(current_app.config['BLOG_MAIL_SENDER'], u'您有一个新留言！',
                       'email/new_message', 
                       name = form.name.data if hasattr(form, 'name') else u"您")
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
    form = AdminForm() if current_user.is_authenticated else CommentForm()
    if form.validate_on_submit():
        default_reply_to = post.comments.order_by(Comment.timestamp.asc()).first()
        comments_count = Comment.query.count()+1
        post.add_comment(form, default_reply_to, current_user)
        page = (comments_count-2) // \
                    current_app.config['BLOG_COMMENTS_PER_PAGE'] + 1
        send_email(current_app.config['BLOG_MAIL_SENDER'], u'您有一个新回复！',
                       'email/new_reply_to_me', 
                       name = form.name.data if hasattr(form, 'name') else u"您", 
                       page=page,  
                       post_id = post.id,
                       comment_index=str(comments_count-1))
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
    form = AdminForm() if current_user.is_authenticated else ReplyForm()
    if form.validate_on_submit():
        post = reply_to.post
        comment = post.add_comment(form, reply_to, current_user)        
        if comment and reply_to.email_remind:
            comments_count = comment.comment_index+1
            page = (comments_count-2) // \
                    current_app.config['BLOG_COMMENTS_PER_PAGE'] + 1
            send_email(reply_to.email, u'您的评论有一个新回复！',
                       'email/new_reply', 
                       name = 'YYQ' if current_user.is_authenticated else form.name.data, 
                       page=page,  
                       post_id = post.id,
                       comment_index=str(comments_count-1),
                       reply_to_id=reply_to.id)
        return redirect(url_for('.blog_post', id=post.id, page=-1))
    return render_template('reply.html', form=form, reply_to=reply_to)
    

def ajax_reply(obj_response, id):
    reply_to = Comment.query.get_or_404(id)
    form = AdminForm() if current_user.is_authenticated else ReplyForm()
    template = render_template('reply.html', form=form, reply_to=reply_to)
    renderedForm = pq(template)
    obj_response.html_append("div.replyToggle", renderedForm(".ajax-reply").html())