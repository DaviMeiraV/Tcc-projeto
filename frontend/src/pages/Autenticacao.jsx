import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Campo } from '../components/Campos'
import { api, setSessao } from '../lib/api'

export function Login() {
  const navegar = useNavigate()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  async function enviar(e) {
    e.preventDefault()
    setErro('')
    setCarregando(true)
    try {
      const r = await api.login({ email, senha })
      setSessao(r.access_token, r.usuario)
      navegar('/formulario', { replace: true })
    } catch (erroLogin) {
      setErro(erroLogin.message)
      setCarregando(false)
    }
  }

  return (
    <div className="pagina">
      <form className="cartao auth" onSubmit={enviar}>
        <h1>Entrar</h1>
        <p className="ajuda">Sistema de predição de risco de lesão — TCC.</p>
        {erro && <div className="alerta">{erro}</div>}

        <Campo rotulo="E-mail" obrigatorio>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </Campo>
        <Campo rotulo="Senha" obrigatorio>
          <input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required autoComplete="current-password" />
        </Campo>

        <button className="btn primario" disabled={carregando}>{carregando ? 'Entrando…' : 'Entrar'}</button>
        <div className="alternar">
          Ainda não tem conta? <Link to="/cadastro">Cadastre-se</Link>
        </div>
      </form>
    </div>
  )
}

export function Cadastro() {
  const navegar = useNavigate()
  const [form, setForm] = useState({ nome: '', email: '', senha: '', confirmacao: '' })
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  const set = (chave) => (e) => setForm((f) => ({ ...f, [chave]: e.target.value }))

  async function enviar(e) {
    e.preventDefault()
    setErro('')
    if (form.senha.length < 6) return setErro('A senha deve ter pelo menos 6 caracteres.')
    if (form.senha !== form.confirmacao) return setErro('As senhas não coincidem.')

    setCarregando(true)
    try {
      const r = await api.cadastro({ nome: form.nome, email: form.email, senha: form.senha })
      setSessao(r.access_token, r.usuario)
      navegar('/formulario', { replace: true })
    } catch (erroCadastro) {
      setErro(erroCadastro.message)
      setCarregando(false)
    }
  }

  return (
    <div className="pagina">
      <form className="cartao auth" onSubmit={enviar}>
        <h1>Criar conta</h1>
        <p className="ajuda">Cadastre-se para registrar suas avaliações e acompanhar o histórico.</p>
        {erro && <div className="alerta">{erro}</div>}

        <Campo rotulo="Nome" obrigatorio>
          <input type="text" value={form.nome} onChange={set('nome')} required minLength={2} />
        </Campo>
        <Campo rotulo="E-mail" obrigatorio>
          <input type="email" value={form.email} onChange={set('email')} required autoComplete="email" />
        </Campo>
        <Campo rotulo="Senha" obrigatorio ajuda="Mínimo de 6 caracteres.">
          <input type="password" value={form.senha} onChange={set('senha')} required autoComplete="new-password" />
        </Campo>
        <Campo rotulo="Confirme a senha" obrigatorio>
          <input type="password" value={form.confirmacao} onChange={set('confirmacao')} required autoComplete="new-password" />
        </Campo>

        <button className="btn primario" disabled={carregando}>{carregando ? 'Criando…' : 'Criar conta'}</button>
        <div className="alternar">
          Já tem conta? <Link to="/login">Entrar</Link>
        </div>
      </form>
    </div>
  )
}
