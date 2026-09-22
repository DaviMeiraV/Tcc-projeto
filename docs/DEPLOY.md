# Deploy gratuito

O sistema fica no ar sem custo usando dois serviços:

| Peça | Onde | Plano | Por quê |
|---|---|---|---|
| Banco PostgreSQL | [Neon](https://neon.com) | Free | Gratuito **permanente**, sem cartão de crédito |
| API + telas + Swagger | [Render](https://render.com) | Free | Roda o `Dockerfile` do projeto direto do GitHub |

```mermaid
flowchart LR
    U[Participante<br/>navegador] -->|HTTPS| R[Render<br/>container Docker<br/>React + FastAPI]
    R -->|SQL / SSL| N[(Neon<br/>PostgreSQL)]
    R -.->|fotos e CSV| D[Disco temporário<br/>do container]
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
tabelas `usuarios`, `avaliacoes` e `fotos` devem aparecer com o registro.

Esse é o link para mandar aos participantes.

---

## Limites do plano gratuito

| Situação | O que acontece | Impacto |
|---|---|---|
| 15 min sem nenhum acesso | O Render **desliga** o container | O próximo acesso demora **cerca de 1 minuto** para abrir |
| Container desligado, reiniciado ou com novo deploy | O disco é **apagado** | Fotos e CSVs enviados somem (veja abaixo) |
| 5 min sem consultas | O Neon suspende o banco | A primeira consulta seguinte demora um pouco mais; nada se perde |
| Banco passa de 0,5 GB | O Neon bloqueia gravações | Improvável: cada envio ocupa poucos KB no banco |
| 750 horas de container por mês | Suficiente para 1 serviço ligado o mês inteiro | Nenhum |

**Antes de mandar o link para alguém**, abra o sistema você mesmo e espere carregar. Assim o
participante não pega a espera de 1 minuto e não desiste achando que está fora do ar.

### Arquivos enviados são temporários

O banco (Neon) é permanente: **todas as respostas do questionário ficam guardadas**. Já as fotos
e os CSVs ficam no disco do container do Render, que é apagado quando o container:

- faz um novo deploy — **o que acontece a cada `git push` na `main`**;
- reinicia;
- dorme depois de 15 minutos sem acesso.

Quando isso acontece, o registro do envio continua no banco com o nome do arquivo, mas a imagem
em `/uploads/...` passa a responder 404.

Para não perder arquivos durante uma rodada de coleta:

- **Evite dar push na `main`** enquanto os participantes estiverem respondendo. Se precisar
  trabalhar no código, desligue *Auto-Deploy* em **Settings** do serviço no Render.
- **Baixe os arquivos logo depois** de cada rodada (veja abaixo).

Se as fotos passarem a ser necessárias para a análise do TCC, a solução definitiva é guardá-las
fora do container (no próprio banco ou em um armazenamento de objetos gratuito). Isso exige uma
mudança pequena no backend.

### Baixando os dados coletados

- **Respostas:** exporte do Neon com a consulta de
  [BANCO-DE-DADOS.md](BANCO-DE-DADOS.md#exportar-a-coleta-para-análise-csv).
- **Fotos e CSVs:** enquanto o container estiver no ar, cada arquivo abre em
  `https://SEU-APP.onrender.com/uploads/NOME_DO_ARQUIVO`. Os nomes estão nas colunas
  `fotos.arquivo` e `avaliacoes.csv_arquivo`.

---

## Atualizando o sistema

Com o Blueprint, **todo `git push` na `main` gera um deploy automático**. Não há nada para fazer no
Render — mas lembre que o deploy apaga os arquivos enviados até então.

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

**Uma foto antiga não abre (404).**
Esperado depois de um deploy, reinício ou período sem uso. Veja
[Arquivos enviados são temporários](#arquivos-enviados-são-temporários).
