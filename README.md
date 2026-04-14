# Store Platform

Standalone multi-store retail platform, India-first and desktop-offline-first.

This repository currently contains the Wave 1 foundation:
- shared retail domain packages for RBAC, barcode, printing, and sync
- FastAPI backend core for tenant, catalog, inventory, GST billing, and IRP-ready export/import
- initial React shells for platform admin, owner web, and store desktop

## Workspace Commands

```bash
npm install
npm run test
npm run build
npm run typecheck
python -m pytest services/api/tests -q
```
