-- 数据库字段修复脚本
-- 执行前请备份数据库！

-- 1. 检查并添加缺失的字段
-- 检查inventory表是否缺少inventory_type字段
SELECT COUNT(*) as has_inventory_type
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'inventory' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'inventory_type';

-- 如果缺少inventory_type字段，添加它
-- ALTER TABLE inventory ADD COLUMN inventory_type VARCHAR(20) DEFAULT 'normal' COMMENT '库存类型';

-- 2. 检查outbound_record表的字段
-- 确保export_mode字段存在（而不是exit_mode）
SELECT COUNT(*) as has_export_mode
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'outbound_record' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'export_mode';

-- 3. 检查warehouse表的字段
-- 确保warehouse_name字段存在（而不是name）
SELECT COUNT(*) as has_warehouse_name
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'warehouse' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'warehouse_name';

-- 4. 检查user表的字段
-- 确保warehouse_id字段存在（而不是associated_warehouse_id）
SELECT COUNT(*) as has_warehouse_id
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'user' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'warehouse_id';

-- 5. 修复重复的唯一约束问题
-- 检查当前的唯一约束
SELECT 
    CONSTRAINT_NAME,
    COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_NAME = 'outbound_record' 
    AND TABLE_SCHEMA = DATABASE()
    AND CONSTRAINT_NAME LIKE '%identification%';

-- 如果有错误的唯一约束，删除它们
-- DROP INDEX uk_outbound_identification_code ON outbound_record;

-- 创建正确的复合唯一约束（支持分批出货）
-- ALTER TABLE outbound_record 
-- ADD CONSTRAINT uk_outbound_identification_batch 
-- UNIQUE (identification_code, batch_sequence);

-- 6. 验证修复结果
SELECT '=== 数据库字段检查完成 ===' as status;
