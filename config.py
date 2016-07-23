# -*- coding: utf-8 -*-
"""
Created on Sun Jun 19 20:27:23 2016

@author: Administrator
"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))
dbconn = "mysql://root:password@localhost/"


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'say you love me'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False
    MAIL_SERVER = 'smtp.126.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    BLOG_MAIL_SUBJECT_PREFIX = '[YBLOG]'
    BLOG_MAIL_SENDER = 'YBLOG <dante3@126.com>'
    BLOG_ADMIN = os.environ.get('YBLOG_ADMIN') or "YBOLG ADMIN"
    BLOG_POSTS_PER_PAGE = 20
    BLOG_FOLLOWERS_PER_PAGE = 50
    BLOG_COMMENTS_PER_PAGE = 30
    SQLALCHEMY_RECORD_QUERIES = True
    BLOG_DB_QUERY_TIMEOUT = 0.5
    BLOG_POSTS_DIR = os.path.join(basedir, 'post')
    SIJAX_STATIC_PATH = os.path.join(basedir, 'app/static/js/sijax/')
    SIJAX_JSON_URI = os.path.join(SIJAX_STATIC_PATH, 'json2.js')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BLOG_SLOW_DB_QUERY_TIME = 0.5

    @staticmethod
    def init_app(app):
        pass
    

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        dbconn+'data_dev'+'?charset=utf8'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        dbconn+'data_test'+'?charset=utf8'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        dbconn+'data_prod'+'?charset=utf8'

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.BLOG_MAIL_SENDER,
            toaddrs=[cls.BLOG_ADMIN],
            subject=cls.BLOG_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,

    'default': DevelopmentConfig
}