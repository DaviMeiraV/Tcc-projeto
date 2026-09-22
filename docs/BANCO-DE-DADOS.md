# Banco de dados

PostgreSQL 16. Localmente roda no Docker; em produção, no [Neon](https://neon.com) (plano gratuito).

As tabelas são criadas automaticamente quando a API sobe (`Base.metadata.create_all` em
`backend/app/main.py`), a partir dos modelos em [`backend/app/models.py`](../backend/app/models.py).
Não há migrations: para alterar uma tabela que já existe, veja [Alterando o esquema](#alterando-o-esquema).

---

## Visão geral

```mermaid
erDiagram
    usuarios ||--o{ avaliacoes : "envia"
    avaliacoes ||--o{ fotos : "tem até 3"
    avaliacoes ||--o{ sessoes_treino : "reservada"
    fotos }o--|| arquivos : "conteúdo em"
    avaliacoes }o--o| arquivos : "CSV em"

    usuarios {
        int id PK
        varchar nome
        varchar email UK
        varchar senha_hash
        timestamptz criado_em
    }
    avaliacoes {
        int id PK
        int usuario_id FK
        timestamptz criado_em
        int idade
        varchar sexo
        varchar esporte
        int rpe_dor_fadiga_sono_recuperacao "5 colunas 0-10"
        bool lesao_previa
        bool dor_limita
        varchar csv_arquivo
        float score_risco "reservada, nula"
    }
    fotos {
        int id PK
        int avaliacao_id FK
        varchar arquivo
        varchar modalidade
        varchar fase
        varchar joelho_frente
    }
    sessoes_treino {
        int id PK
        int avaliacao_id FK
        timestamptz data
        float carga
    }
    arquivos {
        varchar nome PK
        varchar tipo
        int tamanho_bytes
        bytea conteudo
        timestamptz criado_em
    }
```

| Tabela | O que guarda | Em uso hoje? |
|---|---|---|
| `usuarios` | Contas de acesso (login) | Sim |
| `avaliacoes` | Um formulário enviado: dados pessoais, questionário e referência ao CSV | Sim |
| `fotos` | Cada fotografia enviada, com os rótulos escolhidos pelo participante | Sim |
| `sessoes_treino` | Linhas do CSV já interpretadas | **Não** — reservada para o cálculo de carga |
| `arquivos` | Conteúdo das fotos e dos CSVs enviados | Sim |

**Exclusão em cascata:** apagar um usuário apaga as avaliações dele; apagar uma avaliação apaga
as fotos e sessões dela (`ON DELETE CASCADE`). A rota `DELETE /api/avaliacoes/{id}` também apaga
as linhas correspondentes em `arquivos`.

---

## Tabelas

### `usuarios`

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `id` | `integer` | não | Chave primária |
| `nome` | `varchar(120)` | não | Nome informado no cadastro |
| `email` | `varchar(180)` | não | Único e indexado; gravado sempre em minúsculas |
| `senha_hash` | `varchar(255)` | não | Hash **bcrypt** — a senha em si nunca é armazenada |
| `criado_em` | `timestamptz` | não | Data do cadastro (UTC) |

### `avaliacoes`

Uma linha por formulário enviado. O mesmo usuário pode enviar vários.

**Identificação**

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `id` | `integer` | não | Chave primária |
| `usuario_id` | `integer` | não | FK → `usuarios.id`, indexada |
| `criado_em` | `timestamptz` | não | Momento do envio (UTC) |

**Etapa 1 — participante**

| Coluna | Tipo | Nulo | Valores |
|---|---|---|---|
| `idade` | `integer` | não | 10 a 90 |
| `sexo` | `varchar(20)` | não | `masculino`, `feminino`, `outro` |
| `esporte` | `varchar(20)` | não | `corrida`, `ciclismo` |
| `tempo_pratica` | `varchar(40)` | não | `menos_6_meses`, `6_meses_1_ano`, `1_3_anos`, `3_5_anos`, `mais_5_anos` |
| `peso_kg` | `float` | não | 20 a 250 |
| `altura_cm` | `float` | não | 100 a 250 |

**Etapa 1 — questionário**

| Coluna | Tipo | Nulo | Escala |
|---|---|---|---|
| `rpe` | `integer` | não | Esforço percebido: 1 = muito leve · 10 = máximo |
| `dor` | `integer` | não | 0 = nenhuma · 10 = muito intensa |
| `fadiga` | `integer` | não | 0 = nenhuma · 10 = extrema |
| `sono` | `integer` | não | 0 = muito ruim · 10 = excelente |
| `recuperacao` | `integer` | não | 0 = nada · 10 = totalmente |
| `lesao_previa` | `boolean` | não | Já sofreu lesão relacionada ao esporte |
| `dor_limita` | `boolean` | não | A dor atual limita os treinos |
| `lesao_descricao` | `text` | sim | Texto livre; só quando `lesao_previa` é verdadeiro |
| `lesao_quando` | `varchar(40)` | sim | `menos_3_meses`, `3_6_meses`, `6_12_meses`, `mais_1_ano` |

> Atenção à direção das escalas: em `dor` e `fadiga` **maior é pior**; em `sono` e
> `recuperacao` **maior é melhor**. Isso importa na hora de montar o score.

**Etapa 2 — arquivos**

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `consentimento_foto` | `boolean` | não | Marcou a autorização de uso das fotos |
| `csv_arquivo` | `varchar(255)` | sim | Nome gerado (ex. `3f2a….csv`) → `arquivos.nome` |
| `csv_nome_original` | `varchar(255)` | sim | Nome do arquivo no computador do participante |

**Reservadas para o score** — existem na tabela, mas hoje ficam **sempre nulas**:

| Coluna | Tipo | Uso previsto |
|---|---|---|
| `acwr` | `float` | Razão carga aguda : crônica |
| `carga_aguda` | `float` | Carga média dos últimos 7 dias |
| `carga_cronica` | `float` | Carga média dos últimos 28 dias |
| `score_risco` | `float` | Pontuação final |
| `classificacao` | `varchar(20)` | Faixa de risco |
| `detalhes` | `jsonb` | Memória de cálculo |

### `fotos`

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `id` | `integer` | não | Chave primária |
| `avaliacao_id` | `integer` | não | FK → `avaliacoes.id`, indexada |
| `arquivo` | `varchar(255)` | não | Nome gerado (ex. `9c1d….jpg`) → `arquivos.nome`; a imagem abre em `/uploads/{arquivo}` |
| `nome_original` | `varchar(255)` | não | Nome no computador do participante |
| `modalidade` | `varchar(20)` | não | `corrida`, `ciclismo` |
| `fase` | `varchar(40)` | não | Corrida: `contato_inicial`, `apoio_medio` · Ciclismo: `fase_superior`, `extensao_maxima` |
| `joelho_frente` | `varchar(20)` | sim | `esquerdo`, `direito` — só em corrida |
| `analise` | `jsonb` | sim | Reservada, sempre nula |

### `sessoes_treino`

Criada mas **não preenchida** nesta fase: o CSV é guardado inteiro, sem leitura. Quando o cálculo
de carga for implementado, cada linha do CSV vira uma linha aqui.

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `id` | `integer` | não | Chave primária |
| `avaliacao_id` | `integer` | não | FK → `avaliacoes.id`, indexada |
| `data` | `timestamptz` | não | Data do treino |
| `duracao_min` | `float` | não | Duração em minutos |
| `distancia_km` | `float` | sim | Distância |
| `rpe` | `float` | sim | Esforço percebido da sessão |
| `carga` | `float` | não | Carga da sessão |

---

### `arquivos`

Guarda o conteúdo das fotos e dos CSVs. Fica no banco, e não em disco, porque o disco do Render
gratuito é apagado a cada deploy ou quando o serviço dorme.

| Coluna | Tipo | Nulo | Descrição |
|---|---|---|---|
| `nome` | `varchar(255)` | não | Chave primária, gerada aleatoriamente (`<hex>.jpg` ou `<hex>.csv`) |
| `tipo` | `varchar(100)` | não | `image/jpeg` ou `text/csv` |
| `tamanho_bytes` | `integer` | não | Tamanho do conteúdo |
| `conteudo` | `bytea` | não | O arquivo em si |
| `criado_em` | `timestamptz` | não | Momento do envio (UTC) |

- **Fotos** são convertidas para JPEG com no máximo 1920 px de lado (qualidade 85) antes de
  gravar e ficam com algumas centenas de KB. Um arquivo que não seja uma imagem válida é recusado.
- **CSVs** são guardados exatamente como enviados, byte a byte.
- Qualquer arquivo abre em `/uploads/{nome}` sem precisar de login (para a foto aparecer numa
  tag `<img>`); os nomes são aleatórios e não dá para adivinhá-los.

---

## Consultas úteis

### Exportar a coleta para análise (CSV)

Uma linha por envio, pronta para abrir no Excel, R ou Python:

```sql
SELECT
    a.id                    AS envio,
    a.criado_em,
    a.idade, a.sexo, a.esporte, a.tempo_pratica,
    a.peso_kg, a.altura_cm,
    ROUND((a.peso_kg / (a.altura_cm / 100) ^ 2)::numeric, 1) AS imc,
    a.rpe, a.dor, a.fadiga, a.sono, a.recuperacao,
    a.lesao_previa, a.lesao_quando, a.lesao_descricao, a.dor_limita,
    a.csv_nome_original     AS historico_treino,
    COUNT(f.id)             AS qtd_fotos
FROM avaliacoes a
LEFT JOIN fotos f ON f.avaliacao_id = a.id
GROUP BY a.id
ORDER BY a.id;
```

Para gerar o arquivo:

```bash
# Local (Docker)
docker exec tcc_postgres psql -U postgres -d injuryrisk \
  -c "COPY (<consulta acima, sem o ponto e vírgula>) TO STDOUT WITH CSV HEADER" > coleta.csv

# Produção (Neon) — use a connection string do painel do Neon
psql "postgresql://usuario:senha@host.neon.tech/neondb?sslmode=require" \
  -c "\copy (<consulta acima, sem o ponto e vírgula>) TO 'coleta.csv' WITH CSV HEADER"
```

No Neon também dá para rodar qualquer consulta pelo navegador, em **SQL Editor** no painel do projeto.

### Outras

```sql
-- Quantos envios por esporte
SELECT esporte, COUNT(*) FROM avaliacoes GROUP BY esporte;

-- Médias do questionário
SELECT ROUND(AVG(dor), 1) AS dor, ROUND(AVG(fadiga), 1) AS fadiga,
       ROUND(AVG(sono), 1) AS sono, ROUND(AVG(recuperacao), 1) AS recuperacao
FROM avaliacoes;

-- Fotos com seus rótulos (abra cada uma em /uploads/<arquivo>)
SELECT a.id AS envio, f.modalidade, f.fase, f.joelho_frente, f.arquivo
FROM fotos f JOIN avaliacoes a ON a.id = f.avaliacao_id
ORDER BY a.id;

-- Espaço ocupado (o Neon gratuito permite 0,5 GB)
SELECT pg_size_pretty(pg_database_size(current_database())) AS banco_inteiro,
       pg_size_pretty(COALESCE(SUM(tamanho_bytes), 0))     AS so_arquivos,
       COUNT(*) FILTER (WHERE tipo = 'image/jpeg')         AS fotos
FROM arquivos;
```

### Acessar o banco pelo terminal

```bash
# Local (Docker)
docker exec -it tcc_postgres psql -U postgres -d injuryrisk

# Produção (Neon)
psql "<connection string do Neon>"
```

Comandos úteis dentro do `psql`: `\dt` lista as tabelas, `\d avaliacoes` mostra as colunas,
`\q` sai.

Também funciona com clientes gráficos (DBeaver, pgAdmin, Beekeeper): host `localhost`,
porta `5433`, banco `injuryrisk`, usuário e senha `postgres`.

---

## Alterando o esquema

Como não há migrations, `create_all` **cria tabelas que faltam, mas não altera tabelas que já
existem**. Ao adicionar uma coluna em `models.py`, aplique a mudança manualmente:

```sql
ALTER TABLE avaliacoes ADD COLUMN IF NOT EXISTS nova_coluna VARCHAR(50);
```

Rode isso no banco local **e** no Neon. Se o esquema começar a mudar com frequência, vale adotar
o [Alembic](https://alembic.sqlalchemy.org).

---

## Dados pessoais

As respostas incluem dados de saúde, que a LGPD trata como dados sensíveis. O que já está feito:
senhas guardadas apenas como hash bcrypt; cada usuário só enxerga os próprios envios; o
consentimento de uso das fotos é registrado em `consentimento_foto`.

Na hora de publicar resultados, use a exportação acima **sem** as colunas de identificação
(`usuario_id`, `lesao_descricao` e os nomes originais de arquivo).
