"""
SQL Parser Service

Handles SQL parsing and validation using sqlglot.
"""
from typing import Any

import sqlglot
from sqlglot import exp


class SQLParserService:
    """Service for parsing and validating SQL queries."""

    @staticmethod
    def validate(sql: str) -> exp.Expression:
        """
        Validate that the SQL is a valid SELECT statement.

        Args:
            sql: The SQL query to validate

        Returns:
            The parsed SQL expression

        Raises:
            ValueError: If SQL is invalid or not a SELECT statement
        """
        if not sql or not sql.strip():
            raise ValueError("SQL statement cannot be empty")

        try:
            parsed = sqlglot.parse_one(sql)
        except Exception as e:
            raise ValueError(f"SQL syntax error: {e}")

        if not parsed:
            raise ValueError("Invalid SQL statement")

        # Check if it's a SELECT statement
        if not isinstance(parsed, exp.Select):
            raise ValueError("Only SELECT statements are allowed")

        return parsed

    @staticmethod
    def add_limit(sql: str, limit: int = 100) -> str:
        """
        Add LIMIT clause to SQL if not already present.

        Args:
            sql: The SQL query
            limit: The limit value (default 100)

        Returns:
            SQL with LIMIT clause
        """
        # First clean the SQL
        cleaned_sql = SQLParserService._clean_sql(sql)

        # Parse the cleaned SQL
        parsed = sqlglot.parse_one(cleaned_sql)

        # Check if already has LIMIT
        if parsed.find(exp.Limit):
            return cleaned_sql

        # Add LIMIT using sqlglot
        limit_clause = exp.Limit(expression=exp.Literal.number(limit))
        parsed.set("limit", limit_clause)

        return parsed.sql()

    @staticmethod
    def _clean_sql(sql: str) -> str:
        """
        Clean SQL by removing semicolons, newlines, and ANSI codes.

        Args:
            sql: Raw SQL string

        Returns:
            Cleaned SQL string
        """
        import re

        # Remove ANSI color codes like [4m, [0m, etc.
        sql = re.sub(r'\x1b\[[0-9;]*m', '', sql)

        # Remove markdown code blocks
        sql = re.sub(r'```[\w]*', '', sql)
        sql = re.sub(r'```', '', sql)

        # Remove semicolons and whitespace around them
        sql = re.sub(r'\s*;\s*', ' ', sql)

        # Remove trailing semicolon
        sql = sql.rstrip().rstrip(';').rstrip()

        # Remove any leading/trailing newlines
        sql = sql.strip()

        return sql

    @staticmethod
    def get_table_names(sql: str) -> list[str]:
        """
        Extract table names from a SQL SELECT statement.

        Args:
            sql: The SQL query

        Returns:
            List of table names referenced in the query

        Raises:
            ValueError: If SQL is invalid
        """
        parsed = SQLParserService.validate(sql)

        tables = []
        for table in parsed.find_all(exp.Table):
            if table.name:
                tables.append(table.name)

        return tables

    @staticmethod
    def get_columns(sql: str) -> list[str]:
        """
        Extract column names from a SQL SELECT statement.

        Args:
            sql: The SQL query

        Returns:
            List of column names in the SELECT clause

        Raises:
            ValueError: If SQL is invalid
        """
        parsed = SQLParserService.validate(sql)

        columns = []
        select = parsed.find(exp.Select)
        if select:
            for expr in select.expressions:
                if isinstance(expr, exp.Alias):
                    columns.append(expr.alias)
                elif isinstance(expr, exp.Column):
                    columns.append(expr.name)
                elif isinstance(expr, exp.Star):
                    return ["*"]
                else:
                    columns.append(str(expr))

        return columns

    @staticmethod
    def is_safe_query(sql: str) -> bool:
        """
        Check if the SQL query is safe to execute.

        A query is considered safe if:
        - It is a SELECT statement
        - It does not contain dangerous keywords

        Args:
            sql: The SQL query to check

        Returns:
            True if the query is safe, False otherwise
        """
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
            "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE"
        ]

        upper_sql = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in upper_sql:
                return False

        return True
