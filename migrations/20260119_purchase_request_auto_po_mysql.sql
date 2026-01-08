-- 采购申请自动下单能力增强（MySQL）

ALTER TABLE `purchase_requests`
    ADD COLUMN `supplier_id` INT NULL COMMENT '供应商ID' AFTER `machine_id`,
    ADD COLUMN `source_type` VARCHAR(20) DEFAULT 'MANUAL' COMMENT '来源类型(BOM/SHORTAGE/MANUAL)' AFTER `supplier_id`,
    ADD COLUMN `source_id` INT NULL COMMENT '来源业务ID' AFTER `source_type`,
    ADD COLUMN `auto_po_created` TINYINT(1) DEFAULT 0 COMMENT '是否已自动生成采购订单' AFTER `status`,
    ADD COLUMN `auto_po_created_at` DATETIME NULL COMMENT '自动下单时间' AFTER `auto_po_created`,
    ADD COLUMN `auto_po_created_by` INT NULL COMMENT '自动下单人' AFTER `auto_po_created_at`;

ALTER TABLE `purchase_orders`
    ADD COLUMN `source_request_id` INT NULL COMMENT '来源采购申请ID' AFTER `project_id`;

CREATE INDEX `idx_purchase_requests_supplier` ON `purchase_requests`(`supplier_id`);
CREATE INDEX `idx_purchase_requests_source` ON `purchase_requests`(`source_type`);
CREATE INDEX `idx_purchase_orders_source_request` ON `purchase_orders`(`source_request_id`);
