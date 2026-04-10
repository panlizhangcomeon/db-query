"""
Connection Service

Handles MySQL connection URL parsing, database discovery, and metadata caching.
"""
import re
from dataclasses import dataclass
from typing import Any

from src.database.sqlite_db import (
    ConnectionRepository,
    DiscoveredDatabaseRepository,
    TableMetadataRepository,
    ColumnMetadataRepository,
)
from src.database.mysql_pool import MySQLPoolManager
from src.services.encryption import Encryptor


@dataclass
class ParsedConnectionUrl:
    """Parsed MySQL connection URL components."""
    host: str
    port: int
    username: str
    password: str
    database: str | None


class ConnectionService:
    """Service for managing MySQL server connections."""

    @staticmethod
    def parse_mysql_url(url: str) -> ParsedConnectionUrl:
        """
        Parse a MySQL connection URL.

        URL format: mysql://user:password@host:port/database

        Args:
            url: MySQL connection URL

        Returns:
            ParsedConnectionUrl with components

        Raises:
            ValueError: If URL format is invalid
        """
        # Regex to parse MySQL URL
        pattern = r"mysql://(?:(?P<username>[^:@]+)(?::(?P<password>[^@]*))?@)?(?P<host>[^:@]+)(?::(?P<port>\d+))?(?:/(?P<database>[^?]*))?(?:\?.*)?"
        match = re.match(pattern, url)

        if not match:
            raise ValueError(f"Invalid MySQL URL format: {url}")

        host = match.group("host")
        if not host:
            raise ValueError("URL must include a host")

        username = match.group("username") or "root"
        password = match.group("password") or ""
        port = int(match.group("port")) if match.group("port") else 3306
        database = match.group("database")

        return ParsedConnectionUrl(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database
        )

    @staticmethod
    async def create_connection(name: str, url: str) -> dict[str, Any]:
        """
        Create a new MySQL server connection.

        Args:
            name: User-friendly connection name
            url: MySQL connection URL

        Returns:
            Connection info with discovered databases

        Raises:
            ValueError: If URL is invalid or connection fails
        """
        # Parse URL
        parsed = ConnectionService.parse_mysql_url(url)

        # Test connection
        is_connected = await MySQLPoolManager.test_connection(
            host=parsed.host,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password
        )

        if not is_connected:
            raise ValueError("Failed to connect to MySQL server. Please check credentials and network.")

        # Encrypt password for storage
        encrypted_password = Encryptor.encrypt(parsed.password)

        # Create connection record
        connection = ConnectionRepository.create(
            name=name,
            db_type="mysql",
            host=parsed.host,
            port=parsed.port,
            username=parsed.username,
            password_encrypted=encrypted_password
        )

        connection_id = connection["id"]

        # Discover databases and cache metadata
        databases = await ConnectionService._discover_and_cache_databases(connection_id, parsed)

        return {
            "connectionId": connection_id,
            "name": name,
            "host": parsed.host,
            "port": parsed.port,
            "databases": [db["name"] for db in databases]
        }

    @staticmethod
    async def _discover_and_cache_databases(
        connection_id: int,
        parsed: ParsedConnectionUrl
    ) -> list[dict[str, Any]]:
        """Discover databases on MySQL server and cache metadata."""
        # Get all databases
        databases = await MySQLPoolManager.get_databases(
            connection_id=connection_id,
            host=parsed.host,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password
        )

        cached_databases = []
        for db_info in databases:
            db_name = db_info["name"]

            # Cache database
            cached_db = DiscoveredDatabaseRepository.upsert(
                connection_id=connection_id,
                name=db_name,
                charset=db_info.get("charset"),
                collation=db_info.get("collation")
            )

            # Discover and cache tables
            await ConnectionService._discover_and_cache_tables(
                connection_id=connection_id,
                host=parsed.host,
                port=parsed.port,
                username=parsed.username,
                password=parsed.password,
                database_id=cached_db["id"],
                database=db_name
            )

            cached_databases.append(cached_db)

        return cached_databases

    @staticmethod
    async def _discover_and_cache_tables(
        connection_id: int,
        host: str,
        port: int,
        username: str,
        password: str,
        database_id: int,
        database: str
    ) -> None:
        """Discover tables in a database and cache metadata."""
        # Get all tables
        tables = await MySQLPoolManager.get_tables(
            connection_id=connection_id,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database
        )

        for table_info in tables:
            table_name = table_info["name"]
            table_type = table_info["type"]

            # Cache table
            cached_table = TableMetadataRepository.upsert(
                database_id=database_id,
                name=table_name,
                table_type=table_type
            )

            # Get and cache columns
            columns = await MySQLPoolManager.get_columns(
                connection_id=connection_id,
                host=host,
                port=port,
                username=username,
                password=password,
                database=database,
                table=table_name
            )

            ColumnMetadataRepository.bulk_insert(
                table_id=cached_table["id"],
                columns=columns
            )

    @staticmethod
    async def get_connection_databases(connection_id: int) -> list[dict[str, Any]]:
        """Get all discovered databases for a connection."""
        return DiscoveredDatabaseRepository.get_by_connection(connection_id)

    @staticmethod
    async def get_database_tables(connection_id: int, database_name: str) -> list[dict[str, Any]]:
        """Get all tables for a database."""
        # Get database
        db = DiscoveredDatabaseRepository.get_by_name(connection_id, database_name)
        if not db:
            return []

        # Get tables from cache
        tables = TableMetadataRepository.get_by_database(db["id"])

        # If cache is empty, refresh from MySQL
        if not tables:
            # Get connection credentials
            connection = ConnectionRepository.get_by_id(connection_id)
            if not connection:
                return []

            host, port, username, password = ConnectionService.get_connection_credentials(connection)

            # Discover and cache tables
            await ConnectionService._discover_and_cache_tables(
                connection_id=connection_id,
                host=host,
                port=port,
                username=username,
                password=password,
                database_id=db["id"],
                database=database_name
            )

            # Get tables from cache again
            tables = TableMetadataRepository.get_by_database(db["id"])

        result = []
        for table in tables:
            # Get columns for this table
            columns = ColumnMetadataRepository.get_by_table(table["id"])
            result.append({
                "id": table["id"],
                "name": table["name"],
                "type": table["type"],
                "columns": columns
            })

        return result

    @staticmethod
    async def get_table_columns(connection_id: int, database_name: str, table_name: str) -> list[dict[str, Any]]:
        """Get all columns for a table."""
        # Get database
        db = DiscoveredDatabaseRepository.get_by_name(connection_id, database_name)
        if not db:
            return []

        # Get table
        table = TableMetadataRepository.get_by_name(db["id"], table_name)
        if not table:
            return []

        # Get columns
        return ColumnMetadataRepository.get_by_table(table["id"])

    @staticmethod
    def get_connection_credentials(connection: dict[str, Any]) -> tuple[str, str]:
        """
        Get decrypted credentials for a connection.

        Returns:
            Tuple of (host, port, username, password)
        """
        password = Encryptor.decrypt(connection["password_encrypted"])
        return (
            connection["host"],
            connection["port"],
            connection["username"],
            password
        )
