# AURA360 Monorepo Migration Guide

This document describes the migration from the previous flat structure to the current monorepo organization.

## New Structure

```
AURA360/
├── .github/                      # GitHub configuration
│   ├── workflows/                # CI/CD pipelines
│   │   ├── ci-api.yml
│   │   ├── ci-mobile.yml
│   │   ├── ci-web.yml
│   │   ├── ci-agents.yml
│   │   └── ci-vectordb.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
│
├── apps/                         # Client applications
│   ├── mobile/                   # Flutter mobile app (was: aura_mobile)
│   └── web/                      # Angular frontend (was: aura360-front)
│
├── services/                     # Backend services
│   ├── api/                      # Django API (was: backend)
│   ├── agents/                   # AI agents service (was: agents-service)
│   ├── vectordb/                 # Vector database (was: vectorial_db)
│   └── pdf-extraction/           # PDF processing service
│
├── docs/                         # Centralized documentation
│   ├── architecture/
│   ├── testing/
│   │   ├── reports/              # Test reports (was: test-reports)
│   │   └── shared-tests/         # Shared test utilities
│   ├── modules/                  # Module implementation docs
│   │   ├── AGENTS.md
│   │   └── BODY_MODULE_IMPLEMENTATION_SUMMARY.md
│   ├── api/
│   └── EXTERNAL_DEPENDENCIES.md
│
├── scripts/                      # Shared scripts
│
├── .gitignore                    # Global gitignore (consolidated)
├── README.md                     # Main repository README
├── CONTRIBUTING.md               # Contribution guidelines
├── docs/runbooks/agents/CLAUDE.md # AI development guide (ubicación actual)
└── AURA360.code-workspace        # VS Code workspace configuration
```

## Path Mapping (Old → New)

| Old Path | New Path | Type |
|----------|----------|------|
| `aura_mobile/` | `apps/mobile/` | Mobile App |
| `aura360-front/` | `apps/web/` | Web Frontend |
| `backend/` | `services/api/` | Backend API |
| `agents-service/` | `services/agents/` | AI Agents |
| `vectorial_db/` | `services/vectordb/` | Vector DB |
| `pdf-extraction-service/` | `services/pdf-extraction/` | PDF Service |
| `test-reports/` | `docs/testing/reports/` | Test Reports |
| `tests/` | `docs/testing/shared-tests/` | Shared Tests |
| `AGENTS.md` | `docs/modules/AGENTS.md` | Documentation |
| Multiple `.md` files | `docs/testing/*.md` | Documentation |

## Updated Commands

### Before Migration

```bash
# Mobile
cd aura_mobile && flutter run

# Web
cd aura360-front && ng serve

# API
cd backend && uv run python manage.py runserver

# Agents
cd agents-service && uv run uvicorn main:app --reload

# Vector DB
cd vectorial_db && docker compose up
```

### After Migration

```bash
# Mobile
cd apps/mobile && flutter run

# Web
cd apps/web && ng serve

# API
cd services/api && uv run python manage.py runserver

# Agents
cd services/agents && uv run uvicorn main:app --reload

# Vector DB
cd services/vectordb && docker compose up
```

## Git Migration Steps

If you're migrating an existing git repository:

### Option 1: Preserve Git History (Recommended for Production)

```bash
# Backup first!
cp -r AURA360 AURA360-backup

# Use git-filter-repo or similar to preserve history
# Install: pip install git-filter-repo

git filter-repo --path-rename aura_mobile:apps/mobile
git filter-repo --path-rename aura360-front:apps/web
git filter-repo --path-rename backend:services/api
git filter-repo --path-rename agents-service:services/agents
git filter-repo --path-rename vectorial_db:services/vectordb
```

### Option 2: Fresh Start (Simpler)

```bash
# Inside AURA360 directory
git init
git add .
git commit -m "chore: migrate to monorepo structure

- Reorganize client apps under apps/
- Move backend services under services/
- Centralize documentation in docs/
- Add GitHub workflows and templates
- Consolidate .gitignore files"
```

## Environment Variables

Update any hardcoded paths in environment files:

- `apps/mobile/env/local.env`
- `services/api/.env`
- `services/agents/.env`
- `services/vectordb/.env`

## CI/CD Configuration

New GitHub Actions workflows automatically detect changes by path:

- **ci-mobile.yml**: Triggered by changes in `apps/mobile/**`
- **ci-web.yml**: Triggered by changes in `apps/web/**`
- **ci-api.yml**: Triggered by changes in `services/api/**`
- **ci-agents.yml**: Triggered by changes in `services/agents/**`
- **ci-vectordb.yml**: Triggered by changes in `services/vectordb/**`

This ensures only affected services are tested on each PR.

## Files Removed

The following files were removed during migration:

- `cred.json` (empty credentials file)
- `PDF's/` (temporary PDF storage)
- `.pytest_cache/` (pytest cache)

These are now properly ignored by `.gitignore`.

## Files Requiring Manual Review

- **adk-python/**: Google ADK SDK vendored in repo
  - Consider using published package instead
  - See `docs/EXTERNAL_DEPENDENCIES.md`

## Verification Checklist

After migration, verify:

- [ ] All services start correctly from new paths
- [ ] Tests pass in all services
- [ ] Environment variables are correctly set
- [ ] CI/CD workflows trigger correctly
- [ ] Documentation paths are updated
- [ ] VS Code workspace configuration works
- [ ] Import paths in code are correct (if any absolute imports existed)

## Rollback Plan

If issues arise:

```bash
# Restore from backup
rm -rf AURA360
cp -r AURA360-backup AURA360
```

## Benefits of New Structure

1. **Clear Separation**: Client apps vs backend services
2. **Scalability**: Easy to add new apps/services
3. **CI/CD Efficiency**: Only test what changed
4. **Documentation**: Centralized and organized
5. **Onboarding**: New developers understand structure immediately
6. **Monorepo Tools**: Can use tools like Turborepo, Nx, or Bazel in future

## Next Steps

1. Initialize git repository (if not done)
2. Set up GitHub repository
3. Configure branch protection rules
4. Set up required status checks
5. Configure Supabase and other external services
6. Deploy services to staging environment
7. Update team documentation and runbooks

## Questions?

Refer to:
- [README.md](../README.md) for quick start
- [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines
- [CLAUDE.md](./runbooks/agents/CLAUDE.md) for AI development assistance
