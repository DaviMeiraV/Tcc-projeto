import { ESPORTES, FASES, rotuloDe } from '../lib/opcoes'

const formatarScore = (valor) => valor.toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })

function CartaoResultado({ titulo, children, className = '' }) {
  return (
    <section className={`resultado-cartao ${className}`}>
      <h3>{titulo}</h3>
      {children}
    </section>
  )
}

export function ImagemTratada({ fotos = [], scores = [], analisando, tentarNovamente }) {
  const pendentes = fotos.some((foto) => foto.analise?.status !== 'concluida')

  return (
    <CartaoResultado titulo="Análise da imagem" className="resultado-imagens">
      {fotos.length === 0 && <p className="resultado-mensagem">Nenhuma fotografia enviada.</p>}
      {fotos.map((foto, i) => {
        const analise = foto.analise
        const tratada = analise?.imagem_tratada?.arquivo
        const normalizado = scores.find((score) => score.foto_id === foto.id)?.score_normalizado
        return (
          <article className="resultado-foto" key={foto.id}>
            <div className="resultado-foto-cabecalho">
              <div>
                <h4>Foto {i + 1} · {rotuloDe(ESPORTES, foto.modalidade)}</h4>
                <p className="resultado-mensagem">
                  {rotuloDe(FASES[foto.modalidade] || [], foto.fase)}
                  {foto.joelho_frente && ` · Joelho ${foto.joelho_frente}`}
                </p>
              </div>
              {analise?.status === 'concluida' && (
                <div className="resultado-score-postural">
                  <span>Score postural</span>
                  <strong>{analise.score.toLocaleString('pt-BR', { maximumFractionDigits: 4 })} / 1</strong>
                  <small>Quanto maior, melhor</small>
                  {Number.isFinite(normalizado) && <small>Score padronizado: {formatarScore(normalizado)} / 1 · Quanto maior, maior o desvio dos padrões.</small>}
                </div>
              )}
            </div>
            {analise?.status === 'concluida' && tratada ? (
              <>
                <a className="resultado-imagem" href={`/uploads/${tratada}`} target="_blank" rel="noreferrer">
                  <img src={`/uploads/${tratada}`} alt={`Análise postural da foto ${i + 1}`} />
                </a>
                {typeof analise.resumo === 'string' && <p className="resultado-mensagem">{analise.resumo}</p>}
                <div className="resultado-links">
                  <a href={`/uploads/${tratada}`} target="_blank" rel="noreferrer">Abrir imagem tratada</a>
                  <a href={`/uploads/${foto.arquivo}`} target="_blank" rel="noreferrer">Ver foto enviada</a>
                </div>
              </>
            ) : (
              <>
                <p className="resultado-mensagem" role="status">
                  {analise?.erro || 'A análise desta foto ainda não foi concluída.'} Seus dados continuam salvos.
                </p>
                <a href={`/uploads/${foto.arquivo}`} target="_blank" rel="noreferrer">Ver foto enviada</a>
              </>
            )}
          </article>
        )
      })}
      {pendentes && (
        <button type="button" className="btn secundario" onClick={tentarNovamente} disabled={analisando}>
          {analisando ? 'Analisando fotos…' : 'Tentar análises pendentes novamente'}
        </button>
      )}
    </CartaoResultado>
  )
}

export function ScoreAcwr({ resultado, normalizado }) {
  const valor = resultado?.acwr
  const formatar = (numero) => numero.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
  return (
    <CartaoResultado titulo="Score da planilha (ACWR)" className="resultado-acwr">
      <div className="resultado-valor">
        {Number.isFinite(valor)
          ? <strong>{valor.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}</strong>
          : <p className="resultado-mensagem">{resultado?.erro || (resultado ? 'ACWR indisponível: a carga crônica é zero.' : 'Nenhuma planilha analisada.')}</p>}
      </div>
      {resultado?.status === 'concluida' && (
        <>
          <dl className="resultado-totais">
            <div><dt>Últimos 7 dias</dt><dd>{resultado.semana.atividades} atividades · {formatar(resultado.semana.minutos)} min</dd></div>
            <div><dt>Últimos 28 dias</dt><dd>{resultado.mes.atividades} atividades · {formatar(resultado.mes.minutos)} min</dd></div>
          </dl>
          <p className="resultado-mensagem">Referência: {new Date(`${resultado.referencia}T12:00:00`).toLocaleDateString('pt-BR')} (última atividade).</p>
          {resultado.atividades_com_rpe_formulario > 0 && (
            <p className="resultado-mensagem">
              <strong>ACWR com carga parcialmente ou totalmente estimada.</strong>{' '}
              O esforço geral do formulário ({resultado.rpe_formulario}/10) foi usado como aproximação em {resultado.atividades_com_rpe_formulario} de {resultado.mes.atividades} atividades.
              {' '}Esse valor não foi informado individualmente para cada sessão. Os RPEs presentes na planilha foram preservados.
            </p>
          )}
          {resultado.historico_incompleto && <p className="resultado-mensagem">O histórico enviado cobre menos de 28 dias. Dias sem registros contam como carga zero.</p>}
        </>
      )}
      <p className="resultado-formula">
        {Number.isFinite(normalizado) && <span>Score normalizado: {formatarScore(normalizado)} / 1</span>}
        <span>Carga = minutos × RPE (informado ou aproximado).</span>
        <span>Aguda = média diária de 7 dias; crônica = média diária de 28 dias.</span>
        <span>ACWR = carga aguda ÷ carga crônica.</span>
      </p>
    </CartaoResultado>
  )
}

export function ScoreAtleta({ resultado }) {
  const concluido = resultado?.status === 'concluida' && Number.isFinite(resultado.score)
  return (
    <CartaoResultado titulo="Score dos dados do atleta">
      <div className="resultado-valor">
        {concluido ? (
          <strong>{formatarScore(resultado.score)} / 1</strong>
        ) : (
          <p className="resultado-mensagem">Índice indisponível: faltam respostas válidas para o cálculo.</p>
        )}
      </div>
      <p className="resultado-mensagem">Índice subjetivo experimental (ICSA). Quanto maior, mais desfavorável a condição subjetiva. Não representa probabilidade de lesão.</p>
    </CartaoResultado>
  )
}

export function ScoreFinal({ resultado }) {
  return (
    <CartaoResultado titulo="Score final" className="resultado-final">
      <div className="resultado-valor">
        {Number.isFinite(resultado?.score_final)
          ? <strong>{formatarScore(resultado.score_final)} / 1</strong>
          : <p className="resultado-mensagem">Score final indisponível. {resultado?.motivos?.join(' ') || 'São necessárias as três análises válidas.'}</p>}
      </div>
      <p className="resultado-mensagem">Resultado composto das análises ACWR, postural e dos dados subjetivos. Quanto maior, maior a intensidade dos indicadores desfavoráveis segundo o modelo.</p>
      <p className="resultado-mensagem">Indicador experimental de composição das três análises. Não representa probabilidade clínica de lesão.</p>
    </CartaoResultado>
  )
}
