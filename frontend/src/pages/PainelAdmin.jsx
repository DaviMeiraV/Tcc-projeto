import { useEffect, useState } from 'react'

import { api } from '../lib/api'
import { ESPORTES, rotuloDe } from '../lib/opcoes'

function formatarScore(valor, casas = 4) {
  return Number.isFinite(valor)
    ? valor.toLocaleString('pt-BR', { maximumFractionDigits: casas })
    : 'Indisponível'
}

function Indicador({ titulo, valor, detalhe }) {
  return (
    <div className="admin-indicador">
      <span>{titulo}</span>
      <strong>{formatarScore(valor)}</strong>
      {detalhe && <small>{detalhe}</small>}
    </div>
  )
}

function rotuloStatus(status) {
  if (status === 'concluida') return 'Análise concluída'
  if (status === 'erro') return 'Análise com erro'
  return 'Análise pendente'
}

export function CartaoAvaliacao({ avaliacao }) {
  const posturais = avaliacao.fotos
    .map((foto) => foto.score_postural)
    .filter(Number.isFinite)

  return (
    <article className="admin-avaliacao">
      <header className="admin-avaliacao-cabecalho">
        <div>
          <h2>Avaliação #{avaliacao.id}</h2>
          <p>
            {avaliacao.usuario_nome} · {avaliacao.usuario_email}
          </p>
        </div>
        <div className="admin-avaliacao-data">
          <span>{new Date(avaliacao.criado_em).toLocaleString('pt-BR')}</span>
          <strong>{rotuloDe(ESPORTES, avaliacao.esporte)}</strong>
        </div>
      </header>

      <div className="admin-indicadores">
        <Indicador
          titulo="ACWR"
          valor={avaliacao.score_acwr}
          detalhe={`Normalizado: ${formatarScore(avaliacao.score_acwr_normalizado)} / 1`}
        />
        <Indicador titulo="Subjetivo (ICSA)" valor={avaliacao.score_subjetivo} />
        <Indicador
          titulo="Postural"
          valor={posturais.length === 1 ? posturais[0] : null}
          detalhe={posturais.length > 1 ? `${posturais.length} scores, um por foto abaixo` : 'Score original / 1'}
        />
        <Indicador titulo="Final (IMCA)" valor={avaliacao.score_final} detalhe="Escala de 0 a 1" />
      </div>

      {avaliacao.motivos_score_final?.length > 0 && (
        <p className="resultado-mensagem">IMCA indisponível: {avaliacao.motivos_score_final.join(" ")}</p>
      )}

      <section className="admin-fotos" aria-label={`Fotos da avaliação ${avaliacao.id}`}>
        <h3>Fotos analisadas</h3>
        {avaliacao.fotos.length === 0 && <p className="vazio">Nenhuma foto enviada.</p>}
        {avaliacao.fotos.length > 0 && (
          <div className="admin-fotos-lista">
            {avaliacao.fotos.map((foto) => (
              <article className="admin-foto" key={foto.id}>
                <h4>{rotuloDe(ESPORTES, foto.modalidade)} · {foto.fase.replaceAll('_', ' ')}</h4>
                <p>{rotuloStatus(foto.status_analise)}</p>
                {Number.isFinite(foto.score_postural) && (
                  <p>Score postural: <strong>{formatarScore(foto.score_postural)} / 1</strong></p>
                )}
                {foto.imagem_tratada ? (
                  <a
                    className="admin-foto-link"
                    href={`/uploads/${encodeURIComponent(foto.imagem_tratada)}`}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Abrir foto tratada da avaliação ${avaliacao.id}`}
                  >
                    <img
                      src={`/uploads/${encodeURIComponent(foto.imagem_tratada)}`}
                      alt={`Foto tratada da avaliação ${avaliacao.id}`}
                      loading="lazy"
                    />
                    <span>Abrir imagem tratada</span>
                  </a>
                ) : (
                  <p className="resultado-mensagem">A foto tratada ainda não está disponível.</p>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </article>
  )
}

export default function PainelAdmin() {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')

  useEffect(() => {
    let ativo = true
    api.painelAdmin()
      .then((resultado) => { if (ativo) setDados(resultado) })
      .catch((e) => { if (ativo) setErro(e.message) })
    return () => { ativo = false }
  }, [])

  return (
    <div className="pagina">
      <div className="cartao admin-painel">
        <header className="admin-painel-cabecalho">
          <div>
            <h1>Painel administrativo</h1>
            <p>Resultados de todos os usuários.</p>
          </div>
          {dados && <strong className="admin-total">{dados.total_avaliacoes} avaliações</strong>}
        </header>

        {erro && <div className="alerta" role="alert">{erro}</div>}
        {!dados && !erro && <p className="vazio" role="status">Carregando avaliações…</p>}
        {dados?.avaliacoes.length === 0 && <p className="vazio">Nenhuma avaliação registrada.</p>}
        {dados?.avaliacoes.map((avaliacao) => (
          <CartaoAvaliacao avaliacao={avaliacao} key={avaliacao.id} />
        ))}
      </div>
    </div>
  )
}
