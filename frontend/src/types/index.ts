/**
 * TypeScript type definitions for AI Database Query Tool
 */

// API Response wrapper
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

// =============================================================================
// Connection Types
// =============================================================================

export interface Connection {
  id: number;
  name: string;
  host: string;
  port: number;
  username: string;
  createdAt: string;
  updatedAt: string;
}

export interface ConnectionCreateRequest {
  name: string;
  url: string;
}

export interface ConnectionCreateResult {
  connectionId: number;
  name: string;
  host: string;
  port: number;
  databases: string[];
}

// =============================================================================
// Database Types
// =============================================================================

export interface Database {
  id: number;
  connectionId: number;
  name: string;
  charset: string | null;
  collation: string | null;
  cachedAt: string;
}

// =============================================================================
// Table/Column Types
// =============================================================================

export interface Column {
  name: string;
  dataType: string;
  isNullable: boolean;
  isPrimaryKey: boolean;
  defaultValue: string | null;
  extra: string | null;
  comment: string;
}

export interface Table {
  id: number;
  name: string;
  type: 'table' | 'view';
  columns: Column[];
}

// =============================================================================
// Query Types
// =============================================================================

export interface QueryRequest {
  connectionId: number;
  database?: string;
  sql: string;
}

export interface NaturalQueryRequest {
  connectionId: number;
  database?: string;
  naturalLanguage: string;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  executionTimeMs?: number;
  sql?: string;
  naturalLanguage?: string;
  generatedSql?: string;
  tablesUsed?: string[];
}

// =============================================================================
// Legacy Types (for backward compatibility)
// =============================================================================

export interface DatabaseConnection {
  id: number;
  name: string;
  url: string;
  createdAt: string;
  updatedAt: string;
}

export interface TableMetadata {
  name: string;
  type: string;
  columns: Column[];
}

export interface DatabaseMetadata {
  name: string;
  tables: TableMetadata[];
  views: TableMetadata[];
}

export interface AddDatabaseRequest {
  url: string;
}
