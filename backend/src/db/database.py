"""
SQLite Database Management

Handles SQLite database initialization and schema management.
Database file is stored at ~/.db_query/db_query.db
"""
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

# Database file path
DB_DIR = Path.home() / ".db_query"
DB_PATH = DB_DIR / "db_query.db"


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create DatabaseConnection table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS database_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Create DatabaseMetadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS database_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            db_connection_id INTEGER NOT NULL,
            table_name TEXT NOT NULL,
            table_type TEXT NOT NULL,
            columns TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (db_connection_id) REFERENCES database_connections(id),
            UNIQUE(db_connection_id, table_name)
        )
    """)

    # Create QueryHistory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            db_connection_id INTEGER NOT NULL,
            query_type TEXT NOT NULL,
            query_text TEXT NOT NULL,
            generated_sql TEXT,
            result TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (db_connection_id) REFERENCES database_connections(id)
        )
    """)

    conn.commit()
    conn.close()


def mask_password(url: str) -> str:
    """Mask password in database URL for security."""
    if "@" in url:
        parts = url.split("@")
        credentials = parts[0].replace("mysql://", "").replace("postgresql://", "").replace("sqlite://", "")
        if ":" in credentials:
            user_pass = credentials.split(":")
            masked = f"{user_pass[0]}:***@"
        else:
            masked = f"***@"
        return parts[0].split(":")[0] + ":" + masked + "@".join(parts[1:])
    return url


class DatabaseConnectionRepository:
    """Repository for database_connections table."""

    @staticmethod
    def create(name: str, url: str) -> dict[str, Any]:
        """Create a new database connection."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            "INSERT INTO database_connections (name, url, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (name, url, now, now)
        )
        conn.commit()
        db_id = cursor.lastrowid
        conn.close()

        return {
            "id": db_id,
            "name": name,
            "url": mask_password(url),
            "createdAt": now,
            "updatedAt": now
        }

    @staticmethod
    def get_by_name(name: str) -> dict[str, Any] | None:
        """Get a database connection by name."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM database_connections WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    @staticmethod
    def get_all() -> list[dict[str, Any]]:
        """Get all database connections."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM database_connections ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    @staticmethod
    def delete(name: str) -> bool:
        """Delete a database connection by name."""
        conn = get_connection()
        cursor = conn.cursor()

        # Get the connection id first
        cursor.execute("SELECT id FROM database_connections WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        db_id = row["id"]

        # Delete related metadata and history first
        cursor.execute("DELETE FROM database_metadata WHERE db_connection_id = ?", (db_id,))
        cursor.execute("DELETE FROM query_history WHERE db_connection_id = ?", (db_id,))
        cursor.execute("DELETE FROM database_connections WHERE id = ?", (db_id,))

        conn.commit()
        conn.close()
        return True


class DatabaseMetadataRepository:
    """Repository for database_metadata table."""

    @staticmethod
    def upsert(db_connection_id: int, table_name: str, table_type: str, columns: list[dict]) -> dict[str, Any]:
        """Insert or update metadata for a table."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        columns_json = json.dumps(columns)

        cursor.execute(
            """
            INSERT INTO database_metadata (db_connection_id, table_name, table_type, columns, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(db_connection_id, table_name) DO UPDATE SET
                table_type = excluded.table_type,
                columns = excluded.columns,
                updated_at = excluded.updated_at
            """,
            (db_connection_id, table_name, table_type, columns_json, now, now)
        )
        conn.commit()
        conn.close()

        return {
            "tableName": table_name,
            "tableType": table_type,
            "columns": columns
        }

    @staticmethod
    def get_by_connection(db_connection_id: int) -> list[dict[str, Any]]:
        """Get all metadata for a database connection."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM database_metadata WHERE db_connection_id = ? ORDER BY table_name",
            (db_connection_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                "name": row["table_name"],
                "type": row["table_type"],
                "columns": json.loads(row["columns"])
            })
        return result


class QueryHistoryRepository:
    """Repository for query_history table."""

    @staticmethod
    def create(
        db_connection_id: int,
        query_type: str,
        query_text: str,
        generated_sql: str | None = None,
        result: list | None = None,
        error: str | None = None
    ) -> dict[str, Any]:
        """Create a new query history entry."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO query_history (db_connection_id, query_type, query_text, generated_sql, result, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (db_connection_id, query_type, query_text, generated_sql, json.dumps(result) if result else None, error, now)
        )
        conn.commit()
        history_id = cursor.lastrowid
        conn.close()

        return {
            "id": history_id,
            "queryType": query_type,
            "queryText": query_text,
            "createdAt": now
        }
