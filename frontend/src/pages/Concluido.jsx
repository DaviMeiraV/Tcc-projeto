import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../lib/api'
import { ImagemTratada, ScoreAcwr, ScoreAtleta, ScoreFinal } from '../components/ResultadosAnalise'

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
      <div className="cartao resultado-pagina">
        <header className="cabecalho resultado-cabecalho">
          <h1>{id && !avaliacao ? 'Detalhes do envio' : 'Enviado com sucesso'}</h1>
          {(!id || avaliacao) && <p>Seus dados foram recebidos e registrados com sucesso.</p>}
          {avaliacao && <p className="resultado-identificacao">Envio #{avaliacao.id}</p>}
        </header>

        {erro && <div className="alerta" role="alert">{erro}</div>}
        {id && !avaliacao && !erro && <p role="status">Carregando envio…</p>}

        {(!id || avaliacao) && (
          <section className="resultado-conteudo" aria-labelledby="titulo-resultado">
            <h2 id="titulo-resultado">Resultado da análise</h2>
            <div className="resultado-grade">
              <ImagemTratada
                fotos={avaliacao?.fotos}
                analisando={analisando}
                tentarNovamente={tentarNovamente}
              />
              <div className="resultado-scores">
                <ScoreAcwr resultado={avaliacao?.detalhes?.acwr} />
                <ScoreAtleta />
                <ScoreFinal />
              </div>
            </div>
          </section>
        )}

        <div className="rodape resultado-acoes">
          <Link to="/historico" className="btn secundario">Ver histórico</Link>
          <Link to="/formulario" className="btn primario">Preencher novamente</Link>
        </div>
      </div>
    </div>
  )
}
