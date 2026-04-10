"""
MySQL Connection Pool Manager

Handles MySQL connections using aiomysql for async operations.
"""
import aiomysql
from typing import Any


class MySQLPoolManager:
    """Manages MySQL connection pools per server."""

    _pools: dict[int, aiomysql.Pool] = {}

    @classmethod
    async def get_pool(cls, connection_id: int, host: str, port: int, username: str, password: str) -> aiomysql.Pool:
        """
        Get or create a connection pool for a MySQL server.

        Args:
            connection_id: The local connection ID
            host: MySQL server host
            port: MySQL server port
            username: Database username
            password: Database password

        Returns:
            aiomysql connection pool
        """
        if connection_id not in cls._pools or cls._pools[connection_id] is None:
            cls._pools[connection_id] = await aiomysql.create_pool(
                host=host,
                port=port,
                user=username,
                password=password,
                autocommit=True,
                charset="utf8mb4",
                connect_timeout=30,
            )
        return cls._pools[connection_id]

    @classmethod
    async def close_pool(cls, connection_id: int) -> None:
        """Close the connection pool for a connection."""
        if connection_id in cls._pools and cls._pools[connection_id] is not None:
            cls._pools[connection_id].close()
            await cls._pools[connection_id].wait_closed()
            cls._pools[connection_id] = None

    @classmethod
    async def close_all_pools(cls) -> None:
        """Close all connection pools."""
        for conn_id in list(cls._pools.keys()):
            await cls.close_pool(conn_id)

    @classmethod
    async def execute_query(
        cls,
        connection_id: int,
        host: str,
        port: int,
        username: str,
        password: str,
        sql: str,
        database: str | None = None
    ) -> dict[str, Any]:
        """
        Execute a query on a MySQL server.

        Args:
            connection_id: The local connection ID
            host: MySQL server host
            port: MySQL server port
            username: Database username
            password: Database password
            sql: SQL query to execute
            database: Optional database name to use

        Returns:
            Query result with columns and rows
        """
        pool = await cls.get_pool(connection_id, host, port, username, password)

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if database:
                    await cursor.execute(f"USE `{database}`")

                await cursor.execute(sql)
                rows = await cursor.fetchall()

                # Get column names from the first row's keys, or empty list if no rows
                columns = list(rows[0].keys()) if rows else []

                return {
                    "columns": columns,
                    "rows": [dict(row) for row in rows],
                    "rowCount": len(rows)
                }

    @classmethod
    async def get_databases(
        cls,
        connection_id: int,
        host: str,
        port: int,
        username: str,
        password: str
    ) -> list[dict[str, Any]]:
        """
        Get all databases on a MySQL server using SHOW DATABASES.

        Args:
            connection_id: The local connection ID
            host: MySQL server host
            port: MySQL server port
            username: Database username
            password: Database password

        Returns:
            List of database info dictionaries
        """
        pool = await cls.get_pool(connection_id, host, port, username, password)

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SHOW DATABASES")
                rows = await cursor.fetchall()

                databases = []
                for row in rows:
                    db_name = row.get("Database")
                    # Skip system databases
                    if db_name not in ("information_schema", "mysql", "performance_schema", "sys"):
                        databases.append({
                            "name": db_name,
                            "charset": None,
                            "collation": None
                        })

                return databases

    @classmethod
    async def get_tables(
        cls,
        connection_id: int,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str
    ) -> list[dict[str, Any]]:
        """
        Get all tables and views in a database.

        Args:
            connection_id: The local connection ID
            host: MySQL server host
            port: MySQL server port
            username: Database username
            password: Database password
            database: Database name

        Returns:
            List of table info dictionaries
        """
        pool = await cls.get_pool(connection_id, host, port, username, password)

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(f"USE `{database}`")

                tables = []

                # Use SHOW FULL TABLES to get tables and views
                # Table_type: BASE TABLE for tables, VIEW for views
                await cursor.execute("SHOW FULL TABLES")
                rows = await cursor.fetchall()
                for row in rows:
                    table_type = row.get("Table_type", "BASE TABLE")
                    tables.append({
                        "name": row.get(f"Tables_in_{database}"),
                        "type": "view" if table_type == "VIEW" else "table"
                    })

                return tables

    @classmethod
    async def get_columns(
        cls,
        connection_id: int,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        table: str
    ) -> list[dict[str, Any]]:
        """
        Get column metadata for a table.

        Args:
            connection_id: The local connection ID
            host: MySQL server host
            port: MySQL server port
            username: Database username
            password: Database password
            database: Database name
            table: Table name

        Returns:
            List of column info dictionaries
        """
        pool = await cls.get_pool(connection_id, host, port, username, password)

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(f"USE `{database}`")
                await cursor.execute(f"SHOW FULL COLUMNS FROM `{table}`")
                rows = await cursor.fetchall()

                columns = []
                for row in rows:
                    columns.append({
                        "name": row["Field"],
                        "dataType": row["Type"],
                        "isNullable": row["Null"] == "YES",
                        "isPrimaryKey": row["Key"] == "PRI",
                        "defaultValue": row["Default"],
                        "extra": row["Extra"],
                        "comment": row["Comment"]
                    })

                return columns

    @classmethod
    async def test_connection(
        cls,
        host: str,
        port: int,
        username: str,
        password: str
    ) -> bool:
        """
        Test if a MySQL connection is valid.

        Args:
            host: MySQL server host
            port: MySQL server port
            username: Database username
            password: Database password

        Returns:
            True if connection is successful, False otherwise
        """
        import asyncio

        temp_pool = None
        try:
            temp_pool = await aiomysql.create_pool(
                host=host,
                port=port,
                user=username,
                password=password,
                connect_timeout=10,
            )

            async with temp_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    return result is not None
        except Exception:
            return False
        finally:
            if temp_pool:
                temp_pool.close()
                await temp_pool.wait_closed()
