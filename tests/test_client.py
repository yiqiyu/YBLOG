# -*- coding: utf-8 -*-

import re
import unittest
from flask import url_for
from app import create_app, db
from app.models import Comment, Post, Follower

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)
        test_post = Post(title='test', body='testtest')
        db.session.add(test_post)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue(b'Welcome to YBLOG!' in response.data)

    def test_subscribe_and_unsubscribe(self):
        # test subscribe
        response = self.client.post(url_for('main.index'), data={
            'email': 'john@example.com',
            'name': 'john'
        })
        self.assertTrue(response.status_code == 302)
        
        # test unsubscribe
        john = Follower.query.filter_by(name='john').first()
        response = self.client.get(url_for('main.unsubscribe', id=john.id, unsubscribe=True), 
        follow_redirects=True)
        self.assertTrue(john.subscribed is False)

    def test_message(self):
        # test message
        response = self.client.post(url_for('main.message_board'), data={
            'email': 'john@example.com',
            'author_name': 'john',
            'body': 'hello!'
        }, follow_redirects=True)
        self.assertTrue(re.search(b'john', response.data))
        self.assertTrue(re.search(b'hello!', response.data))

    def test_comment_and_reply_and_cancel_notice(self):
        # test comment
        response = self.client.post(url_for('main.blog_post', id=1), data={
            'email': 'john@example.com',
            'name': 'kate',
            'body': 'Well done!'
        }, follow_redirects=True)
        kate = Comment.query.filter_by(author_name='kate').first()
        self.assertTrue(kate)
        self.assertTrue(re.search(b'kate', response.data))
        self.assertTrue(re.search(b'Well done!', response.data))

        # test reply    
        response = self.client.post(url_for('main.reply', id=kate.id), data={
            'email': 'eee@example.com',
            'name': 'jack',
            'body': 'I think so!'
        }, follow_redirects=True)
        self.assertTrue(re.search(b'kate', response.data))
        self.assertTrue(Comment.query.filter_by(author_name='jack').first())
        self.assertTrue(re.search(b'jack', response.data))
        self.assertTrue(re.search(b'I think so!', response.data))
        
        # cancel notice
        response = self.client.get(url_for('main.reply_notice_cancel', id=kate.id, notice_cancel=True), 
        follow_redirects=True)
        self.assertTrue(kate.email_remind is False)
        
