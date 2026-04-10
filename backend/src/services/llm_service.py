"""
LLM Service

Handles natural language to SQL conversion using OpenAI-compatible APIs.
"""
import os
import re
from typing import Any

from openai import OpenAI


class LLMService:
    """Service for converting natural language to SQL using LLM."""

    def __init__(self, metadata: list[dict[str, Any]]):
        """
        Initialize with database metadata for context.

        Args:
            metadata: List of table metadata dictionaries with database info
        """
        self.metadata = metadata
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.api_base_url = os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.client = None
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base_url
            )

    def generate_sql(self, natural_query: str, database: str | None = None) -> str:
        """
        Convert natural language query to SQL.

        Args:
            natural_query: The natural language query
            database: Optional default database context

        Returns:
            Generated SQL string

        Raises:
            ValueError: If query cannot be converted
            RuntimeError: If LLM call fails or API key not set
        """
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")

        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        if not natural_query or not natural_query.strip():
            raise ValueError("Natural language query cannot be empty")

        # Build schema description from metadata
        schema_context = self._build_schema_context(database)

        # Create prompt for SQL generation
        prompt = self._build_prompt(natural_query, schema_context, database)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert SQL developer for MySQL. Given a natural language question (may be in Chinese) "
                            "and an EXACT database schema listing, output ONE valid SELECT statement only.\n"
                            "Rules:\n"
                            "- ONLY SELECT; never INSERT, UPDATE, DELETE, DDL, or multiple statements.\n"
                            "- Use ONLY column names that appear verbatim in the schema for each table. "
                            "Do NOT invent or assume common names (e.g. create_time, created_at, update_time, gmt_create) "
                            "if they are not listed. For 'earliest/latest', 'first submitted', '按时间排序', etc., "
                            "you MUST pick time/date columns from that table's listed columns (e.g. add_time, submit_time).\n"
                            "- Prefix every table with database name: `database`.`table` or database.table.\n"
                            "- If the question implies one specific business table (e.g. 补充协议 / agreement), prefer that table "
                            "when its columns fit the question; join other tables only when necessary and only using listed columns.\n"
                            "- Add LIMIT 100 if the query has no LIMIT.\n"
                            "- Output ONLY the SQL, no markdown, no explanation."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=1200,
            )

            sql = response.choices[0].message.content.strip()

            # Clean up markdown formatting
            sql = self._clean_sql(sql)

            # Validate that we got a SELECT statement
            if not sql.upper().startswith("SELECT"):
                raise ValueError(f"Generated SQL is not a SELECT statement: {sql}")

            return sql

        except Exception as e:
            if "api key" in str(e).lower():
                raise RuntimeError("API key is invalid or expired")
            raise RuntimeError(f"LLM call failed: {e}")

    def _build_schema_context(self, default_database: str | None = None) -> str:
        """Build a schema description string from metadata."""
        if not self.metadata:
            return "No schema information available."

        schema_lines = []
        for table in self.metadata:
            table_name = table.get("name", "unknown")
            table_type = table.get("type", "table")
            database = table.get("database", default_database or "unknown")
            columns = table.get("columns", [])

            # Use database.table format
            full_name = f"{database}.{table_name}"
            schema_lines.append(f"// {table_type}: {full_name}")

            if isinstance(columns, list):
                for col in columns:
                    if isinstance(col, dict):
                        col_name = col.get("name", "")
                        col_type = col.get("dataType") or col.get("type", "")
                        col_pk = " (PK)" if col.get("isPrimaryKey") else ""
                        col_nullable = " NULLABLE" if col.get("isNullable") else ""
                        col_comment = f"  -- {col.get('comment')}" if col.get("comment") else ""
                        schema_lines.append(f"  {col_name} {col_type}{col_pk}{col_nullable}{col_comment}")
                    elif isinstance(col, str):
                        schema_lines.append(f"  {col}")
            schema_lines.append("")

        return "\n".join(schema_lines)

    def _build_prompt(self, query: str, schema_context: str, database: str | None = None) -> str:
        """Build the prompt for SQL generation."""
        db_context = f"\nDefault database (use this prefix for tables): {database}" if database else ""
        return f"""Database Schema (every column below exists; do not use any column name not shown for that table):
{schema_context}
{db_context}

User question: {query}

Reply with the single MySQL SELECT statement:"""

    def _clean_sql(self, sql: str) -> str:
        """与 SQLParserService 一致，避免模型/终端夹带 ANSI 或不可见字符。"""
        from src.services.sql_parser import SQLParserService

        return SQLParserService._clean_sql(sql)

    @staticmethod
    def extract_table_names(sql: str) -> list[str]:
        """Extract table names from a SQL query."""
        # Simple regex to find database.table patterns
        pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, sql)
        return [f"{db}.{table}" for db, table in matches]
