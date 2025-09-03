-- CREATE TABLE IF NOT EXISTS patients (
--     id INT PRIMARY KEY,
--     name TEXT,
--     age INT,
--     condition TEXT
-- );

-- postgres/init.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS patients (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  age INT CHECK (age BETWEEN 0 AND 120),
  condition TEXT
);

CREATE TABLE IF NOT EXISTS lab_results (
  id UUID PRIMARY KEY,
  patient_id UUID REFERENCES patients(id),
  test_code TEXT,
  test_name TEXT,
  value NUMERIC,
  unit TEXT,
  result_time TIMESTAMPTZ,
);

CREATE TABLE IF NOT EXISTS medications (
  id UUID PRIMARY KEY,
  patient_id UUID REFERENCES patients(id),
  drug_code TEXT,
  drug_name TEXT,
  dose TEXT,
  route TEXT,
  start_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ,
  ingested_at TIMESTAMPTZ DEFAULT now()
);
