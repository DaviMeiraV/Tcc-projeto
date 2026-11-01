# Auditoria de documentação e desuso do repositório

Data: 31 de outubro de 2026.

A auditoria encontrou documentação desatualizada sobre os cálculos já implementados, instruções operacionais inconsistentes e uma regra CSS sem referência. Não foram identificados arquivos fonte órfãos ou dependências diretas comprovadamente sem uso. Alguns elementos sem escrita atual são legados de banco e não devem ser removidos apenas por esse motivo.

## Alteração de interface concluída

O cartão do ICSA apresenta somente o score atualizado e a explicação dos seis componentes com pesos iguais. Foi removida a opção de consultar versões anteriores dos scores. O componente não recebe mais o histórico da página de resultado.

O arquivamento interno dos cálculos anteriores permanece no backend para preservar a rastreabilidade da mudança de fórmula; isso não cria uma opção de visualização na interface. A página Histórico de envios continua sendo a lista de avaliações realizadas, uma funcionalidade distinta do painel de versões removido.

As descrições da interface em `SCORE-SUBJETIVO.md`, `SCORE-FINAL.md` e na nota de atualização de `REVISAO-CONFORMIDADE-TCC.md` foram ajustadas. Os demais achados abaixo foram identificados para correção posterior, sem remoção de arquivos ou alteração de banco nesta etapa.

Validação desta alteração: **5 testes de frontend aprovados e compilação de produção concluída**. O teste de regressão fornece dados históricos ao componente e verifica que nem os valores antigos nem a opção de consulta aparecem. Não houve alteração de lógica de backend nesta etapa.

## Documentação desatualizada ou incompleta

As linhas referem-se ao estado local inspecionado, incluindo as alterações do ICSA versão 2 ainda não commitadas.

| Prioridade | Local | Problema e evidência | Correção proposta |
|---|---|---|---|
| Alta | `README.md:6–8,106–117`; `docs/ACWR.md:16–17`; `docs/ANALISE-POSTURAL.md:49` | Textos apresentam o questionário ou a composição como não implementados. `backend/app/services/score_subjetivo.py:73` calcula o ICSA e `score_final.py:75` calcula o consolidado; as rotas executam ambos. | Apresentar ICSA v2 e IMCA experimental como implementados. Separar essa funcionalidade da predição clinicamente validada, que não foi demonstrada. |
| Alta | `backend/app/main.py:23–35`; `backend/app/schemas.py:95` | A descrição pública da API e a docstring da resposta ainda indicam ausência de score combinado. `main.py:53` usa essa descrição no Swagger; o JSON atual devolve `detalhes.score_final`. | Atualizar a descrição do Swagger e o contrato documentado da resposta. |
| Média | `docs/BANCO-DE-DADOS.md:70,167–168` | Afirma que o CSV fica sem leitura e que as sessões serão implementadas futuramente. `carga_treino.py:241–299` interpreta as atividades e guarda `sessoes` no resultado. | Explicar `detalhes.acwr.sessoes` como armazenamento atual do cálculo e `sessoes_treino` como tabela legada. |
| Média | `backend/app/models.py:93` | A docstring de `SessaoTreino` diz que suas linhas são usadas no cálculo do ACWR. O serviço atual trabalha com dicionários derivados do CSV; não instancia esse modelo. | Identificar a finalidade de compatibilidade e cascata do modelo legado. |
| Média | `docs/BANCO-DE-DADOS.md:139–150` | A descrição do JSON não detalha seus blocos atuais e a tabela chama `score_risco` de pontuação final, embora o texto diga que permanece nulo. O resultado real é persistido em `score_final.py:99`, no JSON. | Documentar `acwr`, `score_subjetivo`, `score_final` e `historico_scores`, distinguindo os campos legados das saídas atuais. |
| Média | `docs/DEPLOY.md:58–59,138–143`; tabela de variáveis em `docs/COMO-RODAR.md` | Os guias gerais omitem `ANALISE_API_URL` e `ANALISE_API_TIMEOUT`. Essas configurações existem em `core/config.py:15–16`, `docker-compose.yml` e `render.yaml:24–27`. O Compose não inicia a API postural separada. | Incluir as duas variáveis e explicar que o serviço postural deve estar disponível separadamente; apontar para `ANALISE-POSTURAL.md`. Evitar que “um comando sobe tudo” seja interpretado como incluindo essa API. |
| Média | Final de `docs/COMO-RODAR.md`, em “Adicionei uma coluna” | Afirma genericamente que tabelas não são alteradas. `backend/app/migracoes.py:22–28` adiciona explicitamente duas colunas CSV em bancos antigos. | Explicar que alterações arbitrárias não são automáticas, mas existem migrações aditivas específicas. |
| Baixa | `docs/ACWR.md:86` | Referência à função `calcular_csv`, inexistente. A função atual é `calcular_acwr`, em `carga_treino.py:241`. | Corrigir o nome no guia de leitura do código. |
| Baixa | `docs/COMO-RODAR.md:36` | Nome do banco escrito como `injuryqrisk`; `docker-compose.yml:14` cria `injuryrisk`. | Corrigir o nome na tabela de conexão. |
| Baixa | `docs/BANCO-DE-DADOS.md:118`; `frontend/src/lib/opcoes.js:44` | Descrição da escala de RPE começa em 1, mas o schema e o slider aceitam 0 (`schemas.py:69`, `Campos.jsx:60`). | Alinhar os textos à escala 0–10 aceita pelo sistema, explicando o significado de zero conforme a metodologia. |
| Baixa | `docs/BANCO-DE-DADOS.md:111–112` | Intervalos descritos como 20–250 kg e 100–250 cm não deixam claro que os mínimos são exclusivos. `schemas.py:66–67` usa `gt=20` e `gt=100`. | Descrever peso maior que 20 e até 250; altura maior que 100 e até 250. |

Também há rótulos de “Predição de Risco de Lesão” em `frontend/src/App.jsx:30`, `frontend/src/pages/Autenticacao.jsx:32` e no título da API. São nomes ativos, não código morto. Convém harmonizar essa identificação com o caráter experimental do IMCA, já explicado nos cartões de resultado e nos documentos metodológicos.

## Elementos sem uso e legados

| Classificação | Local e evidência | Recomendação |
|---|---|---|
| Sem uso confirmado no código atual | `frontend/src/styles.css:228`: `.resultado-reservado { min-height: 150px; }`. Não foi encontrada aplicação dessa classe nos arquivos JS/JSX. | Candidata a remoção simples. |
| Marcador de diretório dispensável ao funcionamento atual | `uploads/.gitkeep`. `backend/app/armazenamento.py:43–46` grava o conteúdo na tabela `Arquivo`; `main.py:96–100` o lê do banco. | O marcador pode ser removido. A URL `/uploads/{nome}` deve permanecer: é um endpoint ativo, não uma pasta de arquivos estáticos. As regras de ignore podem continuar como proteção. |
| Legado sem escrita atual, com função de compatibilidade | `backend/app/models.py:72–74,92–105`: `SessaoTreino` e `Avaliacao.sessoes`. O relacionamento tem cascata; o cálculo atual persiste sessões em JSON. | Manter até verificar dados em bancos existentes e planejar migração. Não classificar como remoção segura apenas pela ausência de novas inserções. |
| Colunas legadas sem participação no cálculo atual | `backend/app/models.py:66–67`: `score_risco` e `classificacao`. O consolidado fica em `detalhes.score_final`. | Manter por compatibilidade até eventual migração. Não criar classificações clínicas para justificar o uso dessas colunas. |
| Endpoint ativo sem consumidor frontend encontrado | `backend/app/routers/auth.py:70–72`: `GET /api/auth/eu`. Registrado pela aplicação e documentado no README. | Manter como contrato da API. A ausência de chamada React não comprova ausência de consumidores externos. |
| Import necessário apesar de não ter referência lexical | `backend/app/migracoes.py:14`: `import app.models`. Registra os modelos antes de `Base.metadata.create_all`. | Manter. Uma remoção baseada somente em análise de nomes pode impedir a criação das tabelas. |
| Dados internos intencionalmente fora da interface | `detalhes.historico_scores`, em `score_subjetivo.py:87–100`. Preserva os cálculos substituídos na mudança de versão. | Manter para rastreabilidade. A ausência de visualização do histórico agora é o comportamento solicitado, não evidência de código morto. |

Não houve evidência suficiente para recomendar apagar qualquer documento Markdown inteiro. Documentos auxiliares sem link direto no README ainda descrevem partes usadas do sistema. A revisão de conformidade é um registro histórico com uma nota de atualização; seu corpo não deve ser confundido com uma descrição atual de tudo que permanece pendente.

## Cobertura e limites

Foram examinados os arquivos fonte Python e React, imports, exports, rotas, referências de estilos, dependências declaradas, configuração de build e implantação, README, guias em `docs` e documentação incorporada à API. As verificações de documentação e desuso foram feitas em paralelo e consolidadas com a alteração de interface.

Todas as dependências diretas examinadas têm uso identificado, inclusive usos indiretos: `uvicorn` no comando do Dockerfile, `psycopg` na conexão SQLAlchemy, `python-multipart` nos formulários e uploads, e o extra `pydantic[email]` em `EmailStr`. Todos os componentes e páginas React examinados têm consumidores. A análise de referências não substitui evidência de uso em produção.

Não foram consultados dados reais dos bancos nem clientes externos da API. Arquivos gerados, ambientes virtuais, `node_modules` e conteúdos secretos não foram usados como evidência de código mantido pelo projeto. Planos, quotas e garantias dos provedores citados em `DEPLOY.md` e comentários não foram verificados externamente; não são classificados aqui como incorretos. Devem ser verificados nas fontes oficiais quando o guia de hospedagem for atualizado.

## Ordem sugerida para a próxima limpeza

1. Atualizar README, Swagger e guias para descrever corretamente o ICSA v2 e o IMCA implementado.
2. Corrigir instruções de conexão, variáveis da API postural, escala do RPE e nomes de funções.
3. Documentar os blocos JSON e identificar explicitamente os legados do banco.
4. Remover a regra CSS sem uso e, se desejado, o marcador de diretório dispensável.
5. Tratar qualquer remoção de tabelas, colunas ou endpoints como alteração própria, com verificação dos consumidores e dados existentes.
