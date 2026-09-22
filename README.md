# Sistema de Predição de Risco de Lesão — TCC

Sistema web para coleta de dados de atletas de **corrida** e **ciclismo**, base de um modelo de
predição de risco de lesão.

**Fase atual: coleta de dados.** O participante preenche um formulário em três etapas e recebe
apenas a confirmação de que os dados foram recebidos. O **cálculo do score de risco ainda não está
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
| Swagger (`/docs`) | Cada rota da API com exemplos, testável pelo navegador |

---

## O que o sistema coleta

| Etapa | Conteúdo |
|---|---|
| **1. Participante e questionário** | Idade, sexo, esporte, tempo de prática, peso, altura; esforço percebido, dor, fadiga, sono e recuperação (0 a 10); histórico de lesão e se a dor limita os treinos |
| **2. Arquivos** | Até 3 fotografias da prática esportiva, cada uma com modalidade, fase do movimento e joelho à frente; arquivo CSV com o histórico de treino |
| **3. Revisão** | Conferência de tudo antes do envio |

Ao finalizar, tudo vai para o PostgreSQL: respostas, fotos e CSVs. Nada é analisado nesta fase.

## Telas

| Rota | Tela |
|---|---|
| `/login`, `/cadastro` | Acesso por e-mail e senha |
| `/formulario` | Formulário em 3 etapas |
| `/concluido` | Confirmação de recebimento |
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
│       └── services/        rascunhos de score — PARADOS, não usados
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

- colunas `score_risco`, `classificacao`, `acwr`, `carga_aguda`, `carga_cronica` e `detalhes` na
  tabela `avaliacoes`, hoje sempre nulas;
- tabela `sessoes_treino`, para quando o CSV passar a ser interpretado;
- rascunhos **não utilizados** em `backend/app/services/` e `frontend/src/pages/Resultado.jsx`,
  que não são importados por nenhuma rota e podem ser reescritos ou apagados.

## Observações

- O sistema **não emite diagnóstico nem pontuação** ao participante nesta fase.
- As tabelas são criadas automaticamente na subida; não há migrations
  ([ver como alterar o esquema](docs/BANCO-DE-DADOS.md#alterando-o-esquema)).
- Fotos e CSVs ficam no próprio banco, então nada se perde em deploys ou reinícios
  ([detalhes](docs/DEPLOY.md#onde-ficam-as-fotos-e-os-csvs)).
