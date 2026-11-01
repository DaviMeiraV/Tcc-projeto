"""Índice de Condição Subjetiva do Atleta (ICSA), conforme a proposta do TCC.

Escala experimental: 0 = condição mais favorável; 1 = mais desfavorável.
Não representa probabilidade de lesão e não possui faixas de risco clínico.
"""

import math
from copy import deepcopy
from datetime import datetime, timezone

VERSAO_ICSA = 2
CAMPOS = ("dor", "fadiga", "sono", "recuperacao", "dor_limita", "lesao_previa")
PESOS = {campo: 1 / len(CAMPOS) for campo in CAMPOS}
CAMPOS_BINARIOS = {"dor_limita", "lesao_previa"}
ESCALAS_INVERTIDAS = {"sono", "recuperacao"}


def calcular_icsa(respostas: dict) -> dict:
    """Valida as seis respostas e calcula a média dos componentes normalizados.

    RPE e dados de caracterização não participam desta versão da fórmula.
    Respostas ausentes ou inválidas nunca são substituídas por zero.
    """
    respostas_utilizadas = {campo: respostas.get(campo) for campo in PESOS}
    ausentes = []
    invalidos = []
    for campo, valor in respostas_utilizadas.items():
        if valor is None:
            ausentes.append(campo)
        elif campo in CAMPOS_BINARIOS:
            if not isinstance(valor, bool):
                invalidos.append(campo)
        elif (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not math.isfinite(valor)
            or not 0 <= valor <= 10
        ):
            invalidos.append(campo)

    resultado = {
        "versao": VERSAO_ICSA,
        "pesos": dict(PESOS),
        "respostas": respostas_utilizadas,
    }
    if ausentes or invalidos:
        return {
            **resultado,
            "status": "indisponivel",
            "score": None,
            "campos_ausentes": ausentes,
            "campos_invalidos": invalidos,
        }

    componentes = {}
    for campo, valor in respostas_utilizadas.items():
        if campo in CAMPOS_BINARIOS:
            componentes[campo] = 1.0 if valor else 0.0
        elif campo in ESCALAS_INVERTIDAS:
            componentes[campo] = (10 - valor) / 10
        else:
            componentes[campo] = valor / 10

    contribuicoes = {
        campo: componentes[campo] * peso
        for campo, peso in PESOS.items()
    }
    return {
        **resultado,
        "status": "concluida",
        "componentes": componentes,
        "contribuicoes": {campo: round(valor, 4) for campo, valor in contribuicoes.items()},
        "score": round(sum(componentes.values()) / len(CAMPOS), 4),
    }


def atualizar_score_subjetivo(avaliacao) -> bool:
    """Atualiza o ICSA, arquivando os resultados anteriores na troca de versão.

    Retorna se houve alteração para a rota salvar também os envios antigos.
    """
    detalhes = avaliacao.detalhes or {}
    resultado_atual = detalhes.get("score_subjetivo") or {}
    if resultado_atual.get("versao") == VERSAO_ICSA:
        return False

    # Arquiva antes de substituir: o consolidado antigo usou o ICSA anterior.
    # Cópias independentes preservam pesos, respostas e resultados como estavam.
    if resultado_atual or detalhes.get("score_final"):
        anterior = {
            "arquivado_em": datetime.now(timezone.utc).isoformat(),
            "motivo": "atualizacao_icsa",
            "versao_icsa_destino": VERSAO_ICSA,
            "score_subjetivo": deepcopy(detalhes.get("score_subjetivo")),
            "score_final": deepcopy(detalhes.get("score_final")),
        }
        detalhes = {
            **detalhes,
            "historico_scores": [*(detalhes.get("historico_scores") or []), anterior],
        }

    respostas = {campo: getattr(avaliacao, campo, None) for campo in PESOS}
    avaliacao.detalhes = {**detalhes, "score_subjetivo": calcular_icsa(respostas)}
    return True
