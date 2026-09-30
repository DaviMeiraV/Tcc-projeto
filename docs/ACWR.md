# ACWR no resultado

O envio salva o CSV original e calcula o ACWR em `backend/app/services/carga_treino.py`.
O resultado fica em `avaliacoes.acwr`, nas cargas aguda/crônica e em `detalhes.acwr`.
Envios antigos com CSV também são calculados ao abrir o detalhe no histórico.

- Referência: data da última atividade da planilha, incluindo o dia inteiro.
- Semana: últimos 7 dias corridos. Mês de treino: últimos 28 dias, não mês civil.
- Carga: duração × RPE, de 0 a 10. Usa o RPE da sessão quando presente na planilha;
  nas atividades sem RPE, usa o esforço informado pelo atleta no formulário.
  A tela e os logs identificam esse valor e quantas atividades o utilizaram.
- ACWR = (carga total dos 7 dias / 7) ÷ (carga total dos 28 dias / 28).
  Dias sem registros contam como zero. Carga crônica zero não produz score.

A tela identifica o método, a referência e históricos com menos de 28 dias de registros.
O score é uma razão, sem conversão para porcentagem. O score do questionário e a soma final
continuam reservados, sem cálculo nem valores fictícios.

Quando o mesmo RPE maior que zero é aplicado a todas as sessões, ele multiplica ambas
as cargas e se cancela na divisão: o ACWR continua igual à razão calculada por duração.
Se todas as cargas forem zero, o ACWR fica indisponível. Resultados de versões anteriores
são recalculados com o RPE salvo no formulário ao abrir o detalhe do envio.

## Planilha

### Regra de RPE por sessão

1. Se a sessão tem RPE válido na planilha, ele é preservado. **Zero também é um valor válido.**
2. Se a célula está vazia ou a coluna RPE não existe, usa-se o RPE geral do formulário
   **como aproximação**, somente nessa sessão. Os RPEs das demais sessões não são descartados.
3. Um RPE inválido (por exemplo, texto ou valor acima de 10) produz erro de validação;
   não é considerado ausente. Se faltar RPE tanto na sessão quanto no formulário,
   o cálculo não é feito. Não há substituição silenciosa por duração sem RPE.

O esforço geral do último mês não comprova o esforço de cada treino. Por isso, quando
há preenchimento pelo formulário, o resultado é apresentado como **ACWR com carga
parcialmente ou totalmente estimada**, e não como session-RPE medido nessas sessões.
A tela informa o valor usado e a quantidade de atividades preenchidas.

Exemplo: uma sessão de 60 minutos tem RPE 10 e outra de 60 minutos está sem RPE.
Com RPE 5 no formulário, as cargas são **600 e 300**, respectivamente; a primeira
sessão mantém seu valor original.

Em `detalhes.acwr`, `carga_estimada` sinaliza o uso da aproximação.
`atividades_com_rpe_formulario` conta as sessões preenchidas nos 28 dias.
`sessoes` registra, para cada atividade dessa janela: linha do CSV, data, minutos,
`rpe_original`, `rpe_utilizado`, `origem_rpe` (`planilha` ou `formulario`) e carga.
O arquivo CSV original permanece inalterado.

### Formato do arquivo

CSV separado por vírgula, ponto e vírgula ou tabulação, em UTF-8 ou Windows-1252.
São necessárias data e duração; RPE é opcional. Exemplo:

```csv
data,duracao_min,rpe
2026-09-02,60,5
2026-09-29,60,5
```

Esse exemplo resulta em ACWR 2. Datas aceitam ISO (AAAA-MM-DD, com horário opcional),
DD/MM/AAAA e o formato de exportação em inglês `Sep 29, 2026, 08:00:00 AM`.
Também são reconhecidos `Activity Date`/`Elapsed Time` e `Data`/`Tempo`.
`Elapsed Time` e `Moving Time` numéricos são segundos; as demais colunas de duração
numéricas são minutos. Durações com dois-pontos aceitam HH:MM:SS ou MM:SS.
Nenhuma unidade é inferida pelo tamanho do número.

Linhas inválidas produzem uma mensagem no componente ACWR; não são descartadas silenciosamente.
O formulário, o CSV e a análise das fotos são preservados mesmo quando o CSV é inválido.

## Logs

Veja `docker compose logs -f app`. A cada cálculo, o log `ACWR atleta_id=...` informa
referência, método, quantidade de atividades, minutos e carga nos 7 e 28 dias e score.
Também informa `rpe_formulario`, `atividades_com_rpe_formulario` e `carga_estimada`.
O atleta é identificado pelo ID, sem registrar nome, e-mail ou conteúdo completo da planilha.

## Como ler o código

O arquivo `carga_treino.py` está dividido na ordem do processamento:

1. `criar_leitor_csv` e `mapear_colunas`: abrem o CSV e reconhecem seus cabeçalhos.
2. `ler_atividades`: converte e valida cada linha, preservando o RPE original.
3. `definir_carga`: escolhe o RPE de uma sessão e registra sua origem.
4. `somar_atividades`: soma durações e cargas sem arredondamento antecipado.
5. `calcular_csv`: seleciona as janelas, calcula ACWR e monta o resultado.
6. `analisar_planilha`: registra logs e guarda sucesso ou erro na avaliação.

`VERSAO_ACWR` identifica a regra utilizada. Ao abrir um resultado antigo, o sistema
recalcula o ACWR com a versão atual para incluir a identificação das aproximações.
