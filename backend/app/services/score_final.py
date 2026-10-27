"""Ponto de acesso aos três componentes para definir futuramente o score final."""


def calc_score_final(avaliacao) -> dict:
    """Reúne os scores já calculados, sem executar análises novamente.

    ACWR é uma razão bruta. 
    ICSA vai de 0 a 1 (maior é mais desfavorável).
    O postural vai de 0 a 1 (maior é melhor), com um valor por fotografia.
    Resultados ausentes ou com erro ficam como None; zero continua sendo válido.
    """
    detalhes = avaliacao.detalhes or {}
    acwr = detalhes.get("acwr") or {}
    subjetivo = detalhes.get("score_subjetivo") or {}

    score_acwr = acwr.get("acwr") if acwr.get("status") == "concluida" else None
    score_subjetivo = subjetivo.get("score") if subjetivo.get("status") == "concluida" else None

    scores_posturais = []
    for foto in sorted(avaliacao.fotos, key=lambda foto: foto.id):
        analise = foto.analise or {}
        score = analise.get("score") if analise.get("status") == "concluida" else None
        scores_posturais.append({"foto_id": foto.id, "score": score})

    # Defina sua fórmula aqui usando score_acwr, score_subjetivo e scores_posturais.
    # A combinação e a escolha entre múltiplas fotos ainda não foram definidas.
    score_final = None

    return {
        "score_acwr": score_acwr,
        "score_subjetivo": score_subjetivo,
        "scores_posturais": scores_posturais,
        "score_final": score_final,
    }


def atualizar_score_final(avaliacao) -> bool:
    """Atualiza o bloco consolidado preservando os resultados individuais."""
    resultado = calc_score_final(avaliacao)
    detalhes = avaliacao.detalhes or {}
    if detalhes.get("score_final") == resultado:
        return False
    avaliacao.detalhes = {**detalhes, "score_final": resultado}
    return True
