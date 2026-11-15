/**
 * Every error from the API is RFC 9457 Problem Details with a stable `code`, so the interface branches on the
 * code and shows the detail the server wrote, instead of guessing from status numbers.
 */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly body: Record<string, unknown>

  constructor(status: number, body: Record<string, unknown>) {
    super(typeof body.detail === 'string' && body.detail ? body.detail : `The server answered ${status}.`)
    this.status = status
    this.code = typeof body.code === 'string' ? body.code : 'UNKNOWN'
    this.body = body
  }

  get fieldErrors(): { field: string; message: string }[] {
    return Array.isArray(this.body.fields) ? (this.body.fields as { field: string; message: string }[]) : []
  }
}

type TokenSource = () => string | null

let currentToken: TokenSource = () => null
let onExpired: () => void = () => {}

/** Wired once by the session provider: where the token comes from and what to do when it stops working. */
export function connectSession(token: TokenSource, expired: () => void) {
  currentToken = token
  onExpired = expired
}

type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface RequestOptions {
  method?: Method
  /** A plain object is sent as JSON; FormData is sent as a file upload. */
  body?: unknown
  query?: Record<string, string | number | boolean | null | undefined>
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = currentToken()
  const headers: Record<string, string> = { Accept: 'application/json' }
  const isUpload = options.body instanceof FormData

  if (options.body !== undefined && !isUpload) {
    headers['Content-Type'] = 'application/json'
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(withQuery(path, options.query), {
    method: options.method ?? (options.body === undefined ? 'GET' : 'POST'),
    headers,
    body: isUpload ? (options.body as FormData) : options.body === undefined ? undefined : JSON.stringify(options.body),
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    if (response.status === 401 && token) {
      onExpired()
    }
    throw new ApiError(response.status, body)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

function withQuery(path: string, query: RequestOptions['query']): string {
  if (!query) {
    return path
  }

  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== null && value !== undefined && value !== '') {
      params.set(key, String(value))
    }
  }

  const text = params.toString()
  return text ? `${path}?${text}` : path
}
