---
name: pg-backup-restore
description: Backup and restore PostgreSQL databases/schemas in Codespaces — covers pg_dump with gzip, selective schema backup, and restore commands.
---

# PostgreSQL Backup & Restore (Codespaces)

## When to use

User asks to backup, restore, or export a PostgreSQL database or schema. Common after loading large datasets or before schema changes.

## Workflow

### Step 1: Ensure backup directory exists

```bash
mkdir -p /workspaces/ChatFGV/Bases-de-Dados/BACKUP
```

### Step 2: Choose backup scope

| Scope | Command |
|-------|---------|
| Full database | `pg_dump public \| gzip > backup.sql.gz` |
| Single schema | `pg_dump -n censo public \| gzip > backup.sql.gz` |
| Schema data only (no DDL) | `pg_dump -a -n censo public \| gzip > backup.sql.gz` |
| Custom format (selective restore) | `pg_dump -Fc -n censo public > backup.dump` |

### Step 3: Execute backup

```bash
# Full database backup with timestamp
pg_dump -U postgres public | gzip > /workspaces/ChatFGV/Bases-de-Dados/BACKUP/public_$(date +%Y%m%d_%H%M%S).sql.gz

# Single schema backup
pg_dump -U postgres -n censo public | gzip > /workspaces/ChatFGV/Bases-de-Dados/BACKUP/censo_$(date +%Y%m%d_%H%M%S).sql.gz
```

> **Note:** Use `pg_dump -U postgres` (PostgreSQL user flag), NOT `sudo -U postgres` (sudo lists privileges for user, does not run commands).

### Step 4: Verify backup

```bash
ls -lh /workspaces/ChatFGV/Bases-de-Dados/BACKUP/
# Should show file with reasonable size (70-80% smaller than raw SQL)
```

### Step 5: Restore

```bash
# Restore from gzip backup
gunzip -c /workspaces/ChatFGV/Bases-de-Dados/BACKUP/censo_YYYYMMDD_HHMMSS.sql.gz | psql -U postgres public

# Restore from custom format
pg_restore -U postgres -d public /workspaces/ChatFGV/Bases-de-Dados/BACKUP/censo_YYYYMMDD_HHMMSS.dump
```

## Quick Reference

| Operation | Command |
|-----------|---------|
| Backup full DB (gzip) | `pg_dump -U postgres public \| gzip > backup.sql.gz` |
| Restore full DB | `gunzip -c backup.sql.gz \| psql -U postgres public` |
| Backup schema (gzip) | `pg_dump -U postgres -n <schema> public \| gzip > backup.sql.gz` |
| Backup data only | `pg_dump -U postgres -a -n <schema> public \| gzip > backup.sql.gz` |
| Backup custom format | `pg_dump -U postgres -Fc -n <schema> public > backup.dump` |
| Restore custom format | `pg_restore -U postgres -d public backup.dump` |
| List objects in dump | `pg_restore -l backup.dump` |

## Notes

- **gzip** reduces backup size by ~70-80%
- `pg_dump` is a logical backup (SQL text), compatible across PostgreSQL versions
- Custom format (`-Fc`) allows selective restore of specific tables
- Backup does not block the database — reads/writes continue during dump
- Timestamp naming (`$(date +%Y%m%d_%H%M%S)`) enables version control of backups
