-- AS-20: warranty source and out-of-warranty billing fields for field services.
-- SQLite does not support ADD COLUMN IF NOT EXISTS on all target versions, so
-- check the schema before applying this one-off migration.

ALTER TABLE after_sales_field_services ADD COLUMN service_fee NUMERIC(12, 2) DEFAULT 0;
ALTER TABLE after_sales_field_services ADD COLUMN warranty_source VARCHAR(30);
ALTER TABLE after_sales_field_services ADD COLUMN charge_required BOOLEAN DEFAULT 0;
ALTER TABLE after_sales_field_services ADD COLUMN charge_reason VARCHAR(50);
ALTER TABLE after_sales_field_services ADD COLUMN charge_status VARCHAR(20) DEFAULT 'NOT_REQUIRED';
