-- 前端仓出库记录性能优化索引
-- 执行前请备份数据库

-- 1. 出库记录表的复合索引
-- 用于前端仓出库记录列表查询优化
CREATE INDEX IF NOT EXISTS idx_outbound_warehouse_time 
ON outbound_record (operated_warehouse_id, outbound_time DESC);

-- 用于批次号查询优化
CREATE INDEX IF NOT EXISTS idx_outbound_batch_time 
ON outbound_record (batch_no, outbound_time DESC);

-- 用于搜索字段优化
CREATE INDEX IF NOT EXISTS idx_outbound_customer_name 
ON outbound_record (customer_name);

CREATE INDEX IF NOT EXISTS idx_outbound_plate_number 
ON outbound_record (plate_number);

CREATE INDEX IF NOT EXISTS idx_outbound_identification_code 
ON outbound_record (identification_code);

CREATE INDEX IF NOT EXISTS idx_outbound_destination 
ON outbound_record (destination);

CREATE INDEX IF NOT EXISTS idx_outbound_customs_broker 
ON outbound_record (customs_broker);

-- 2. 入库记录表的索引优化
CREATE INDEX IF NOT EXISTS idx_inbound_identification_code 
ON inbound_record (identification_code);

-- 3. 接收记录表的索引优化
CREATE INDEX IF NOT EXISTS idx_receive_batch_no 
ON receive_record (batch_no);

CREATE INDEX IF NOT EXISTS idx_receive_identification_code 
ON receive_record (identification_code);

-- 4. 仓库表的索引优化
CREATE INDEX IF NOT EXISTS idx_warehouse_type 
ON warehouse (warehouse_type);

-- 查看索引创建结果
SHOW INDEX FROM outbound_record;
SHOW INDEX FROM inbound_record;
SHOW INDEX FROM receive_record;
SHOW INDEX FROM warehouse;
