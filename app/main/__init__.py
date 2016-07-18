# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 22:10:14 2016

@author: Administrator
"""

from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors