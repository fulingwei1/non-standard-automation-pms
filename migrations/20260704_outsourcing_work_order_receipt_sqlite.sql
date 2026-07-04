-- PROD-19: 外协订单关联生产工单，支撑交付/收货闭环

ALTER TABLE outsourcing_orders ADD COLUMN work_order_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_os_order_work_order
    ON outsourcing_orders(work_order_id);
