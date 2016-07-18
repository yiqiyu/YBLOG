# -*- coding: utf-8 -*-

import re
import threading
import time
import unittest

from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app import create_app, db
from app.models import Follower, Post


class SeleniumTestCase(unittest.TestCase):
    client = None
    
    @classmethod
    def setUpClass(cls):
        # start Firefox
        try:
            cls.client = webdriver.Firefox()
        except:
            pass

        # skip these tests if the browser could not be started
        if cls.client:
            # create the application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # suppress logging to keep unittest output clean
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # create the database and populate with some fake data
            db.create_all()
            Post.generate_fake()

            # start the Flask server in a thread
            threading.Thread(target=cls.app.run).start()

            # give the server a second to ensure it is up
            time.sleep(1) 

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # stop the flask server and the browser
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.close()

            # destroy database
            db.drop_all()
            db.session.remove()

            # remove application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')
        self.client.implicitly_wait(30)

    def tearDown(self):
        pass
    
    def test_home(self):
        # navigate to home page
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('Welcome to YBLOG!',
                                  self.client.page_source))
                                  
        # navigate to post page
        self.client.find_element_by_link_text(u'详情').click()
        time.sleep(2)
        self.assertTrue(u'评论区' in self.client.page_source)                                  
                                  
    def test_reply(self):
        # comment
        self.client.get('http://localhost:5000/post/1')
        self.client.find_element_by_name('email').\
            send_keys('john@example.com')
        self.client.find_element_by_name('name').send_keys('cat')
        self.client.find_element_by_name('body').send_keys('fake')
        self.client.find_element_by_name('submit').click()
        self.assertTrue('cat' in self.client.page_source)
        self.assertTrue('fake' in self.client.page_source)

        # toggle reply form
        self.client.find_element_by_link_text(u'回复').click()
#        element = WebDriverWait(self.client, 20).until(
#                EC.presence_of_element_located((By.CLASS_NAME, "ajax-reply"))
#                )
#        print element
        time.sleep(13)
        page = etree.HTML(self.client.page_source)
        self.assertTrue(page.xpath('//*[@id="1L"]/div[5]/div'))
        
        
        # receive reply form
        self.assertTrue(page.xpath('//*[@id="1L"]/div[5]/div/form'))

        # send reply
        self.client.find_element_by_xpath('//*[@id="email"][1]').\
            send_keys('john@example.com')
        self.client.find_element_by_xpath('//*[@id="name"][1]').send_keys('dog')
        self.client.find_element_by_xpath('//*[@id="body"][1]').send_keys('fake2')
        self.client.find_element_by_xpath('//*[@id="submit"][1]').click()
        self.assertTrue('dog' in self.client.page_source)
        self.assertTrue('fake2' in self.client.page_source)
        
    def test_message(self):
        self.client.get('http://localhost:5000/message_board')
        self.assertTrue(u'<h1>留言</h1>' in self.client.page_source)
        self.client.find_element_by_name('email').\
            send_keys('john@example.com')
        self.client.find_element_by_name('name').send_keys('cat')
        self.client.find_element_by_name('body').send_keys('fake')
        self.client.find_element_by_name('submit').click()
        self.assertTrue('cat' in self.client.page_source)
        self.assertTrue('fake' in self.client.page_source)
        self.assertTrue('john@example.com' not in self.client.page_source)