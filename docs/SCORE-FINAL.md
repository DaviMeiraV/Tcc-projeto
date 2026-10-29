# Padronização e score final

Veja [Como os três scores são calculados](SCORES.md) para entender as fórmulas,
as escalas e as diferenças de interpretação antes de definir uma combinação.

Edite `calc_score_final(avaliacao)` em `backend/app/services/score_final.py`.
As variáveis já contêm os resultados calculados para a avaliação:

| Variável | Conteúdo |
|---|---|
| `score_acwr` | Razão ACWR bruta, ou `None` se indisponível |
| `score_subjetivo` | ICSA de 0 a 1, maior = mais desfavorável, ou `None` |
| `scores_posturais` | Lista de `{foto_id, score}`, ordenada por ID; maior = melhor alinhamento |

Sem fotos, a lista fica vazia. Fotos pendentes ou com erro mantêm seu ID e recebem
`score: None`. Zero é preservado como valor válido em todos os componentes.
Os valores originais são preservados. A composição usa os componentes padronizados abaixo.

## Fórmulas

```text
C = min(1, max(0, (ACWR − 1,3) / 0,7))
B = 1 − score postural original
S = score subjetivo já calculado, sem mudar seus pesos
Score final = (C + S + B) / 3
```

Todos os componentes utilizados na média têm sentido crescente de indicadores
desfavoráveis segundo o modelo. Os cortes e pesos são experimentais; o resultado
não representa probabilidade de lesão nem recebe classificação clínica.

Exemplo: ACWR 1,8 → C = 0,7143; postural 0,80 → B = 0,20; subjetivo 0,45.
A média, usando a precisão disponível antes de arredondar, é **0,4548**.
As transformações não arredondam intermediários; os valores persistidos e exibidos
usam quatro casas. Os scores originais já arredondados não são recalculados.

## Disponibilidade e seleção da foto

Somente uma avaliação com **exatamente uma foto**, análise concluída e score
postural válido pode usar essa foto na composição. O formulário não define foto
principal nem protocolo de seleção entre fases. Portanto, com várias fotos, o
final permanece indisponível, mesmo se apenas uma análise tiver sucesso. Não há
média, escolha pelo ID ou escolha da melhor/pior pontuação. Cada resultado individual
continua visível, inclusive seu valor invertido.

ACWR deve ser numérico, finito e não negativo. Postural e subjetivo devem ser
numéricos, finitos e estar entre 0 e 1. Booleanos e textos são rejeitados. Ausências
não viram zero e não há média parcial. O final também fica indisponível quando o
ACWR sinaliza `historico_incompleto`, conforme a referência metodológica; o ACWR
bruto, o normalizado e os avisos continuam disponíveis. Carga estimada por RPE do
formulário mantém seu aviso e não bloqueia a composição por si só.

## Persistência e tela

O resultado consolidado fica em `avaliacoes.detalhes.score_final`, JSON já existente,
e é retornado pela API, sem nova tabela, coluna ou migração. A atualização ocorre
após o processamento das fotos, nas novas tentativas e ao consultar o detalhe do envio.
Assim, uma nova tentativa bem-sucedida substitui o valor ausente da foto nesse bloco.
A fórmula será executada novamente na consulta, inclusive para registros anteriores.

O bloco contém `versao`, `status`, `motivos`, valores originais, normalizados e
`foto_id` selecionada. Modalidade/fase permanecem no registro dessa foto, e origem
do RPE e avisos de qualidade permanecem em `detalhes.acwr`. Campos legados como
`score_risco` não são reutilizados. Registros antigos são atualizados ao consultar
o detalhe, sem processamento em massa.

`Concluido.jsx` recebe o JSON na consulta e nas novas tentativas e o repassa para
`ResultadosAnalise.jsx`. O React apenas formata os valores; não repete os cálculos.
ACWR bruto e imagens mantêm sua apresentação; os normalizados aparecem como texto
secundário. O cartão final mostra o valor ou o motivo da indisponibilidade.

Referência: `fundamentacao_imca_tcc.docx` (versão 1.0, outubro/2026), disponibilizada
em Downloads e confirmada pelo usuário em substituição ao nome com sufixo `(2)`.

## Validação

No diretório `backend`: `venv/Scripts/python.exe -m unittest discover -s tests -q`.
No diretório `frontend`: `node --test tests/resultados.test.mjs` e `npm run build`.
Os testes cobrem limites, tipos inválidos, precisão, ausência de componentes,
múltiplas fotos, persistência/consulta pela API e renderização dos cartões React.
Os testes de integração simulam a API postural; não são uma chamada real ao serviço.

## Limpeza

Foram removidos os serviços antigos `acwr.py`, `foto.py` e `risco.py`, a tela fora das
rotas `Resultado.jsx` e seus estilos/rótulos exclusivos. A dependência NumPy foi
removida porque era utilizada somente pelo serviço antigo de foto.

As tabelas e os campos existentes foram preservados. Em particular, o modelo legado
`SessaoTreino` ainda participa do mapeamento do banco e da exclusão em cascata;
removê-lo exige uma decisão de migração, não apenas apagar código sem importações.
