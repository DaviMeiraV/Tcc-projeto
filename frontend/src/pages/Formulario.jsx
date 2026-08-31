import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Campo, Chips, ChipsSimNao, PerguntaSlider } from '../components/Campos'
import { api } from '../lib/api'
import {
  ESPORTES, FASES, JOELHOS, PERGUNTAS, QUANDO_LESAO, SEXOS, TEMPOS_PRATICA, rotuloDe,
} from '../lib/opcoes'

const MAX_FOTOS = 3
const TIPOS_IMAGEM = ['image/jpeg', 'image/jpg', 'image/png']

const ESTADO_INICIAL = {
  idade: '', sexo: '', esporte: '', tempo_pratica: '', peso_kg: '', altura_cm: '',
  ...Object.fromEntries(PERGUNTAS.map((p) => [p.chave, p.inicial])),
  lesao_previa: null, dor_limita: null, lesao_descricao: '', lesao_quando: '',
}

function validarEtapa1(f) {
  const e = {}
  const idade = Number(f.idade)
  if (!f.idade) e.idade = 'Informe a idade.'
  else if (!Number.isInteger(idade) || idade < 10 || idade > 90) e.idade = 'Informe uma idade entre 10 e 90 anos.'

  if (!f.sexo) e.sexo = 'Selecione uma opção.'
  if (!f.esporte) e.esporte = 'Selecione o esporte principal.'
  if (!f.tempo_pratica) e.tempo_pratica = 'Selecione o tempo de prática.'

  const peso = Number(f.peso_kg)
  if (!f.peso_kg) e.peso_kg = 'Informe o peso.'
  else if (!(peso > 20 && peso <= 250)) e.peso_kg = 'Informe um peso entre 20 e 250 kg.'

  const altura = Number(f.altura_cm)
  if (!f.altura_cm) e.altura_cm = 'Informe a altura.'
  else if (!(altura > 100 && altura <= 250)) e.altura_cm = 'Informe a altura em centímetros (100 a 250).'

  if (f.lesao_previa === null) e.lesao_previa = 'Selecione uma opção.'
  if (f.dor_limita === null) e.dor_limita = 'Selecione uma opção.'
  return e
}

function tamanhoLegivel(bytes) {
  return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export default function Formulario() {
  const navegar = useNavigate()
  const [etapa, setEtapa] = useState(1)
  const [form, setForm] = useState(ESTADO_INICIAL)
  const [erros, setErros] = useState({})
  const [fotos, setFotos] = useState([])
  const [csv, setCsv] = useState(null)
  const [consentimento, setConsentimento] = useState(false)
  const [arrastando, setArrastando] = useState(false)
  const [erroGeral, setErroGeral] = useState('')
  const [enviando, setEnviando] = useState(false)

  const refImagens = useRef(null)
  const refCsv = useRef(null)

  useEffect(() => () => fotos.forEach((f) => URL.revokeObjectURL(f.preview)), [fotos])

  const set = (chave) => (valor) => {
    setForm((f) => ({ ...f, [chave]: valor }))
    setErros((e) => ({ ...e, [chave]: undefined }))
  }

  function adicionarImagens(lista) {
    setErroGeral('')
    const novas = []
    for (const arquivo of Array.from(lista)) {
      if (!TIPOS_IMAGEM.includes(arquivo.type)) {
        setErroGeral(`"${arquivo.name}" não é uma imagem JPG, JPEG ou PNG.`)
        continue
      }
      if (arquivo.size > 8 * 1024 * 1024) {
        setErroGeral(`"${arquivo.name}" excede o limite de 8 MB.`)
        continue
      }
      novas.push({
        arquivo,
        preview: URL.createObjectURL(arquivo),
        modalidade: form.esporte || 'corrida',
        fase: '',
        joelho_frente: '',
      })
    }
    setFotos((atuais) => {
      const total = [...atuais, ...novas]
      if (total.length > MAX_FOTOS) setErroGeral(`Envie no máximo ${MAX_FOTOS} imagens.`)
      return total.slice(0, MAX_FOTOS)
    })
  }

  function atualizarFoto(indice, campo, valor) {
    setFotos((atuais) =>
      atuais.map((f, i) => {
        if (i !== indice) return f
        const atualizada = { ...f, [campo]: valor }
        if (campo === 'modalidade') {
          atualizada.fase = ''
          if (valor === 'ciclismo') atualizada.joelho_frente = ''
        }
        return atualizada
      }),
    )
  }

  function removerFoto(indice) {
    setFotos((atuais) => {
      URL.revokeObjectURL(atuais[indice].preview)
      return atuais.filter((_, i) => i !== indice)
    })
  }

  function selecionarCsv(lista) {
    const arquivo = lista?.[0]
    if (!arquivo) return
    if (!arquivo.name.toLowerCase().endsWith('.csv')) {
      setErroGeral('O histórico de treino precisa ser um arquivo .csv.')
      return
    }
    setErroGeral('')
    setCsv(arquivo)
  }

  function avancar() {
    setErroGeral('')
    if (etapa === 1) {
      const e = validarEtapa1(form)
      setErros(e)
      if (Object.keys(e).length) {
        setErroGeral('Revise os campos destacados antes de continuar.')
        return
      }
      // Sugere a modalidade das fotos com base no esporte principal.
      setFotos((atuais) => atuais.map((f) => (f.fase ? f : { ...f, modalidade: form.esporte })))
    }
    if (etapa === 2) {
      if (fotos.length && !consentimento) {
        setErroGeral('Confirme a autorização de uso das fotografias para continuar.')
        return
      }
      if (fotos.some((f) => !f.fase)) {
        setErroGeral('Informe a fase do movimento de cada fotografia.')
        return
      }
      if (fotos.some((f) => f.modalidade === 'corrida' && !f.joelho_frente)) {
        setErroGeral('Informe qual joelho está à frente nas fotos de corrida.')
        return
      }
    }
    setEtapa((n) => Math.min(3, n + 1))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function voltar() {
    setErroGeral('')
    setEtapa((n) => Math.max(1, n - 1))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function enviar() {
    setEnviando(true)
    setErroGeral('')
    try {
      const payload = {
        idade: Number(form.idade),
        sexo: form.sexo,
        esporte: form.esporte,
        tempo_pratica: form.tempo_pratica,
        peso_kg: Number(form.peso_kg),
        altura_cm: Number(form.altura_cm),
        ...Object.fromEntries(PERGUNTAS.map((p) => [p.chave, Number(form[p.chave])])),
        lesao_previa: !!form.lesao_previa,
        dor_limita: !!form.dor_limita,
        lesao_descricao: form.lesao_previa ? form.lesao_descricao || null : null,
        lesao_quando: form.lesao_previa ? form.lesao_quando || null : null,
        consentimento_foto: consentimento,
        fotos_meta: fotos.map((f) => ({
          modalidade: f.modalidade,
          fase: f.fase,
          joelho_frente: f.modalidade === 'corrida' ? f.joelho_frente : null,
        })),
      }

      const dados = new FormData()
      dados.append('payload', JSON.stringify(payload))
      fotos.forEach((f) => dados.append('fotos', f.arquivo))
      if (csv) dados.append('csv_treino', csv)

      const avaliacao = await api.enviarAvaliacao(dados)
      navegar(`/resultado/${avaliacao.id}`, { replace: true })
    } catch (erro) {
      setErroGeral(erro.message)
      setEnviando(false)
    }
  }

  return (
    <div className="pagina">
      <div className="cartao">
        <div className="cabecalho">
          <h1>Pesquisa acadêmica — Coleta de dados de atletas</h1>
          <p>Formulário destinado à coleta de informações para um Trabalho de Conclusão de Curso.</p>
          <p>Os dados fornecidos serão utilizados exclusivamente para fins acadêmicos e de pesquisa.</p>
          <div className="etapas">
            <strong>Etapa {etapa} de 3</strong>
            <span>Participante e questionário → Arquivos → Revisão</span>
          </div>
          <div className="barra">
            <div style={{ width: `${(etapa / 3) * 100}%` }} />
          </div>
        </div>

        {erroGeral && <div className="alerta" style={{ marginTop: 20 }}>{erroGeral}</div>}

        {etapa === 1 && (
          <Etapa1 form={form} erros={erros} set={set} />
        )}

        {etapa === 2 && (
          <Etapa2
            fotos={fotos}
            csv={csv}
            consentimento={consentimento}
            arrastando={arrastando}
            setArrastando={setArrastando}
            setConsentimento={setConsentimento}
            adicionarImagens={adicionarImagens}
            atualizarFoto={atualizarFoto}
            removerFoto={removerFoto}
            selecionarCsv={selecionarCsv}
            removerCsv={() => setCsv(null)}
            refImagens={refImagens}
            refCsv={refCsv}
          />
        )}

        {etapa === 3 && <Etapa3 form={form} fotos={fotos} csv={csv} />}

        <div className="rodape">
          {etapa > 1 && (
            <button type="button" className="btn secundario" onClick={voltar} disabled={enviando}>
              Voltar
            </button>
          )}
          <div className="direita">
            {etapa < 3 ? (
              <button type="button" className="btn primario" onClick={avancar}>
                Continuar
              </button>
            ) : (
              <button type="button" className="btn primario" onClick={enviar} disabled={enviando}>
                {enviando ? 'Analisando…' : 'Enviar e analisar'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function Etapa1({ form, erros, set }) {
  return (
    <>
      <div className="secao">
        <h2>Informações do participante</h2>
        <p className="ajuda">Preencha algumas informações básicas sobre você e sua prática esportiva.</p>
        <div className="grade">
          <Campo rotulo="Idade" obrigatorio erro={erros.idade} ajuda="Informe a idade.">
            <input type="number" value={form.idade} onChange={(e) => set('idade')(e.target.value)} min="10" max="90" />
          </Campo>

          <Campo rotulo="Sexo" obrigatorio erro={erros.sexo} ajuda="Selecione uma opção.">
            <select value={form.sexo} onChange={(e) => set('sexo')(e.target.value)}>
              <option value="">Selecione</option>
              {SEXOS.map((o) => (
                <option key={o.valor} value={o.valor}>{o.rotulo}</option>
              ))}
            </select>
          </Campo>

          <Campo rotulo="Esporte principal" obrigatorio erro={erros.esporte} ajuda="Selecione o esporte principal.">
            <Chips opcoes={ESPORTES} valor={form.esporte} onChange={set('esporte')} />
          </Campo>

          <Campo rotulo="Há quanto tempo pratica esse esporte?" obrigatorio erro={erros.tempo_pratica} ajuda="Selecione o tempo de prática.">
            <select value={form.tempo_pratica} onChange={(e) => set('tempo_pratica')(e.target.value)}>
              <option value="">Selecione</option>
              {TEMPOS_PRATICA.map((o) => (
                <option key={o.valor} value={o.valor}>{o.rotulo}</option>
              ))}
            </select>
          </Campo>

          <Campo rotulo="Peso" obrigatorio unidade="kg" erro={erros.peso_kg} ajuda="Informe o peso.">
            <input type="number" step="0.1" value={form.peso_kg} onChange={(e) => set('peso_kg')(e.target.value)} />
          </Campo>

          <Campo rotulo="Altura" obrigatorio unidade="cm" erro={erros.altura_cm} ajuda="Informe a altura.">
            <input type="number" step="1" value={form.altura_cm} onChange={(e) => set('altura_cm')(e.target.value)} />
          </Campo>
        </div>
      </div>

      <div className="secao">
        <h2>Questionário</h2>
        <p className="ajuda">Responda considerando seu estado atual e sua experiência recente com os treinamentos.</p>
        {PERGUNTAS.map((p) => (
          <PerguntaSlider key={p.chave} titulo={p.titulo} escala={p.escala} valor={form[p.chave]} onChange={set(p.chave)} />
        ))}

        <div className="grade" style={{ marginTop: 18 }}>
          <Campo rotulo="Já sofreu lesão relacionada ao esporte?" obrigatorio erro={erros.lesao_previa} ajuda="Selecione uma opção.">
            <ChipsSimNao valor={form.lesao_previa} onChange={set('lesao_previa')} />
          </Campo>
          <Campo rotulo="Dor atual limita seus treinamentos?" obrigatorio erro={erros.dor_limita} ajuda="Selecione uma opção.">
            <ChipsSimNao valor={form.dor_limita} onChange={set('dor_limita')} />
          </Campo>
        </div>

        {form.lesao_previa === true && (
          <div style={{ borderLeft: '3px solid var(--azul-claro)', paddingLeft: 16, marginTop: 18 }}>
            <Campo rotulo="Descreva brevemente a lesão">
              <textarea value={form.lesao_descricao} onChange={(e) => set('lesao_descricao')(e.target.value)} />
            </Campo>
            <div style={{ marginTop: 14, maxWidth: 320 }}>
              <Campo rotulo="Há quanto tempo ocorreu?">
                <select value={form.lesao_quando} onChange={(e) => set('lesao_quando')(e.target.value)}>
                  <option value="">Selecione</option>
                  {QUANDO_LESAO.map((o) => (
                    <option key={o.valor} value={o.valor}>{o.rotulo}</option>
                  ))}
                </select>
              </Campo>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function Etapa2({
  fotos, csv, consentimento, arrastando, setArrastando, setConsentimento,
  adicionarImagens, atualizarFoto, removerFoto, selecionarCsv, removerCsv, refImagens, refCsv,
}) {
  const [orientacoes, setOrientacoes] = useState(false)

  return (
    <>
      <div className="secao">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
          <div>
            <h2>Fotografias da prática esportiva</h2>
            <p className="ajuda">Envie fotografias que serão associadas às informações desta pesquisa.</p>
          </div>
          <button type="button" className="btn secundario" onClick={() => setOrientacoes((v) => !v)}>
            Orientações para as fotografias
          </button>
        </div>

        {orientacoes && (
          <div className="consentimento" style={{ display: 'block', marginBottom: 14 }}>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Fotografe o atleta de <b>perfil</b>, com o corpo inteiro visível no enquadramento.</li>
              <li>Prefira fundo liso e contrastante em relação à roupa — isso melhora a detecção da silhueta.</li>
              <li>Mantenha a câmera na altura do quadril e paralela ao plano de movimento.</li>
              <li>Capture o instante exato da fase indicada (contato inicial, apoio médio, fase superior ou extensão máxima).</li>
              <li>Evite fotos desfocadas, contra a luz ou com outras pessoas no quadro.</li>
            </ul>
          </div>
        )}

        <div
          className={`dropzone ${arrastando ? 'arrastando' : ''}`}
          onClick={() => refImagens.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setArrastando(true) }}
          onDragLeave={() => setArrastando(false)}
          onDrop={(e) => { e.preventDefault(); setArrastando(false); adicionarImagens(e.dataTransfer.files) }}
        >
          Clique ou arraste imagens para enviar
          <small>JPG, JPEG ou PNG — máximo de {MAX_FOTOS} imagens</small>
        </div>
        <input
          ref={refImagens}
          type="file"
          accept=".jpg,.jpeg,.png"
          multiple
          hidden
          onChange={(e) => { adicionarImagens(e.target.files); e.target.value = '' }}
        />

        {fotos.map((foto, i) => (
          <div className="item-foto" key={foto.preview}>
            <img src={foto.preview} alt={`Pré-visualização da foto ${i + 1}`} />
            <div className="meta">
              <div className="nome">Foto {i + 1} — {foto.arquivo.name}</div>
              <div className="grupo-chips">
                <div>
                  <span>Modalidade</span>
                  <Chips opcoes={ESPORTES} valor={foto.modalidade} onChange={(v) => atualizarFoto(i, 'modalidade', v)} />
                </div>
                <div>
                  <span>Fase do movimento</span>
                  <Chips opcoes={FASES[foto.modalidade]} valor={foto.fase} onChange={(v) => atualizarFoto(i, 'fase', v)} />
                </div>
                {foto.modalidade === 'corrida' && (
                  <div>
                    <span>Joelho à frente</span>
                    <Chips opcoes={JOELHOS} valor={foto.joelho_frente} onChange={(v) => atualizarFoto(i, 'joelho_frente', v)} />
                  </div>
                )}
              </div>
            </div>
            <button type="button" className="remover" onClick={() => removerFoto(i)}>Remover</button>
          </div>
        ))}

        {fotos.length > 0 && (
          <label className="consentimento">
            <input type="checkbox" checked={consentimento} onChange={(e) => setConsentimento(e.target.checked)} />
            Confirmo que sou o participante presente nas fotografias ou que possuo autorização para utilizá-las nesta pesquisa.
          </label>
        )}
      </div>

      <div className="secao">
        <h2>Arquivo de histórico de treinamento</h2>
        <p className="ajuda">Envie o arquivo CSV contendo seus registros recentes de treinamento.</p>

        <div
          className="dropzone"
          onClick={() => refCsv.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); selecionarCsv(e.dataTransfer.files) }}
        >
          Selecionar arquivo CSV
          <small>Ou arraste o arquivo para esta área</small>
        </div>
        <input
          ref={refCsv}
          type="file"
          accept=".csv"
          hidden
          onChange={(e) => { selecionarCsv(e.target.files); e.target.value = '' }}
        />

        {csv && (
          <div className="arquivo-linha">
            <strong>{csv.name}</strong>
            <span className="tam">{tamanhoLegivel(csv.size)}</span>
            <button type="button" className="remover" onClick={removerCsv}>Remover</button>
          </div>
        )}
        <p className="dica" style={{ marginTop: 10 }}>
          O arquivo é usado para calcular o ACWR (razão entre carga aguda e crônica). São reconhecidas exportações do
          Strava e do Garmin, ou uma planilha com colunas de data, duração e — opcionalmente — distância, RPE ou frequência cardíaca.
        </p>
      </div>
    </>
  )
}

function Etapa3({ form, fotos, csv }) {
  const altura = Number(form.altura_cm) / 100
  const imc = altura > 0 ? (Number(form.peso_kg) / (altura * altura)).toFixed(1) : '—'

  const linhas = [
    ['Idade', `${form.idade} anos`],
    ['Sexo', rotuloDe(SEXOS, form.sexo)],
    ['Esporte principal', rotuloDe(ESPORTES, form.esporte)],
    ['Tempo de prática', rotuloDe(TEMPOS_PRATICA, form.tempo_pratica)],
    ['Peso', `${form.peso_kg} kg`],
    ['Altura', `${form.altura_cm} cm`],
    ['IMC', imc],
    ['Esforço percebido', `${form.rpe} / 10`],
    ['Dor', `${form.dor} / 10`],
    ['Fadiga', `${form.fadiga} / 10`],
    ['Qualidade do sono', `${form.sono} / 10`],
    ['Recuperação', `${form.recuperacao} / 10`],
    ['Lesão prévia', form.lesao_previa ? 'Sim' : 'Não'],
    ['Dor limita treinos', form.dor_limita ? 'Sim' : 'Não'],
  ]
  if (form.lesao_previa && form.lesao_quando) linhas.push(['Lesão ocorreu há', rotuloDe(QUANDO_LESAO, form.lesao_quando)])

  return (
    <div className="secao">
      <h2>Revisão</h2>
      <p className="ajuda">Confira as informações antes de enviar. A análise é gerada imediatamente após o envio.</p>

      <div className="revisao">
        {linhas.map(([rotulo, valor]) => (
          <div className="linha" key={rotulo}>
            <span>{rotulo}</span>
            <b>{valor}</b>
          </div>
        ))}
      </div>

      <h2 style={{ marginTop: 26, fontSize: 17 }}>Arquivos</h2>
      <div className="revisao">
        <div className="linha">
          <span>Fotografias</span>
          <b>{fotos.length ? `${fotos.length} imagem(ns)` : 'Nenhuma'}</b>
        </div>
        <div className="linha">
          <span>Histórico de treino</span>
          <b>{csv ? csv.name : 'Nenhum'}</b>
        </div>
      </div>

      {fotos.length > 0 && (
        <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
          {fotos.map((f, i) => (
            <div key={f.preview} style={{ fontSize: 12.5, color: 'var(--texto-suave)' }}>
              <img src={f.preview} alt={`Foto ${i + 1}`} style={{ width: 120, height: 88, objectFit: 'cover', borderRadius: 4, display: 'block' }} />
              {rotuloDe(ESPORTES, f.modalidade)} · {rotuloDe(FASES[f.modalidade], f.fase)}
            </div>
          ))}
        </div>
      )}

      {!csv && (
        <p className="dica" style={{ marginTop: 16 }}>
          Sem o CSV de treino o ACWR não é calculado, e o escore passa a considerar apenas o questionário e as fotografias.
        </p>
      )}
    </div>
  )
}
