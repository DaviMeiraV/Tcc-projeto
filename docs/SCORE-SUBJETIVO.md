# Score dos dados do atleta

Implementa o Índice de Condição Subjetiva do Atleta (ICSA), versão 2, conforme o documento
`Fundamentacao_ICSA_Pesos_Iguais_Revisada - Copia.docx` (outubro de 2026),
com as respostas existentes no formulário. Essa revisão substitui a ponderação
anterior ainda descrita na seção do ICSA de `fundamentacao_imca_tcc.docx`.
É um índice experimental de 0 a 1: valores maiores representam condição subjetiva
mais desfavorável. Não é probabilidade de lesão, não é OSTRC e não recebe classificação
clínica de risco baixo, médio ou alto.

| Resposta | Componente normalizado | Peso |
|---|---|---|
| Dor | dor / 10 | 1/6 |
| Fadiga | fadiga / 10 | 1/6 |
| Sono | (10 − sono) / 10 | 1/6 |
| Recuperação | (10 − recuperação) / 10 | 1/6 |
| Dor limita treino | Sim = 1; Não = 0 | 1/6 |
| Lesão prévia | Sim = 1; Não = 0 | 1/6 |

O escore é a soma dos seis componentes normalizados dividida por seis,
arredondada a quatro casas decimais somente ao final. Cada peso é calculado como
`1 / 6`, sem arredondá-lo previamente para 0,1667. As contribuições guardadas com
quatro casas servem ao detalhamento; o total não é a soma dessas contribuições
já arredondadas. Os pesos são decisões
experimentais da proposta, sem validação clínica. RPE, idade, sexo, peso, altura,
tempo de prática e recência da lesão não entram na fórmula.

Exemplo revisado: dor 6, fadiga 4, sono 7, recuperação 5, limitação por dor Sim
e lesão prévia Não resultam em `(0,6 + 0,4 + 0,3 + 0,5 + 1 + 0) / 6 = 0,4667`.
Na versão 1, as mesmas respostas produziam 0,5300. As respostas são utilizadas como informadas,
sem corrigir automaticamente a combinação dor zero e limitação por dor Sim.

O backend calcula no envio e atualiza registros de outra versão ao abrir seus
detalhes ou tentar novamente as análises.
O JSON `avaliacoes.detalhes.score_subjetivo` guarda versão, pesos, respostas brutas
utilizadas, componentes normalizados, contribuições e resultado. Os demais dados
e resultados, inclusive ACWR, são preservados. Não é necessária nova coluna no banco.
Se faltar uma resposta ou ela for inválida, o escore fica indisponível, com os campos
identificados; não há preenchimento por zero ou redistribuição dos pesos.

Antes de substituir um cálculo anterior, o backend acrescenta uma cópia independente
em `detalhes.historico_scores`, contendo `arquivado_em` (UTC),
`motivo: atualizacao_icsa`, `versao_icsa_destino: 2`, `score_subjetivo` e `score_final`.
Os blocos anteriores são preservados integralmente, inclusive pesos e respostas quando
registrados; dados legados ausentes não são inventados. A data é a do arquivamento,
não uma estimativa da data do cálculo original. Consultas repetidas à versão 2 não
criam novas entradas. Novas avaliações não recebem um histórico artificial.

A versão 1 usava pesos 0,25; 0,15; 0,15; 0,15; 0,20; 0,10, respectivamente.
Essa fórmula fica identificada nos registros históricos, e não é usada em novos cálculos.

O bloco **Score dos dados do atleta** mostra apenas o ICSA atualizado e explica
os pesos iguais. Os resultados anteriores ficam preservados internamente para
rastreabilidade, sem opção de consulta na tela. O IMCA passa a usar o ICSA recalculado,
mantendo a média `(C + ICSA + B) / 3` e as transformações de ACWR e postura.
`detalhes.score_final.versao_icsa` identifica a versão subjetiva consumida.
A atualização é feita por avaliação ao consultar/reanalisar, sem migração de esquema
ou recálculo em massa do banco.

Código: `backend/app/services/score_subjetivo.py`.
Testes: `python -m unittest discover -s tests -v` dentro de `backend`.
