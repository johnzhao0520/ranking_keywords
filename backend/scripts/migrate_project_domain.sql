-- 迁移脚本：重构项目和关键词表
-- 1. projects 表增加 root_domain 和 subdomain
-- 2. keywords 表移除 target_url

-- Step 1: 为 projects 添加新字段
ALTER TABLE projects ADD COLUMN IF NOT EXISTS root_domain VARCHAR(255) NOT NULL DEFAULT 'example.com';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS subdomain VARCHAR(255);

-- Step 2: 从 keywords 表移除 target_url（如果存在）
-- 注意：先备份数据
-- 暂时不做删除，等前端适配后再处理

-- Step 3: 更新现有数据（如果有项目没有域名，给默认值）
UPDATE projects SET root_domain = 'example.com' WHERE root_domain IS NULL OR root_domain = '';

-- 查看结果
SELECT id, name, root_domain, subdomain FROM projects LIMIT 10;
