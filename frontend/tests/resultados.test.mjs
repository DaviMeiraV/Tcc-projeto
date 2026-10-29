import assert from 'node:assert/strict'
import { test, after } from 'node:test'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createRequire } from 'node:module'
import { build } from 'esbuild'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

// Usa o compilador já instalado com Vite e o test runner nativo do Node.
const pasta = mkdtempSync(join(tmpdir(), 'tcc-resultados-'))
after(() => rmSync(pasta, { recursive: true, force: true }))
const arquivo = join(pasta, 'componentes.cjs')
await build({ entryPoints: ['src/components/ResultadosAnalise.jsx'], outfile: arquivo,
  bundle: true, platform: 'node', format: 'cjs', jsx: 'automatic' })
const { ScoreFinal, ScoreAtleta, ScoreAcwr, ImagemTratada } = createRequire(import.meta.url)(arquivo)
const renderizar = (componente, props) => renderToStaticMarkup(React.createElement(componente, props))

test('exibe o final do backend com quatro casas, inclusive zero', () => {
  assert.match(renderizar(ScoreFinal, { resultado: { score_final: 0.4548 } }), /0,4548 \/ 1/)
  assert.match(renderizar(ScoreFinal, { resultado: { score_final: 0 } }), /0,0000 \/ 1/)
  assert.match(renderizar(ScoreAtleta, { resultado: { status: 'concluida', score: 0.45 } }), /0,4500 \/ 1/)
})

test('exibe indisponibilidade e seu motivo sem imputar zero', () => {
  const html = renderizar(ScoreFinal, { resultado: { score_final: null, motivos: ['Há várias fotos.'] } })
  assert.match(html, /Score final indisponível/)
  assert.match(html, /Há várias fotos/)
  assert.doesNotMatch(html, /0,0000 \/ 1/)
})

test('preserva ACWR bruto, avisos e valor normalizado', () => {
  const html = renderizar(ScoreAcwr, { normalizado: 0.7143, resultado: {
    status: 'concluida', acwr: 1.8, referencia: '2026-09-29',
    semana: { atividades: 2, minutos: 120 }, mes: { atividades: 8, minutos: 480 },
    atividades_com_rpe_formulario: 2, rpe_formulario: 5, historico_incompleto: true,
  } })
  assert.match(html, /<strong>1,8<\/strong>/)
  assert.match(html, /Score normalizado: 0,7143 \/ 1/)
  assert.match(html, /carga parcialmente ou totalmente estimada/)
  assert.match(html, /menos de 28 dias/)
})

test('preserva imagem e score postural e mostra inversão recebida do backend', () => {
  const html = renderizar(ImagemTratada, {
    fotos: [{ id: 1, modalidade: 'corrida', fase: 'apoio_medio', arquivo: 'original.png',
      analise: { status: 'concluida', score: 0.8, imagem_tratada: { arquivo: 'tratada.png' } } }],
    scores: [{ foto_id: 1, score_normalizado: 0.2 }],
  })
  assert.match(html, /0,8 \/ 1/)
  assert.match(html, /Score padronizado: 0,2000 \/ 1/)
  assert.match(html, /src="\/uploads\/tratada.png"/)
})
