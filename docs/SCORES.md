# Como os três scores são calculados

Este documento descreve os três cálculos originais, que foram preservados.
A padronização e a composição implementadas estão em [SCORE-FINAL.md](SCORE-FINAL.md).

| Score | Origem | Escala atual | Significado de um valor maior |
|---|---|---|---|
| ACWR | Planilha de treinos e RPE | Razão que pode ultrapassar 1 | Maior carga recente em relação à média dos 28 dias |
| Subjetivo (ICSA) | Respostas do atleta | 0 a 1 | Condição subjetiva mais desfavorável |
| Postural | API de análise da imagem | 0 a 1, por foto | Ângulos mais próximos dos padrões definidos na API |

## 1. Score da planilha — ACWR

O sistema lê a data, a duração e o esforço percebido (RPE de 0 a 10) de cada sessão.

```text
Carga da sessão = duração em minutos × RPE
Carga aguda = soma das cargas dos últimos 7 dias ÷ 7
Carga crônica = soma das cargas dos últimos 28 dias ÷ 28
ACWR = carga aguda ÷ carga crônica
```

Os períodos terminam na data mais recente da planilha, incluindo esse dia. Os 7 dias
também fazem parte dos 28 dias. O campo chamado `mes` representa 28 dias, não um mês
do calendário. Dias sem registros não acrescentam carga; os divisores continuam 7 e
28, mesmo com histórico incompleto, que recebe uma indicação no resultado.

O RPE de cada sessão é preservado. Somente quando estiver ausente, o sistema usa o
RPE do formulário como estimativa, registrando `origem_rpe: formulario` e
`carga_estimada: true`. Esse valor geral não é um session-RPE medido para cada treino.
Um RPE inválido gera erro; não é substituído pelo formulário.

Exemplo: 700 unidades de carga nos 7 dias e 1.400 nos 28 dias resultam em
`(700 ÷ 7) ÷ (1.400 ÷ 28) = 2`. Isso significa que a média diária recente é o dobro
da média diária dos 28 dias. ACWR igual a 1 indica médias iguais; abaixo de 1,
a média recente é menor. Essa razão não é uma porcentagem de risco.

Se a carga crônica for zero, o resultado fica indisponível (`None`). O cálculo é
arredondado para quatro casas decimais. Nesta fórmula, com cargas não negativas e
períodos sobrepostos, a razão fica entre 0 e 4 quando o denominador é positivo.

Código: [carga_treino.py](../backend/app/services/carga_treino.py).

## 2. Score dos dados do atleta — ICSA

O Índice de Condição Subjetiva do Atleta combina seis respostas. Dor e fadiga são
divididas por 10. Sono e recuperação são invertidos, pois respostas maiores nesses
campos representam uma condição mais favorável. Para as respostas sim/não,
sim vale 1 e não vale 0.

```text
ICSA = 0,25 × (dor ÷ 10)
     + 0,15 × (fadiga ÷ 10)
     + 0,15 × ((10 − sono) ÷ 10)
     + 0,15 × ((10 − recuperação) ÷ 10)
     + 0,20 × dor que limita treinos
     + 0,10 × lesão prévia
```

Os pesos somam 1. O resultado vai de 0 (mais favorável) a 1 (mais desfavorável),
com quatro casas decimais. Por exemplo, dor e fadiga iguais a 0, sono e recuperação
iguais a 5, com dor que limita treinos e lesão prévia, produzem ICSA de 0,45.

RPE, idade, peso e os demais dados de caracterização não entram nessa fórmula.
Se uma das seis respostas estiver ausente ou inválida, o score fica indisponível;
ela não é tratada como zero. O ICSA é um índice experimental, não uma probabilidade
de lesão.

Código: [score_subjetivo.py](../backend/app/services/score_subjetivo.py).

## 3. Score postural — imagem

O cálculo acontece na aplicação `OpenCV-BodyPosture`. O MediaPipe identifica os
pontos corporais na imagem, e a aplicação calcula os ângulos usando suas posições.
Cada ângulo é comparado com a faixa configurada para a modalidade e a fase:

| Modalidade e ângulo | Faixa aceita no código atual |
|---|---|
| Ciclismo: tronco em relação à horizontal | 40° a 50° |
| Ciclismo: braço/tronco | 85° a 90° |
| Ciclismo: joelho na fase superior | Pelo menos 68° |
| Ciclismo: joelho na extensão máxima | 140° a 145° |
| Corrida: joelho no contato inicial | Até 160° |
| Corrida: joelho no apoio médio | Até 140° |

Os limites são inclusivos. Dentro da faixa, o desvio é zero. Fora dela, o desvio
é a distância, em graus, até o limite mais próximo, incluindo frações de grau.

```text
Score do ângulo = máximo entre 0 e (1 − 0,01 × desvio em graus)
Score da foto = soma dos scores dos ângulos ÷ quantidade de ângulos
```

No ciclismo, a foto usa a média de três ângulos, com pesos iguais. Na corrida, usa
somente o ângulo do joelho indicado pelo usuário. Um joelho de ciclismo na extensão
máxima medindo 150° tem desvio de 5° e score individual de 0,95.

O score da foto vai de 0 a 1 e é arredondado para quatro casas. Quanto maior,
maior a aderência aos padrões configurados. Sem pose detectada, a API retorna erro
sem atribuir score. O TCC recebe e armazena esse resultado sem recalculá-lo.
Cada foto mantém seu próprio score; não existe média entre fotos no TCC.

Regra conferida no código local da outra aplicação em 27/10/2026:
`src/domain/pontuacao.py`, `src/domain/models.py` e
`src/analyzers/poseAnalyzer.py`. Se essa aplicação mudar, esta descrição deve ser
revisada. Integração no TCC: [analise_postural.py](../backend/app/services/analise_postural.py).

## Por que ainda não somar os valores diretamente?

Os três números medem coisas diferentes. ICSA e postural já estão entre 0 e 1,
mas apontam em sentidos opostos. O ACWR é uma razão de cargas, com outra escala;
um valor maior informa aumento relativo da carga, sem representar diretamente a
mesma condição medida pelos outros scores.

A composição agora transforma o ACWR por `min(1, max(0, (ACWR − 1,3) / 0,7))`,
inverte o postural por `1 − P` e reutiliza o ICSA. O final é a média dos três
componentes padronizados, com pesos iguais. Colocá-los no mesmo intervalo não
garante significado clínico equivalente: trata-se de uma regra experimental.

[score_final.py](../backend/app/services/score_final.py) preserva os valores brutos
e retorna também os normalizados. Dados ausentes ou inválidos, histórico marcado
como incompleto ou várias fotos sem protocolo de seleção deixam o final `None`.
Zero continua sendo um resultado válido. Veja as regras completas em
[SCORE-FINAL.md](SCORE-FINAL.md).
