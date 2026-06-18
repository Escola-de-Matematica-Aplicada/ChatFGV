---
name: data-dictionary
description: Create a data dictionary for a CSV file by matching columns against official documentation — produces organized markdown with variable descriptions, types, and notes.
---

# Data Dictionary Creator (CSV + Official Docs)

## When to use

User asks to create a data dictionary for a CSV file, especially when an official documentation/dictionary file exists in the project.

## Workflow

### Step 1: Read the CSV header

```bash
head -1 FILE.csv | tr ';' '\n'
```

Identify all column names and their naming pattern (e.g., `V00644`–`V01005` for IBGE census variables).

### Step 2: Locate the official dictionary

Search the project for documentation files:

```bash
# Look for dictionary/docs files
find . -name "*dicionario*" -o -name "*dictionary*" -o -name "*data-dict*" | head -10
```

If the user specifies a file path with `@`, read it. If the file doesn't exist, use glob to find a similar file in the same directory.

### Step 3: Match CSV columns to official descriptions

For each CSV column, find its description in the official dictionary. Common patterns:

- **IBGE Census variables**: V-prefixed 5-digit codes (e.g., `V00644`). Search the dictionary for the exact variable code.
- **Column ranges**: If columns follow a sequential pattern (V00644–V01005), read the dictionary in that range and note the grouping logic.

Use `grep` to find the relevant section:

```bash
grep -n "V00644\|V00645\|V00646" path/to/dictionary.md
```

### Step 4: Organize into logical groups

Don't dump 300+ rows in one flat list. Group by sub-theme:

- Group by demographic dimension (age, sex, race/ethnicity)
- Group by status (total population, literate, illiterate)
- Group by cross-tabulation pattern

### Step 5: Write the dictionary file

Create a markdown file with:

1. **Header**: File name, source, encoding, delimiter, column count, theme
2. **Identifier column**: The primary key / row identifier
3. **Variable groups**: Each group as a section with a table
4. **Notes**: How to compute derived metrics (rates, percentages), special values ("X" = suppressed), data caveats

Structure:

```markdown
# Dicionário de Dados — [Dataset Name]

**Arquivo**: `filename.csv`
**Fonte**: [Official source]
**Delimitador**: `;`
**Codificação**: ISO-8859-1
**Total de colunas**: N

---

## Identificador
| Coluna | Tipo | Descrição |
|--------|------|-----------|

## Grupo 1: [Theme] (VARIABLES)
| Variável | Descrição |
|----------|-----------|
```

### Step 6: Validate

Check that:
- Every CSV column has a corresponding entry in the dictionary
- Variable ranges are continuous (no gaps)
- Group counts add up to total column count minus identifier
- Portuguese descriptions match the official source exactly

## Known patterns in this project

- **IBGE Census dictionaries**: Large files (1000+ lines), pipe-delimited markdown tables with columns: `Tipo | Tema | Variável | Descrição`
- **Variable naming**: Sequential V-prefixed codes, grouped by theme (Domicílio, Pessoas, Alfabetização, Demografia, Parentesco)
- **Suppressed values**: `"X"` in CSV = data withheld by IBGE for privacy (small sample sizes)
- **Alfabetização variables** (V00644–V01005): 12 sub-groups covering age × race/ethnicity × sex × literacy status
- **Output location**: `Bases-de-Dados/[Theme]/dicionario_[dataset].md`
