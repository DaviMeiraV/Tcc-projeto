# Sistema de Predição de Risco de Lesão — TCC

**Fase atual: coleta de dados.**

O software recebe e armazena os dados dos participantes (questionário, fotografias da prática
esportiva e arquivo de histórico de treino). Ao final do formulário o participante vê apenas a
confirmação de que os dados foram recebidos.

O **cálculo do score de risco ainda não está implementado**: a lógica de pontuação será definida
e validada cientificamente pelo autor do TCC, depois da primeira rodada de coletas.

Stack: **FastAPI + PostgreSQL + React (Vite)**.

---

## Como rodar

### 1. Banco de dados

```bash
docker compose up -d
```

Sobe um PostgreSQL 16 em `localhost:5433` (base `injuryrisk`, usuário/senha `postgres`).

> Se preferir usar um Postgres já instalado, ajuste `DATABASE_URL` em `backend/.env`.

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # já vem configurado para o docker-compose
uvicorn app.main:app --reload
```

API em <http://localhost:8000> · documentação interativa em <http://localhost:8000/docs>.

As tabelas são criadas automaticamente na subida da aplicação.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Interface em <http://localhost:5173>. O Vite faz proxy de `/api` e `/uploads` para o backend.

### 4. Testar

Crie uma conta em `/cadastro` e preencha o formulário. O arquivo `exemplo_treinos.csv`
(na raiz do projeto) serve como histórico de treino de exemplo. Ao finalizar, a tela confirma
que os dados foram recebidos; os registros ficam visíveis em `/historico`.

---

## Fluxo da aplicação

| Tela | Rota | Conteúdo |
|------|------|----------|
| Login / Cadastro | `/login`, `/cadastro` | Autenticação simples por e-mail e senha (JWT) |
| Etapa 1 | `/formulario` | Dados do participante + questionário com sliders 0-10 |
| Etapa 2 | `/formulario` | Upload de até 3 fotos (modalidade, fase, joelho) + CSV de treino |
| Etapa 3 | `/formulario` | Revisão de todos os dados antes do envio |
| Conclusão | `/concluido` | Confirmação de que os dados foram recebidos |
| Enviados | `/historico` | Lista dos formulários já enviados pela conta |

---

## O que ainda não está implementado

O **score de risco**. Essa é a contribuição científica do trabalho e será construída a partir
das respostas coletadas nesta fase, com validação na literatura.

Já existe estrutura pronta para receber essa lógica quando ela for definida:

- a tabela `avaliacoes` tem as colunas `score_risco`, `classificacao`, `acwr`, `carga_aguda`,
  `carga_cronica` e `detalhes`, hoje sempre nulas;
- a tabela `sessoes_treino` está criada para quando o CSV passar a ser interpretado;
- há rascunhos **não utilizados** em `backend/app/services/` (`acwr.py`, `foto.py`, `risco.py`)
  e em `frontend/src/pages/Resultado.jsx`. Eles não são importados por nenhuma rota e servem
  apenas como material de apoio — podem ser reescritos ou apagados.

## Formato do CSV de treino

Nesta fase o arquivo é apenas **armazenado**, sem leitura do conteúdo. O formato sugerido aos
participantes é a exportação do **Strava** ou do **Garmin**, que já traz data, duração,
distância e frequência cardíaca — campos que serão úteis quando o cálculo de carga for feito.

```csv
Activity Date,Activity Type,Elapsed Time,Distance,Average Heart Rate
2026-08-20 07:12:00,Run,2700,8200,152
```

O nome original do arquivo fica registrado em `avaliacoes.csv_nome_original`, e o arquivo em `uploads/`.

---

## Estrutura

```
backend/
  app/
    core/        configuração e segurança (bcrypt + JWT)
    routers/     auth.py, avaliacoes.py
    services/    acwr.py, foto.py, risco.py  (PARADOS — nao usados)
    models.py    tabelas: usuarios, avaliacoes, fotos, sessoes_treino
    schemas.py   validação de entrada e saída
    main.py
frontend/
  src/
    pages/       Autenticacao, Formulario (3 etapas), Concluido, Historico
                 Resultado.jsx (PARADO — fora das rotas)
    components/  campos, chips e sliders reutilizáveis
    lib/         cliente da API e listas de opções
uploads/         fotos e arquivos CSV enviados
docker-compose.yml
exemplo_treinos.csv
```

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/auth/cadastro` | Cria conta e devolve token |
| `POST` | `/auth/login` | Autentica e devolve token |
| `GET` | `/auth/eu` | Dados do usuário autenticado |
| `POST` | `/avaliacoes` | Envia o formulário completo (multipart) e registra os dados |
| `GET` | `/avaliacoes` | Lista os envios do usuário |
| `GET` | `/avaliacoes/{id}` | Detalha um envio |
| `DELETE` | `/avaliacoes/{id}` | Remove um envio e seus arquivos |

---

## Observações para a defesa do TCC

- Nesta fase o sistema **não emite nenhum diagnóstico nem pontuação** ao participante: apenas
  confirma o recebimento dos dados.
- As tabelas são criadas com `create_all` na subida — adequado para o MVP. Para produção,
  migre para **Alembic**.
- As fotos ficam em disco na pasta `uploads/`; para deploy real, use um bucket (S3 ou similar).
- `SECRET_KEY` em `.env` deve ser trocada antes de qualquer publicação.
