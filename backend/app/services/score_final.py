"""Padronização e composição dos scores, preservando os cálculos originais."""

import math

VERSAO_SCORE_FINAL = 1


def numero_valido(valor, maximo=None) -> bool:
    return (
        isinstance(valor, (int, float)) and not isinstance(valor, bool)
        and math.isfinite(valor) and valor >= 0
        and (maximo is None or valor <= maximo)
    )


def normalizar_acwr(acwr):
    if not numero_valido(acwr):
        return None
    # Mantém a precisão até a composição; arredonda somente na saída.
    return min(1.0, max(0.0, (acwr - 1.3) / 0.7))


def normalizar_postural(score):
    return 1.0 - score if numero_valido(score, 1) else None


def arredondar(score):
    return round(score, 4) if score is not None else None


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
    if not numero_valido(score_subjetivo, 1):
        score_subjetivo = None
    acwr_normalizado = normalizar_acwr(score_acwr)

    scores_posturais = []
    for foto in sorted(avaliacao.fotos, key=lambda foto: foto.id):
        analise = foto.analise or {}
        score = analise.get("score") if analise.get("status") == "concluida" else None
        scores_posturais.append({
            "foto_id": foto.id, "score": score,
            "score_normalizado": arredondar(normalizar_postural(score)),
        })

    # Não existe protocolo de seleção entre várias fotos no formulário atual.
    foto_selecionada = scores_posturais[0] if len(scores_posturais) == 1 else None
    postural_original = foto_selecionada["score"] if foto_selecionada else None
    postural_normalizado = normalizar_postural(postural_original)
    motivos = []
    if acwr_normalizado is None:
        motivos.append("ACWR ausente ou inválido.")
    if acwr.get("historico_incompleto"):
        motivos.append("Histórico de treinamento inferior a 28 dias.")
    if score_subjetivo is None:
        motivos.append("Score subjetivo ausente ou inválido.")
    if len(scores_posturais) > 1:
        motivos.append("Há várias fotos e nenhum protocolo define qual usar no score final.")
    elif postural_normalizado is None:
        motivos.append("Score postural ausente ou inválido.")

    # Média simples: cada componente tem peso 1/3.
    score_final = None if motivos else (acwr_normalizado + score_subjetivo + postural_normalizado) / 3

    return {
        "versao": VERSAO_SCORE_FINAL,
        "status": "indisponivel" if motivos else "concluida",
        "motivos": motivos,
        "score_acwr": score_acwr,
        "score_acwr_normalizado": arredondar(acwr_normalizado),
        "score_subjetivo": score_subjetivo,
        "scores_posturais": scores_posturais,
        "foto_id": foto_selecionada["foto_id"] if foto_selecionada else None,
        "score_postural_original": postural_original,
        "score_postural_normalizado": arredondar(postural_normalizado),
        "score_final": arredondar(score_final),
    }


def atualizar_score_final(avaliacao) -> bool:
    """Atualiza o bloco consolidado preservando os resultados individuais."""
    resultado = calc_score_final(avaliacao)
    detalhes = avaliacao.detalhes or {}
    if detalhes.get("score_final") == resultado:
        return False
    avaliacao.detalhes = {**detalhes, "score_final": resultado}
    return True
