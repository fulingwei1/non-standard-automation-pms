-- PROD-16: 发货单明细与发货门禁支撑表

CREATE TABLE IF NOT EXISTS delivery_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_order_id INTEGER NOT NULL,
    sales_order_item_id INTEGER,
    material_id INTEGER,
    item_name VARCHAR(200) NOT NULL,
    item_spec VARCHAR(200),
    delivery_qty NUMERIC(10, 2) NOT NULL,
    unit VARCHAR(20),
    unit_price NUMERIC(12, 2),
    amount NUMERIC(12, 2),
    quality_status VARCHAR(20) DEFAULT 'pending',
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (delivery_order_id) REFERENCES delivery_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (sales_order_item_id) REFERENCES sales_order_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE INDEX IF NOT EXISTS idx_delivery_order_item_order
    ON delivery_order_items(delivery_order_id);

CREATE INDEX IF NOT EXISTS idx_delivery_order_item_sales_item
    ON delivery_order_items(sales_order_item_id);

CREATE INDEX IF NOT EXISTS idx_delivery_order_item_material
    ON delivery_order_items(material_id);
