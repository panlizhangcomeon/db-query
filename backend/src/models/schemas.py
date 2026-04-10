"""
Pydantic Models for API Requests and Responses

All models use camelCase for JSON serialization.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    code: int = 200
    message: str = "success"
    data: Any = None


# =============================================================================
# Connection Models
# =============================================================================

class ConnectionCreateRequest(BaseModel):
    """Request model for creating a MySQL server connection."""
    name: str = Field(..., description="User-friendly connection name")
    url: str = Field(..., description="MySQL connection URL (mysql://user:pass@host:port)")


class ConnectionResponse(BaseModel):
    """Response model for a connection."""
    id: int
    name: str
    host: str
    port: int
    username: str
    createdAt: str
    updatedAt: str

    class Config:
        from_attributes = True


# =============================================================================
# Database Models
# =============================================================================

class DatabaseResponse(BaseModel):
    """Response model for a database."""
    id: int
    connectionId: int
    name: str
    charset: str | None = None
    collation: str | None = None
    cachedAt: str


# =============================================================================
# Table/Column Models
# =============================================================================

class ColumnResponse(BaseModel):
    """Response model for a column."""
    name: str
    dataType: str
    isNullable: bool
    isPrimaryKey: bool
    defaultValue: str | None = None
    extra: str | None = None
    comment: str = ""


class TableResponse(BaseModel):
    """Response model for a table or view."""
    id: int
    name: str
    type: str
    columns: list[ColumnResponse] = []


# =============================================================================
# Query Models
# =============================================================================

class QueryRequest(BaseModel):
    """Request model for SQL query execution."""
    connectionId: int = Field(..., description="Connection ID")
    database: str | None = Field(None, description="Default database to use")
    sql: str = Field(..., description="SQL query statement")


class NaturalQueryRequest(BaseModel):
    """Request model for natural language query."""
    connectionId: int = Field(..., description="Connection ID")
    database: str | None = Field(None, description="Default database context")
    naturalLanguage: str = Field(..., description="Natural language query")


class QueryResponseData(BaseModel):
    """Response data for query results."""
    columns: list[str]
    rows: list[dict[str, Any]]
    rowCount: int
    executionTimeMs: float | None = None
    sql: str | None = None
    naturalLanguage: str | None = None
    generatedSql: str | None = None
    tablesUsed: list[str] | None = None


class QueryResponse(BaseModel):
    """Response model for query results."""
    code: int = 200
    message: str = "success"
    data: QueryResponseData | None = None


# =============================================================================
# Legacy Models (for backward compatibility)
# =============================================================================

class DatabaseConnectionCreate(BaseModel):
    """Legacy: Request model for adding a database connection."""
    url: str = Field(..., description="Database connection URL")


class DatabaseConnectionResponse(BaseModel):
    """Legacy: Response model for a database connection."""
    id: int
    name: str
    url: str
    createdAt: str
    updatedAt: str

    class Config:
        from_attributes = True


class ColumnInfo(BaseModel):
    """Legacy: Column information schema."""
    name: str
    type: str
    nullable: bool
    isPrimaryKey: bool
    comment: str = ""


class TableMetadata(BaseModel):
    """Legacy: Table or view metadata."""
    name: str
    type: str
    columns: list[ColumnInfo] = []


class DatabaseMetadataResponse(BaseModel):
    """Legacy: Response model for database metadata."""
    name: str
    tables: list[TableMetadata] = []
    views: list[TableMetadata] = []


class QueryResponseDataLegacy(BaseModel):
    """Legacy: Response data for query results."""
    columns: list[str]
    rows: list[list[Any]]
    rowCount: int
    sql: str
    executionTime: float | None = None
    naturalQuery: str | None = None
