.PHONY: help setup build up down restart logs clean backup restore mysql db-stats rebuild

# Default target
help:
	@echo "Edgewater Inventory Manager - Available Commands:"
	@echo ""
	@echo "Setup & Build:"
	@echo "  make setup      - Initial setup (create directories, copy env)"
	@echo "  make build      - Build Docker containers"
	@echo "  make rebuild    - Force rebuild (no cache)"
	@echo ""
	@echo "Container Management:"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make status     - Check container status"
	@echo ""
	@echo "Logs & Monitoring:"
	@echo "  make logs       - View all container logs"
	@echo "  make logs-db    - View database logs"
	@echo ""
	@echo "Database Operations:"
	@echo "  make mysql      - Connect to MySQL shell"
	@echo "  make backup     - Backup database"
	@echo "  make restore    - Restore database from backup"
	@echo "  make db-stats   - View database statistics"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean      - Remove containers, volumes, and images"
	@echo ""
	@echo "Services:"
	@echo "  - MySQL: localhost:3306"
	@echo "  - phpMyAdmin: http://localhost:8080"

# Initial setup
setup:
	@echo "Setting up Edgewater Inventory Manager..."
	@mkdir -p database/datasource
	@mkdir -p backups
	@mkdir -p logs/mysql
	@touch backups/.gitkeep
	@if [ ! -f .env ]; then cp .env.example .env; echo "✓ Created .env file - please update with your credentials"; fi
	@if [ ! -f database/CreateSchema.sql ]; then echo "⚠ Warning: database/CreateSchema.sql not found"; fi
	@if [ ! -f database/LoadData.sql ]; then echo "⚠ Warning: database/LoadData.sql not found"; fi
	@if [ ! -f database/Relationships.sql ]; then echo "⚠ Warning: database/Relationships.sql not found"; fi
	@echo "✓ Setup complete! Edit .env file before running 'make up'"

# Build containers
build:
	@echo "Building Docker containers..."
	docker-compose build --no-cache
	@echo "✓ Build complete!"

# Force rebuild with volume cleanup
rebuild:
	@echo "Force rebuilding (removing volumes and cache)..."
	docker-compose down -v
	docker-compose build --no-cache --pull
	@echo "✓ Force rebuild complete!"

# Start services
up:
	@echo "Starting services..."
	docker-compose up -d
	@echo ""
	@echo "✓ Services started!"
	@echo "  - MySQL: localhost:3306"
	@echo "  - phpMyAdmin: http://localhost:8080"
	@echo ""
	@echo "Run 'make logs' to view startup logs"
	@echo "Run 'make db-stats' to verify data loaded correctly"

# Stop services
down:
	@echo "Stopping services..."
	docker-compose down
	@echo "✓ Services stopped"

# Restart services  
restart:
	@echo "Restarting services..."
	docker-compose restart
	@echo "✓ Services restarted"

# View all logs
logs:
	docker-compose logs -f

# View database logs
logs-db:
	docker-compose logs -f mysql

# Check service status
status:
	@echo "Container Status:"
	@docker-compose ps
	@echo ""
	@echo "Database Connection Test:"
	@docker exec edgewater_mysql mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} 2>/dev/null && echo "✓ Database is responsive" || echo "✗ Database is not responding"

# Clean everything (WARNING: Destructive!)
clean:
	@echo "⚠  WARNING: This will remove all containers, volumes, and data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..." && read confirm
	docker-compose down -v --rmi all
	@echo "✓ Cleaned all Docker resources"

# Backup database
backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	docker exec edgewater_mysql mysqldump \
		-u root -p${MYSQL_ROOT_PASSWORD} \
		--single-transaction \
		--routines \
		--triggers \
		--events \
		${MYSQL_DATABASE} > backups/edgewater_$$TIMESTAMP.sql && \
	echo "✓ Backup created: backups/edgewater_$$TIMESTAMP.sql" || \
	echo "✗ Backup failed"

# Restore database
restore:
	@echo "Available backups:"
	@ls -1 backups/*.sql 2>/dev/null || echo "No backups found"
	@echo ""
	@read -p "Enter backup filename (or full path): " filename; \
	if [ -f "$$filename" ]; then \
		docker exec -i edgewater_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} < $$filename && \
		echo "✓ Database restored successfully"; \
	elif [ -f "backups/$$filename" ]; then \
		docker exec -i edgewater_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} < backups/$$filename && \
		echo "✓ Database restored successfully"; \
	else \
		echo "✗ Backup file not found"; \
	fi

# Connect to MySQL shell
mysql:
	@echo "Connecting to MySQL shell..."
	@echo "Database: ${MYSQL_DATABASE}"
	@docker exec -it edgewater_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE}

# View database statistics
db-stats:
	@echo "Database Statistics:"
	@echo "===================="
	@docker exec edgewater_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "\
		USE ${MYSQL_DATABASE}; \
		SELECT 'Database Summary' as ''; \
		SELECT \
			'T_Items' as 'Table', \
			COUNT(*) as 'Records', \
			CONCAT(ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2), ' MB') as 'Size' \
		FROM T_Items, information_schema.TABLES \
		WHERE information_schema.TABLES.TABLE_SCHEMA = '${MYSQL_DATABASE}' \
		AND information_schema.TABLES.TABLE_NAME = 'T_Items' \
		UNION ALL \
		SELECT 'T_Orders', COUNT(*), CONCAT(ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2), ' MB') \
		FROM T_Orders, information_schema.TABLES \
		WHERE information_schema.TABLES.TABLE_SCHEMA = '${MYSQL_DATABASE}' \
		AND information_schema.TABLES.TABLE_NAME = 'T_Orders' \
		UNION ALL \
		SELECT 'T_OrderItems', COUNT(*), CONCAT(ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2), ' MB') \
		FROM T_OrderItems, information_schema.TABLES \
		WHERE information_schema.TABLES.TABLE_SCHEMA = '${MYSQL_DATABASE}' \
		AND information_schema.TABLES.TABLE_NAME = 'T_OrderItems' \
		UNION ALL \
		SELECT 'T_Suppliers', COUNT(*), CONCAT(ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2), ' MB') \
		FROM T_Suppliers, information_schema.TABLES \
		WHERE information_schema.TABLES.TABLE_SCHEMA = '${MYSQL_DATABASE}' \
		AND information_schema.TABLES.TABLE_NAME = 'T_Suppliers' \
		UNION ALL \
		SELECT 'T_Plantings', COUNT(*), CONCAT(ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2), ' MB') \
		FROM T_Plantings, information_schema.TABLES \
		WHERE information_schema.TABLES.TABLE_SCHEMA = '${MYSQL_DATABASE}' \
		AND information_schema.TABLES.TABLE_NAME = 'T_Plantings' \
		UNION ALL \
		SELECT 'T_Inventory', COUNT(*), CONCAT(ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2), ' MB') \
		FROM T_Inventory, information_schema.TABLES \
		WHERE information_schema.TABLES.TABLE_SCHEMA = '${MYSQL_DATABASE}' \
		AND information_schema.TABLES.TABLE_NAME = 'T_Inventory' \
		UNION ALL \
		SELECT 'T_Pitch', COUNT(*), CONCAT(ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2), ' MB') \
		FROM T_Pitch, information_schema.TABLES \
		WHERE information_schema.TABLES.TABLE_SCHEMA = '${MYSQL_DATABASE}' \
		AND information_schema.TABLES.TABLE_NAME = 'T_Pitch';" 2>/dev/null

# Verify database setup
verify:
	@echo "Verifying database setup..."
	@docker exec edgewater_mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "\
		USE ${MYSQL_DATABASE}; \
		SHOW TABLES;" 2>/dev/null && \
	echo "✓ Database schema exists" || \
	echo "✗ Database schema missing"