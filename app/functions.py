# -*- coding: utf-8 -*-
"""
Created on Sun Sep 04 21:17:35 2016

@author: Administrator
"""
import traceback
import functools

from . import db
from flask import current_app, flash


def otherwise_rollback(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        try:
            func(*args, **kw)
            flag = True
            category = 'info'
        except Exception:
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
    return wrapper

            
def add_otherwise_rollback(entity, message):
    try:
        db.session.add(entity)
        db.session.commit()
        flag = True
        category = 'info'
    except Exception:
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


