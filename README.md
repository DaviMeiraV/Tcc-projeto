# Sistema de Predição de Risco de Lesão — TCC

Sistema web para coleta de dados de atletas de **corrida** e **ciclismo** e cálculo do
Índice Multidimensional de Condição do Atleta (IMCA), um indicador experimental.

**Fase atual: coleta e cálculo de ACWR, ICSA e IMCA, com análise postural das fotos.**
O participante preenche um formulário em três etapas e consulta os scores atualizados,
suas explicações e as imagens tratadas pela API externa. O ICSA versão 2 usa pesos iguais
nas seis dimensões. O IMCA combina carga, condição subjetiva e postura quando os três
componentes atendem às regras de disponibilidade. Não representa probabilidade clínica
de lesão; a validação preditiva permanece como etapa futura.

**Stack:** FastAPI · PostgreSQL · React (Vite) · Docker

---

## Rodar em 1 minuto

Com o [Docker Desktop](https://www.docker.com/products/docker-desktop/) aberto:

```bash
docker compose up --build
```

Esse comando inicia o banco e a aplicação web. A **API postural é um serviço separado**:
configure `ANALISE_API_URL` para um endereço acessível pelo backend. No Compose, o padrão
é `http://host.docker.internal:8001`. Veja [Análise postural](docs/ANALISE-POSTURAL.md).

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
| [ICSA](docs/SCORE-SUBJETIVO.md) | Seis componentes subjetivos com pesos iguais e preservação interna de versões |
| [Score final](docs/SCORE-FINAL.md) | Padronização dos três componentes, média e regras de disponibilidade |
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
│       └── services/        análise postural, ACWR, ICSA e consolidação dos scores
├── frontend/
│   └── src/
│       ├── pages/           Autenticacao, Formulario, Concluido, Historico
│       ├── components/      campos, chips e sliders reutilizáveis
│       └── lib/             cliente da API e listas de opções
└── exemplo_treinos.csv      histórico de treino de exemplo para testes
```

## Resultados implementados e limites

- o ICSA versão 2 fica em `detalhes.score_subjetivo`, com componentes, pesos e respostas;
- `acwr`, `carga_aguda`, `carga_cronica` e `detalhes.acwr` já recebem o cálculo da planilha;
- `services/score_final.py` padroniza ACWR e postura e guarda o IMCA em `detalhes.score_final`, incluindo a versão do ICSA utilizada;
- resultados anteriores são preservados internamente em `detalhes.historico_scores` na troca de versão do ICSA; a tela mostra somente os scores atualizados;
- colunas legadas `score_risco` e `classificacao` não são preenchidas pelos cálculos atuais;
- o mapeamento legado `sessoes_treino` é mantido para preservar a compatibilidade com bancos existentes e a exclusão em cascata. O cálculo atual guarda suas sessões em `detalhes.acwr`.

O IMCA fica indisponível quando falta um componente válido, o histórico é marcado como
incompleto ou há várias fotos sem protocolo de seleção. Não há classificação clínica
de risco nem predição validada de lesões. Veja [Score final](docs/SCORE-FINAL.md).

## Observações

- O sistema exibe o score postural de cada foto, o ACWR, o ICSA e o IMCA disponível, com suas explicações.
- As tabelas são criadas e as colunas de CSV de bancos antigos são adicionadas automaticamente na subida
  ([ver como alterar o esquema](docs/BANCO-DE-DADOS.md#alterando-o-esquema)).
- Fotos e CSVs ficam no próprio banco, então nada se perde em deploys ou reinícios
  ([detalhes](docs/DEPLOY.md#onde-ficam-as-fotos-e-os-csvs)).
