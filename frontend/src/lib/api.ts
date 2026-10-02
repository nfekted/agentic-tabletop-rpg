export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function req<T>(method: string, url: string, body?: unknown): Promise<T> {
  const init: RequestInit = { method }
  if (body instanceof FormData) {
    init.body = body
  } else if (body !== undefined) {
    init.headers = { 'Content-Type': 'application/json' }
    init.body = JSON.stringify(body)
  }
  let res: Response
  try {
    res = await fetch(`/api${url}`, init)
  } catch {
    throw new ApiError('Não foi possível falar com a API. Ela está rodando?', 0)
  }
  if (!res.ok) {
    let msg = `Erro ${res.status}`
    try {
      const data = await res.json()
      if (typeof data.detail === 'string') msg = data.detail
      else if (Array.isArray(data.detail)) msg = data.detail.map((d: { msg: string }) => d.msg).join('; ')
    } catch {
      /* corpo não era JSON */
    }
    throw new ApiError(msg, res.status)
  }
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(url: string) => req<T>('GET', url),
  post: <T>(url: string, body?: unknown) => req<T>('POST', url, body ?? {}),
  put: <T>(url: string, body?: unknown) => req<T>('PUT', url, body ?? {}),
  del: <T>(url: string) => req<T>('DELETE', url),
}

export const avatarUrl = (nome: string, v: number | null) =>
  v ? `/api/jogadores/${encodeURIComponent(nome)}/avatar?v=${v}` : null

export const tokenImagemUrl = (categoria: string, arquivo: string, v?: number) =>
  `/api/tokens/${categoria}/${encodeURIComponent(arquivo)}/imagem${v ? `?v=${v}` : ''}`
