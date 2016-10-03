# -*- coding: utf-8 -*-
from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, login_required
from . import auth
from .. import db
from ..models import Administrator, Comment, Message
from ..email import send_email
from .forms import LoginForm


@auth.route('/myadmin', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    user = Administrator.query.get(1)
    if form.validate_on_submit():
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/comment/<int:id>/delete')
@login_required
def delete_comment(id):
    comment = Comment.query.get(id)
    post_id = comment.post_id
    comment.delete_comment()
    return redirect(url_for('main.blog_post', id=post_id, _anchor='comments'))


@auth.route('/message/<int:id>/delete')
@login_required
def delete_message(id):
    message = Message.query.get(id)
    message.delete_message()
    return redirect(url_for('main.message_board'))

#增加回复后通知功能