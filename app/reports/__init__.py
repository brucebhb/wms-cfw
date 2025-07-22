#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计报表模块
"""

from flask import Blueprint

bp = Blueprint('reports', __name__)

from app.reports import routes
