# Conformidade do código com o artigo V2

Análise de 1 de novembro de 2026.

**O código não está 100% de acordo com o artigo.** As fórmulas principais estão
alinhadas, inclusive o ICSA com pesos iguais. Persistem diferenças no domínio das
entradas, na descrição do fluxo implementado e na apresentação dos resultados,
além de controles e evidências ainda incompletos.

Fonte: [Artigo TCC Outubro 2026 V2](C:/Users/Dell/Downloads/Artigo_TCC_Outubro_2026_V2_Formatado_ModeloTESTE).
O arquivo está sem extensão, mas seu conteúdo é um documento Word OOXML. Foi feita
leitura do conteúdo textual e das tabelas; as localizações abaixo são seções e tabelas,
não números de página. As instruções presentes no documento foram tratadas como
conteúdo a revisar. O artigo não foi alterado.

## O que coincide com o artigo

| Especificação | Local no artigo | Evidência no código |
|---|---|---|
| Carga igual a duração em minutos multiplicada por RPE | 2.4.1 | `backend/app/services/carga_treino.py:182–204` |
| ACWR acoplado por médias diárias de 7 e 28 dias; denominador zero indefinido | 2.4.1 | `carga_treino.py:250–275` |
| `C = min(1, max(0, (ACWR - 1.3) / 0.7))` | 2.4.1, tabela 1 | `backend/app/services/score_final.py:16–20` |
| ICSA com seis componentes, peso 1/6, sono/recuperação invertidos e binários 0/1 | 2.4.2, tabela 2 | `backend/app/services/score_subjetivo.py:11–15,55–73` |
| RPE não entra novamente no ICSA | 4.5 | Campos da fórmula em `score_subjetivo.py:12` |
| RPE do formulário pode substituir session-RPE ausente, com origem estimada identificada | 2.6, tabela 6 | `carga_treino.py:182–203,278–293`; aviso em `ResultadosAnalise.jsx:91–96` |
| `B = 1 - P_foto` | 2.4.3 | `score_final.py:23–24` |
| `IMCA = (C + S + B) / 3` | 2.3 e 2.4.4 | `score_final.py:74–75` |
| Falhas ou ausência reconhecidas no cálculo não viram zero e não há média parcial | 2.4.4 | `score_subjetivo.py:27–53`; `score_final.py:43–75` |
| Postura estática, fases informadas e ausência de média entre fotografias | 2.2 e 2.4.3 | `schemas.py:41–58`; `analise_postural.py:27–39`; `score_final.py:58–72` |
| Landmarks e limites angulares das tabelas 3 e 4 | 2.4.3 | Dependência local `OpenCV-BodyPosture/src/analyzers/poseAnalyzer.py:43–109` |
| Penalização angular de 0,01 por grau e média dos ângulos da foto | 2.4.3, tabela 5 | Dependência local `src/domain/pontuacao.py:13–41` e `src/domain/models.py:29–34` |
| Caráter experimental, sem interpretação como probabilidade clínica | 2.3, 2.4.4, 4.6 e conclusão | `frontend/src/components/ResultadosAnalise.jsx:122–140` |

A correspondência postural foi verificada no código local da dependência em
`C:/Users/Dell/Documents/OpenCV-BodyPosture`. Isso não comprova que a API hospedada
esteja executando a mesma versão. A consistência das faixas com o artigo também não
comprova a validade científica das referências que as fundamentam.

## Divergências confirmadas

### Escala do RPE

Na seção 2.4.1, o artigo define RPE de **1 a 10**. O sistema aceita **0 a 10** em
`backend/app/schemas.py:69`, no CSV (`carga_treino.py:163`) e no slider
(`frontend/src/components/Campos.jsx:60`). O texto de ajuda ainda começa em 1.

**Adequação necessária:** definir uma única escala metodológica. Se o artigo for a
especificação definitiva, validar 1–10 no formulário, API e CSV, revisando testes e
tratamento de registros anteriores. Se zero for intencional, atualizar o artigo e
a explicação do controle. Não alterar dados antigos silenciosamente.

### Campos e duração dos arquivos de treino

A seção 4.2 descreve extração de distância, ritmo, frequência cardíaca e volume
semanal, com uso desses dados na carga. O parser atual reconhece apenas **data,
duração e RPE** (`carga_treino.py:19–34`). Ele soma duração e carga; não usa distância,
ritmo ou frequência cardíaca no ACWR. Ter uma coluna legada `distancia_km` no modelo
não equivale a extrair esse valor no fluxo atual.

A seção 2.4.1 também define duração como tempo total, enquanto o parser aceita
alternativamente tempo em movimento e tempo decorrido. Sem um protocolo de coluna
de origem, esses conceitos não são necessariamente equivalentes.

**Adequação necessária:** atualizar a seção 4.2 para separar a POC e os campos
disponíveis na exportação dos efetivamente utilizados. Explicitar qual duração deve
ser usada e a precedência dos cabeçalhos. Não é necessário adicionar variáveis à
fórmula apenas para sustentar uma descrição antiga do desenvolvimento.

### Fluxo de processamento das imagens

A seção 4.3 afirma que, no código atual, o sistema lista imagens de uma pasta e
pergunta modalidade e fase pelo terminal. A aplicação integrada recebe uploads e
metadados no formulário, persiste os dados e envia um `POST /analises` por foto
(`backend/app/routers/avaliacoes.py:114–167`; `analise_postural.py:27–47,88–110`).

**Adequação necessária:** identificar o processamento por pasta como etapa histórica
da POC e descrever o fluxo web/API como implementação integrada atual. Não substituir
o fluxo web por terminal para reproduzir uma descrição histórica.

### Respostas relevantes separadas no resultado

A tabela 6, na seção 2.6, orienta exibir componentes e respostas relevantes
separadamente para não ocultar sinais pela média. Os três pilares aparecem na tela,
mas o cartão subjetivo apresenta o ICSA agregado e sua explicação; não mostra os
valores individuais de dor e limitação (`ResultadosAnalise.jsx:111–128`).
Essas respostas só aparecem na revisão anterior ao envio em `Formulario.jsx:482–488`.

**Adequação necessária:** apresentar as respostas atuais relevantes junto ao score,
por exemplo dor e limitação. Isso não exige exibir versões históricas dos scores e
é compatível com a solicitação de mostrar apenas o resultado atualizado.

## Implementações parciais e controles que precisam ser explicitados

| Tema | Evidência e relação com o artigo | Proposta |
|---|---|---|
| Foto previamente selecionada | A seção 2.4.3 pede uma imagem selecionada previamente. `score_final.py:59` usa a única foto se houver exatamente uma e bloqueia várias; o formulário permite até três e não oferece seleção para o IMCA. | Explicitar a restrição atual de uma foto no artigo ou definir seleção prévia e persistida quando houver várias. Não escolher pelo score obtido. |
| Validade das respostas | A seção 2.4.4 exige não transformar informação insuficiente em índice completo. `opcoes.js:43–48` preenche escalas com valores iniciais, enviados sem confirmação individual (`Formulario.jsx:19–39,178`). | Exigir confirmação de cada resposta; zero deliberado permanece válido nas escalas que o permitem. É uma lacuna da coleta, embora a função matemática trate corretamente `None`. |
| Cobertura do histórico | `historico_incompleto` compara apenas a primeira data com o início da janela (`carga_treino.py:296–298`); não distingue descanso confirmado de dias sem informação. | Definir como comprovar cobertura e quais ausências tornam os dados insuficientes. O artigo não especifica esse protocolo com precisão suficiente para certificar conformidade integral. |
| Qualidade angular | A seção 2.4.3 condiciona o score a fotografia válida. Na dependência local, vetores nulos retornam ângulo zero (`poseAnalyzer.py:129–130`), que pode receber score 1 na corrida. | Tratar geometria degenerada como medição inválida e explicitar critérios de qualidade. A tabela 5 reconhece score máximo para flexão acentuada válida; isso não justifica pontuar uma medição indefinida. |
| Sensibilidade dos parâmetros | A seção 2.6 inclui análise exploratória de sensibilidade. Há testes de cálculo, mas não foram encontrados scripts ou resultados desse experimento no repositório. | Documentar onde será executado e os resultados obtidos. Como a análise está declarada em andamento, é evidência pendente, não prova de fórmula incorreta. |

## Pontos que a inspeção do código não comprova

- A participação de aproximadamente 10–20 atletas e o andamento da coleta (seção 2.2).
- A validação de exportações reais do Garmin afirmada na seção 4.2. Existe teste
  de duração Garmin/segundos Strava em `backend/tests/test_carga_treino.py:28`, mas
  ele não comprova compatibilidade com todas as exportações, idiomas e formatos.
- Os procedimentos éticos efetivamente adotados, a versão da API implantada e
  resultados de coleta ou estudos realizados fora do repositório.
- A validade científica das fontes e qualquer eficácia preventiva ou preditiva.
  Não foi feita revisão bibliográfica nem avaliação clínica nesta comparação.

Por isso, a afirmação da seção 4.6 de que o desenvolvimento técnico foi concluído
deve ser qualificada pelo escopo implementado e pelos critérios de aceite ainda
pendentes. Não há base para atribuir um percentual numérico de conformidade sem
uma lista fechada de requisitos e seus critérios de validação.

## Verificações e conclusão

No estado local analisado, passaram **49 testes do backend**, **5 testes do frontend**,
a geração do OpenAPI com as descrições atualizadas, a compilação de produção e
`git diff --check`. Os testes de integração simulam a API postural e usam banco
isolado; não são uma execução de MediaPipe sobre fotos reais nem validação em produção.

As correções de README, Swagger, guias, nome do banco, referência de função e CSS
solicitadas anteriormente foram mantidas após essas verificações. Elas não resolvem
as divergências metodológicas e de coleta identificadas neste artigo.

**Parecer:** as fórmulas centrais são compatíveis com o artigo V2, mas a conformidade
integral ainda depende de harmonizar o texto com o fluxo atual, resolver a escala
do RPE, apresentar as respostas relevantes e definir/verificar os controles de
seleção e qualidade dos dados. Parte das correções pertence ao artigo; parte ao sistema.
