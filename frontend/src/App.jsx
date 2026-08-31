import { Navigate, NavLink, Outlet, Route, Routes, useNavigate } from 'react-router-dom'

import { Cadastro, Login } from './pages/Autenticacao'
import Formulario from './pages/Formulario'
import Historico from './pages/Historico'
import Resultado from './pages/Resultado'
import { getToken, getUsuario, limparSessao } from './lib/api'

function Protegido() {
  if (!getToken()) return <Navigate to="/login" replace />
  return (
    <>
      <Topo />
      <Outlet />
    </>
  )
}

function Topo() {
  const navegar = useNavigate()
  const usuario = getUsuario()

  function sair() {
    limparSessao()
    navegar('/login', { replace: true })
  }

  return (
    <header className="topo">
      <div className="marca">Predição de Risco de Lesão</div>
      <nav>
        <NavLink to="/formulario" className={({ isActive }) => (isActive ? 'ativo' : '')}>Nova avaliação</NavLink>
        <NavLink to="/historico" className={({ isActive }) => (isActive ? 'ativo' : '')}>Histórico</NavLink>
        <span style={{ fontSize: 14 }}>{usuario?.nome}</span>
        <button type="button" onClick={sair}>Sair</button>
      </nav>
    </header>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/cadastro" element={<Cadastro />} />
      <Route element={<Protegido />}>
        <Route path="/formulario" element={<Formulario />} />
        <Route path="/historico" element={<Historico />} />
        <Route path="/resultado/:id" element={<Resultado />} />
      </Route>
      <Route path="*" element={<Navigate to={getToken() ? '/formulario' : '/login'} replace />} />
    </Routes>
  )
}
