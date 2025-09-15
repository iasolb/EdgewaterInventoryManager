FROM mysql:5.7

# Set environment variables
ENV MYSQL_DATABASE=EdgewaterMaster
ENV MYSQL_ROOT_PASSWORD=edgewater123
ENV MYSQL_USER=edgewater
ENV MYSQL_PASSWORD=edgewater123

# Copy database initialization files
COPY CreateSchema.sql /docker-entrypoint-initdb.d/01-CreateSchema.sql
COPY LoadData.sql /docker-entrypoint-initdb.d/02-LoadData.sql
COPY datasource/ /docker-entrypoint-initdb.d/datasource/

# Expose MySQL port
EXPOSE 3306

# Enable local_infile for CSV loading
CMD ["mysqld", "--local-infile=1"]