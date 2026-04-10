"""
API Routes for Multi-Database Query Tool

All endpoints follow the /api/v1 prefix.
Supports:
- Connection management (MySQL server connections)
- Database discovery (all databases on a server)
- Cross-database SQL queries
- Natural language to SQL generation
"""
from fastapi import APIRouter, HTTPException, Path

from src.models.schemas import (
    ApiResponse,
    ConnectionCreateRequest,
    ConnectionResponse,
    DatabaseResponse,
    TableResponse,
    ColumnResponse,
    QueryRequest,
    QueryResponseData,
    NaturalQueryRequest,
    QueryResponse,
)

router = APIRouter()


# =============================================================================
# Connection Management
# =============================================================================

@router.post("/connections", response_model=ApiResponse)
async def create_connection(body: ConnectionCreateRequest):
    """
    POST /api/v1/connections
    Create a new MySQL server connection and discover all databases.
    """
    from src.services.connection_service import ConnectionService

    if not body.name:
        raise HTTPException(status_code=400, detail="Connection name is required")
    if not body.url:
        raise HTTPException(status_code=400, detail="Connection URL is required")

    try:
        result = await ConnectionService.create_connection(body.name, body.url)
        return ApiResponse(
            code=200,
            message="Connected successfully",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")


@router.get("/connections", response_model=ApiResponse)
async def list_connections():
    """
    GET /api/v1/connections
    List all saved MySQL server connections.
    """
    from src.database.sqlite_db import ConnectionRepository

    connections = ConnectionRepository.get_all()
    return ApiResponse(
        code=200,
        message="Success",
        data={"connections": connections}
    )


@router.get("/connections/{connection_id}", response_model=ApiResponse)
async def get_connection(connection_id: int = Path(..., description="Connection ID")):
    """
    GET /api/v1/connections/{connectionId}
    Get a specific connection by ID.
    """
    from src.database.sqlite_db import ConnectionRepository

    connection = ConnectionRepository.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")

    return ApiResponse(
        code=200,
        message="Success",
        data=connection
    )


@router.delete("/connections/{connection_id}", response_model=ApiResponse)
async def delete_connection(connection_id: int = Path(..., description="Connection ID")):
    """
    DELETE /api/v1/connections/{connectionId}
    Delete a saved connection.
    """
    from src.database.sqlite_db import ConnectionRepository
    from src.database.mysql_pool import MySQLPoolManager

    connection = ConnectionRepository.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")

    # Close any open pool
    await MySQLPoolManager.close_pool(connection_id)

    # Delete connection and all related data
    success = ConnectionRepository.delete(connection_id)

    if success:
        return ApiResponse(code=200, message="Connection deleted", data={"deleted": True})
    else:
        raise HTTPException(status_code=500, detail="Failed to delete connection")


# =============================================================================
# Database Discovery
# =============================================================================

@router.get("/connections/{connection_id}/databases", response_model=ApiResponse)
async def get_connection_databases(connection_id: int = Path(..., description="Connection ID")):
    """
    GET /api/v1/connections/{connectionId}/databases
    Get all discovered databases for a connection.
    """
    from src.database.sqlite_db import ConnectionRepository

    connection = ConnectionRepository.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")

    from src.services.connection_service import ConnectionService
    databases = await ConnectionService.get_connection_databases(connection_id)

    return ApiResponse(
        code=200,
        message="Success",
        data={"databases": databases}
    )


@router.get("/connections/{connection_id}/databases/{database}/tables", response_model=ApiResponse)
async def get_database_tables(
    connection_id: int = Path(..., description="Connection ID"),
    database: str = Path(..., description="Database name")
):
    """
    GET /api/v1/connections/{connectionId}/databases/{database}/tables
    Get all tables and views in a database.
    """
    from src.database.sqlite_db import ConnectionRepository

    connection = ConnectionRepository.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")

    from src.services.connection_service import ConnectionService
    tables = await ConnectionService.get_database_tables(connection_id, database)

    return ApiResponse(
        code=200,
        message="Success",
        data={"tables": tables}
    )


@router.get("/connections/{connection_id}/databases/{database}/tables/{table}/columns", response_model=ApiResponse)
async def get_table_columns(
    connection_id: int = Path(..., description="Connection ID"),
    database: str = Path(..., description="Database name"),
    table: str = Path(..., description="Table name")
):
    """
    GET /api/v1/connections/{connectionId}/databases/{database}/tables/{table}/columns
    Get column metadata for a table.
    """
    from src.database.sqlite_db import ConnectionRepository

    connection = ConnectionRepository.get_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")

    from src.services.connection_service import ConnectionService
    columns = await ConnectionService.get_table_columns(connection_id, database, table)

    return ApiResponse(
        code=200,
        message="Success",
        data={"columns": columns}
    )


# =============================================================================
# Query Execution
# =============================================================================

@router.post("/query", response_model=ApiResponse)
async def execute_query(body: QueryRequest):
    """
    POST /api/v1/query
    Execute a SQL query using a saved connection.
    """
    from src.database.sqlite_db import ConnectionRepository, QueryHistoryRepository
    from src.database.mysql_pool import MySQLPoolManager
    from src.services.connection_service import ConnectionService
    from src.services.sql_parser import SQLParserService

    if not body.connectionId:
        raise HTTPException(status_code=400, detail="connectionId is required")
    if not body.sql:
        raise HTTPException(status_code=400, detail="SQL is required")

    connection = ConnectionRepository.get_by_id(body.connectionId)
    if not connection:
        raise HTTPException(status_code=404, detail=f"Connection {body.connectionId} not found")

    try:
        # Validate SQL - must be SELECT
        parsed = SQLParserService.validate(body.sql)

        # Add LIMIT if not present
        sql = SQLParserService.add_limit(body.sql)

        # Get credentials
        host, port, username, password = ConnectionService.get_connection_credentials(connection)

        # Execute query
        import time
        start_time = time.time()

        result = await MySQLPoolManager.execute_query(
            connection_id=body.connectionId,
            host=host,
            port=port,
            username=username,
            password=password,
            sql=sql,
            database=body.database
        )

        execution_time = (time.time() - start_time) * 1000

        # Save to query history
        QueryHistoryRepository.create(
            connection_id=body.connectionId,
            sql_text=sql,
            execution_time_ms=execution_time,
            row_count=result["rowCount"]
        )

        return ApiResponse(
            code=200,
            message="Success",
            data={
                "columns": result["columns"],
                "rows": result["rows"],
                "rowCount": result["rowCount"],
                "executionTimeMs": execution_time
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.post("/query/natural", response_model=ApiResponse)
async def execute_natural_query(body: NaturalQueryRequest):
    """
    POST /api/v1/query/natural
    Generate SQL from natural language and execute it.
    """
    from src.database.sqlite_db import ConnectionRepository, DiscoveredDatabaseRepository, TableMetadataRepository, ColumnMetadataRepository, QueryHistoryRepository
    from src.database.mysql_pool import MySQLPoolManager
    from src.services.connection_service import ConnectionService
    from src.services.sql_parser import SQLParserService

    if not body.connectionId:
        raise HTTPException(status_code=400, detail="connectionId is required")
    if not body.naturalLanguage:
        raise HTTPException(status_code=400, detail="naturalLanguage is required")

    connection = ConnectionRepository.get_by_id(body.connectionId)
    if not connection:
        raise HTTPException(status_code=404, detail=f"Connection {body.connectionId} not found")

    try:
        # Get metadata for LLM context - only for the specified database (or first few if none specified)
        target_database = body.database

        # Get databases to search
        if target_database:
            # Only get metadata for the target database
            databases = [{"name": target_database}]
        else:
            # If no database specified, only get first 3 databases to avoid token limit
            all_dbs = await ConnectionService.get_connection_databases(body.connectionId)
            databases = all_dbs[:3]

        # Build metadata list for LLM (limit columns to essential info)
        all_metadata = []
        for db in databases:
            tables = await ConnectionService.get_database_tables(body.connectionId, db["name"])
            for table in tables:
                # Only include essential column info to reduce tokens
                simplified_columns = []
                for col in table.get("columns", [])[:10]:  # Limit to 10 columns per table
                    simplified_columns.append({
                        "name": col.get("name", ""),
                        "type": col.get("dataType", ""),
                        "comment": col.get("comment", "")[:50] if col.get("comment") else ""  # Truncate comment
                    })
                all_metadata.append({
                    "name": table["name"],
                    "type": table["type"],
                    "database": db["name"],
                    "columns": simplified_columns
                })

        # Generate SQL using LLM
        from src.services.llm_service import LLMService
        llm_service = LLMService(all_metadata)
        sql = llm_service.generate_sql(body.naturalLanguage, database=body.database)

        # Validate the generated SQL
        SQLParserService.validate(sql)

        # Add LIMIT if not present
        sql = SQLParserService.add_limit(sql)

        # Get credentials and execute
        host, port, username, password = ConnectionService.get_connection_credentials(connection)

        import time
        start_time = time.time()

        result = await MySQLPoolManager.execute_query(
            connection_id=body.connectionId,
            host=host,
            port=port,
            username=username,
            password=password,
            sql=sql,
            database=body.database
        )

        execution_time = (time.time() - start_time) * 1000

        # Save to query history
        QueryHistoryRepository.create(
            connection_id=body.connectionId,
            sql_text=sql,
            execution_time_ms=execution_time,
            row_count=result["rowCount"]
        )

        return ApiResponse(
            code=200,
            message="Success",
            data={
                "generatedSql": sql,
                "tablesUsed": LLMService.extract_table_names(sql),
                "columns": result["columns"],
                "rows": result["rows"],
                "rowCount": result["rowCount"],
                "executionTimeMs": execution_time,
                "naturalLanguage": body.naturalLanguage
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Natural query failed: {str(e)}")
