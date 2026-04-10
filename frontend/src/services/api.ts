/**
 * API Service for AI Database Query Tool
 */
import type {
  ApiResponse,
  Connection,
  ConnectionCreateRequest,
  ConnectionCreateResult,
  Database,
  Table,
  Column,
  QueryRequest,
  QueryResult,
  NaturalQueryRequest,
} from '../types';

const API_BASE_URL = '/api/v1';

// =============================================================================
// Connection Management
// =============================================================================

export async function createConnection(
  request: ConnectionCreateRequest
): Promise<ApiResponse<ConnectionCreateResult>> {
  const response = await fetch(`${API_BASE_URL}/connections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return response.json();
}

export async function listConnections(): Promise<ApiResponse<{ connections: Connection[] }>> {
  const response = await fetch(`${API_BASE_URL}/connections`);
  return response.json();
}

export async function getConnection(
  connectionId: number
): Promise<ApiResponse<Connection>> {
  const response = await fetch(`${API_BASE_URL}/connections/${connectionId}`);
  return response.json();
}

export async function deleteConnection(
  connectionId: number
): Promise<ApiResponse<{ deleted: boolean }>> {
  const response = await fetch(`${API_BASE_URL}/connections/${connectionId}`, {
    method: 'DELETE',
  });
  return response.json();
}

// =============================================================================
// Database Discovery
// =============================================================================

export async function getConnectionDatabases(
  connectionId: number
): Promise<ApiResponse<{ databases: Database[] }>> {
  const response = await fetch(`${API_BASE_URL}/connections/${connectionId}/databases`);
  return response.json();
}

export async function getDatabaseTables(
  connectionId: number,
  database: string
): Promise<ApiResponse<{ tables: Table[] }>> {
  const response = await fetch(
    `${API_BASE_URL}/connections/${connectionId}/databases/${encodeURIComponent(database)}/tables`
  );
  return response.json();
}

export async function getTableColumns(
  connectionId: number,
  database: string,
  table: string
): Promise<ApiResponse<{ columns: Column[] }>> {
  const response = await fetch(
    `${API_BASE_URL}/connections/${connectionId}/databases/${encodeURIComponent(database)}/tables/${encodeURIComponent(table)}/columns`
  );
  return response.json();
}

// =============================================================================
// Query Execution
// =============================================================================

export async function executeQuery(
  request: QueryRequest
): Promise<ApiResponse<QueryResult>> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return response.json();
}

export async function executeNaturalQuery(
  request: NaturalQueryRequest
): Promise<ApiResponse<QueryResult>> {
  const response = await fetch(`${API_BASE_URL}/query/natural`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return response.json();
}

// =============================================================================
// Legacy API (backward compatibility)
// =============================================================================

export async function listDatabasesLegacy(): Promise<ApiResponse<unknown[]>> {
  const response = await fetch(`${API_BASE_URL}/dbs`);
  return response.json();
}

export async function addDatabaseLegacy(
  name: string,
  request: { url: string }
): Promise<ApiResponse<unknown>> {
  const response = await fetch(`${API_BASE_URL}/dbs/${name}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return response.json();
}
