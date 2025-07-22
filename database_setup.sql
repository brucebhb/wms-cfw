-- 仓储管理系统数据库初始化脚本
-- 针对生产环境优化

-- 创建数据库
CREATE DATABASE IF NOT EXISTS warehouse_production 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE warehouse_production;

-- 创建用户和授权
CREATE USER IF NOT EXISTS 'warehouse_user'@'localhost' IDENTIFIED BY 'warehouse_secure_2024';
GRANT ALL PRIVILEGES ON warehouse_production.* TO 'warehouse_user'@'localhost';

-- 创建只读用户（用于备份和监控）
CREATE USER IF NOT EXISTS 'warehouse_readonly'@'localhost' IDENTIFIED BY 'readonly_2024';
GRANT SELECT ON warehouse_production.* TO 'warehouse_readonly'@'localhost';

FLUSH PRIVILEGES;

-- 创建仓库表
CREATE TABLE IF NOT EXISTS warehouses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_code VARCHAR(20) NOT NULL UNIQUE,
    warehouse_name VARCHAR(100) NOT NULL,
    warehouse_type ENUM('frontend', 'backend') NOT NULL,
    address TEXT,
    contact_person VARCHAR(50),
    contact_phone VARCHAR(20),
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_warehouse_code (warehouse_code),
    INDEX idx_warehouse_type (warehouse_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入初始仓库数据
INSERT IGNORE INTO warehouses (warehouse_code, warehouse_name, warehouse_type, address, contact_person, contact_phone) VALUES
('PH', '平湖仓', 'frontend', '广东省深圳市平湖物流园区A区', '张经理', '13800138001'),
('KS', '昆山仓', 'frontend', '江苏省苏州市昆山经济开发区B区', '李经理', '13800138002'),
('CD', '成都仓', 'frontend', '四川省成都市双流区物流中心C区', '王经理', '13800138003'),
('PX', '凭祥北投仓', 'backend', '广西壮族自治区崇左市凭祥市北投物流园', '赵经理', '13800138004');

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    employee_id VARCHAR(50),
    warehouse_id INT,
    user_type ENUM('admin', 'manager', 'operator', 'customer') DEFAULT 'operator',
    is_admin BOOLEAN DEFAULT FALSE,
    status ENUM('active', 'inactive', 'locked') DEFAULT 'active',
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_warehouse_id (warehouse_id),
    INDEX idx_user_type (user_type),
    INDEX idx_status (status),
    INDEX idx_employee_id (employee_id),
    
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建入库记录表
CREATE TABLE IF NOT EXISTS inbound_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inbound_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_plate_number VARCHAR(20),
    plate_number VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    identification_code VARCHAR(100) UNIQUE,
    pallet_count INT DEFAULT 0,
    package_count INT DEFAULT 0,
    weight DECIMAL(10,2) DEFAULT 0,
    volume DECIMAL(10,2) DEFAULT 0,
    export_mode VARCHAR(50),
    order_type VARCHAR(50),
    customs_broker VARCHAR(100),
    location VARCHAR(50),
    documents VARCHAR(100),
    service_staff VARCHAR(50),
    batch_no VARCHAR(50),
    batch_total INT DEFAULT 0,
    batch_sequence INT DEFAULT 0,
    inbound_plate VARCHAR(20),
    document_no VARCHAR(100),
    document_count INT,
    remark1 VARCHAR(200) DEFAULT '',
    remark2 VARCHAR(200) DEFAULT '',
    record_type VARCHAR(20) DEFAULT 'direct',
    operated_by_user_id INT,
    operated_warehouse_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version INT DEFAULT 1,
    
    INDEX idx_inbound_time (inbound_time),
    INDEX idx_plate_number (plate_number),
    INDEX idx_customer_name (customer_name),
    INDEX idx_identification_code (identification_code),
    INDEX idx_batch_no (batch_no),
    INDEX idx_operated_warehouse_id (operated_warehouse_id),
    INDEX idx_operated_by_user_id (operated_by_user_id),
    INDEX idx_record_type (record_type),
    INDEX idx_created_at (created_at),
    
    FOREIGN KEY (operated_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (operated_warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建出库记录表
CREATE TABLE IF NOT EXISTS outbound_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outbound_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_plate_number VARCHAR(20),
    plate_number VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    identification_code VARCHAR(100),
    pallet_count INT DEFAULT 0,
    package_count INT DEFAULT 0,
    weight DECIMAL(10,2) DEFAULT 0,
    volume DECIMAL(10,2) DEFAULT 0,
    destination VARCHAR(100),
    destination_warehouse_id INT,
    warehouse_address VARCHAR(255),
    transport_company VARCHAR(100),
    order_type VARCHAR(50),
    service_staff VARCHAR(50),
    receiver_id INT,
    remarks VARCHAR(200) DEFAULT '',
    remark1 VARCHAR(200) DEFAULT '',
    remark2 VARCHAR(200) DEFAULT '',
    documents VARCHAR(100),
    large_layer INT DEFAULT 0,
    small_layer INT DEFAULT 0,
    pallet_board INT DEFAULT 0,
    inbound_plate VARCHAR(20),
    document_no VARCHAR(100),
    document_count INT,
    export_mode VARCHAR(50),
    customs_broker VARCHAR(100),
    location VARCHAR(50),
    batch_no VARCHAR(50),
    batch_total INT DEFAULT 0,
    batch_sequence INT DEFAULT 1,
    vehicle_type VARCHAR(50),
    driver_name VARCHAR(50),
    driver_phone VARCHAR(50),
    arrival_time TIMESTAMP NULL,
    loading_start_time TIMESTAMP NULL,
    loading_end_time TIMESTAMP NULL,
    departure_time TIMESTAMP NULL,
    detailed_address VARCHAR(255),
    contact_window VARCHAR(100),
    inbound_date TIMESTAMP NULL,
    trailer VARCHAR(50),
    container_number VARCHAR(50),
    operated_by_user_id INT,
    operated_warehouse_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version INT DEFAULT 1,
    
    INDEX idx_outbound_time (outbound_time),
    INDEX idx_plate_number (plate_number),
    INDEX idx_customer_name (customer_name),
    INDEX idx_identification_code (identification_code),
    INDEX idx_batch_no (batch_no),
    INDEX idx_destination_warehouse_id (destination_warehouse_id),
    INDEX idx_operated_warehouse_id (operated_warehouse_id),
    INDEX idx_operated_by_user_id (operated_by_user_id),
    INDEX idx_departure_time (departure_time),
    INDEX idx_created_at (created_at),
    
    FOREIGN KEY (operated_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (operated_warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL,
    FOREIGN KEY (destination_warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建库存表
CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100),
    identification_code VARCHAR(100) UNIQUE,
    inbound_pallet_count INT,
    inbound_package_count INT,
    pallet_count INT,
    package_count INT,
    weight DECIMAL(10,2),
    volume DECIMAL(10,2),
    location VARCHAR(50),
    documents VARCHAR(100),
    export_mode VARCHAR(50),
    order_type VARCHAR(50),
    customs_broker VARCHAR(100),
    inbound_time TIMESTAMP NULL,
    plate_number VARCHAR(20),
    service_staff VARCHAR(50),
    original_identification_code VARCHAR(100),
    operated_by_user_id INT,
    operated_warehouse_id INT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version INT DEFAULT 1,
    
    INDEX idx_customer_name (customer_name),
    INDEX idx_identification_code (identification_code),
    INDEX idx_operated_warehouse_id (operated_warehouse_id),
    INDEX idx_operated_by_user_id (operated_by_user_id),
    INDEX idx_inbound_time (inbound_time),
    INDEX idx_last_updated (last_updated),
    
    FOREIGN KEY (operated_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (operated_warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建收货人信息表
CREATE TABLE IF NOT EXISTS receivers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_name VARCHAR(100) NOT NULL UNIQUE,
    address VARCHAR(255) NOT NULL,
    contact VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_warehouse_name (warehouse_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入收货人信息
INSERT IGNORE INTO receivers (warehouse_name, address, contact) VALUES
('平湖仓', '广东省深圳市平湖物流园区A区', '张经理 13800138001'),
('昆山仓', '江苏省苏州市昆山经济开发区B区', '李经理 13800138002'),
('成都仓', '四川省成都市双流区物流中心C区', '王经理 13800138003'),
('凭祥北投仓', '广西壮族自治区崇左市凭祥市北投物流园', '赵经理 13800138004');

-- 创建性能优化视图
CREATE OR REPLACE VIEW v_inventory_summary AS
SELECT 
    operated_warehouse_id,
    COUNT(*) as total_items,
    SUM(pallet_count) as total_pallets,
    SUM(package_count) as total_packages,
    SUM(weight) as total_weight,
    SUM(volume) as total_volume
FROM inventory 
WHERE pallet_count > 0 OR package_count > 0
GROUP BY operated_warehouse_id;

-- 创建出入库统计视图
CREATE OR REPLACE VIEW v_daily_operations AS
SELECT 
    DATE(created_at) as operation_date,
    operated_warehouse_id,
    'inbound' as operation_type,
    COUNT(*) as record_count,
    SUM(pallet_count) as total_pallets,
    SUM(package_count) as total_packages
FROM inbound_records 
WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(created_at), operated_warehouse_id

UNION ALL

SELECT 
    DATE(created_at) as operation_date,
    operated_warehouse_id,
    'outbound' as operation_type,
    COUNT(*) as record_count,
    SUM(pallet_count) as total_pallets,
    SUM(package_count) as total_packages
FROM outbound_records 
WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(created_at), operated_warehouse_id;

-- 显示创建结果
SELECT 'Database warehouse_production initialized successfully!' as Result;
SHOW TABLES;

-- 显示索引信息
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'warehouse_production'
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
