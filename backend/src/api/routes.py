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


def _build_llm_table_metadata(table: dict, database_name: str, max_columns: int | None) -> dict:
    """
    Normalize table dict from ConnectionService for LLM context.
    Includes ALL columns by default so the model does not invent names (e.g. create_time vs add_time).
    """
    raw_cols = table.get("columns") or []
    if max_columns is not None and max_columns > 0:
        raw_cols = raw_cols[:max_columns]
    simplified_columns = []
    for col in raw_cols:
        comment = (col.get("comment") or "").strip()
        simplified_columns.append({
            "name": col.get("name", ""),
            "dataType": col.get("dataType") or col.get("type", ""),
            "isPrimaryKey": bool(col.get("isPrimaryKey")),
            "isNullable": bool(col.get("isNullable")),
            "comment": comment[:200] if comment else "",
        })
    return {
        "name": table["name"],
        "type": table.get("type", "table"),
        "database": database_name,
        "columns": simplified_columns,
    }


async def _generate_sql_for_natural_query(body: NaturalQueryRequest) -> str:
    """
    Build schema context, call LLM, validate SELECT-only, append LIMIT.
    Does not touch MySQL. Raises ValueError, RuntimeError; caller maps to HTTP.
    """
    import os

    from src.database.sqlite_db import ConnectionRepository
    from src.services.connection_service import ConnectionService
    from src.services.llm_service import LLMService
    from src.services.sql_parser import SQLParserService

    if not body.connectionId:
        raise HTTPException(status_code=400, detail="connectionId is required")
    if not body.naturalLanguage:
        raise HTTPException(status_code=400, detail="naturalLanguage is required")

    connection = ConnectionRepository.get_by_id(body.connectionId)
    if not connection:
        raise HTTPException(status_code=404, detail=f"Connection {body.connectionId} not found")

    max_cols_env = os.environ.get("LLM_SCHEMA_MAX_COLUMNS", "").strip()
    max_columns: int | None = int(max_cols_env) if max_cols_env.isdigit() else None

    target_database = body.database
    if target_database:
        databases = [{"name": target_database}]
    else:
        all_dbs = await ConnectionService.get_connection_databases(body.connectionId)
        databases = all_dbs[:3]

    all_metadata: list[dict] = []
    for db in databases:
        tables = await ConnectionService.get_database_tables(body.connectionId, db["name"])
        for table in tables:
            all_metadata.append(_build_llm_table_metadata(table, db["name"], max_columns))

    llm_service = LLMService(all_metadata)
    generated_sql = llm_service.generate_sql(body.naturalLanguage, database=body.database)
    SQLParserService.validate(generated_sql)
    return SQLParserService.add_limit(generated_sql)


@router.post("/query/natural/generate", response_model=ApiResponse)
async def generate_sql_from_natural_language(body: NaturalQueryRequest):
    """
    POST /api/v1/query/natural/generate
    仅根据自然语言生成 SQL（校验 SELECT + LIMIT），不执行查询。
    """
    from src.services.llm_service import LLMService

    try:
        sql_to_run = await _generate_sql_for_natural_query(body)
        return ApiResponse(
            code=200,
            message="Success",
            data={
                "generatedSql": sql_to_run,
                "tablesUsed": LLMService.extract_table_names(sql_to_run),
                "naturalLanguage": body.naturalLanguage,
            },
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/query/natural", response_model=ApiResponse)
async def execute_natural_query(body: NaturalQueryRequest):
    """
    POST /api/v1/query/natural
    Generate SQL from natural language and execute it (兼容旧调用；前端请用 /query/natural/generate + /query)。
    """
    from src.database.sqlite_db import ConnectionRepository, QueryHistoryRepository
    from src.database.mysql_pool import MySQLPoolManager
    from src.services.connection_service import ConnectionService
    from src.services.llm_service import LLMService

    generated_sql: str | None = None
    sql_to_run: str | None = None

    try:
        sql_to_run = await _generate_sql_for_natural_query(body)
        generated_sql = sql_to_run

        connection = ConnectionRepository.get_by_id(body.connectionId)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {body.connectionId} not found")

        host, port, username, password = ConnectionService.get_connection_credentials(connection)

        import time
        start_time = time.time()

        result = await MySQLPoolManager.execute_query(
            connection_id=body.connectionId,
            host=host,
            port=port,
            username=username,
            password=password,
            sql=sql_to_run,
            database=body.database
        )

        execution_time = (time.time() - start_time) * 1000

        QueryHistoryRepository.create(
            connection_id=body.connectionId,
            sql_text=sql_to_run,
            execution_time_ms=execution_time,
            row_count=result["rowCount"]
        )

        return ApiResponse(
            code=200,
            message="Success",
            data={
                "generatedSql": sql_to_run,
                "tablesUsed": LLMService.extract_table_names(sql_to_run),
                "columns": result["columns"],
                "rows": result["rows"],
                "rowCount": result["rowCount"],
                "executionTimeMs": execution_time,
                "naturalLanguage": body.naturalLanguage
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        import pymysql.err

        err = str(e)
        sql_for_user = sql_to_run or generated_sql
        if sql_for_user:
            detail = (
                f"{err}\n\n本次生成的 SQL（便于排查列名/表名是否与库中一致）:\n{sql_for_user}"
            )
        else:
            detail = err

        if isinstance(e, pymysql.err.Error):
            raise HTTPException(status_code=400, detail=detail)
        raise HTTPException(status_code=500, detail=detail)
