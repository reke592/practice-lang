## Alembic migration

```sh
# initialize database migration directory
alembic init ./src/infrastructure/database/migrations

# create new migration file
alembic revision -m "sample description"

# run migration
alembic upgrade head

# rollback
alembic rollback -1
```