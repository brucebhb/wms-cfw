-- 修复分批出货的数据库约束问题
-- 识别编码保持唯一不变，通过batch_sequence实现分批出货

-- 1. 检查当前约束
SELECT 
    CONSTRAINT_NAME,
    COLUMN_NAME,
    CONSTRAINT_TYPE
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_NAME = 'outbound_record' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'identification_code';

-- 2. 显示当前重复的识别编码
SELECT 
    identification_code,
    COUNT(*) as record_count,
    GROUP_CONCAT(id ORDER BY created_at) as record_ids,
    GROUP_CONCAT(batch_sequence ORDER BY created_at) as batch_sequences
FROM outbound_record 
WHERE identification_code IS NOT NULL
GROUP BY identification_code 
HAVING COUNT(*) > 1
ORDER BY record_count DESC
LIMIT 10;

-- 3. 修复batch_sequence（确保同一识别编码的记录有正确的批次序号）
SET @row_number = 0;
SET @prev_code = '';

UPDATE outbound_record o1
JOIN (
    SELECT 
        id,
        identification_code,
        @row_number := CASE 
            WHEN @prev_code = identification_code THEN @row_number + 1
            ELSE 1
        END AS new_batch_sequence,
        @prev_code := identification_code
    FROM outbound_record 
    WHERE identification_code IS NOT NULL
    ORDER BY identification_code, created_at
) o2 ON o1.id = o2.id
SET o1.batch_sequence = o2.new_batch_sequence;

-- 4. 删除错误的唯一约束（如果存在）
-- 注意：约束名称可能不同，需要根据实际情况调整
SET @constraint_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_NAME = 'outbound_record' 
        AND TABLE_SCHEMA = DATABASE()
        AND COLUMN_NAME = 'identification_code'
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

-- 5. 创建正确的复合唯一约束（可选，如果需要严格控制）
-- ALTER TABLE outbound_record 
-- ADD CONSTRAINT uk_outbound_identification_batch 
-- UNIQUE (identification_code, batch_sequence);

-- 6. 验证修复结果
SELECT '=== 修复后验证 ===' as status;

-- 检查是否还有重复的 (identification_code, batch_sequence) 组合
SELECT 
    identification_code,
    batch_sequence,
    COUNT(*) as count
FROM outbound_record 
GROUP BY identification_code, batch_sequence
HAVING COUNT(*) > 1;

-- 显示分批出货的示例
SELECT 
    identification_code,
    batch_sequence,
    outbound_time,
    pallet_count,
    package_count,
    created_at
FROM outbound_record 
WHERE identification_code IN (
    SELECT identification_code 
    FROM outbound_record 
    GROUP BY identification_code 
    HAVING COUNT(*) > 1 
    LIMIT 3
)
ORDER BY identification_code, batch_sequence;
