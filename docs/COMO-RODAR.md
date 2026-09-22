# Como rodar o projeto

Há dois jeitos. Para **usar ou apresentar** o sistema, use o Docker: um comando sobe tudo. Para
**mexer no código** com recarga automática, use o modo de desenvolvimento.

---

## Opção A — Docker (recomendado)

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e **aberto**
  (o ícone da baleia precisa estar ativo na bandeja do Windows)
- Git

### Subir

```bash
git clone https://github.com/DaviMeiraV/Tcc-projeto.git
cd Tcc-projeto
docker compose up --build
```

Na primeira vez leva alguns minutos (baixa as imagens e compila o frontend). Está pronto quando o
terminal mostrar:

```
tcc_app  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

| Endereço | O quê |
|---|---|
| <http://localhost:8000> | Sistema (login, formulário) |
| <http://localhost:8000/docs> | Swagger — documentação interativa da API |
| <http://localhost:8000/redoc> | Mesma documentação, em formato de leitura |
| `localhost:5433` | PostgreSQL (usuário `postgres`, senha `postgres`, banco `injuryrisk`) |

O que sobe:

| Container | Imagem | Função |
|---|---|---|
| `tcc_postgres` | `postgres:16-alpine` | Banco de dados |
| `tcc_app` | construída pelo `Dockerfile` | API FastAPI servindo também as telas React |

### Comandos do dia a dia

```bash
docker compose up -d --build     # sobe em segundo plano (libera o terminal)
docker compose logs -f app       # acompanha os logs da aplicação
docker compose ps                # mostra o que está rodando
docker compose down              # desliga (os dados continuam salvos)
docker compose down -v           # desliga e APAGA banco e arquivos enviados
```

Mudou algum código? Rode `docker compose up -d --build` de novo para reconstruir a imagem.

Banco e arquivos enviados ficam em volumes do Docker (`dados_postgres` e `uploads`), então
sobrevivem a `down` e a reinícios do computador. Só `down -v` os apaga.

---

## Opção B — Desenvolvimento

Frontend e backend rodam separados, cada um recarregando sozinho ao salvar um arquivo. O banco
continua no Docker.

### Pré-requisitos

- Docker Desktop (só para o banco)
- Python 3.12 ou mais recente
- Node.js 20 ou mais recente

### 1. Banco

```bash
docker compose up -d db
```

### 2. Backend — terminal 1

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate           # Windows (PowerShell ou cmd)
# source .venv/bin/activate      # Linux / macOS / Git Bash
pip install -r requirements.txt
copy .env.example .env           # Linux/macOS: cp .env.example .env
uvicorn app.main:app --reload
```

API em <http://localhost:8000>, Swagger em <http://localhost:8000/docs>.

### 3. Frontend — terminal 2

```bash
cd frontend
npm install
npm run dev
```

Sistema em <http://localhost:5173>. O Vite repassa `/api`, `/uploads` e `/docs` para a API na
porta 8000 (configurado em `frontend/vite.config.js`), então não é preciso configurar CORS nem
endereço da API.

> Não rode a Opção A e a Opção B ao mesmo tempo: as duas usam a porta 8000.
> Antes de começar a B, desligue o container da aplicação com `docker compose stop app`.

---

## Variáveis de ambiente

O backend lê de `backend/.env` (modo desenvolvimento) ou do ambiente (Docker e Render).
Um modelo pronto está em [`backend/.env.example`](../backend/.env.example).

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5433/injuryrisk` | Conexão com o banco. Aceita também `postgresql://` e `postgres://`, como Neon e Render entregam |
| `SECRET_KEY` | `dev-secret-change-me` | Assina os tokens de login. **Troque em produção** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Validade do login (24 horas) |
| `UPLOAD_DIR` | `../uploads` | Onde fotos e CSVs são gravados |
| `STATIC_DIR` | `static` | Build do React. Se existir, a API também serve as telas |
| `CORS_ORIGINS` | `http://localhost:5173` | Origens liberadas para chamar a API, separadas por vírgula |
| `PORT` | `8000` | Porta do servidor dentro do container |

---

## Testando

### Pela interface

1. Abra o sistema e clique em **Cadastre-se**.
2. Preencha as 3 etapas. O arquivo [`exemplo_treinos.csv`](../exemplo_treinos.csv) serve como
   histórico de treino.
3. Ao clicar em **Finalizar**, a tela confirma o recebimento.
4. O envio aparece em **Histórico**, no menu do topo.

### Pelo Swagger

1. Abra `/docs`.
2. Em **auth → POST /api/auth/cadastro**, clique em *Try it out* → *Execute*. O corpo já vem
   preenchido com um exemplo; troque o e-mail se ele já existir.
3. Copie o valor de `access_token` da resposta.
4. Clique em **Authorize** (cadeado, no topo), cole o token e confirme.
5. Em **avaliacoes → POST /api/avaliacoes**, *Try it out*: o campo `payload` já vem com um JSON
   de exemplo. Anexe fotos e CSV se quiser (lembrando que cada foto precisa de um item em
   `fotos_meta` e de `"consentimento_foto": true`) e clique em *Execute*.

O token fica salvo no navegador mesmo recarregando a página do Swagger.

### Pelo terminal

```bash
curl http://localhost:8000/api/saude

curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"voce@exemplo.com","senha":"123456"}'
```

---

## Problemas comuns

**`error during connect ... dockerDesktopLinuxEngine`**
O Docker Desktop não está aberto. Abra, espere a baleia ficar estável e rode de novo.

**`port is already allocated` / porta 8000 ou 5433 em uso**
Outro programa está usando a porta. Pare o que estiver rodando (uma API iniciada pela Opção B,
por exemplo) ou troque o lado esquerdo do mapeamento em `docker-compose.yml`
(`"8001:8000"` e acesse `localhost:8001`).

**A tela abre mas o login falha com erro de conexão**
O banco não subiu. Veja com `docker compose ps` se `tcc_postgres` está `healthy`.

**Adicionei uma coluna em `models.py` e a aplicação quebrou**
As tabelas são criadas automaticamente, mas **não alteradas**. Veja
[Alterando o esquema](BANCO-DE-DADOS.md#alterando-o-esquema).

**`pip install` falha compilando `numpy` no Windows**
Versões antigas não têm pacote pronto para Python recente. Atualize o pip
(`python -m pip install --upgrade pip`) e instale de novo; o `requirements.txt` já pede versões
compatíveis com Python 3.14.
