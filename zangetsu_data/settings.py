import os

from zangetsu_logger import initialize

logger = initialize()

DATABASES = {
    "ezample_postgresql": {
        "HOST": os.getenv("PGHOST"),
        "PORT": os.getenv("PG_PORT_CONTAINER"),
        "USER": os.getenv("PGUSER"),
        "PASSWORD": os.getenv("PGPASSWORD"),
        "DB_NAME": os.getenv("PGDATABASE"),
    },
    "exaple_bigquery": {
        "project_id": os.getenv("PROJECT_ID"),
        "dataset_id": os.getenv("DATASET_ID"),
        "credentials_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    },
}
