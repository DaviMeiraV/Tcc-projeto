# Sistema de Predição de Risco de Lesão — TCC

Sistema web para coleta de dados de atletas de **corrida** e **ciclismo**, base de um modelo de
predição de risco de lesão.

**Fase atual: coleta de dados e análise postural das fotos.** O participante preenche um formulário
em três etapas e pode consultar as imagens tratadas pela API externa. O **cálculo do score de risco ainda não está
implementado**: a lógica será definida e validada cientificamente pelo autor do TCC a partir das
respostas coletadas.

**Stack:** FastAPI · PostgreSQL · React (Vite) · Docker

---

## Rodar em 1 minuto

Com o [Docker Desktop](https://www.docker.com/products/docker-desktop/) aberto:

```bash
docker compose up --build
```

| Endereço | O quê |
|---|---|
| <http://localhost:8000> | Sistema |
| <http://localhost:8000/docs> | Swagger (documentação interativa da API) |

## Documentação

| Guia | Conteúdo |
|---|---|
| [Como rodar](docs/COMO-RODAR.md) | Docker, modo de desenvolvimento, variáveis de ambiente, testes e problemas comuns |
| [Banco de dados](docs/BANCO-DE-DADOS.md) | Diagrama, todas as tabelas e colunas, onde ficam os arquivos, consultas para exportar a coleta |
| [Deploy gratuito](docs/DEPLOY.md) | Passo a passo no Neon + Render, limites do plano gratuito |
| [Análise postural](docs/ANALISE-POSTURAL.md) | Configuração da API externa, envio das fotos, resultados e novas tentativas |
| [ACWR](docs/ACWR.md) | Leitura da planilha, cálculo das cargas e logs |
| Swagger (`/docs`) | Cada rota da API com exemplos, testável pelo navegador |

---

## O que o sistema coleta

| Etapa | Conteúdo |
|---|---|
| **1. Participante e questionário** | Idade, sexo, esporte, tempo de prática, peso, altura; esforço percebido, dor, fadiga, sono e recuperação (0 a 10); histórico de lesão e se a dor limita os treinos |
| **2. Arquivos** | Até 3 fotografias da prática esportiva, cada uma com modalidade, fase do movimento e joelho à frente; arquivo CSV com o histórico de treino |
| **3. Revisão** | Conferência de tudo antes do envio |

Ao finalizar, tudo vai para o PostgreSQL: respostas, fotos e CSVs. As fotos são então enviadas
à API postural; seus resultados e PNGs tratados também ficam salvos no banco.

## Telas

| Rota | Tela |
|---|---|
| `/login`, `/cadastro` | Acesso por e-mail e senha |
| `/formulario` | Formulário em 3 etapas |
| `/concluido` | Confirmação de recebimento |
| `/concluido/{id}` | Detalhe do envio, imagens tratadas e novas tentativas de análise |
| `/historico` | Formulários já enviados pela conta |

## API

Todas as rotas ficam sob `/api`. Detalhes, exemplos e testes em `/docs`.

| Método | Rota | Descrição | Token |
|---|---|---|---|
| `POST` | `/api/auth/cadastro` | Cria conta e devolve o token | |
| `POST` | `/api/auth/login` | Autentica e devolve o token | |
| `GET` | `/api/auth/eu` | Dados do usuário autenticado | ✓ |
| `POST` | `/api/avaliacoes` | Envia o formulário (`multipart/form-data`) | ✓ |
| `GET` | `/api/avaliacoes` | Lista os envios do usuário | ✓ |
| `GET` | `/api/avaliacoes/{id}` | Detalha um envio | ✓ |
| `POST` | `/api/avaliacoes/{id}/analises` | Tenta novamente as análises não concluídas | ✓ |
| `DELETE` | `/api/avaliacoes/{id}` | Exclui um envio e seus arquivos | ✓ |
| `GET` | `/api/saude` | Status do serviço | |

---

## Estrutura

```
├── Dockerfile               imagem única: compila o React e serve tudo pela API
├── docker-compose.yml       banco + aplicação para rodar localmente
├── render.yaml              configuração do deploy no Render
├── docs/                    guias do projeto
├── backend/
│   └── app/
│       ├── main.py          criação da API, Swagger e entrega das telas
│       ├── models.py        tabelas do banco
│       ├── schemas.py       validação de entrada e saída
│       ├── db.py            conexão com o PostgreSQL
│       ├── armazenamento.py fotos e CSVs gravados no banco
│       ├── core/            configuração e segurança (bcrypt + JWT)
│       ├── routers/         rotas: auth.py, avaliacoes.py
│       └── services/        integração postural e rascunhos de score ainda parados
├── frontend/
│   └── src/
│       ├── pages/           Autenticacao, Formulario, Concluido, Historico
│       │                    (Resultado.jsx: rascunho PARADO, fora das rotas)
│       ├── components/      campos, chips e sliders reutilizáveis
│       └── lib/             cliente da API e listas de opções
└── exemplo_treinos.csv      histórico de treino de exemplo para testes
```

## O que ainda não está implementado

O **score de risco** — a contribuição científica do trabalho. A estrutura para recebê-lo já existe:

- colunas `score_risco` e `classificacao` na tabela `avaliacoes`, ainda nulas;
- `acwr`, `carga_aguda`, `carga_cronica` e `detalhes.acwr` já recebem o cálculo da planilha;
- tabela `sessoes_treino`, para quando o CSV passar a ser interpretado;
- rascunhos **não utilizados** em `backend/app/services/foto.py`, `acwr.py`, `risco.py` e `frontend/src/pages/Resultado.jsx`,
  que não são importados por nenhuma rota e podem ser reescritos ou apagados.

## Observações

- O sistema exibe o score postural retornado pela API (0 a 1), sem calcular o score combinado de risco.
- As tabelas são criadas e as colunas de CSV de bancos antigos são adicionadas automaticamente na subida
  ([ver como alterar o esquema](docs/BANCO-DE-DADOS.md#alterando-o-esquema)).
- Fotos e CSVs ficam no próprio banco, então nada se perde em deploys ou reinícios
  ([detalhes](docs/DEPLOY.md#onde-ficam-as-fotos-e-os-csvs)).
