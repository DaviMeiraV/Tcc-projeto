# Sistema de Predição de Risco de Lesão — TCC

Software que estima o risco de lesão de atletas de corrida e ciclismo a partir de três fontes:

1. **Questionário de prontidão** — dor, fadiga, sono, recuperação, RPE, histórico de lesão.
2. **Histórico de treino (ACWR)** — arquivo CSV do Strava/Garmin, com cálculo da razão carga aguda:crônica.
3. **Fotografias da prática esportiva** — análise postural automática (inclinação de tronco, simetria, alinhamento).

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

Crie uma conta em `/cadastro`, preencha o formulário e use o arquivo `exemplo_treinos.csv`
(na raiz do projeto) como histórico de treino — ele contém 24 sessões com um pico de carga
proposital na última semana, gerando um ACWR na zona de risco.

---

## Fluxo da aplicação

| Tela | Rota | Conteúdo |
|------|------|----------|
| Login / Cadastro | `/login`, `/cadastro` | Autenticação simples por e-mail e senha (JWT) |
| Etapa 1 | `/formulario` | Dados do participante + questionário com sliders 0-10 |
| Etapa 2 | `/formulario` | Upload de até 3 fotos (modalidade, fase, joelho) + CSV de treino |
| Etapa 3 | `/formulario` | Revisão de todos os dados antes do envio |
| Resultado | `/resultado/:id` | Escore de risco, ACWR, gráfico de carga, alertas e recomendações |
| Histórico | `/historico` | Todas as avaliações do usuário, com evolução do escore |

---

## Como o risco é calculado

O escore final vai de **0 a 100** e combina três blocos:

| Bloco | Peso | Base |
|-------|------|------|
| Questionário de prontidão | 40% | Dor, fadiga, sono, recuperação, RPE, lesão prévia, IMC, tempo de prática |
| Carga de treino (ACWR) | 40% | Razão aguda:crônica, monotonia de Foster, volume |
| Análise das fotografias | 20% | Desvios posturais detectados na imagem |

Quando um bloco não tem dados (sem CSV ou sem foto), **seu peso é redistribuído** entre os
blocos disponíveis, mantendo a escala de 0 a 100 comparável.

Classificação: `< 30` baixo · `30–54` moderado · `55–74` alto · `≥ 75` muito alto.

### ACWR

Carga da sessão = **duração (min) × RPE** (método sRPE de Foster). Quando o CSV não traz RPE,
ele é estimado a partir da frequência cardíaca média ou da velocidade.

```
ACWR = média diária dos últimos 7 dias / média diária dos últimos 28 dias
```

Faixas de referência (Gabbett, 2016): `< 0,80` subcarga · `0,80–1,30` faixa ideal ·
`1,31–1,50` atenção · `> 1,50` risco elevado.

### Análise da foto

A silhueta do atleta é isolada do fundo por contraste e gradiente, e sobre ela são medidos o
eixo principal do corpo (inclinação do tronco), a simetria lateral da distribuição de massa e
o alinhamento entre tronco e base de apoio. Esses valores, cruzados com a fase do movimento
declarada, geram alertas biomecânicos qualitativos.

Para melhores resultados: foto **de perfil**, corpo inteiro, fundo contrastante, câmera na
altura do quadril.

---

## Formato do CSV de treino

São reconhecidas automaticamente exportações do **Strava** e do **Garmin**. Para planilha
própria, basta ter uma coluna de data e uma de duração; distância, RPE e frequência cardíaca
são opcionais e melhoram a precisão.

```csv
Activity Date,Activity Type,Elapsed Time,Distance,Average Heart Rate
2026-08-20 07:12:00,Run,2700,8200,152
```

Duração aceita minutos, segundos ou `HH:MM:SS`; distância aceita metros ou quilômetros.

---

## Estrutura

```
backend/
  app/
    core/        configuração e segurança (bcrypt + JWT)
    routers/     auth.py, avaliacoes.py
    services/    acwr.py, foto.py, risco.py
    models.py    tabelas: usuarios, avaliacoes, fotos, sessoes_treino
    schemas.py   validação de entrada e saída
    main.py
frontend/
  src/
    pages/       Autenticacao, Formulario (3 etapas), Resultado, Historico
    components/  campos, chips e sliders reutilizáveis
    lib/         cliente da API e listas de opções
uploads/         fotos enviadas
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
| `POST` | `/avaliacoes` | Envia o formulário completo (multipart) e recebe a análise |
| `GET` | `/avaliacoes` | Lista as avaliações do usuário |
| `GET` | `/avaliacoes/{id}` | Detalha uma avaliação |
| `DELETE` | `/avaliacoes/{id}` | Remove uma avaliação e suas fotos |

---

## Observações para a defesa do TCC

- O resultado é uma **triagem exploratória de caráter acadêmico** e não substitui avaliação
  clínica presencial. Esse aviso aparece na tela de resultado.
- As tabelas são criadas com `create_all` na subida — adequado para o MVP. Para produção,
  migre para **Alembic**.
- As fotos ficam em disco na pasta `uploads/`; para deploy real, use um bucket (S3 ou similar).
- `SECRET_KEY` em `.env` deve ser trocada antes de qualquer publicação.
