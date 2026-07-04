-- AS-10/AS-11: device archive and after-sales machine linkage.

ALTER TABLE machines ADD COLUMN customer_id INTEGER REFERENCES customers(id);
ALTER TABLE machines ADD COLUMN serial_no VARCHAR(100);
ALTER TABLE machines ADD COLUMN warranty VARCHAR(100);

ALTER TABLE service_tickets ADD COLUMN machine_id INTEGER REFERENCES machines(id);
ALTER TABLE service_records ADD COLUMN machine_id INTEGER REFERENCES machines(id);

CREATE INDEX IF NOT EXISTS idx_machines_customer ON machines(customer_id);
CREATE INDEX IF NOT EXISTS idx_machines_serial_no ON machines(serial_no);
CREATE INDEX IF NOT EXISTS idx_service_ticket_machine ON service_tickets(machine_id);
CREATE INDEX IF NOT EXISTS idx_service_record_machine ON service_records(machine_id);
