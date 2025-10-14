# Edgewater Inventory Manager 

## Complete Directory Layout

```
edgewater-inventory-manager/
│
├── 📁 database/                    # Database files
│   ├── CreateSchema.sql           # Table schema definitions
│   ├── LoadData.sql               # CSV import script
│   ├── Relationships.sql          # Foreign keys & indexes
│   └── 📁 datasource/             # Source CSV files
│       ├── Brokers.csv
│       ├── ExportItems.csv
│       ├── GrowingSeason.csv
│       ├── Inventory.csv
│       ├── items_cleaned.csv
│       ├── Items.csv
│       ├── ItemType.csv
│       ├── OrderItems.csv
│       ├── OrderItemTypes.csv
│       ├── OrderNotes.csv
│       ├── Orders.csv
│       ├── Pitch.csv
│       ├── Plantings.csv
│       ├── Prices.csv
│       ├── Shippers.csv
│       ├── Sun.csv
│       ├── Suppliers.csv
│       ├── UnitCategory.csv
│       └── Units.csv
│
├── 📁 backups/                     # Database backups
│   └── .gitkeep
│
├── 📁 logs/                        # Application logs
│   ├── 📁 mysql/                  # MySQL logs
│   └── app.log                    # Python application logs
│
├── 📁 uploads/                     # File uploads (future use)
│   └── .gitkeep
│
├── 📄 config.py                    # Configuration management
├── 📄 database.py                  # Database connection utilities
├── 📄 models.py                    # SQLAlchemy ORM models
├── 📄 test_connection.py          # Connection test script
│
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env                         # Environment variables (not in git)
├── 📄 .env.example                 # Environment template
├── 📄 .gitignore                   # Git ignore rules
├── 📄 .dockerignore                # Docker ignore rules
│
├── 📄 docker-compose.yml           # Docker orchestration
├── 📄 Dockerfile                   # MySQL Docker image
├── 📄 Makefile                     # Helper commands
│
└── 📄 README.md                    # Main documentation
```

## File Purposes

### Core Python Files

**config.py**
- Environment-based configuration
- Database connection strings
- Application settings
- Path management

**database.py**
- Database connection management
- Query execution utilities
- SQLAlchemy session handling
- Connection pooling
- Transaction management

**models.py**
- SQLAlchemy ORM models for all tables
- Relationship definitions
- Type definitions
- Model methods

**test_connection.py**
- Database connectivity tests
- Statistics gathering
- Sample queries
- Verification script

### Docker & Infrastructure

**Dockerfile**
- MySQL 8.0 base image
- Schema initialization
- CSV data loading
- Foreign key setup

**docker-compose.yml**
- MySQL service definition
- phpMyAdmin service
- Volume management
- Network configuration
- Environment variables

**Makefile**
- Convenient command shortcuts
- Setup automation
- Backup/restore operations
- Database operations
- Container management

### Database Files

**database/CreateSchema.sql**
- All table definitions
- Primary keys
- Column types
- Default values

**database/LoadData.sql**
- LOAD DATA INFILE commands for all CSVs
- NULL handling
- Boolean conversions
- Data type casting

**database/Relationships.sql**
- Foreign key constraints
- Index definitions
- Referential integrity

**database/datasource/\*.csv**
- Source data from Access database
- Must maintain exact filenames
- UTF-8 encoding required

### Configuration Files

**.env**
- Private credentials
- Database passwords
- Port configurations
- NOT committed to git

**.env.example**
- Template for .env
- Safe to commit
- Documents required variables

**.gitignore**
- Excludes sensitive files
- Ignores logs and backups
- Excludes virtual environments

**requirements.txt**
- Python package dependencies
- Pinned versions
- Development and production packages

## Setup Order

1. **Initial Setup**
   ```bash
   make setup
   ```
   - Creates directory structure
   - Copies .env.example to .env

2. **Place CSV Files**
   - Copy all CSV files to `database/datasource/`
   - Verify filenames match exactly

3. **Configure Environment**
   - Edit `.env` with your credentials
   - Set database passwords
   - Configure ports if needed

4. **Build Database**
   ```bash
   make build
   make up
   ```
   - Builds Docker images
   - Starts MySQL container
   - Runs initialization scripts
   - Loads all CSV data
   - Applies relationships

5. **Setup Python**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Verify**
   ```bash
   python test_connection.py
   make db-stats
   ```

## Adding New Files

### Adding a Python Module

```python
# my_module.py
from database import Database, get_db_session
from models import Item
from config import get_config

# Your code here
```

### Adding a Script

```bash
# scripts/my_script.py
#!/usr/bin/env python3
import sys
sys.path.insert(0, '..')  # Add parent directory to path

from database import Database
# Your script code
```

### Adding SQL Queries

```sql
-- queries/custom_query.sql
-- Place custom SQL queries here for reference
SELECT * FROM T_Items WHERE ...;
```

## File Permissions

```bash
# Make scripts executable
chmod +x test_connection.py

# Ensure CSV files are readable
chmod 644 database/datasource/*.csv

# Protect environment file
chmod 600 .env
```

## Migration Notes

This structure is designed to:
- ✅ Keep database and application code separate
- ✅ Allow easy Docker deployment
- ✅ Support both raw SQL and ORM approaches
- ✅ Enable backup/restore operations
- ✅ Facilitate future web frontend development
- ✅ Maintain clean version control
- ✅ Support multiple Python frameworks (Flask, FastAPI, Streamlit)

## Next Steps

After setup, you can:
1. Build a web interface (Flask/FastAPI/Streamlit)
2. Create data analysis scripts
3. Add automated reports
4. Implement data visualization
5. Build REST API endpoints
6. Add authentication layer