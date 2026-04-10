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
  NaturalGenerateResult,
} from '../types';

const API_BASE_URL = '/api/v1';

function formatFastApiDetail(detail: unknown): string {
  if (detail == null) {
    return '';
  }
  if (typeof detail === 'string') {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item: { msg?: string; loc?: unknown[] }) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          return String(item.msg);
        }
        return JSON.stringify(item);
      })
      .join('；');
  }
  if (typeof detail === 'object' && detail !== null && 'message' in detail) {
    return String((detail as { message: unknown }).message);
  }
  return JSON.stringify(detail);
}

/** 将 HTTP 错误体 `{ detail }` 转为带 code/message 的 ApiResponse，便于界面展示 */
async function readApiResponse<T>(response: Response): Promise<ApiResponse<T>> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return {
      code: response.status,
      message: response.statusText || '请求失败',
      data: null,
    };
  }
  if (!response.ok) {
    const b = body as { detail?: unknown; message?: string };
    const msg = formatFastApiDetail(b.detail) || b.message || response.statusText || '请求失败';
    return {
      code: response.status,
      message: msg,
      data: null,
    };
  }
  return body as ApiResponse<T>;
}

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
  return readApiResponse<QueryResult>(response);
}

/** 仅生成 SQL，不执行（用户需在左侧点「执行查询」） */
export async function generateNaturalSql(
  request: NaturalQueryRequest
): Promise<ApiResponse<NaturalGenerateResult>> {
  const response = await fetch(`${API_BASE_URL}/query/natural/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return readApiResponse<NaturalGenerateResult>(response);
}

/** 生成并立即执行（兼容旧客户端） */
export async function executeNaturalQuery(
  request: NaturalQueryRequest
): Promise<ApiResponse<QueryResult>> {
  const response = await fetch(`${API_BASE_URL}/query/natural`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return readApiResponse<QueryResult>(response);
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
