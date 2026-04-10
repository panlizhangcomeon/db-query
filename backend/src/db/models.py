"""
SQLAlchemy Models

Defines ORM models for database connections using SQLAlchemy.
"""
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class DatabaseConnectionModel(Base):
    """
    Database connection ORM model.

    Stores database connection configurations.
    """
    __tablename__ = "database_connections"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(255), unique=True, nullable=False)
    url: Mapped[str] = Column(Text, nullable=False)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    table_metadata: Mapped[list["DatabaseMetadataModel"]] = relationship(
        "DatabaseMetadataModel",
        back_populates="db_connection",
        cascade="all, delete-orphan"
    )
    query_history: Mapped[list["QueryHistoryModel"]] = relationship(
        "QueryHistoryModel",
        back_populates="db_connection",
        cascade="all, delete-orphan"
    )

    def to_dict(self, mask_password: bool = True) -> dict[str, Any]:
        """Convert model to dictionary."""
        url = self.url
        if mask_password and "@" in url:
            url = _mask_password_in_url(url)
        return {
            "id": self.id,
            "name": self.name,
            "url": url,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class DatabaseMetadataModel(Base):
    """
    Database metadata ORM model.

    Stores table and view metadata for database connections.
    """
    __tablename__ = "database_metadata"
    __table_args__ = (
        UniqueConstraint("db_connection_id", "table_name", name="uq_db_connection_table"),
    )

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    db_connection_id: Mapped[int] = Column(
        Integer,
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False
    )
    table_name: Mapped[str] = Column(String(255), nullable=False)
    table_type: Mapped[str] = Column(String(50), nullable=False)  # 'table' or 'view'
    columns: Mapped[str] = Column(Text, nullable=False)  # JSON string
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    db_connection: Mapped["DatabaseConnectionModel"] = relationship(
        "DatabaseConnectionModel",
        back_populates="metadata"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        import json
        return {
            "name": self.table_name,
            "type": self.table_type,
            "columns": json.loads(self.columns) if self.columns else [],
        }


class QueryHistoryModel(Base):
    """
    Query history ORM model.

    Stores query execution history.
    """
    __tablename__ = "query_history"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    db_connection_id: Mapped[int] = Column(
        Integer,
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False
    )
    query_type: Mapped[str] = Column(String(50), nullable=False)  # 'sql' or 'natural'
    query_text: Mapped[str] = Column(Text, nullable=False)
    generated_sql: Mapped[str | None] = Column(Text, nullable=True)
    result: Mapped[str | None] = Column(Text, nullable=True)  # JSON string
    error: Mapped[str | None] = Column(Text, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    # Relationships
    db_connection: Mapped["DatabaseConnectionModel"] = relationship(
        "DatabaseConnectionModel",
        back_populates="query_history"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        import json
        return {
            "id": self.id,
            "queryType": self.query_type,
            "queryText": self.query_text,
            "generatedSql": self.generated_sql,
            "result": json.loads(self.result) if self.result else None,
            "error": self.error,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


def _mask_password_in_url(url: str) -> str:
    """Mask password in database URL for security."""
    if "@" not in url:
        return url

    # Handle mysql://, postgresql://, etc.
    for db_type in ["mysql://", "postgresql://", "sqlite://", "mssql://"]:
        if db_type in url:
            rest = url[len(db_type):]
            if "@" in rest:
                credentials = rest.split("@")[0]
                if ":" in credentials:
                    parts = credentials.split(":")
                    masked = f"{parts[0]}:***"
                else:
                    masked = "***"
                return f"{db_type}{masked}@{rest.split('@')[1]}"
    return url
