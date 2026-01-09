-- 添加身份证号字段到员工表
-- 用于生成初始密码（姓名拼音 + 身份证后4位）

-- 添加身份证号字段
ALTER TABLE employees ADD COLUMN id_card VARCHAR(18);

-- 确保 pinyin_name 字段存在（如果之前的迁移未执行）
-- SQLite 不支持 IF NOT EXISTS 语法用于 ALTER TABLE，所以这里可能会报错
-- 如果已存在则忽略错误
-- ALTER TABLE employees ADD COLUMN pinyin_name VARCHAR(100);
