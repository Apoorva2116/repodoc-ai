#!/usr/bin/env bash

DB_NAME="realworlddb"
DB_USER="testuser"
DB_PASSWORD="changeme"
DB_HOST="postgres"

TABLES=(
    "article_comments"
    "articles_favorites"
    "articles_tags"
    "articles"
    "tags"
    "user_follows"
    "users"
)

for TABLE in "${TABLES[@]}"; do
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "TRUNCATE TABLE $TABLE RESTART IDENTITY CASCADE;"
done