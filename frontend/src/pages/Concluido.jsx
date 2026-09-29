import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../lib/api'
import { ESPORTES, FASES, rotuloDe } from '../lib/opcoes'

export default function Concluido() {
  const { id } = useParams()
  const [avaliacao, setAvaliacao] = useState(null)
  const [erro, setErro] = useState('')
  const [analisando, setAnalisando] = useState(false)

  useEffect(() => {
    let ativo = true
    setAvaliacao(null)
    setErro('')
    if (id) api.detalharAvaliacao(id)
      .then((dados) => { if (ativo) setAvaliacao(dados) })
      .catch((e) => { if (ativo) setErro(e.message) })
    return () => { ativo = false }
  }, [id])

  async function tentarNovamente() {
    setAnalisando(true)
    setErro('')
    try {
      setAvaliacao(await api.repetirAnalises(id))
    } catch (e) {
      setErro(e.message)
    } finally {
      setAnalisando(false)
    }
  }

  return (
    <div className="pagina">
      <div className="cartao centralizado">
        <h1>{id && !avaliacao ? 'Detalhes do envio' : 'Enviado com sucesso'}</h1>
        {avaliacao && <p>Envio #{avaliacao.id}</p>}
        {erro && <div className="alerta" role="alert">{erro}</div>}
        {id && !avaliacao && !erro && <p>Carregando envio…</p>}
        {(!id || avaliacao) && <p>Seus dados foram recebidos e registrados com sucesso.</p>}
        {avaliacao?.fotos.map((foto, i) => {
          const analise = foto.analise
          const tratada = analise?.imagem_tratada?.arquivo
          return (
            <div className="secao" key={foto.id} style={{ textAlign: 'left' }}>
              <h2>Foto {i + 1} · {rotuloDe(ESPORTES, foto.modalidade)}</h2>
              <p className="ajuda">
                {rotuloDe(FASES[foto.modalidade] || [], foto.fase)}
                {foto.joelho_frente && ` · Joelho ${foto.joelho_frente}`}
              </p>
              <a href={`/uploads/${foto.arquivo}`} target="_blank" rel="noreferrer">Ver foto enviada</a>
              {analise?.status === 'concluida' && tratada ? (
                <>
                  <p>Score postural: <b>{analise.score.toLocaleString('pt-BR', { maximumFractionDigits: 4 })} / 1</b> (quanto maior, melhor).</p>
                  {typeof analise.resumo === 'string' && <p>{analise.resumo}</p>}
                  <a href={`/uploads/${tratada}`} target="_blank" rel="noreferrer">
                    <img src={`/uploads/${tratada}`} alt={`Análise postural da foto ${i + 1}`} style={{ display: 'block', width: '100%', height: 'auto', margin: '16px 0' }} />
                    Abrir imagem tratada
                  </a>
                </>
              ) : (
                <p role="status">{analise?.erro || 'A análise desta foto ainda não foi concluída.'} Seus dados continuam salvos.</p>
              )}
            </div>
          )
        })}
        {avaliacao?.fotos.some((f) => f.analise?.status !== 'concluida') && (
          <button type="button" className="btn secundario" onClick={tentarNovamente} disabled={analisando}>
            {analisando ? 'Analisando fotos…' : 'Tentar análises pendentes novamente'}
          </button>
        )}
        <div style={{ marginTop: 26 }}>
          <Link to="/historico" className="btn secundario">Ver histórico</Link>{' '}
          <Link to="/formulario" className="btn primario" style={{ textDecoration: 'none' }}>
            Preencher novamente
          </Link>
        </div>
      </div>
    </div>
  )
}
