import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api } from '../lib/api'
import { ESPORTES, ROTULOS_RISCO, rotuloDe } from '../lib/opcoes'

const CORES = {
  baixo: 'var(--ok)',
  moderado: 'var(--atencao)',
  alto: 'var(--alto)',
  muito_alto: 'var(--critico)',
}

export default function Historico() {
  const navegar = useNavigate()
  const [itens, setItens] = useState(null)
  const [erro, setErro] = useState('')

  function carregar() {
    api.listarAvaliacoes().then(setItens).catch((e) => setErro(e.message))
  }

  useEffect(carregar, [])

  async function remover(id) {
    if (!confirm('Excluir esta avaliação? A ação não pode ser desfeita.')) return
    try {
      await api.removerAvaliacao(id)
      carregar()
    } catch (e) {
      setErro(e.message)
    }
  }

  return (
    <div className="pagina">
      <div className="cartao">
        <div className="cabecalho" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
          <div>
            <h1>Histórico de avaliações</h1>
            <p>Acompanhe a evolução do risco estimado ao longo do tempo.</p>
          </div>
          <Link to="/formulario" className="btn primario" style={{ textDecoration: 'none' }}>Nova avaliação</Link>
        </div>

        {erro && <div className="alerta" style={{ marginTop: 20 }}>{erro}</div>}

        <div className="secao">
          {itens === null && <p className="vazio">Carregando…</p>}
          {itens?.length === 0 && (
            <p className="vazio">Nenhuma avaliação registrada ainda. Preencha o formulário para gerar a primeira análise.</p>
          )}
          {itens?.length > 0 && (
            <table className="tabela">
              <thead>
                <tr>
                  <th>#</th><th>Data</th><th>Esporte</th><th>ACWR</th><th>Escore</th><th>Classificação</th><th />
                </tr>
              </thead>
              <tbody>
                {itens.map((a) => (
                  <tr key={a.id}>
                    <td>{a.id}</td>
                    <td>{new Date(a.criado_em).toLocaleString('pt-BR')}</td>
                    <td>{rotuloDe(ESPORTES, a.esporte)}</td>
                    <td>{a.acwr?.toFixed(2) ?? '—'}</td>
                    <td><b>{a.score_risco != null ? Math.round(a.score_risco) : '—'}</b></td>
                    <td>
                      <span className="etiqueta" style={{ background: CORES[a.classificacao] }}>
                        {ROTULOS_RISCO[a.classificacao] ?? '—'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <button type="button" className="btn secundario" onClick={() => navegar(`/resultado/${a.id}`)}>
                        Abrir
                      </button>{' '}
                      <button type="button" className="remover" onClick={() => remover(a.id)}>Excluir</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
