"""
Database Connection Service

Handles database connections and metadata fetching using SQLAlchemy.
"""
import json
from typing import Any

# Initialize pymysql for MySQL support
import pymysql
pymysql.install_as_MySQLdb()

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.db.models import DatabaseMetadataModel, DatabaseConnectionModel
from src.db.database import get_connection


class DatabaseConnectionService:
    """Service for managing database connections."""

    def __init__(self, url: str):
        """
        Initialize with database URL.

        Args:
            url: Database connection URL (e.g., mysql://user:pass@localhost:3306/db)
        """
        self.url = url
        self._engine: Engine | None = None

    def _get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(self.url)
        return self._engine

    def test_connection(self) -> bool:
        """
        Test if the database connection is valid.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def fetch_metadata(self) -> list[dict[str, Any]]:
        """
        Fetch table and view metadata from the database.

        Returns:
            List of metadata dictionaries with table/view information

        Raises:
            Exception: If metadata fetching fails
        """
        engine = self._get_engine()
        inspector = inspect(engine)
        db_name = self.url.split('/')[-1].split('?')[0]

        metadata_list = []

        # Get tables using dialect-specific approach
        try:
            # For MySQL/PostgreSQL, use table_names() and view_names()
            table_names = inspector.get_table_names(schema=db_name)
            for table_name in table_names:
                columns = self._fetch_columns(engine, table_name, db_name)
                metadata_list.append({
                    "name": table_name,
                    "type": "table",
                    "columns": columns,
                })
        except Exception as e:
            raise Exception(f"Failed to fetch tables: {e}")

        # Get views
        try:
            view_names = inspector.get_view_names(schema=db_name)
            for view_name in view_names:
                columns = self._fetch_columns(engine, view_name, db_name)
                metadata_list.append({
                    "name": view_name,
                    "type": "view",
                    "columns": columns,
                })
        except Exception:
            # Some databases might not support views
            pass

        return metadata_list

    def _fetch_columns(self, engine: Engine, table_name: str, schema: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch column metadata for a table.

        Args:
            engine: SQLAlchemy engine
            table_name: Name of the table
            schema: Database name (for MySQL)

        Returns:
            List of column metadata dictionaries
        """
        inspector = inspect(engine)
        columns = []

        try:
            for col in inspector.get_columns(table_name, schema=schema):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "isPrimaryKey": col.get("primary_key", False),
                    "comment": col.get("comment", ""),
                })
        except Exception:
            # If we can't get column info, return empty
            pass

        return columns

    def get_db_type(self) -> str:
        """
        Get the database type from URL.

        Returns:
            Database type (mysql, postgresql, sqlite, etc.)
        """
        if "mysql" in self.url:
            return "mysql"
        elif "postgresql" in self.url or "postgres" in self.url:
            return "postgresql"
        elif "sqlite" in self.url:
            return "sqlite"
        elif "mssql" in self.url:
            return "mssql"
        return "unknown"


def sync_metadata_to_db(db_name: str, metadata: list[dict[str, Any]]) -> None:
    """
    Sync database metadata to local SQLite storage.

    Args:
        db_name: Name of the database connection in local storage
        metadata: List of metadata dictionaries
    """
    # Get the database connection from local storage
    conn = get_connection()
    cursor = conn.cursor()

    # Get the db_connection_id
    cursor.execute("SELECT id FROM database_connections WHERE name = ?", (db_name,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise ValueError(f"Database connection '{db_name}' not found in local storage")

    db_connection_id = row["id"]

    # Clear existing metadata
    cursor.execute("DELETE FROM database_metadata WHERE db_connection_id = ?", (db_connection_id,))

    # Insert new metadata
    from datetime import datetime
    now = datetime.utcnow().isoformat()

    for table_meta in metadata:
        table_name = table_meta.get("name")
        table_type = table_meta.get("type", "table")
        columns = table_meta.get("columns", [])
        columns_json = json.dumps(columns)

        cursor.execute(
            """
            INSERT INTO database_metadata (db_connection_id, table_name, table_type, columns, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (db_connection_id, table_name, table_type, columns_json, now, now)
        )

    conn.commit()
    conn.close()
