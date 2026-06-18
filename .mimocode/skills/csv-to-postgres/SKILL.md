---
name: csv-to-postgres
description: Load a Brazilian CSV file into PostgreSQL — handles BOM, delimiter detection, "X" suppressed values, float conversion, VARCHAR sizing, and Codespaces trust auth.
---

# CSV → PostgreSQL Loader (Brazilian Data)

## When to use

User asks to load a CSV file into a PostgreSQL table, especially when the CSV uses Brazilian conventions (semicolon or comma delimiters, ISO-8859-1 or UTF-8-BOM encoding).

## Workflow

### Step 1: Inspect the CSV — detect delimiter, encoding, BOM

```bash
# Check for BOM and encoding
head -2 FILE.csv | cat -v | head -1
# "M-oM-;M-?" at start → UTF-8 BOM present
# If BOM, use encoding='utf-8-sig' in pandas

# Detect delimiter: look at first 2 data lines
head -2 FILE.csv | cat -v | head -2
# Commas between fields → delimiter=','
# Semicolons between fields → delimiter=';'

# Count columns (adjust delimiter)
head -1 FILE.csv | tr ',' '\n' | wc -l   # for comma-delimited
head -1 FILE.csv | tr ';' '\n' | wc -l   # for semicolon-delimited

# Confirm encoding
file FILE.csv
```

**Do NOT assume** the delimiter based on other files in the project. Each CSV must be checked independently. Common patterns:
- Most IBGE census files: `;` delimiter, ISO-8859-1, comma decimal separator
- Some census exports: `,` delimiter, UTF-8-BOM, dot decimal separator
- Traffic accident data (PRF): `;` delimiter, ISO-8859-1

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

### Step 3: Create schema and table — naming and type rules

Use the project's `Agent-Instructions.md` or data dictionary to define the table. Key rules:

- **Schema name**: match the dataset theme (e.g., `datatran`, `censo`)
- **Table name**: descriptive, **lowercase with underscores** (PostgreSQL lowercases unquoted identifiers; `BR_setores_CD2022` → `br_setores_cd2022`)
- **Name columns (`NM_*`)**: use `VARCHAR(100)` — Brazilian municipality names can exceed 60 chars
- **Code columns (`CD_*`)**: use `VARCHAR(10)` or `BIGINT` depending on data
- **Unpredictable text columns**: use `TEXT` (e.g., `CD_FCU`)
- **Counts**: `BIGINT` for large populations
- **Decimals**: `DECIMAL(precision,scale)` for averages/percentages
- Add indices on frequently-queried columns (uf, date, municipality)

### Step 4: Load data — TEXT staging approach (recommended)

The safest approach for Brazilian CSVs with mixed types, `"X"` suppressed values, and decimal separators:

**Phase 1: Create TEXT table + COPY**

```python
import pandas as pd
import psycopg2
from io import StringIO

CSV_PATH = 'path/to/file.csv'

# Adjust sep and encoding based on Step 1 inspection
df = pd.read_csv(CSV_PATH, sep=',', encoding='utf-8-sig', dtype=str)

# Handle special values
df = df.replace('.', None)  # "." = missing in some census files
df = df.replace('X', None)  # "X" = suppressed by IBGE

# Fix decimal separator if needed (comma → dot)
for col in df.columns:
    if col.startswith('v') or col == 'AREA_KM2':
        df[col] = df[col].str.replace(',', '.', regex=False)

conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='public', user='postgres')
cur = conn.cursor()

# Create table with ALL columns as TEXT
cur.execute("""CREATE TABLE schema.table_name (
    col1 TEXT, col2 TEXT, col3 TEXT, ...
);""")
conn.commit()

# COPY via buffer
buffer = StringIO()
df.to_csv(buffer, sep='\t', index=False, header=False, na_rep='\\N')
buffer.seek(0)
columns = list(df.columns)
col_list = ', '.join(columns)
copy_sql = f"COPY schema.table_name ({col_list}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '\\N')"
cur.copy_expert(copy_sql, buffer)
conn.commit()
```

**Phase 2: Convert types via ALTER TABLE**

```python
# Convert each column to its final type
alter_cmds = [
    "ALTER TABLE schema.table_name ALTER COLUMN col1 TYPE VARCHAR(15);",
    "ALTER TABLE schema.table_name ALTER COLUMN col2 TYPE INTEGER USING col2::INTEGER;",
    "ALTER TABLE schema.table_name ALTER COLUMN col3 TYPE DECIMAL(12,7) USING col3::DECIMAL(12,7);",
    # ... one per column
]
for cmd in alter_cmds:
    try:
        cur.execute(cmd)
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()

# Add primary key and indices
cur.execute("ALTER TABLE schema.table_name ADD PRIMARY KEY (col1);")
cur.execute("CREATE INDEX idx_table_col2 ON schema.table_name (col2);")
conn.commit()
```

**Why TEXT staging instead of direct typed COPY?**
- Avoids `InvalidTextRepresentation` from float ".0" on integer columns
- Avoids `StringDataRightTruncation` from undersized VARCHAR
- Handles `"X"`, `"."`, empty strings gracefully
- ALTER TABLE per-column is fine for <50 columns; for 100+ columns, use Python pandas conversion in memory instead

### Step 5: Validate

```sql
SELECT COUNT(*) FROM schema.table_name;
SELECT * FROM schema.table_name LIMIT 5;
-- Check distribution
SELECT col_category, COUNT(*) FROM schema.table_name GROUP BY col_category;
```

### Step 6: Update instruction file

If `Bases-de-Dados/Agent-Instructions.md` exists, add a new section documenting the table creation, data dictionary reference, and loading steps.

## Error Reference

### BOM (Byte Order Mark) — single column read

**Symptom:** pandas reads CSV as 1 column: `Shape: (N, 1)`
**Cause:** UTF-8 BOM (`ï»¿`) not stripped; `ISO-8859-1` doesn't handle BOM
**Fix:** Use `encoding='utf-8-sig'`
**Diagnosis:** `head -1 file.csv | cat -v` — look for `M-oM-;M-?`

### Float adds ".0" to integers

**Symptom:** `invalid input syntax for type bigint: "1100015006.0"`
**Cause:** `pd.to_numeric()` with NaN uses float64; `to_csv()` outputs `.0` suffix
**Fix:** Use TEXT staging + ALTER TABLE instead of pandas numeric conversion

### VARCHAR too small

**Symptom:** `value too long for type character varying(60)`
**Cause:** Brazilian municipality names can be 70+ characters
**Fix:** Use `VARCHAR(100)` for `NM_*` columns, `TEXT` for unpredictable data

### PostgreSQL lowercases identifiers

**Symptom:** `relation "schema.TableName" does not exist`
**Cause:** PostgreSQL converts unquoted identifiers to lowercase
**Fix:** Use lowercase table/column names from the start

## Known issues in this project

- **pg_hba.conf**: Codespaces container uses `scram-sha-256` by default; need `trust` for local connections
- **"X" values**: Census data uses `"X"` for suppressed data — must convert to NULL during load
- **"." values**: Some census geographic columns use `"."` for inapplicable hierarchy levels
- **Encoding varies**: Some files ISO-8859-1, some UTF-8-BOM — always check with `cat -v`
- **Delimiter varies**: Most use `;`, some use `,` — always verify before loading
- **Decimal separator varies**: Some use `,` (European), some use `.` — check and convert if needed
- **Column count**: Census files can have 300+ columns — Python approach preferred over ALTER TABLE
