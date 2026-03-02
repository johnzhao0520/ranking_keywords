-- 添加 tracking_interval_hours 列（如果不存在）
ALTER TABLE keywords ADD COLUMN IF NOT EXISTS tracking_interval_hours INTEGER DEFAULT 24;
