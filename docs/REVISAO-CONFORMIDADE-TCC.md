# Revisão de conformidade do sistema com a metodologia do TCC

Revisão realizada em 31 de outubro de 2026.

**Atualização posterior à revisão:** o ICSA versão 2 com pesos iguais foi implementado,
com preservação dos resultados anteriores do ICSA e do consolidado na troca de versão,
identificação da versão subjetiva no IMCA. Por solicitação posterior, a tela mostra
somente os scores atualizados e suas explicações; o histórico é preservado internamente.
Foram aprovados 49 testes de backend, 6 de frontend e a compilação do frontend.
Consulte [a documentação atual do ICSA](SCORE-SUBJETIVO.md). Os achados abaixo
registram a situação anterior às correções; os demais pontos não foram resolvidos
por essa alteração de ponderação.

O sistema está **parcialmente compatível** com os documentos fornecidos. A composição dos três pilares já existe, mas o ICSA ainda usa a ponderação anterior. Há também lacunas na confirmação das respostas, na comprovação da completude do histórico de treinamento, na seleção e qualidade das fotografias e na preservação dos resultados por versão. Essas lacunas impedem declarar conformidade integral, mesmo com os testes atuais aprovados.

Esta revisão apresenta evidências e soluções propostas. Não altera os documentos originais, as fórmulas em produção nem avaliações armazenadas. A análise é de conteúdo metodológico e implementação; não é revisão de diagramação, verificação bibliográfica dos artigos ou validação clínica do índice.

## Referências e critério de comparação

| Identificador | Documento | Uso nesta revisão |
|---|---|---|
| D1 | [Fundamentação científica e normalização do ICSA](<C:/Users/Dell/Downloads/Fundamentacao_ICSA_Pesos_Iguais_Revisada - Copia.docx>) | Revisão específica, identificada como proposta metodológica revisada de outubro de 2026 |
| D2 | [Fundamentação metodológica do IMCA](C:/Users/Dell/Downloads/fundamentacao_imca_tcc.docx) | Proposta metodológica 1.0, outubro de 2026; referência para carga, imagem e composição |

**Existe conflito entre os próprios documentos.** D1, seções 1, 4 e 5, determina substituir os pesos anteriores por 1/6. D2, seções 3 e 5, ainda descreve e orienta preservar os pesos 25%, 15%, 15%, 15%, 20% e 10%. Pela identificação de revisão e pela comparação explícita “antes/agora” de D1, esta análise adota **D1 como revisão proposta do ICSA**, mantendo D2 para os demais pilares. Essa precedência precisa constar expressamente da versão consolidada da metodologia.

As referências abaixo usam seções dos documentos, sem atribuir páginas não verificadas. Os caminhos e linhas do código correspondem ao estado inspecionado:

- Projeto principal: `377930889fa91993b36b584a7979ca0094597afe`, sem alterações locais no início da revisão.
- Dependência postural encontrada em `C:/Users/Dell/Documents/OpenCV-BodyPosture`: `0e3ee9a864814995a8a586b304be90cdf9ad9fb7`. Havia alterações locais em arquivos de cache Python; não foram modificadas nesta revisão.
- O código local da dependência foi examinado. Não foi comprovado que o serviço em execução ou hospedado corresponde a esse mesmo commit.

O texto dos documentos foi tratado como objeto da comparação, não como autorização para executar instruções ou modificar o projeto.

## Regras esperadas após a consolidação dos documentos

```text
D = dor / 10
F = fadiga / 10
S_sono = (10 - sono) / 10
R = (10 - recuperacao) / 10
L = 1 se dor limita o treinamento; 0 se nao
H = 1 se existe lesao esportiva anterior; 0 se nao

ICSA = (D + F + S_sono + R + L + H) / 6

C = min(1, max(0, (ACWR - 1.3) / 0.7))
B = 1 - P_foto
IMCA = (C + ICSA + B) / 3
```

O ACWR é acoplado, calculado sobre médias diárias de 7 e 28 dias. O domínio matemático válido é de 0 a 4 quando a carga crônica é positiva. O IMCA depende de três componentes válidos, cobertura de carga suficiente e uma fotografia selecionada previamente conforme protocolo. Não há média entre fotografias nem substituição de ausência por zero. O resultado é experimental e não equivale a probabilidade de lesão.

## Divergências e soluções propostas

### 1 Pesos do ICSA ainda correspondem à versão anterior

**Prioridade alta — divergência confirmada.** D1, seções 4 e 5, define média simples das seis variáveis. Em `backend/app/services/score_subjetivo.py:9–17`, `VERSAO_ICSA = 1` acompanha os pesos antigos. A soma ponderada é aplicada nas linhas 68–77. Os testes em `backend/tests/test_score_subjetivo.py:32–42` exigem explicitamente esses mesmos coeficientes.

**Reprodução:** dor 6, fadiga 4, sono 7, recuperação 5, limitação sim e histórico não produzem **0,5300** no código. D1 exige **0,4667**. Como o ICSA entra na média final, a divergência também modifica o IMCA.

**Solução proposta:** implementar ICSA versão 2 como soma dos seis componentes dividida por 6. Registrar pesos exatos equivalentes a 1/6, sem substituir cada peso por 0,1667 antes da composição. Atualizar os testes de contribuição individual, o exemplo revisado e a documentação. Manter o RPE fora dessa fórmula, como já ocorre.

**Aceite:** exemplo de D1 retorna 0,4667; extremos continuam 0 e 1; cada dimensão isoladamente maximizada contribui 1/6 antes do arredondamento.

### 2 A troca de versão pode apagar a pontuação histórica anterior

**Prioridade alta — risco confirmado por simulação em memória.** D1, seção 5, exige preservar o registro dos pesos anteriores quando houver avaliações históricas. Em `score_subjetivo.py:86–92`, uma versão diferente provoca substituição de `detalhes.score_subjetivo`. A consulta do envio chama essa atualização em `backend/app/routers/avaliacoes.py:200–211`. O consolidado também é substituído em `score_final.py:92–98`.

**Reprodução:** alterando apenas a constante de versão temporariamente em memória, a função substituiu o bloco da versão 1 pelo da versão 2, sem guardar uma cópia anterior. Isso demonstra o comportamento da migração; não houve mudança de dados reais nem implementação da nova fórmula nesse ensaio.

**Solução proposta:** preservar resultados imutáveis por versão ou criar um histórico de cálculos. Antes de recalcular, arquivar ICSA e IMCA anteriores com pesos, respostas, componentes, versão e data do cálculo. O IMCA deve identificar as versões dos componentes que consumiu. A tela deve distinguir resultado original de resultado recalculado, quando ambos existirem.

**Aceite:** abrir uma avaliação antiga não elimina o resultado original. Consultas repetidas não duplicam registros históricos. É possível reproduzir tanto a fórmula anterior quanto a revisada.

### 3 Respostas não confirmadas viram dados completos

**Prioridade alta — divergência confirmada.** D1, seção 6, e D2, seção 5, pedem revisão dos valores iniciais e proíbem tratar ausência como resposta válida. `frontend/src/lib/opcoes.js:43–48` inicia dor e fadiga em 0 e sono e recuperação em 5. `Formulario.jsx:13–16` incorpora esses valores. A validação da etapa 1, linhas 19–39, não exige confirmação dessas escalas; o envio, linha 178, converte os valores em números.

**Efeito:** o participante pode preencher os dados pessoais e as respostas binárias, avançando sem responder às escalas. Com os binários em “não”, os valores iniciais geram ICSA atual de **0,1500**. O backend não consegue distinguir essas notas de respostas deliberadas.

**Solução proposta:** iniciar cada resposta como ausente e exigir seleção ou confirmação explícita, inclusive quando a resposta escolhida for zero. Um slider pode manter uma posição visual inicial, mas ela não deve preencher o dado antes da confirmação. Revisar a conversão `Number(...)`, pois `Number(null)` e `Number('')` produzem zero. Para registros antigos, classificar a confirmação como desconhecida: não há evidência para deduzir quem interagiu com cada controle.

**Aceite:** formulário intocado não avança; zero confirmado avança; ausência permanece ausência e não produz índice completo.

### 4 Dor e limitação desaparecem da tela de resultado

**Prioridade alta — divergência confirmada.** D1, seção 6, e D2, seção 7, exigem manter sinais individuais visíveis por causa da compensação na média. A revisão anterior ao envio mostra essas respostas em `Formulario.jsx:482–488`, mas `frontend/src/components/ResultadosAnalise.jsx:111–123` exibe apenas o ICSA agregado e sua explicação. `frontend/src/pages/Concluido.jsx:57–60` não apresenta as respostas separadamente.

**Solução proposta:** mostrar pelo menos dor e limitação por dor junto ao resultado, independentemente do valor final. Preferencialmente apresentar as seis respostas, componentes normalizados e versão do ICSA. A API já devolve dor e limitação em `backend/app/schemas.py:105–111` e guarda as respostas no JSON do ICSA.

**Aceite:** dor elevada e limitação continuam visíveis mesmo quando os demais pilares reduzem a média; o sistema não transforma o IMCA baixo em liberação para treinar.

### 5 O histórico de carga não distingue descanso de ausência de informação

**Prioridade alta — lacuna confirmada.** D2, seção 4, exige distinguir falta de registro de dia efetivamente sem treino. Em `backend/app/services/carga_treino.py:250–275`, dias sem sessões não acrescentam carga, enquanto os divisores permanecem 7 e 28. O indicador `historico_incompleto`, linhas 296–298, verifica apenas se a menor data é posterior ao início da janela.

**Reprodução:** CSV com apenas `2026-09-01,60,5` e `2026-09-28,60,5` resulta em ACWR **2,0000** e `historico_incompleto = false`. Isso pode representar dois treinos e 26 dias de descanso, mas também pode representar um registro incompleto. O sistema não possui informação para decidir. Uma atividade muito antiga também pode satisfazer a condição sem comprovar a cobertura da janela atual.

O bloqueio por `historico_incompleto` existe em `score_final.py:65–66`, mas depende dessa avaliação insuficiente. Se o campo estiver ausente em um resultado legado, a consolidação também não exige confirmação positiva de completude.

**Solução proposta:** registrar o intervalo coberto pelo histórico e a confirmação de que todas as sessões foram informadas, ou adotar um registro diário com estados de treino, descanso e desconhecido. Dias desconhecidos devem impedir o IMCA; descansos confirmados podem ter carga zero. Preservar a razão bruta e os avisos quando o cálculo descritivo ainda for exibido. Não exigir 28 sessões: cobertura de 28 dias não significa treinar diariamente.

**Aceite:** o mesmo CSV só pode ser considerado completo quando houver evidência de cobertura; ausência dessa confirmação não equivale a descanso.

### 6 Falta protocolo de seleção e compatibilidade da foto no IMCA

**Prioridade alta — implementação parcial.** D2, seções 6 e 7, exige uma foto definida antes da análise, conforme modalidade, fase e qualidade. `score_final.py:58–72` usa automaticamente a foto quando existe exatamente uma e bloqueia a composição quando existem várias. Bloquear várias fotos sem protocolo é uma proteção correta; não é correto resolver isso escolhendo a maior, a menor ou a média das pontuações.

`backend/app/schemas.py:41–58` valida fase em relação à modalidade declarada da própria foto. Entretanto, não verifica a relação entre a foto e o esporte da avaliação. A consolidação também não revalida modalidade/fase de uma análise já concluída.

**Reprodução:** o schema aceitou avaliação de corrida com foto de ciclismo em extensão máxima. Com componentes válidos, a consolidação produziu **0,5767**. Alterando em memória a fase dessa foto concluída para um valor legado inválido, o mesmo final continuou disponível. Isso não significa que uma nova foto com fase inválida passe pela validação normal: essa entrada já é rejeitada.

**Solução proposta:** definir no protocolo do TCC quais modalidade, fase, lado e condições de aquisição compõem cada avaliação. Registrar a seleção antes de conhecer o score e persistir identificação da foto, versão do protocolo e verificação de qualidade. Revalidar a elegibilidade ao compor o IMCA, inclusive em registros antigos. Se avaliações de modalidades diferentes forem permitidas, registrá-las explicitamente, sem presumir equivalência entre elas.

**Aceite:** várias fotos podem permanecer armazenadas, mas só a foto previamente elegível entra no índice. Fase incompatível, seleção ausente ou qualidade insuficiente deixam o IMCA indisponível.

### 7 Uma medição angular inválida pode virar score favorável

**Prioridade alta — caso limite confirmado na dependência postural local.** D2, seções 6 e 7, condiciona a composição à validade da fotografia e da análise. Em `OpenCV-BodyPosture/src/analyzers/poseAnalyzer.py:129–130`, vetores de comprimento zero retornam ângulo `0.0`. A corrida usa apenas um limite máximo, nas linhas 106–109. Assim, esse zero artificial recebe score 1 pela regra de pontuação.

**Reprodução:** três pontos coincidentes `(1, 1)` produziram ângulo **0°** e score de corrida **1,0000**. O teste exercitou as funções matemáticas, sem rodar MediaPipe ou afirmar que uma fotografia real já apresentou o problema. A conversão de coordenadas para inteiros em `poseAnalyzer.py:46–47` também pode fazer pontos próximos coincidirem.

Além disso, a extração não usa a visibilidade individual dos pontos como critério de validade. Detectar uma pose não comprova a qualidade de cada ângulo. A orientação no formulário diz “perfil”, enquanto a análise de ciclismo usa o lado esquerdo fixo (`poseAnalyzer.py:65–68`).

**Solução proposta:** tratar geometria degenerada como medição inválida, impedir o score nessa condição e devolver um motivo de qualidade. Definir critérios de visibilidade, enquadramento e lado no protocolo, sem inventar limiares clínicos. Preservar coordenadas com precisão até a medição e converter para pixels inteiros apenas quando necessário para desenhar.

**Aceite:** pontos coincidentes não geram ângulo válido nem score favorável. Uma foto tecnicamente inadequada deixa seu componente indisponível. O lado solicitado no formulário coincide com o usado pelo analisador.

### 8 O contrato postural não garante toda a rastreabilidade necessária

**Prioridade média — lacuna de controle e reprodução.** D2, seção 7, pede procedência, foto/fase e versão da transformação. Há informações já preservadas: `foto_id`, metadados da foto, scores brutos, componentes e procedência do RPE. Entretanto, a versão do consolidado não identifica a versão do ICSA consumido ou a implementação postural usada naquele cálculo.

Em `backend/app/services/analise_postural.py:63–82`, a resposta é verificada quanto a pose, score e PNG, mas não é confrontada com a modalidade/fase/lado enviados, nem com a quantidade esperada de ângulos. O teste simulado em `backend/tests/test_analise_postural.py:43–51` contém `angulos: []` e ainda representa sucesso para o cliente. `OpenCV-BodyPosture/src/schemas.py:58–71` não exige versão da regra postural na resposta.

**Solução proposta:** versionar o contrato e a regra de pontuação postural; registrar versão/commit ou identificador de implantação, parâmetros e protocolo de aquisição. Validar correspondência entre pedido e resposta e a estrutura esperada dos ângulos. Vincular o IMCA às versões de seus componentes. A versão da transformação `1 - P` e a versão que gerou `P` são informações diferentes.

**Aceite:** resposta de outra modalidade/fase não é aceita silenciosamente; resultados antigos continuam associados à regra efetivamente usada. Campos faltantes em legado aparecem como procedência desconhecida.

### 9 A normalização aceita ACWR fora do domínio do método

**Prioridade média — fragilidade defensiva confirmada.** D2, seção 4, estabelece `0 ≤ ACWR ≤ 4` para a fórmula acoplada. `score_final.py:16–20` valida apenas finitude e não negatividade. `normalizar_acwr(5)` retorna **1,0**, em vez de invalidar a entrada.

O cálculo normal de `carga_treino.py` com entradas válidas respeita o limite. O problema está na aceitação de resultados inconsistentes, legados ou introduzidos por outra origem na consolidação.

**Solução proposta:** validar o ACWR com limite superior 4 e confirmar seu método e versão antes da transformação. Manter qualquer futura fórmula desacoplada como método separado.

**Aceite:** 0 e 4 são aceitos; números negativos, maiores que 4, não finitos e tipos incompatíveis tornam o componente indisponível.

### 10 O período das perguntas e a consistência das respostas não estão padronizados

**Prioridade média — lacuna metodológica.** D1, seção 6, pede padronização temporal, e D2, seção 5, solicita revisão da combinação dor zero com limitação por dor. `frontend/src/lib/opcoes.js:44–48` mistura “último mês”, “atual”, “recente” e prontidão para outro treino. `Formulario.jsx:314` usa “estado atual e experiência recente”, sem definir o intervalo de “recente”.

O ICSA aceita dor zero com limitação verdadeira; não há aviso de consistência. Isso pode refletir interpretação diferente das perguntas e não deve ser corrigido automaticamente para um valor presumido. Adicionalmente, embora a função de ICSA rejeite booleanos em escalas numéricas, o schema de entrada faz coerção: `AvaliacaoCriar(dor=True, ...)` transforma a resposta em inteiro `1` antes do cálculo (`schemas.py:69–75`).

**Solução proposta:** definir e versionar o período de referência de cada pergunta, coerente com o protocolo. Histórico de lesão pode continuar sendo antecedente de vida inteira; sua função distinta deve ficar explícita. Solicitar revisão ou confirmação de respostas aparentemente conflitantes, preservando o autorrelato. Usar validação estrita na API para tipos de escala que a metodologia considere inválidos.

**Aceite:** o participante sabe qual período avaliar; período e versão do questionário são recuperáveis; incoerências recebem sinalização; booleanos não viram notas numéricas silenciosamente.

### 11 A documentação e os rótulos não descrevem uma única versão do projeto

**Prioridade média — divergência documental confirmada.** Além do conflito entre D1 e D2:

| Local | Divergência | Atualização proposta |
|---|---|---|
| D2, seções 3 e 5 | Preserva pesos antigos e apresenta resultado final como ainda não calculado | Referenciar ICSA revisado e descrever a implementação atual com suas pendências |
| `docs/SCORE-SUBJETIVO.md:9–25` e `docs/SCORES.md:51–62` | Fórmula, tabela e exemplos anteriores | Publicar a regra revisada e identificar a anterior como versão histórica |
| `docs/SCORE-SUBJETIVO.md:34–36` e `docs/ACWR.md:15–17` | Dizem que a agregação ou o questionário continuam sem cálculo | Registrar que o consolidado experimental já existe |
| `docs/SCORE-FINAL.md:24,39–51` | Preserva pesos e descreve limitações da foto e validação atuais | Atualizar após implementar os requisitos revisados, sem antecipar conformidade |
| `README.md:1–8,108–117` | Enquadra o projeto como predição e não esclarece suficientemente a diferença entre índice composto existente e predição validada ausente | Descrever IMCA experimental implementado; manter predição validada como finalidade futura |
| `frontend/src/pages/Autenticacao.jsx:32` | “Sistema de predição de risco de lesão” sem qualificação na tela inicial | Usar identificação do IMCA experimental ou explicitar a finalidade futura |
| `frontend/src/components/ResultadosAnalise.jsx:129` | Rótulo genérico “Score final” | Identificar IMCA para conectar interface, metodologia e resultados |
| `docs/BANCO-DE-DADOS.md:167` | Afirma que o CSV é guardado sem leitura | Descrever leitura atual e armazenamento de sessões em `detalhes.acwr` |

As mensagens de índice experimental e ausência de probabilidade clínica em `ResultadosAnalise.jsx:122,135–136` estão adequadas. Os campos legados `score_risco` e `classificacao` permanecerem nulos não é falha: o IMCA está em `detalhes.score_final` e os documentos não autorizam criar faixas clínicas arbitrárias.

**Aceite:** metodologia, interface, README, documentação das fórmulas e testes descrevem a mesma versão; resultados implementados e trabalhos futuros ficam claramente identificados.

## Itens que já estão alinhados

| Requisito documental | Evidência no código | Avaliação |
|---|---|---|
| Seis dimensões subjetivas, sem RPE ou dados antropométricos na fórmula | `score_subjetivo.py:10–19,28` | Atendido quanto à seleção de variáveis |
| Inversão de sono e recuperação, binários 0/1 | `score_subjetivo.py:59–66` | Atendido |
| Ausências e valores inválidos não viram zero na função de ICSA | `score_subjetivo.py:31–57` | Atendido na função; coleta e coerção têm as ressalvas apontadas |
| Carga por duração multiplicada pelo RPE | `carga_treino.py:182–204` | Atendido |
| RPE da sessão preferencial; formulário usado como estimativa identificada | `carga_treino.py:186–203,225–236,278–293` | Atendido; aviso também aparece na interface |
| ACWR acoplado 7/28, referência na última data, denominador zero indefinido | `carga_treino.py:250–275` | Atendido quanto à fórmula |
| Transformação do ACWR entre 1,3 e 2,0 | `score_final.py:16–20` | Atendido para valores válidos |
| Inversão postural `B = 1 - P` | `score_final.py:23–24` | Atendido |
| Média dos três pilares, cada um com peso 1/3 | `score_final.py:74–75` | Atendido; recebe o ICSA antigo |
| Sem média parcial e sem converter erro em zero | `score_final.py:43–75` | Atendido para as condições reconhecidas pelo código |
| Sem agregação de fotografias diferentes | `score_final.py:58–70` | Atendido; falta seleção protocolizada |
| Fórmula angular `max(0, 1 - 0,01 × desvio)` e média dentro da foto | `OpenCV-BodyPosture/src/domain/pontuacao.py:13–41`; `src/domain/models.py:29–34` | Atendido no código local para medições válidas |
| Um ângulo na corrida e três no ciclismo | `OpenCV-BodyPosture/src/analyzers/poseAnalyzer.py:78–109` | Atendido no código local |
| Ausência de pose gera erro | `OpenCV-BodyPosture/src/services/processamento.py:10–13`; `src/api.py:88–97` | Atendido; não cobre toda falha de qualidade geométrica |
| Valores originais, normalizados, foto e procedência do RPE preservados | `score_final.py:77–88`; `carga_treino.py:225–236`; `models.py:77–87` | Atendido em parte; falta histórico completo por versão |
| Resultado não apresentado como porcentagem de probabilidade | `ResultadosAnalise.jsx:111–137` | Atendido nos cartões; harmonizar a identificação inicial |

As faixas angulares listadas em `docs/SCORES.md:77–84` coincidem com as constantes locais de `poseAnalyzer.py:92–109`. Essa correspondência comprova consistência entre documentação e implementação local, não sustentação científica das faixas. D2, seção 6, já reconhece a necessidade de justificar essas referências individualmente.

## Verificações executadas e alcance dos resultados

| Verificação | Resultado |
|---|---|
| `backend/venv/Scripts/python.exe -B -m unittest discover -s tests -q`, executado dentro de `backend` | 44 testes aprovados |
| `node --test tests/resultados.test.mjs`, executado dentro de `frontend` | 4 testes aprovados |
| Exemplo revisado do ICSA | Código 0,5300; documento 0,4667 |
| Troca de versão simulada em memória | Bloco anterior substituído, sem histórico |
| Duas sessões separadas por 27 dias | ACWR 2,0000, histórico marcado como completo |
| Avaliação de corrida com foto de ciclismo | Entrada aceita; consolidado calculado |
| Foto concluída com fase legada inválida | Consolidado continuou disponível |
| ACWR 5 passado ao normalizador | Aceito como normalizado 1,0 |
| Valores iniciais dos sliders, binários em “não” | ICSA 0,1500 |
| Três pontos coincidentes no cálculo angular | Ângulo 0°, score de corrida 1,0 |
| Booleano em campo numérico do schema | `dor=True` convertido para `dor=1` |

Os testes de integração existentes usam banco isolado SQLite e API postural simulada. A aprovação não comprova comportamento de implantação, análise real de uma foto pelo MediaPipe, conformidade integral com D1 ou validade preditiva. Os testes existentes do ICSA protegem a versão antiga, por isso passam apesar da divergência com a revisão documental.

Não houve consulta a avaliações reais, reprocessamento de participantes ou chamada ao serviço postural hospedado. As reproduções adicionais usaram dados sintéticos e objetos em memória.

## Plano de adequação e critérios de conclusão

1. **Consolidar a metodologia.** Declarar D1 como revisão do ICSA em D2; definir períodos das perguntas, protocolo da foto e critério de cobertura do histórico. São definições de pesquisa ainda insuficientemente especificadas, não coeficientes que devam ser inventados no código.
2. **Preparar a preservação histórica.** Acrescentar armazenamento dos resultados anteriores e vínculo entre versões dos pilares e IMCA antes de disponibilizar qualquer recálculo com pesos novos.
3. **Implementar ICSA versão 2.** Atualizar fórmula, exemplos e testes; separar cálculos históricos da regra para novas avaliações. Não basta trocar a constante de versão.
4. **Corrigir a coleta e a apresentação.** Exigir respostas explícitas, informar períodos, sinalizar inconsistências e manter dor e limitação visíveis no resultado.
5. **Fechar a elegibilidade dos pilares.** Confirmar cobertura de carga, selecionar foto previamente, verificar compatibilidade e qualidade, rejeitar geometria inválida e fortalecer o contrato postural.
6. **Atualizar documentação e ampliar os testes pelos requisitos.** Cobrir o exemplo revisado, migração sem perda, sliders intocados, descanso versus desconhecido, foto incompatível, geometria degenerada e tipos/domínios inválidos. Repetir os testes do fluxo completo após as correções.

A conclusão da adequação exige que cada divergência tenha evidência de correção e teste de aceite. Enquanto isso, a descrição correta é “índice experimental parcialmente alinhado à metodologia revisada”.

## Experimentos e decisões que não devem ser confundidos com defeitos de implementação

D2, seção 8, propõe sensibilidade das transformações e dos pesos, ablação descritiva e comparação entre RPE medido e estimado. D1, seção 5, recomenda comparar o ICSA anterior com o revisado. Não foram encontrados scripts específicos desses experimentos no projeto inspecionado. São entregas metodológicas propostas para o TCC; sua ausência não significa, por si só, que a fórmula da aplicação esteja programada incorretamente.

Para produzir evidências do trabalho, recomenda-se um procedimento reproduzível que compare as versões e registre diferenças nas pontuações e na ordenação dos participantes, quando houver dados apropriados. A decisão de pesos deve preceder a leitura de resultados usada para defender a hipótese. Corrida e ciclismo devem ser apresentados separadamente quando a amostra permitir, conforme D2.

Também convém explicitar a política de arredondamento: ACWR e ICSA são armazenados com quatro casas (`carga_treino.py:273`, `score_subjetivo.py:77`), e a normalização usa esses valores persistidos. A função final evita novo arredondamento antes da média, mas não recupera precisão já perdida. Isso é descrito em `docs/SCORE-FINAL.md:34–35`; trata-se de uma decisão a documentar e testar, não de evidência de fórmula diferente por si só.

ACWR desacoplado, média de várias fotos, vídeo, aprendizado de máquina e predição prospectivamente validada estão fora do escopo implementado descrito em D2. Não é necessário adicioná-los para corrigir as divergências identificadas. A conformidade de software deve ser demonstrada separadamente da eventual validade clínica ou prognóstica do IMCA.
