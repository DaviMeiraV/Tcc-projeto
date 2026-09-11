export const SEXOS = [
  { valor: 'masculino', rotulo: 'Masculino' },
  { valor: 'feminino', rotulo: 'Feminino' },
  { valor: 'outro', rotulo: 'Outro / prefiro não informar' },
]

export const TEMPOS_PRATICA = [
  { valor: 'menos_6_meses', rotulo: 'Menos de 6 meses' },
  { valor: '6_meses_1_ano', rotulo: '6 meses a 1 ano' },
  { valor: '1_3_anos', rotulo: '1 a 3 anos' },
  { valor: '3_5_anos', rotulo: '3 a 5 anos' },
  { valor: 'mais_5_anos', rotulo: 'Mais de 5 anos' },
]

export const QUANDO_LESAO = [
  { valor: 'menos_3_meses', rotulo: 'Menos de 3 meses' },
  { valor: '3_6_meses', rotulo: 'De 3 a 6 meses' },
  { valor: '6_12_meses', rotulo: 'De 6 a 12 meses' },
  { valor: 'mais_1_ano', rotulo: 'Mais de 1 ano' },
]

export const ESPORTES = [
  { valor: 'corrida', rotulo: 'Corrida' },
  { valor: 'ciclismo', rotulo: 'Ciclismo' },
]

export const FASES = {
  corrida: [
    { valor: 'contato_inicial', rotulo: 'Contato inicial' },
    { valor: 'apoio_medio', rotulo: 'Apoio médio' },
  ],
  ciclismo: [
    { valor: 'fase_superior', rotulo: 'Fase superior' },
    { valor: 'extensao_maxima', rotulo: 'Extensão máxima' },
  ],
}

export const JOELHOS = [
  { valor: 'esquerdo', rotulo: 'Esquerdo' },
  { valor: 'direito', rotulo: 'Direito' },
]

export const PERGUNTAS = [
  { chave: 'rpe', titulo: 'Como você avalia o esforço percebido nos treinos recentes?', escala: '1 = muito leve · 10 = máximo', inicial: 5 },
  { chave: 'dor', titulo: 'Qual é seu nível atual de dor ou desconforto físico?', escala: '0 = nenhuma · 10 = muito intensa', inicial: 0 },
  { chave: 'fadiga', titulo: 'Qual é seu nível atual de fadiga?', escala: '0 = nenhuma · 10 = extrema', inicial: 0 },
  { chave: 'sono', titulo: 'Como você avalia sua qualidade de sono recente?', escala: '0 = muito ruim · 10 = excelente', inicial: 5 },
  { chave: 'recuperacao', titulo: 'Quão recuperado se sente para outro treino?', escala: '0 = nada · 10 = totalmente', inicial: 5 },
]

// Usados apenas pela tela parada de resultado.
export const ROTULOS_RISCO = {
  baixo: 'Risco baixo',
  moderado: 'Risco moderado',
  alto: 'Risco alto',
  muito_alto: 'Risco muito alto',
}

export const ROTULOS_ACWR = {
  subcarga: 'Subcarga',
  ideal: 'Faixa ideal',
  atencao: 'Atenção',
  risco: 'Risco elevado',
}

export function rotuloDe(lista, valor) {
  return lista.find((o) => o.valor === valor)?.rotulo ?? valor ?? '—'
}
