-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Charset (default but explicit)
ALTER DATABASE ozon_bot SET client_encoding TO 'UTF8';
