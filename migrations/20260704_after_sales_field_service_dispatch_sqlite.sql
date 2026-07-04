-- AS-18: link existing after-sales field service rows to installation dispatch orders.
-- SQLite does not support ADD COLUMN IF NOT EXISTS on all target versions, so
-- check the schema before applying this one-off migration.

ALTER TABLE after_sales_field_services ADD COLUMN dispatch_order_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_asfs_dispatch_order
ON after_sales_field_services(dispatch_order_id);
