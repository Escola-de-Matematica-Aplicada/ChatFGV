---
name: csv-to-postgres
description: Load a Brazilian CSV file into PostgreSQL — handles semicolon delimiters, ISO-8859-1 encoding, "X" suppressed values, and Codespaces trust auth setup.
---

# CSV → PostgreSQL Loader (Brazilian Data)

## When to use

User asks to load a CSV file into a PostgreSQL table, especially when the CSV uses Brazilian conventions (semicolon delimiters, ISO-8859-1 encoding).

## Workflow

### Step 1: Inspect the CSV

```bash
# Count columns
head -1 FILE.csv | tr ';' '\n' | wc -l

# Check delimiter and encoding
file FILE.csv
head -3 FILE.csv | cat -v | head -1
```

Confirm: semicolon-delimited (`;`), encoding ISO-8859-1, header row present.

### Step 2: Check PostgreSQL availability

```bash
sudo service postgresql start 2>/dev/null
pg_isready -h localhost -p 5432 -U postgres
```

If connection fails with password error, update pg_hba.conf for trust auth:

```bash
sudo sed -i 's/scram-sha-256/trust/g' /etc/postgresql/16/main/pg_hba.conf
sudo service postgresql reload
```

Or use the `.devcontainer/pg_hba.conf` approach (mount trust config).

### Step 3: Create schema and table

Use the project's `Agent-Instructions.md` or data dictionary to define the table. Key rules:

- Schema name: match the dataset theme (e.g., `datatran`, `censo`)
- Table name: descriptive, lowercase with underscores
- Use `INTEGER` for counts, `VARCHAR` for text, `DATE`/`TIME` for temporal fields
- Add indices on frequently-queried columns (uf, date, municipality)

### Step 4: Load data — handle "X" suppressed values

**Brazilian census/survey data** often uses `"X"` for suppressed values (privacy). PostgreSQL `COPY` fails if column is INTEGER and value is `"X"`.

**Solution — two-phase load:**

1. Create table with all columns as `TEXT`
2. `COPY` the CSV (TEXT accepts "X")
3. Convert columns to `INTEGER` with `CASE WHEN col = 'X' THEN NULL ELSE col::INTEGER END`

```sql
-- Phase 1: TEXT table + COPY
CREATE TABLE schema.table_name (col1 VARCHAR(50), col2 TEXT, col3 TEXT, ...);
COPY schema.table_name FROM '/path/to/file.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ';', ENCODING 'ISO-8859-1');

-- Phase 2: Convert to INTEGER (can be slow for 300+ columns — consider Python alternative)
ALTER TABLE schema.table_name ALTER COLUMN col2 TYPE INTEGER USING CASE WHEN col2 = 'X' THEN NULL ELSE col2::INTEGER END;
```

**For large column counts (100+)**, use Python instead of ALTER TABLE:

```python
import pandas as pd
import psycopg2

df = pd.read_csv('file.csv', sep=';', encoding='ISO-8859-1', dtype=str)
df = df.replace('X', None)
for col in df.columns:
    if col != 'ID_COL':
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='public', user='postgres')
# ... create table and use COPY with StringIO buffer
```

### Step 5: Validate

```sql
SELECT COUNT(*) FROM schema.table_name;
SELECT * FROM schema.table_name LIMIT 5;
-- Check for unexpected NULLs or X values
SELECT COUNT(*) FROM schema.table_name WHERE col = 'X';  -- should be 0 after conversion
```

### Step 6: Update instruction file

If `Bases-de-Dados/Agent-Instructions.md` exists, add a new section documenting the table creation, data dictionary reference, and loading steps.

## Known issues in this project

- **pg_hba.conf**: Codespaces container uses `scram-sha-256` by default; need `trust` for local connections
- **"X" values**: Census data uses `"X"` for suppressed data — must convert to NULL during load
- **Encoding**: Always specify `ENCODING 'ISO-8859-1'` in COPY for Brazilian data
- **Delimiter**: Always `DELIMITER ';'` for Brazilian CSVs
- **Column count**: Census files can have 300+ columns — Python approach preferred over ALTER TABLE
- **Python psycopg2 trust**: If connecting via TCP (127.0.0.1), pg_hba.conf must have `trust` for that host
