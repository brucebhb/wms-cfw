-- MySQL数据库初始化脚本
-- 创建仓储管理系统数据库

-- 创建数据库
CREATE DATABASE IF NOT EXISTS warehouse_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 创建用户（如果不存在）
CREATE USER IF NOT EXISTS 'warehouse_user'@'localhost' IDENTIFIED BY 'warehouse123';

-- 授权
GRANT ALL PRIVILEGES ON warehouse_db.* TO 'warehouse_user'@'localhost';

-- 也为root用户授权（开发环境）
GRANT ALL PRIVILEGES ON warehouse_db.* TO 'root'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 使用数据库
USE warehouse_db;

-- 显示创建结果
SELECT 'Database warehouse_db created successfully!' as Result;
SHOW DATABASES LIKE 'warehouse_db';
