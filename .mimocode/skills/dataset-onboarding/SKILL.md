---
name: dataset-onboarding
description: End-to-end pipeline for onboarding a new CSV dataset into PostgreSQL — chains data-dictionary, csv-to-postgres, and pg-backup-restore skills, then updates Agent-Instructions.md.
---

# Dataset Onboarding Pipeline

## When to use

User asks to load a new dataset end-to-end: create data dictionary, create schema/table, load CSV, validate, document, and backup. This orchestrates the `data-dictionary`, `csv-to-postgres`, and `pg-backup-restore` skills.

**Trigger phrases**: "load this CSV", "create a table from", "onboard this dataset", "create data dictionary and load"

## Inputs

| Parameter | Source | Example |
|-----------|--------|---------|
| CSV path | User `@` reference | `Bases-de-Dados/Censo/data.csv` |
| Official dictionary path | User `@` reference or auto-discover | `Censo/dicionario.md` |
| Schema name | Infer from dataset theme | `censo`, `dnit`, `datatran` |
| Table name | Infer from CSV filename | `agregados_por_setores_basico_br` |

## Pipeline (6 steps)

### Step 1: Inspect CSV + locate official dictionary

```bash
# Detect delimiter, encoding, BOM, column count
head -2 FILE.csv | cat -v | head -1
file FILE.csv
head -1 FILE.csv | tr ';' '\n' | wc -l

# Count data rows
wc -l FILE.csv
```

Auto-discover dictionary if not specified:
```bash
find Bases-de-Dados/THEME/ -name "*dicionario*" -o -name "*dictionary*" | head -5
```

### Step 2: Create data dictionary

Delegate to `data-dictionary` skill:
- Read CSV header
- Match columns against official dictionary
- Group variables by theme
- Write `Bases-de-Dados/THEME/dicionario_DATASET.md`

### Step 3: Create schema + table + load data

Delegate to `csv-to-postgres` skill:
- Ensure PostgreSQL is running (`pg_isready`)
- Create schema: `CREATE SCHEMA IF NOT EXISTS <schema>;`
- Load via Python TEXT staging:
  1. Create table with all TEXT columns
  2. COPY data (handle `-` → NULL, `"X"` → NULL, `,` → `.` decimal)
  3. ALTER TABLE to convert types
  4. Add PRIMARY KEY and indices

**Column naming rules** (from project conventions):
- `NM_*` → `VARCHAR(100)` (Brazilian names can exceed 60 chars)
- `CD_*` → `VARCHAR(10)` or `BIGINT`
- Unpredictable text → `TEXT`
- Counts → `BIGINT`
- Decimals → `DECIMAL(precision,scale)`
- All names **lowercase** (PostgreSQL lowercases unquoted identifiers)

### Step 4: Validate

```sql
-- Total records
SELECT COUNT(*) FROM schema.table;

-- Distribution by key categorical column
SELECT category_col, COUNT(*) FROM schema.table GROUP BY category_col ORDER BY count DESC;

-- Sample with data
SELECT * FROM schema.table WHERE volume_col IS NOT NULL LIMIT 5;

-- Column types verification
SELECT column_name, data_type FROM information_schema.columns
WHERE table_schema = 'schema' AND table_name = 'table'
ORDER BY ordinal_position;
```

### Step 5: Update Agent-Instructions.md

Add a new section at the end of `Bases-de-Dados/Agent-Instructions.md` following this template:

```markdown
## [Source] — [Dataset Name]

### Visão Geral

[1-2 sentence description of the dataset]

- **Arquivo fonte**: `[path]`
- **Dicionário de dados**: `[path]`
- **Schema**: `[schema]`
- **Tabela**: `[schema].[table]`

### Estrutura do Arquivo CSV

| Propriedade | Valor |
|-------------|-------|
| Delimitador | `;` |
| Codificação | ISO-8859-1 |
| Separador decimal | `,` |
| Cabeçalho | Sim |
| Total de registros | ~N |
| Total de colunas | N |

### Colunas

| Coluna | Tipo SQL | Descrição |
|--------|----------|-----------|
| ... | ... | ... |

### Criação da Tabela

```sql
CREATE SCHEMA IF NOT EXISTS [schema];
-- Table DDL or Python loading approach
```

### Carregamento dos Dados (Python)

```python
# Python loading script snippet
```

### Validação

```sql
-- Validation queries
```

### Consultas Úteis

```sql
-- Example analytical queries
```

### Backup e Restore

```bash
# Schema backup
pg_dump -U postgres -n [schema] public | gzip > /workspaces/ChatFGV/Bases-de-Dados/BACKUP/[schema]_$(date +%Y%m%d_%H%M%S).sql.gz
```
```

### Step 6: Backup

```bash
# Full database backup
mkdir -p /workspaces/ChatFGV/Bases-de-Dados/BACKUP
pg_dump -U postgres public | gzip > /workspaces/ChatFGV/Bases-de-Dados/BACKUP/public_$(date +%Y%m%d_%H%M%S).sql.gz

# Verify
ls -lh /workspaces/ChatFGV/Bases-de-Dados/BACKUP/public_*.sql.gz | tail -1
```

## Checklist

Before marking the pipeline complete, verify:

- [ ] Data dictionary `.md` covers all CSV columns
- [ ] Schema created in PostgreSQL
- [ ] Table has correct types (not all TEXT)
- [ ] Primary key set
- [ ] Indices on frequent query columns (UF, date, municipality)
- [ ] `SELECT COUNT(*)` matches expected row count
- [ ] Sample query returns valid data
- [ ] Agent-Instructions.md updated with new section
- [ ] Backup file exists and has reasonable size

## Common issues

- **`Peer authentication failed`**: Use `pg_dump -U postgres` (not `sudo -U postgres`). The `-U` flag is for PostgreSQL user, not sudo user.
- **Column name with special characters**: `classificação` → `classificacao` (strip accents for SQL safety)
- **Duplicate column names after normalization**: Append `_2` suffix
- **`-` values in numeric columns**: Convert to NULL before COPY
- **Comma decimal separator**: Replace `,` with `.` for NUMERIC columns before COPY

## Sub-skills referenced

| Skill | Step |
|-------|------|
| `data-dictionary` | Step 2 |
| `csv-to-postgres` | Step 3 |
| `pg-backup-restore` | Step 6 |
