"""
SQLite Database Management for Multi-Database Query Tool

Handles SQLite database initialization and schema management.
Database file is stored at ~/.db_query/db_query.db
"""
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

# Database file path from config
DB_DIR = Path.home() / ".db_query"
DB_PATH = DB_DIR / "db_query.db"


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize the database schema for multi-database support."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create connections table (MySQL server connections)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            db_type TEXT NOT NULL DEFAULT 'mysql',
            host TEXT NOT NULL,
            port INTEGER NOT NULL DEFAULT 3306,
            username TEXT NOT NULL,
            password_encrypted TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Create discovered_databases table (databases found on each connection)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discovered_databases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            connection_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            charset TEXT,
            collation TEXT,
            cached_at TEXT NOT NULL,
            FOREIGN KEY (connection_id) REFERENCES connections(id),
            UNIQUE(connection_id, name)
        )
    """)

    # Create table_metadata table (tables/views in each database)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS table_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            database_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'table',
            cached_at TEXT NOT NULL,
            FOREIGN KEY (database_id) REFERENCES discovered_databases(id),
            UNIQUE(database_id, name)
        )
    """)

    # Create column_metadata table (columns in each table)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS column_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            data_type TEXT NOT NULL,
            is_nullable INTEGER DEFAULT 1,
            is_primary_key INTEGER DEFAULT 0,
            default_value TEXT,
            extra TEXT,
            comment TEXT,
            FOREIGN KEY (table_id) REFERENCES table_metadata(id),
            UNIQUE(table_id, name)
        )
    """)

    # Create query_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            connection_id INTEGER NOT NULL,
            sql_text TEXT NOT NULL,
            execution_time_ms REAL,
            row_count INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (connection_id) REFERENCES connections(id)
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


class ConnectionRepository:
    """Repository for connections table (MySQL server connections)."""

    @staticmethod
    def create(
        name: str,
        db_type: str,
        host: str,
        port: int,
        username: str,
        password_encrypted: str
    ) -> dict[str, Any]:
        """Create a new MySQL server connection."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO connections (name, db_type, host, port, username, password_encrypted, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, db_type, host, port, username, password_encrypted, now, now)
        )
        conn.commit()
        db_id = cursor.lastrowid
        conn.close()

        return {
            "id": db_id,
            "name": name,
            "dbType": db_type,
            "host": host,
            "port": port,
            "username": username,
            "createdAt": now,
            "updatedAt": now
        }

    @staticmethod
    def get_by_id(connection_id: int) -> dict[str, Any] | None:
        """Get a connection by ID."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM connections WHERE id = ?", (connection_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    @staticmethod
    def get_by_name(name: str) -> dict[str, Any] | None:
        """Get a connection by name."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM connections WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    @staticmethod
    def get_all() -> list[dict[str, Any]]:
        """Get all connections."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, db_type, host, port, username, created_at, updated_at FROM connections ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "name": row["name"],
                "dbType": row["db_type"],
                "host": row["host"],
                "port": row["port"],
                "username": row["username"],
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"]
            })
        return result

    @staticmethod
    def delete(connection_id: int) -> bool:
        """Delete a connection by ID."""
        conn = get_connection()
        cursor = conn.cursor()

        # Delete related data first
        cursor.execute("DELETE FROM column_metadata WHERE table_id IN (SELECT id FROM table_metadata WHERE database_id IN (SELECT id FROM discovered_databases WHERE connection_id = ?))", (connection_id,))
        cursor.execute("DELETE FROM table_metadata WHERE database_id IN (SELECT id FROM discovered_databases WHERE connection_id = ?)", (connection_id,))
        cursor.execute("DELETE FROM discovered_databases WHERE connection_id = ?", (connection_id,))
        cursor.execute("DELETE FROM query_history WHERE connection_id = ?", (connection_id,))
        cursor.execute("DELETE FROM connections WHERE id = ?", (connection_id,))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success


class DiscoveredDatabaseRepository:
    """Repository for discovered_databases table."""

    @staticmethod
    def upsert(
        connection_id: int,
        name: str,
        charset: str | None = None,
        collation: str | None = None
    ) -> dict[str, Any]:
        """Insert or update a discovered database."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO discovered_databases (connection_id, name, charset, collation, cached_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(connection_id, name) DO UPDATE SET
                charset = excluded.charset,
                collation = excluded.collation,
                cached_at = excluded.cached_at
            """,
            (connection_id, name, charset, collation, now)
        )
        conn.commit()

        cursor.execute("SELECT id FROM discovered_databases WHERE connection_id = ? AND name = ?", (connection_id, name))
        row = cursor.fetchone()
        conn.close()

        return {
            "id": row["id"],
            "connectionId": connection_id,
            "name": name,
            "charset": charset,
            "collation": collation,
            "cachedAt": now
        }

    @staticmethod
    def get_by_connection(connection_id: int) -> list[dict[str, Any]]:
        """Get all databases for a connection."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM discovered_databases WHERE connection_id = ? ORDER BY name",
            (connection_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "connectionId": row["connection_id"],
                "name": row["name"],
                "charset": row["charset"],
                "collation": row["collation"],
                "cachedAt": row["cached_at"]
            })
        return result

    @staticmethod
    def get_by_name(connection_id: int, name: str) -> dict[str, Any] | None:
        """Get a specific database by name."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM discovered_databases WHERE connection_id = ? AND name = ?",
            (connection_id, name)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "connectionId": row["connection_id"],
                "name": row["name"],
                "charset": row["charset"],
                "collation": row["collation"],
                "cachedAt": row["cached_at"]
            }
        return None


class TableMetadataRepository:
    """Repository for table_metadata table."""

    @staticmethod
    def upsert(database_id: int, name: str, table_type: str) -> dict[str, Any]:
        """Insert or update table metadata."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO table_metadata (database_id, name, type, cached_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(database_id, name) DO UPDATE SET
                type = excluded.type,
                cached_at = excluded.cached_at
            """,
            (database_id, name, table_type, now)
        )
        conn.commit()

        cursor.execute("SELECT id FROM table_metadata WHERE database_id = ? AND name = ?", (database_id, name))
        row = cursor.fetchone()
        conn.close()

        return {
            "id": row["id"],
            "databaseId": database_id,
            "name": name,
            "type": table_type,
            "cachedAt": now
        }

    @staticmethod
    def get_by_database(database_id: int) -> list[dict[str, Any]]:
        """Get all tables for a database."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM table_metadata WHERE database_id = ? ORDER BY name",
            (database_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "databaseId": row["database_id"],
                "name": row["name"],
                "type": row["type"],
                "cachedAt": row["cached_at"]
            })
        return result

    @staticmethod
    def get_by_name(database_id: int, name: str) -> dict[str, Any] | None:
        """Get a specific table by name."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM table_metadata WHERE database_id = ? AND name = ?",
            (database_id, name)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "databaseId": row["database_id"],
                "name": row["name"],
                "type": row["type"],
                "cachedAt": row["cached_at"]
            }
        return None


class ColumnMetadataRepository:
    """Repository for column_metadata table."""

    @staticmethod
    def bulk_insert(table_id: int, columns: list[dict[str, Any]]) -> None:
        """Insert multiple columns for a table."""
        conn = get_connection()
        cursor = conn.cursor()

        # Delete existing columns
        cursor.execute("DELETE FROM column_metadata WHERE table_id = ?", (table_id,))

        # Insert new columns
        for col in columns:
            cursor.execute(
                """
                INSERT INTO column_metadata (table_id, name, data_type, is_nullable, is_primary_key, default_value, extra, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    table_id,
                    col.get("name"),
                    col.get("dataType") or col.get("type"),
                    1 if col.get("isNullable") else 0,
                    1 if col.get("isPrimaryKey") else 0,
                    col.get("defaultValue"),
                    col.get("extra"),
                    col.get("comment")
                )
            )

        conn.commit()
        conn.close()

    @staticmethod
    def get_by_table(table_id: int) -> list[dict[str, Any]]:
        """Get all columns for a table."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM column_metadata WHERE table_id = ? ORDER BY id",
            (table_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                "name": row["name"],
                "dataType": row["data_type"],
                "isNullable": bool(row["is_nullable"]),
                "isPrimaryKey": bool(row["is_primary_key"]),
                "defaultValue": row["default_value"],
                "extra": row["extra"],
                "comment": row["comment"]
            })
        return result


class QueryHistoryRepository:
    """Repository for query_history table."""

    @staticmethod
    def create(
        connection_id: int,
        sql_text: str,
        execution_time_ms: float | None = None,
        row_count: int = 0,
        error_message: str | None = None
    ) -> dict[str, Any]:
        """Create a new query history entry."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO query_history (connection_id, sql_text, execution_time_ms, row_count, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (connection_id, sql_text, execution_time_ms, row_count, error_message, now)
        )
        conn.commit()
        history_id = cursor.lastrowid
        conn.close()

        return {
            "id": history_id,
            "connectionId": connection_id,
            "sqlText": sql_text,
            "executionTimeMs": execution_time_ms,
            "rowCount": row_count,
            "errorMessage": error_message,
            "createdAt": now
        }
