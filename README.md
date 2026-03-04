# Edgewater Inventory Manager

A full-stack inventory management system built for Edgewater Farm. Migrated from a legacy Microsoft Access database to a modern MySQL + Python + Streamlit architecture. Manages plant inventory, planting records, order tracking, label generation, and employee workflows across greenhouse and field operations.

**Author:** Ian Solberg

---

## Tech Stack

### Database Layer

**MySQL 8.0** — Primary data store, running in Docker. The schema was reverse-engineered from an Access `.accdb` file and rebuilt as normalized MySQL with proper foreign key constraints, indexes, and SQL views.

**Key components:**

- `CreateSchema.sql` — 22 tables including items, inventory, plantings, orders, order items, prices, suppliers, shippers, brokers, growing seasons, locations, users, passwords, seasonal notes, and junction tables for destinations
- `LoadData.sql` — Bulk CSV import using `LOAD DATA INFILE` with date format handling (`M/D/YY` and ISO), boolean conversion, and NULL coercion
- `CleanupOrphans.sql` — Pre-relationship data integrity pass that resolves orphaned foreign keys (sets to 0 for "Unknown" or deletes cascade-style orphans)
- `Relationships.sql` — Foreign key constraints with `RESTRICT` for history preservation and `CASCADE` for ownership relationships, plus performance indexes on all FK columns
- `views.sql` — Five SQL views (`v_inventory_full`, `v_plantings_full`, `v_orders_full`, `v_label_data_full`, `v_pitch_full`) that pre-join related tables for read-heavy frontend queries

### ORM & Database Access

**SQLAlchemy 2.x** — ORM layer mapping all 22 tables plus 5 view models. Uses `declarative_base` with explicit column typing, relationship definitions with `back_populates`, and context-managed sessions via `get_db_session()`.

**PyMySQL** — MySQL driver for SQLAlchemy. Uses `caching_sha2_password` auth (requires the `cryptography` package).

**Key files:**

- `database.py` — Connection pooling, session management, engine configuration via environment variables
- `models.py` — All SQLAlchemy models including base table models (with relationships) and read-only view models
- `payloads.py` — TypedDict definitions for every table and view, providing autocomplete support for all database operations

### API Layer

**`rest/api.py`** — `EdgewaterAPI` class providing a complete CRUD interface to the database. Contains:

- **Generic CRUD methods** — `_get_all()`, `_get_by_id()`, `_create()`, `_update()`, `_delete()` with automatic type coercion via SQLAlchemy column introspection
- **Table-specific add methods** — `table_add_inventory()`, `table_add_planting()`, `table_add_order()`, etc. with typed parameters and payload validation
- **`generic_update()`** — Field-filtered updates with allowed field sets, optional preprocessors, and strict mode for view-to-table editing
- **View cache getters** — Methods that query SQL views and return sorted DataFrames
- **Display methods** — Column-subset DataFrames for specific frontend pages (inventory display, plantings display, orders summary, label display)

#### Two-Tier Caching Architecture

**Tier 1 — `@st.cache_data` for lookup tables** (10-minute TTL): Items, item types, units, unit categories, locations, suppliers, shippers, brokers, growing seasons, order item types, order notes. Small, rarely-changing reference data shared across sessions. Accessed via `@property` accessors (`api.item_cache`, `api.unit_cache`, etc.). Force-clear with `api.clear_lookup_caches()`.

**Tier 2 — `st.session_state` for view/table caches**: Inventory, plantings, orders, labels, pitch views plus single-table admin caches. Loaded lazily on first access, persist across reruns within a session. Force-refresh with `api.refresh_view_cache("inventory")` or `api.refresh_view_cache("all")`.

**Tier 2.5 — Filtered working sets**: Pages store their currently-filtered DataFrame subset via `api.set_working_set("inventory", filtered_df)` so card expansions and detail lookups operate on the filtered data rather than the full dataset.

### Frontend

**Streamlit 1.55** — All UI pages. Uses `st.set_page_config()` for per-page configuration, `st.session_state` for cross-rerun persistence, and `st.switch_page()` for navigation.

#### Page Architecture

**Landing & Navigation:**

- `edgewater.py` — Main landing page with navigation buttons to all sections
- `pages/admin_landing.py` — Admin hub with buttons to all 20 individual table CRUD pages

**Admin Workflow Pages (card-based, sidebar filters):**

- `pages/inventory_manager.py` — Card/table toggle view, sidebar search + type/location/status filters, inline edit with location support, add form, delete confirmation flow
- `pages/plantings.py` — Same pattern with planting location, destination tracking, seasonal notes display
- `pages/order_tracking.py` — Four-tab layout: Order Summary (expandable per-supplier), Timeline (weekly grouping with overdue detection), All Items (flat searchable table), Receiving (per-order and per-item receive workflow with condition notes)
- `pages/label_generator.py` — Three-tab layout: Search & Add (item search with type filter, quantity input), Label Order (editable list with price display), Export (JSON and CSV download with preview)

**Employee Pages (mobile-first, big touch targets):**

- `pages/employee_pitch.py` — Quick item search, reason quick-select bar (10 preset reasons), pitch form, today's log with reason badges and weekly stats
- `pages/employee_plantings.py` — Location quick-select buttons (excludes Pitch Pile), item search, planting form with auto-location, today's log with location badges

**Admin Table Pages (20 pages, one per table):**

All follow the same template: header with back/title/refresh, expandable add form with lookup dropdowns, search/filter section, data_editor with edit mode toggle, bulk operations (delete, and table-specific bulk actions), CSV export.

`item.py`, `item_type.py`, `inventory.py`, `order.py`, `order_item.py`, `order_item_destination.py`, `order_item_type.py`, `order_note.py`, `pitch.py`, `planting.py`, `price.py`, `seasonal_notes.py`, `locations.py`, `broker.py`, `growing_season.py`, `shipper.py`, `supplier.py`, `unit.py`, `unit_category.py`, `users.py`

### Authentication

**`rest/authenticate.py`** — Authentication module (imported but not yet wired into page routing). `T_Passwords` table stores bcrypt hashes with reset tokens, expiry, failed attempt tracking, and account locking. `T_Users` stores roles and permission levels.

**Planned permission tiers:**

1. **Super Admin** — Full access to all tables including users
2. **Delegated Editor** — Full table access except users
3. **Farm Worker** — Employee workflow pages only (pitch, plantings), can edit only their own recent entries

### Infrastructure

**Docker** — MySQL 8.0 container with initialization scripts auto-run via `/docker-entrypoint-initdb.d/` ordering (`01-schema.sql`, `02-load-data.sql`, `03-cleanup-orphans.sql`, `04-relationships.sql`, `05-views.sql`). CSV files copied to `/var/lib/mysql-files/` for `LOAD DATA INFILE`.

**docker-compose.yml** — MySQL service with persistent volume, phpMyAdmin for visual DB management, environment variable configuration.

**Makefile** — Shortcut commands for setup, Docker operations, backups, and database utilities.

---

## Dependencies

```
# Database
SQLAlchemy>=2.0,<3.0
pymysql>=1.1,<2.0
cryptography>=42.0,<44.0

# Web UI
streamlit>=1.38,<2.0

# Data Processing
pandas>=2.1,<3.0
numpy>=1.26,<3.0

# Environment & Config
python-dotenv>=1.0,<2.0

# Logging
loguru>=0.7,<1.0

# Validation / Payloads
pydantic>=2.5,<3.0

# Date/Time
python-dateutil>=2.8,<3.0

# HTTP
requests>=2.31,<3.0

# Dev tools
pytest>=7.4,<9.0
black>=23.12,<25.0
flake8>=6.1,<8.0
mypy>=1.7,<2.0
```

---

## Project Structure

```
EdgewaterInventoryManager/
├── database/
│   ├── CreateSchema.sql
│   ├── LoadData.sql
│   ├── CleanupOrphans.sql
│   ├── Relationships.sql
│   ├── views.sql
│   └── datasource/
│       ├── *.csv                  # 24 source data files
│       └── image_assets/
│           └── SunConditions/     # Sun condition images
│
├── frontend/
│   ├── edgewater.py               # Landing page
│   └── pages/
│       ├── admin_landing.py       # Admin navigation hub
│       ├── inventory_manager.py   # Inventory workflow
│       ├── plantings.py           # Plantings workflow
│       ├── order_tracking.py      # Order tracking workflow
│       ├── label_generator.py     # Label generation workflow
│       ├── employee_pitch.py      # Employee pitch entry
│       ├── employee_plantings.py  # Employee planting entry
│       └── *.py                   # 20 admin table CRUD pages
│
├── rest/
│   ├── api.py                     # EdgewaterAPI class
│   └── authenticate.py            # Auth module
│
├── models.py                      # SQLAlchemy ORM models
├── payloads.py                    # TypedDict payload definitions
├── database.py                    # DB connection management
├── config.py                      # Environment configuration
│
├── Dockerfile                     # MySQL container definition
├── docker-compose.yml             # Service orchestration
├── Makefile                       # Helper commands
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- Docker Desktop
- MySQL 8.0 (via Docker)

### 1. Clone and configure

```bash
git clone https://github.com/iasolb/EdgewaterInventoryManager.git
cd EdgewaterInventoryManager
cp .env.example .env
# Edit .env with your database credentials
```

### 2. Start the database

```bash
docker-compose up -d
```

This builds the MySQL container, runs all SQL initialization scripts in order, and loads all CSV data. phpMyAdmin is available at `http://localhost:8080`.

### 3. Set up Python environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run frontend/edgewater.py
```

The app will be available at `http://localhost:8501`.

### 5. Verify database connection

Check the terminal output for SQLAlchemy connection logs. If you see `'cryptography' package is required`, run:

```bash
pip install "cryptography>=42.0,<44.0"
```

---

## Database Schema

22 tables organized into four groups:

**Lookup/Reference:** `T_ItemType`, `T_UnitCategory`, `T_Units`, `T_Brokers`, `T_Shippers`, `T_Suppliers`, `T_GrowingSeason`, `T_OrderItemTypes`, `T_OrderNotes`, `T_Sun`, `T_Locations`

**Core Data:** `T_Items`, `T_Prices`, `T_Inventory`, `T_Plantings`, `T_Pitch`, `T_Orders`, `T_OrderItems`

**Junction/Detail:** `T_OrderItemDestination`, `T_PlantingDestinations`, `T_SeasonalNotes`

**Auth:** `T_Users`, `T_Passwords`

**Views:** `v_inventory_full`, `v_plantings_full`, `v_orders_full`, `v_label_data_full`, `v_pitch_full`

---

## License

Private repository. All rights reserved.
