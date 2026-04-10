"""
SQL Query Service

Handles SQL parsing, validation, and execution.
"""
from typing import Any

# Initialize pymysql for MySQL support
import pymysql
pymysql.install_as_MySQLdb()

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.services.sql_parser import SQLParserService


class QueryService:
    """Service for executing SQL queries."""

    def __init__(self, url: str):
        """
        Initialize with database URL.

        Args:
            url: Database connection URL
        """
        self.url = url
        self._engine: Engine | None = None
        self._parser = SQLParserService()

    def _get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(self.url)
        return self._engine

    def validate_sql(self, sql: str) -> None:
        """
        Validate that the SQL is a SELECT statement.

        Args:
            sql: The SQL query to validate

        Raises:
            ValueError: If SQL is invalid or not a SELECT statement
        """
        self._parser.validate(sql)

    def add_limit(self, sql: str, limit: int = 100) -> str:
        """
        Add LIMIT clause to SQL if not already present.

        Args:
            sql: The SQL query
            limit: The limit value (default 100)

        Returns:
            SQL with LIMIT clause
        """
        return self._parser.add_limit(sql, limit)

    def execute_query(self, sql: str) -> dict[str, Any]:
        """
        Validate and execute a SQL query.

        Args:
            sql: The SQL query to execute

        Returns:
            Query result with columns, rows, and row count

        Raises:
            ValueError: If SQL is invalid or not a SELECT statement
        """
        # Validate SQL using parser service
        self._parser.validate(sql)

        # Add LIMIT if not present
        sql = self._parser.add_limit(sql)

        # Execute the query
        engine = self._get_engine()

        try:
            with engine.connect() as conn:
                result = conn.execute(text(sql))
                columns = list(result.keys())
                rows = [list(row) for row in result.fetchall()]
                row_count = len(rows)

                return {
                    "columns": columns,
                    "rows": rows,
                    "rowCount": row_count,
                    "sql": sql,
                }
        except Exception as e:
            raise ValueError(f"Query execution failed: {e}")
