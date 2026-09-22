# Deploy gratuito

O sistema fica no ar sem custo usando dois serviços:

| Peça | Onde | Plano | Por quê |
|---|---|---|---|
| Banco PostgreSQL | [Neon](https://neon.com) | Free | Gratuito **permanente**, sem cartão de crédito |
| API + telas + Swagger | [Render](https://render.com) | Free | Roda o `Dockerfile` do projeto direto do GitHub |

Respostas, fotos e CSVs ficam **todos no banco**, que é permanente.

```mermaid
flowchart LR
    U[Participante<br/>navegador] -->|HTTPS| R[Render<br/>container Docker<br/>React + FastAPI]
    R -->|SQL / SSL| N[(Neon<br/>PostgreSQL<br/>respostas + fotos + CSVs)]
```

> **Por que o banco não fica no Render?** O Postgres gratuito do Render **expira 30 dias após a
> criação**. Para uma coleta de pesquisa isso significaria perder os dados. O Neon não expira.

Tempo total: uns 15 minutos, quase todo esperando o primeiro build.

---

## Passo 1 — Banco no Neon

1. Acesse [neon.com](https://neon.com) e crie a conta (dá para entrar com o GitHub).
2. Crie um projeto:
   - **Project name:** `tcc-risco-lesao`
   - **Postgres version:** 16 ou mais recente
   - **Region:** `AWS US East 1 (N. Virginia)` — a mesma região do Render, o que deixa as consultas mais rápidas
3. No painel do projeto, clique em **Connect**.
4. **Desmarque "Connection pooling"** e copie a connection string. Ela tem este formato:

   ```
   postgresql://neondb_owner:SENHA@ep-xxxx-xxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

   Confira que o host **não** tem `-pooler` no nome. A conexão direta é a mais simples e basta
   para o volume de uma pesquisa.

Guarde essa URL: ela é a senha do banco. Não coloque no código nem no GitHub.

Não é preciso criar tabelas: a aplicação cria tudo sozinha na primeira vez que sobe.

---

## Passo 2 — Aplicação no Render

O repositório já tem um [`render.yaml`](../render.yaml) que descreve o serviço inteiro, então é só
apontar o Render para ele.

1. Acesse [render.com](https://render.com) e entre com o **GitHub** (a mesma conta dona do repositório).
2. No painel, clique em **New +** → **Blueprint**.
3. Conecte o repositório **`DaviMeiraV/Tcc-projeto`**. Se ele não aparecer, clique em
   *Configure account* e libere o acesso do Render a esse repositório.
4. O Render lê o `render.yaml` e mostra o serviço `tcc-risco-lesao` a ser criado.
   Ele vai pedir o valor de **`DATABASE_URL`**: cole a URL do Neon do passo 1.
   A `SECRET_KEY` é gerada automaticamente.
5. Clique em **Apply** (ou *Deploy Blueprint*).

O primeiro build leva de 5 a 10 minutos: ele compila o React e instala as dependências do Python.
Acompanhe em **Logs**. Quando aparecer `Uvicorn running on http://0.0.0.0:10000` e o status ficar
**Live**, está no ar.

O endereço aparece no topo da página do serviço, algo como:

```
https://tcc-risco-lesao.onrender.com
```

(Se esse nome já estiver em uso, o Render acrescenta um sufixo.)

---

## Passo 3 — Conferir

| Endereço | Deve mostrar |
|---|---|
| `https://SEU-APP.onrender.com/api/saude` | `{"status":"ok"}` |
| `https://SEU-APP.onrender.com` | Tela de login |
| `https://SEU-APP.onrender.com/docs` | Swagger da API |

Crie uma conta pela tela de cadastro e envie um formulário de teste. No Neon, em **Tables**, as
tabelas `usuarios`, `avaliacoes`, `fotos` e `arquivos` devem aparecer com o registro.

Esse é o link para mandar aos participantes.

---

## Limites do plano gratuito

| Situação | O que acontece | Impacto |
|---|---|---|
| 15 min sem nenhum acesso | O Render **desliga** o container | O próximo acesso demora **cerca de 1 minuto** para abrir |
| 5 min sem consultas | O Neon suspende o banco | A primeira consulta seguinte demora um pouco mais; nada se perde |
| Banco passa de 0,5 GB | O Neon bloqueia gravações | Improvável: cabem mais de mil fotos (veja abaixo) |
| 750 horas de container por mês | Suficiente para 1 serviço ligado o mês inteiro | Nenhum |

**Antes de mandar o link para alguém**, abra o sistema você mesmo e espere carregar. Assim o
participante não pega a espera de 1 minuto e não desiste achando que está fora do ar.

### Onde ficam as fotos e os CSVs

**No banco, junto com as respostas** (tabela `arquivos`). O disco do Render é apagado a cada
deploy, reinício ou quando o serviço dorme, então nada é gravado nele. Tudo o que o participante
envia fica no Neon e é permanente.

As fotos são convertidas para JPEG com no máximo 1920 px de lado antes de gravar: uma foto de
celular de 3 a 5 MB passa a ocupar algumas centenas de KB e continua nítida. Com os 0,5 GB do
Neon, cabem **mais de mil fotos**. Para acompanhar o espaço usado, veja a consulta de tamanho em
[BANCO-DE-DADOS.md](BANCO-DE-DADOS.md#outras).

### Baixando os dados coletados

- **Respostas:** exporte do Neon com a consulta de
  [BANCO-DE-DADOS.md](BANCO-DE-DADOS.md#exportar-a-coleta-para-análise-csv).
- **Fotos e CSVs:** cada arquivo abre em `https://SEU-APP.onrender.com/uploads/NOME_DO_ARQUIVO`.
  Os nomes estão nas colunas `fotos.arquivo` e `avaliacoes.csv_arquivo`; a consulta
  "Fotos com seus rótulos" de [BANCO-DE-DADOS.md](BANCO-DE-DADOS.md#outras) lista todos.

---

## Atualizando o sistema

Com o Blueprint, **todo `git push` na `main` gera um deploy automático**. Não há nada para fazer no
Render, e nenhum dado se perde: respostas e arquivos estão no banco.

Durante o deploy (alguns minutos) o sistema fica fora do ar. Evite fazer push enquanto
participantes estiverem respondendo.

Para acompanhar ou refazer um deploy: painel do serviço → **Events** / **Manual Deploy**.

## Variáveis de ambiente em produção

Ficam no Render, em **Environment**, nunca no código.

| Variável | Valor | Origem |
|---|---|---|
| `DATABASE_URL` | Connection string do Neon | Você cola no passo 2 |
| `SECRET_KEY` | Chave aleatória que assina os logins | Gerada pelo Render |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 h) | `render.yaml` |
| `PORT` | `10000` | Definida pelo próprio Render |

Trocar a `SECRET_KEY` desloga todo mundo; não afeta os dados.

---

## Problemas comuns

**O build falha no Render.**
Abra **Logs** e procure a primeira linha com `ERROR`. Rode `docker compose up --build` na sua
máquina: se falhar localmente também, o problema está no código, não no Render.

**O deploy termina, mas o serviço não fica *Live* e o log mostra erro de conexão com o banco.**
Quase sempre é a `DATABASE_URL`. Confira em **Environment** se ela está completa, termina com
`?sslmode=require` e se o projeto no Neon está ativo.

**A página abre, mas o login dá erro 500.**
Mesma causa acima: a tela é servida sem o banco, mas o login precisa dele.

**Demora muito para abrir.**
É o container acordando. Espere cerca de 1 minuto e recarregue.
