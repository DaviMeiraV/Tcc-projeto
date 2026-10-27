# Onde manipular os três scores

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
Não há média automática entre fotos, inversão de escala ou normalização do ACWR.

A linha `score_final = None` marca onde definir sua combinação. O resultado consolidado
fica em `avaliacoes.detalhes.score_final` e é retornado pela API. A atualização ocorre
após o processamento das fotos, nas novas tentativas e ao consultar o detalhe do envio.
Assim, uma nova tentativa bem-sucedida substitui o valor ausente da foto nesse bloco.
A fórmula será executada novamente na consulta, inclusive para registros anteriores.

O bloco visual de score final permanece reservado. Quando a fórmula estiver definida,
será necessário ligar o valor à sua exibição. Os scores individuais continuam iguais.

## Limpeza

Foram removidos os serviços antigos `acwr.py`, `foto.py` e `risco.py`, a tela fora das
rotas `Resultado.jsx` e seus estilos/rótulos exclusivos. A dependência NumPy foi
removida porque era utilizada somente pelo serviço antigo de foto.

As tabelas e os campos existentes foram preservados. Em particular, o modelo legado
`SessaoTreino` ainda participa do mapeamento do banco e da exclusão em cascata;
removê-lo exige uma decisão de migração, não apenas apagar código sem importações.
