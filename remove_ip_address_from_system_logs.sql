-- Remove the unused ip_address column from the system_logs table
ALTER TABLE system_logs DROP COLUMN ip_address;