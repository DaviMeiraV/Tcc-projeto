import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../lib/api'
import { ESPORTES, FASES, ROTULOS_ACWR, ROTULOS_RISCO, rotuloDe } from '../lib/opcoes'

const CORES_ACWR = {
  subcarga: 'var(--atencao)',
  ideal: 'var(--ok)',
  atencao: 'var(--alto)',
  risco: 'var(--critico)',
}

export default function Resultado() {
  const { id } = useParams()
  const [avaliacao, setAvaliacao] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    api.detalharAvaliacao(id).then(setAvaliacao).catch((e) => setErro(e.message))
  }, [id])

  if (erro) return <div className="pagina"><div className="cartao"><div className="alerta">{erro}</div></div></div>
  if (!avaliacao) return <div className="pagina"><div className="cartao"><p className="vazio">Carregando análise…</p></div></div>

  const d = avaliacao.detalhes || {}
  const acwr = d.acwr || {}
  const classe = avaliacao.classificacao || 'baixo'
  const maiorCarga = Math.max(1, ...(acwr.serie_diaria || []).map((p) => p.carga))

  return (
    <div className="pagina">
      <div className="cartao">
        <div className="cabecalho">
          <h1>Resultado da análise</h1>
          <p>
            Avaliação #{avaliacao.id} · {new Date(avaliacao.criado_em).toLocaleString('pt-BR')} ·{' '}
            {rotuloDe(ESPORTES, avaliacao.esporte)}
          </p>
        </div>

        <div className="secao">
          <div className="medidor">
            <div className={`selo nivel-${classe}`}>
              <b>{Math.round(avaliacao.score_risco)}</b>
              <small>de 100</small>
            </div>
            <div style={{ flex: 1, minWidth: 260 }}>
              <h2 style={{ marginTop: 0 }}>{ROTULOS_RISCO[classe]}</h2>
              <p style={{ color: 'var(--texto-suave)', margin: 0 }}>
                Escore composto por questionário de prontidão
                {d.blocos?.carga !== null && d.blocos?.carga !== undefined && ', carga de treino (ACWR)'}
                {d.blocos?.foto !== null && d.blocos?.foto !== undefined && ' e análise das fotografias'}.
              </p>
              <div className="cartoes-numero">
                <Bloco titulo="Questionário" valor={d.blocos?.questionario} peso={d.pesos_aplicados?.questionario} />
                <Bloco titulo="Carga / ACWR" valor={d.blocos?.carga} peso={d.pesos_aplicados?.carga} />
                <Bloco titulo="Fotografias" valor={d.blocos?.foto} peso={d.pesos_aplicados?.foto} />
              </div>
            </div>
          </div>
        </div>

        {acwr.acwr != null && (
          <div className="secao">
            <h2>Carga de treino</h2>
            <p className="ajuda">
              ACWR = carga aguda (7 dias) ÷ carga crônica (28 dias), com carga da sessão calculada por duração × RPE.
            </p>
            <div className="cartoes-numero">
              <div className="numero">
                <span>ACWR</span>
                <b style={{ color: CORES_ACWR[acwr.faixa] }}>{acwr.acwr.toFixed(2)}</b>
                <small>{ROTULOS_ACWR[acwr.faixa]}</small>
              </div>
              <div className="numero">
                <span>Carga aguda</span>
                <b>{acwr.carga_aguda}</b>
                <small>UA/dia (7 dias)</small>
              </div>
              <div className="numero">
                <span>Carga crônica</span>
                <b>{acwr.carga_cronica}</b>
                <small>UA/dia (28 dias)</small>
              </div>
              <div className="numero">
                <span>Monotonia</span>
                <b>{acwr.monotonia ?? '—'}</b>
                <small>Índice de Foster</small>
              </div>
              <div className="numero">
                <span>Sessões lidas</span>
                <b>{acwr.total_sessoes}</b>
                <small>do arquivo CSV</small>
              </div>
            </div>

            <h3 style={{ fontSize: 15, marginTop: 24, marginBottom: 4 }}>Carga diária nos últimos 28 dias</h3>
            <div className="grafico">
              {(acwr.serie_diaria || []).map((p, i) => (
                <div
                  key={p.data}
                  className={`col ${i >= (acwr.serie_diaria.length - 7) ? 'recente' : ''}`}
                  style={{ height: `${(p.carga / maiorCarga) * 100}%` }}
                  title={`${new Date(p.data + 'T00:00:00').toLocaleDateString('pt-BR')}: ${p.carga} UA`}
                />
              ))}
            </div>
            <p className="dica">Barras em azul escuro correspondem à janela aguda (últimos 7 dias).</p>
          </div>
        )}

        {avaliacao.fotos?.length > 0 && (
          <div className="secao">
            <h2>Análise das fotografias</h2>
            {avaliacao.fotos.map((foto, i) => (
              <div className="item-foto" key={foto.id} style={{ alignItems: 'stretch' }}>
                <img src={`/uploads/${foto.arquivo}`} alt={`Foto ${i + 1}`} />
                <div className="meta">
                  <div className="nome">
                    Foto {i + 1} · {rotuloDe(ESPORTES, foto.modalidade)} · {rotuloDe(FASES[foto.modalidade] || [], foto.fase)}
                    {foto.joelho_frente && ` · joelho ${foto.joelho_frente}`}
                  </div>
                  {foto.analise?.ok ? (
                    <>
                      <div style={{ display: 'flex', gap: 22, flexWrap: 'wrap', fontSize: 13.5, marginBottom: 10 }}>
                        <span>Inclinação do tronco: <b>{foto.analise.inclinacao_tronco_graus}°</b></span>
                        <span>Simetria: <b>{foto.analise.simetria_percent}%</b></span>
                        <span>Desvio de alinhamento: <b>{foto.analise.desvio_alinhamento_percent}%</b></span>
                      </div>
                      {foto.analise.alertas?.length ? (
                        foto.analise.alertas.map((a) => (
                          <div className={`fator ${a.nivel}`} key={a.titulo}>
                            <b>{a.titulo}</b>
                            <p>{a.descricao}</p>
                          </div>
                        ))
                      ) : (
                        <p className="dica">Nenhum desvio postural relevante foi detectado nesta imagem.</p>
                      )}
                    </>
                  ) : (
                    <div className="fator info">
                      <b>Análise não concluída</b>
                      <p>{foto.analise?.erro || 'Não foi possível processar esta imagem.'}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="secao">
          <h2>Fatores que mais pesaram</h2>
          {d.fatores?.length ? (
            d.fatores.map((f, i) => (
              <div className={`fator ${f.impacto}`} key={`${f.fator}-${i}`}>
                <b>{f.fator}</b>
                <p>{f.detalhe}</p>
              </div>
            ))
          ) : (
            <p className="dica">Nenhum fator de risco relevante identificado.</p>
          )}
        </div>

        <div className="secao">
          <h2>Recomendações</h2>
          <ul className="lista-recomendacoes">
            {(d.recomendacoes || []).map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>

        {avaliacao.sessoes?.length > 0 && (
          <div className="secao">
            <h2>Sessões lidas do arquivo</h2>
            <div style={{ maxHeight: 320, overflow: 'auto' }}>
              <table className="tabela">
                <thead>
                  <tr>
                    <th>Data</th><th>Duração</th><th>Distância</th><th>RPE</th><th>Carga (UA)</th>
                  </tr>
                </thead>
                <tbody>
                  {[...avaliacao.sessoes].reverse().map((s, i) => (
                    <tr key={i}>
                      <td>{new Date(s.data).toLocaleDateString('pt-BR')}</td>
                      <td>{s.duracao_min.toFixed(0)} min</td>
                      <td>{s.distancia_km ? `${s.distancia_km} km` : '—'}</td>
                      <td>{s.rpe ?? '—'}</td>
                      <td>{s.carga}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="secao">
          <p className="dica">
            Este resultado é uma triagem exploratória de caráter acadêmico e não substitui avaliação clínica
            presencial por profissional de saúde.
          </p>
        </div>

        <div className="rodape">
          <Link to="/historico" className="btn secundario">Ver histórico</Link>
          <div className="direita">
            <Link to="/formulario" className="btn primario">Nova avaliação</Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function Bloco({ titulo, valor, peso }) {
  return (
    <div className="numero">
      <span>{titulo}</span>
      <b>{valor == null ? '—' : Math.round(valor)}</b>
      <small>{valor == null ? 'sem dados' : `peso ${Math.round((peso || 0) * 100)}%`}</small>
    </div>
  )
}
