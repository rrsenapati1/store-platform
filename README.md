# Store Platform

Standalone multi-store retail platform, India-first and desktop-offline-first.

This repository currently contains the Wave 1 foundation:
- shared retail domain packages for RBAC, barcode, printing, and sync
- FastAPI backend core for tenant, catalog, inventory, GST billing, and IRP-ready export/import
- initial React shells for platform admin, owner web, and store desktop
- the first Android `store-mobile` runtime slices for handheld and inventory-tablet spoke pairing, scan/lookup, store operations, and branch-runtime posture

## Release Docs

Start here if you are using or operating the product:

- docs index: [docs/DOCS_INDEX.md](./docs/DOCS_INDEX.md)
- tenant onboarding: [docs/public/tenant-onboarding-guide.md](./docs/public/tenant-onboarding-guide.md)
- Store Desktop install: [docs/public/store-desktop-installation-guide.md](./docs/public/store-desktop-installation-guide.md)
- troubleshooting: [docs/public/troubleshooting-guide.md](./docs/public/troubleshooting-guide.md)
- support triage: [docs/support/support-triage-playbook.md](./docs/support/support-triage-playbook.md)

## Workspace Commands

```bash
npm install
npm run test
npm run build
npm run typecheck
python -m pytest services/api/tests -q
```

Mobile runtime scaffold:

```bash
npm run ci:store-mobile
```
