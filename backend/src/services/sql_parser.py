"""
SQL Parser Service

Handles SQL parsing and validation using sqlglot.
"""
import re
from typing import Any

import sqlglot
from sqlglot import exp

# 与执行端 MySQL 一致；反引号标识符必须用 mysql 方言解析
_SQL_DIALECT = "mysql"


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

        cleaned = SQLParserService._clean_sql(sql)

        try:
            parsed = sqlglot.parse_one(cleaned, dialect=_SQL_DIALECT)
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
        parsed = sqlglot.parse_one(cleaned_sql, dialect=_SQL_DIALECT)

        # Check if already has LIMIT
        if parsed.find(exp.Limit):
            return cleaned_sql

        # Add LIMIT using sqlglot
        limit_clause = exp.Limit(expression=exp.Literal.number(limit))
        parsed.set("limit", limit_clause)

        return parsed.sql(dialect=_SQL_DIALECT)

    @staticmethod
    def _clean_sql(sql: str) -> str:
        """
        Clean SQL by removing semicolons, newlines, ANSI codes, and invisible chars.

        Args:
            sql: Raw SQL string

        Returns:
            Cleaned SQL string
        """
        # BOM、零宽字符（部分模型或终端会夹带）
        sql = sql.replace("\ufeff", "")
        sql = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", sql)

        # ESC 序列（含着色/下划线），以及偶发的裸 CSI 片段
        sql = re.sub(r"\x1b\[[0-9;]*[mK]", "", sql)
        sql = re.sub(r"\x1b\][^\x07]*\x07", "", sql)  # OSC
        # 粘贴时 ESC 丢失时残留的常见 SGR（如 [4m 下划线、[0m 重置）
        sql = re.sub(r"\[[0-9]{1,2}m", "", sql)

        # Remove markdown code blocks
        sql = re.sub(r"```[\w]*", "", sql)
        sql = re.sub(r"```", "", sql)

        # Remove semicolons and whitespace around them
        sql = re.sub(r"\s*;\s*", " ", sql)

        # Remove trailing semicolon
        sql = sql.rstrip().rstrip(";").rstrip()

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
