-- 知识库文档上传功能 - 添加文件字段
-- 日期: 2026-01-13
-- 描述: 为 knowledge_base 表添加文件上传支持

-- 添加文件相关字段
ALTER TABLE knowledge_base ADD COLUMN file_path VARCHAR(500);      -- 文件路径
ALTER TABLE knowledge_base ADD COLUMN file_name VARCHAR(200);      -- 原始文件名
ALTER TABLE knowledge_base ADD COLUMN file_size INTEGER;           -- 文件大小（字节）
ALTER TABLE knowledge_base ADD COLUMN file_type VARCHAR(100);      -- 文件MIME类型

-- 添加下载计数和下载权限字段
ALTER TABLE knowledge_base ADD COLUMN download_count INTEGER DEFAULT 0;  -- 下载次数
ALTER TABLE knowledge_base ADD COLUMN allow_download BOOLEAN DEFAULT 1;  -- 是否允许他人下载

-- 添加采用计数字段（表示文档被实际应用到工作中）
ALTER TABLE knowledge_base ADD COLUMN adopt_count INTEGER DEFAULT 0;     -- 采用次数

-- 修改 content 字段为可空（因为上传文件时内容可以为空）
-- SQLite 不支持直接修改列，所以这里只是注释说明
-- 如果需要，可以通过重建表的方式来修改

-- 注意：运行此脚本后，需要确保 uploads/knowledge_base 目录存在
