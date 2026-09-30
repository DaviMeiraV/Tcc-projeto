# Envio e análise das fotografias

1. Ao selecionar uma foto, o formulário mantém o arquivo, a modalidade, a fase e o joelho juntos na memória do navegador. É possível avançar e voltar entre etapas sem perder esses dados. Recarregar ou sair do formulário descarta esse rascunho.
2. Ao clicar em **Finalizar**, o React envia o formulário, as fotos e o CSV em `multipart/form-data` para `POST /api/avaliacoes`.
3. O backend valida e grava tudo no PostgreSQL. Como antes, as fotos são orientadas conforme o EXIF e convertidas para JPEG de até 1920 px de lado. Essa mesma versão é enviada à análise.
4. O backend faz um `POST /analises` por foto, em sequência. Apenas os dados da foto são enviados à API externa; o questionário e o CSV ficam neste sistema.
5. O PNG retornado em `imagem_tratada.base64` é decodificado e salvo na tabela `arquivos`, sem redimensionamento. O resultado fica em `fotos.analise`, com `status: "concluida"` e o nome local em `imagem_tratada.arquivo`. O Base64 não é duplicado no JSON, e o caminho `saida/...` do servidor externo não é usado como URL.
6. A página `/concluido/{id}` mostra a imagem tratada e o score postural de **0 a 1**. Também fica acessível em **Histórico → Ver envio**.

## Configuração

Instale as dependências atualizadas com `python -m pip install -r requirements.txt` dentro de `backend`, usando o ambiente virtual do projeto.

No `backend/.env`, para desenvolvimento local:

```env
ANALISE_API_URL=http://127.0.0.1:8001
ANALISE_API_TIMEOUT=120
```

Execute o projeto separado da API postural com `python main.py --host 0.0.0.0 --port 8001`. O sistema web usa a porta 8000; por isso a API postural deve usar outra porta quando ambos estiverem na mesma máquina. Configure a URL base, **sem** `/analises` no final.

No Docker Compose, o endereço padrão é `http://host.docker.internal:8001`, que acessa a API executada na máquina hospedeira. Para outra instalação, defina `ANALISE_API_URL` no ambiente do Compose. No Render, configure essa variável com a URL HTTPS acessível do serviço postural hospedado separadamente; `localhost` não aponta para seu computador.

O timeout padrão é de 120 segundos por foto. A primeira análise pode demorar pelo carregamento do modelo. A comunicação ocorre no backend, sem necessidade de CORS entre o navegador e a API postural.

## Conversão dos campos

| Formulário | JSON enviado à API |
|---|---|
| `corrida` / `ciclismo` | `modalidade: "corrida"` / `"bike"` |
| `contato_inicial` / `fase_superior` | `fase_joelho: 1` |
| `apoio_medio` / `extensao_maxima` | `fase_joelho: 2` |
| `esquerdo` / `direito` (corrida) | `joelho_frente: "E"` / `"D"` |
| Arquivo JPEG armazenado | `imagem_base64`: Base64 puro, sem prefixo `data:` |

Na bike, `joelho_frente` é omitido. Fases incompatíveis e corrida sem joelho são rejeitadas antes de salvar o envio.

## Falhas e novas tentativas

Se a API estiver indisponível, demorar demais, rejeitar a foto ou retornar uma resposta inválida, o formulário permanece salvo. A foto recebe `status: "erro"` e uma mensagem; as demais fotos continuam sendo processadas. O HTTP 201 do envio confirma o armazenamento, não o sucesso de todas as análises.

Use **Tentar análises pendentes novamente** no detalhe do envio. O botão chama `POST /api/avaliacoes/{id}/analises` com o token do usuário e reutiliza as fotos e os dados salvos, sem criar outro formulário. Fotos já concluídas não são reenviadas. Se o processamento for interrompido, fotos sem resultado também podem ser retomadas. Envios antigos continuam acessíveis.

São reutilizados `fotos.analise` e `arquivos`. Na inicialização, bancos antigos recebem automaticamente as colunas opcionais `avaliacoes.csv_arquivo` e `avaliacoes.csv_nome_original` se estiverem ausentes, sem apagar dados. Isso corrige o erro 500 `column csv_arquivo does not exist`, que interrompia o envio antes da análise. Para atualizar o Docker, execute `docker compose up -d --build app`.

Excluir um envio remove também seus PNGs tratados deste banco; não remove a cópia mantida pela API externa em `saida/`.

O score postural não é o score combinado de risco de lesão, que continua sem implementação. O CSV também alimenta o [cálculo de ACWR](ACWR.md), exibido em um componente próprio na página final.

## Verificação

Dentro de `backend`, execute `python -m unittest discover -s tests -v`. Os testes simulam a API externa e verificam conversão dos campos, armazenamento, erros, novas tentativas, exclusão e acesso por usuário, sem MediaPipe. Para verificar o serviço real, finalize um formulário com uma foto de perfil válida e abra o resultado no histórico.
