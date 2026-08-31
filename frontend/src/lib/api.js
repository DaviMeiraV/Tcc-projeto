const BASE = '/api'

export function getToken() {
  return localStorage.getItem('token')
}

export function setSessao(token, usuario) {
  localStorage.setItem('token', token)
  localStorage.setItem('usuario', JSON.stringify(usuario))
}

export function getUsuario() {
  try {
    return JSON.parse(localStorage.getItem('usuario'))
  } catch {
    return null
  }
}

export function limparSessao() {
  localStorage.removeItem('token')
  localStorage.removeItem('usuario')
}

function mensagemErro(corpo, status) {
  const d = corpo?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    const p = d[0]
    const campo = p?.loc?.slice(-1)[0]
    return campo ? `Campo "${campo}": ${p.msg}` : p?.msg || 'Dados inválidos.'
  }
  return `Erro ${status} ao comunicar com o servidor.`
}

async function requisicao(caminho, { method = 'GET', body, headers = {}, json = true } = {}) {
  const token = getToken()
  const cabecalhos = { ...headers }
  if (token) cabecalhos.Authorization = `Bearer ${token}`
  if (json && body !== undefined) cabecalhos['Content-Type'] = 'application/json'

  const resposta = await fetch(BASE + caminho, {
    method,
    headers: cabecalhos,
    body: json && body !== undefined ? JSON.stringify(body) : body,
  })

  if (resposta.status === 401) {
    limparSessao()
    if (!location.pathname.startsWith('/login')) location.href = '/login'
    throw new Error('Sessão expirada. Entre novamente.')
  }
  if (resposta.status === 204) return null

  let corpo = null
  try {
    corpo = await resposta.json()
  } catch {
    /* resposta sem corpo */
  }
  if (!resposta.ok) throw new Error(mensagemErro(corpo, resposta.status))
  return corpo
}

export const api = {
  cadastro: (dados) => requisicao('/auth/cadastro', { method: 'POST', body: dados }),
  login: (dados) => requisicao('/auth/login', { method: 'POST', body: dados }),
  eu: () => requisicao('/auth/eu'),
  listarAvaliacoes: () => requisicao('/avaliacoes'),
  detalharAvaliacao: (id) => requisicao(`/avaliacoes/${id}`),
  removerAvaliacao: (id) => requisicao(`/avaliacoes/${id}`, { method: 'DELETE' }),
  enviarAvaliacao: (formData) =>
    requisicao('/avaliacoes', { method: 'POST', body: formData, json: false }),
}
