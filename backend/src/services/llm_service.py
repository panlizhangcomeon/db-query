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
                            "You are an expert SQL developer. Given a natural language query and a database schema, "
                            "generate a valid SQL SELECT statement. Only generate SELECT statements - never generate "
                            "INSERT, UPDATE, DELETE, or any other modifying statements. "
                            "ALWAYS include the database name as a prefix for all tables using the format: database.table "
                            "For example: SELECT * FROM mydb.users WHERE ... "
                            "Always add a LIMIT 100 clause unless the query already has one. "
                            "Return ONLY the SQL query, no explanations."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=500,
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
                        col_nullable = " NULL" if col.get("isNullable") else ""
                        col_comment = f" // {col.get('comment')}" if col.get("comment") else ""
                        schema_lines.append(f"  {col_name}: {col_type}{col_pk}{col_nullable}{col_comment}")
                    elif isinstance(col, str):
                        schema_lines.append(f"  {col}")
            schema_lines.append("")

        return "\n".join(schema_lines)

    def _build_prompt(self, query: str, schema_context: str, database: str | None = None) -> str:
        """Build the prompt for SQL generation."""
        db_context = f"\nDefault database: {database}" if database else ""
        return f"""Database Schema:
{schema_context}
{db_context}

Natural Language Query: {query}

Generate the SQL SELECT statement with database prefixes:"""

    def _clean_sql(self, sql: str) -> str:
        """Clean SQL by removing semicolons, newlines and ANSI codes."""
        import re

        # Remove ANSI color codes
        sql = re.sub(r'\x1b\[[0-9;]*m', '', sql)

        # Remove markdown code blocks
        sql = re.sub(r'```[\w]*', '', sql)
        sql = re.sub(r'```', '', sql)

        # Remove semicolons
        sql = re.sub(r'\s*;\s*', ' ', sql)
        sql = sql.rstrip().rstrip(';').rstrip()

        return sql.strip()

    @staticmethod
    def extract_table_names(sql: str) -> list[str]:
        """Extract table names from a SQL query."""
        # Simple regex to find database.table patterns
        pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, sql)
        return [f"{db}.{table}" for db, table in matches]
