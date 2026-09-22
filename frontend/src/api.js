export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: 'same-origin',
    ...options,
    headers: options.body instanceof FormData
      ? options.headers
      : { 'Content-Type': 'application/json', ...options.headers },
  })
  let body
  try { body = await response.json() } catch { body = null }
  if (!response.ok) {
    const detail = typeof body?.detail === 'string' ? body.detail : '请求未完成，请稍后重试。'
    throw new Error(detail)
  }
  return body
}

export function post(path, value) {
  return api(path, { method: 'POST', body: JSON.stringify(value) })
}

export function downloadText(text, filename) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
