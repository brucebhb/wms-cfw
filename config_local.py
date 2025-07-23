#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地开发配置文件
"""

import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-local-development'
    
    # 使用SQLite作为本地开发数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///warehouse_local.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': False  # 设置为True可以看到SQL语句
    }
    
    # Redis配置（本地开发可以禁用）
    REDIS_URL = os.environ.get('REDIS_URL') or None
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=6)
    SESSION_COOKIE_SECURE = False  # 本地开发设置为False
    SESSION_COOKIE_HTTPONLY = True
    
    # 日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = 'logs/app_local.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 分页配置
    RECORDS_PER_PAGE = 20
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    
    # 开发模式配置
    DEBUG = True
    TESTING = False
    
    # 禁用CSRF（仅用于本地开发调试）
    WTF_CSRF_ENABLED = False
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保日志目录存在
        log_dir = os.path.dirname(Config.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 确保上传目录存在
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': True  # 开发环境显示SQL
    }

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
