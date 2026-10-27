# Score dos dados do atleta

Implementa o Índice de Condição Subjetiva do Atleta (ICSA), conforme o documento
`proposta_score_subjetivo_tcc.docx`, com as respostas existentes no formulário.
É um índice experimental de 0 a 1: valores maiores representam condição subjetiva
mais desfavorável. Não é probabilidade de lesão, não é OSTRC e não recebe classificação
clínica de risco baixo, médio ou alto.

| Resposta | Componente normalizado | Peso |
|---|---|---|
| Dor | dor / 10 | 0,25 |
| Fadiga | fadiga / 10 | 0,15 |
| Sono | (10 − sono) / 10 | 0,15 |
| Recuperação | (10 − recuperação) / 10 | 0,15 |
| Dor limita treino | Sim = 1; Não = 0 | 0,20 |
| Lesão prévia | Sim = 1; Não = 0 | 0,10 |

O escore é a soma dos seis componentes multiplicados pelos respectivos pesos,
arredondada a quatro casas decimais somente ao final. Os pesos são decisões
experimentais da proposta, sem validação clínica. RPE, idade, sexo, peso, altura,
tempo de prática e recência da lesão não entram na fórmula.

Exemplo da proposta: dor 0, fadiga 0, sono 5, recuperação 5, limitação por dor Sim
e lesão prévia Sim resultam em **0,45**. As respostas são utilizadas como informadas,
sem corrigir automaticamente a combinação dor zero e limitação por dor Sim.

O backend calcula no envio e preenche registros antigos ao abrir seus detalhes.
O JSON `avaliacoes.detalhes.score_subjetivo` guarda versão, pesos, respostas brutas
utilizadas, componentes normalizados, contribuições e resultado. Os demais dados
e resultados, inclusive ACWR, são preservados. Não é necessária nova coluna no banco.
Se faltar uma resposta ou ela for inválida, o escore fica indisponível, com os campos
identificados; não há preenchimento por zero ou redistribuição dos pesos.

A única mudança visual ocorre no bloco **Score dos dados do atleta** da tela final.
O formulário e o score final combinado permanecem inalterados. A transformação do
ACWR e os pesos globais ainda precisam ser definidos antes de implementar a agregação.

Código: `backend/app/services/score_subjetivo.py`.
Testes: `python -m unittest discover -s tests -v` dentro de `backend`.
