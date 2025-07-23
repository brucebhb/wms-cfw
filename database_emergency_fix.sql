-- 紧急修复数据库约束和字段问题
-- 执行前请备份数据库！

-- 1. 检查当前约束
SELECT 
    CONSTRAINT_NAME,
    COLUMN_NAME,
    CONSTRAINT_TYPE
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_NAME = 'outbound_record' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'identification_code';

-- 2. 删除错误的唯一约束（如果存在）
SET @constraint_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_NAME = 'outbound_record' 
        AND TABLE_SCHEMA = DATABASE()
        AND COLUMN_NAME = 'identification_code'
        AND CONSTRAINT_NAME LIKE '%identification%'
        AND CONSTRAINT_NAME != 'PRIMARY'
    LIMIT 1
);

SET @sql = CASE 
    WHEN @constraint_name IS NOT NULL THEN 
        CONCAT('ALTER TABLE outbound_record DROP INDEX ', @constraint_name)
    ELSE 
        'SELECT "没有找到需要删除的约束" as message'
END;

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. 修复batch_sequence，确保同一识别编码的记录有正确的批次序号
UPDATE outbound_record o1
JOIN (
    SELECT 
        id,
        identification_code,
        ROW_NUMBER() OVER (PARTITION BY identification_code ORDER BY created_at) AS new_batch_sequence
    FROM outbound_record 
    WHERE identification_code IS NOT NULL
) o2 ON o1.id = o2.id
SET o1.batch_sequence = o2.new_batch_sequence;

-- 4. 创建正确的复合唯一约束（可选）
-- ALTER TABLE outbound_record 
-- ADD CONSTRAINT uk_outbound_identification_batch 
-- UNIQUE (identification_code, batch_sequence);

-- 5. 检查inventory表是否缺少inventory_type字段
SELECT COUNT(*) as has_inventory_type
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'inventory' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'inventory_type';

-- 6. 如果缺少inventory_type字段，添加它
-- ALTER TABLE inventory ADD COLUMN inventory_type VARCHAR(20) DEFAULT 'normal' COMMENT '库存类型';

-- 7. 验证修复结果
SELECT '=== 修复验证 ===' as status;

-- 检查重复的识别编码
SELECT 
    identification_code,
    COUNT(*) as count,
    GROUP_CONCAT(batch_sequence ORDER BY batch_sequence) as batch_sequences
FROM outbound_record 
WHERE identification_code IS NOT NULL
GROUP BY identification_code 
HAVING COUNT(*) > 1
LIMIT 5;

-- 检查是否还有重复的 (identification_code, batch_sequence) 组合
SELECT 
    identification_code,
    batch_sequence,
    COUNT(*) as count
FROM outbound_record 
GROUP BY identification_code, batch_sequence
HAVING COUNT(*) > 1;
