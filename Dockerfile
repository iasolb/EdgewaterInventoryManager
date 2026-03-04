FROM mysql:8.0

# Set environment variables
ENV MYSQL_ROOT_PASSWORD=edgewater_root_pass
ENV MYSQL_DATABASE=EdgewaterMaster
ENV MYSQL_USER=edgewater_user
ENV MYSQL_PASSWORD=edgewater_pass

# Copy SQL scripts
COPY database/CreateSchema.sql /docker-entrypoint-initdb.d/01-schema.sql
COPY database/LoadData.sql /docker-entrypoint-initdb.d/02-load-data.sql
COPY database/CleanupOrphans.sql /docker-entrypoint-initdb.d/03-cleanup-orphans.sql
COPY database/Relationships.sql /docker-entrypoint-initdb.d/04-relationships.sql
COPY database/views.sql /docker-entrypoint-initdb.d/05-views.sql

# Copy CSV files for import
COPY database/datasource/*.csv /var/lib/mysql-files/

# Normalize ALL CSVs: strip BOM, convert \r\n to \n, ensure trailing newline
RUN for f in /var/lib/mysql-files/*.csv; do \
      sed -i '1s/^\xEF\xBB\xBF//' "$f" && \
      sed -i 's/\r$//' "$f" && \
      [ -n "$(tail -c 1 "$f")" ] && echo "" >> "$f" || true; \
    done

# Set proper permissions
RUN chmod 644 /docker-entrypoint-initdb.d/*.sql

EXPOSE 3306