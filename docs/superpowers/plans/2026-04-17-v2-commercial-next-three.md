# V2 Commercial Next Three Slices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the next three serial `V2-005` commercial slices: promotion arbitration controls, price tier foundation, and customer price-tier checkout application.

**Architecture:** Extend the existing control-plane commercial engine rather than creating parallel pricing or discount paths. Promotions stay centralized in `checkout_pricing.py`, price tiers become another commercial input, and desktop orchestration grows through extracted helper actions instead of adding more mixed logic to the 2400-line runtime workspace hook.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, React, TypeScript, Vitest, pytest.

---

## Task Map

### Slice 1: Promotion Arbitration Controls

- add failing backend tests for priority and stacking arbitration
- extend promotion campaign models/schemas/types with `priority` and `stacking_rule`
- implement arbitration in checkout pricing, billing, and checkout payment sessions
- add owner-web management and tests
- commit slice

### Slice 2: Price Tier Foundation

- add failing backend tests for price tiers and branch tier prices
- add models/migration/routes/services/types for price tiers
- add owner-web management and tests
- commit slice

### Slice 3: Customer Price-Tier Checkout Application

- add failing backend, desktop, and owner-web tests
- extend customer profiles with `default_price_tier_id`
- extract desktop customer-commercial helper actions from the runtime workspace
- apply tier-aware pricing in preview, sale, and checkout-session snapshots
- commit slice

### Finalization

- run targeted backend, owner-web, and desktop verification
- run full owner-web and store-desktop suites plus relevant backend test set
- update `docs/WORKLOG.md`
- merge to `main`
- push `origin/main`
