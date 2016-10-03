# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import PasswordField, BooleanField, SubmitField
from wtforms.validators import Required


class LoginForm(Form):
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in', default="checked")
    submit = SubmitField('Log In')
