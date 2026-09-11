import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../lib/api'
import { ESPORTES, rotuloDe } from '../lib/opcoes'

export default function Historico() {
  const [itens, setItens] = useState(null)
  const [erro, setErro] = useState('')

  function carregar() {
    api.listarAvaliacoes().then(setItens).catch((e) => setErro(e.message))
  }

  useEffect(carregar, [])

  async function remover(id) {
    if (!confirm('Excluir este envio? A ação não pode ser desfeita.')) return
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
            <h1>Formulários enviados</h1>
            <p>Registros de coleta já enviados por esta conta.</p>
          </div>
          <Link to="/formulario" className="btn primario" style={{ textDecoration: 'none' }}>Novo formulário</Link>
        </div>

        {erro && <div className="alerta" style={{ marginTop: 20 }}>{erro}</div>}

        <div className="secao">
          {itens === null && <p className="vazio">Carregando…</p>}
          {itens?.length === 0 && (
            <p className="vazio">Nenhum formulário enviado ainda.</p>
          )}
          {itens?.length > 0 && (
            <table className="tabela">
              <thead>
                <tr>
                  <th>#</th><th>Data do envio</th><th>Esporte</th><th>Histórico de treino</th><th />
                </tr>
              </thead>
              <tbody>
                {itens.map((a) => (
                  <tr key={a.id}>
                    <td>{a.id}</td>
                    <td>{new Date(a.criado_em).toLocaleString('pt-BR')}</td>
                    <td>{rotuloDe(ESPORTES, a.esporte)}</td>
                    <td>{a.csv_nome_original || '—'}</td>
                    <td style={{ textAlign: 'right' }}>
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
