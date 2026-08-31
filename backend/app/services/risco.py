"""Motor de predição de risco de lesão.

O escore final (0-100) combina três blocos, cada um com peso próprio:

    Questionário de prontidão (40%) — dor, fadiga, sono, recuperação, RPE,
        histórico de lesão e limitação atual.
    Carga de treino / ACWR (40%) — razão aguda:crônica, monotonia e volume.
    Análise das fotografias (20%) — desvios posturais detectados.

Quando um bloco não tem dados (sem CSV ou sem foto), seu peso é redistribuído
proporcionalmente entre os blocos disponíveis, para que o escore continue
comparável em uma escala de 0 a 100.
"""

from __future__ import annotations

PESOS = {"questionario": 0.40, "carga": 0.40, "foto": 0.20}


def _bloco_questionario(d: dict) -> tuple[float, list[dict]]:
    """Retorna escore 0-100 do bloco e os fatores que mais contribuíram."""
    fatores: list[dict] = []
    pontos = 0.0

    dor = d["dor"]
    if dor >= 7:
        pontos += 30
        fatores.append({"fator": "Dor elevada", "detalhe": f"Nível de dor {dor}/10.", "impacto": "alto"})
    elif dor >= 4:
        pontos += 16
        fatores.append({"fator": "Dor moderada", "detalhe": f"Nível de dor {dor}/10.", "impacto": "medio"})
    elif dor >= 2:
        pontos += 6

    fadiga = d["fadiga"]
    if fadiga >= 7:
        pontos += 20
        fatores.append({"fator": "Fadiga elevada", "detalhe": f"Fadiga {fadiga}/10.", "impacto": "alto"})
    elif fadiga >= 4:
        pontos += 10
        fatores.append({"fator": "Fadiga moderada", "detalhe": f"Fadiga {fadiga}/10.", "impacto": "medio"})

    sono = d["sono"]
    if sono <= 3:
        pontos += 18
        fatores.append({"fator": "Sono ruim", "detalhe": f"Qualidade do sono {sono}/10. O sono insuficiente é um dos preditores mais fortes de lesão.", "impacto": "alto"})
    elif sono <= 5:
        pontos += 9
        fatores.append({"fator": "Sono irregular", "detalhe": f"Qualidade do sono {sono}/10.", "impacto": "medio"})

    rec = d["recuperacao"]
    if rec <= 3:
        pontos += 15
        fatores.append({"fator": "Recuperação insuficiente", "detalhe": f"Sensação de recuperação {rec}/10.", "impacto": "alto"})
    elif rec <= 5:
        pontos += 7

    rpe = d["rpe"]
    if rpe >= 8:
        pontos += 10
        fatores.append({"fator": "Esforço percebido alto", "detalhe": f"RPE médio recente {rpe}/10.", "impacto": "medio"})
    elif rpe >= 6:
        pontos += 5

    if d["lesao_previa"]:
        pontos += 15
        detalhe = "Histórico de lesão prévia no esporte — o fator de risco isolado mais consistente na literatura."
        if d.get("lesao_quando") in {"menos_3_meses", "3_6_meses"}:
            pontos += 8
            detalhe += " Ocorrência recente aumenta a probabilidade de recidiva."
        fatores.append({"fator": "Lesão prévia", "detalhe": detalhe, "impacto": "alto"})

    if d["dor_limita"]:
        pontos += 20
        fatores.append({"fator": "Dor limitante", "detalhe": "A dor atual já limita a execução dos treinos — sinal de alerta para interrupção da progressão de carga.", "impacto": "alto"})

    # IMC como modulador leve.
    altura_m = d["altura_cm"] / 100
    imc = d["peso_kg"] / (altura_m**2) if altura_m > 0 else 0
    if imc >= 30:
        pontos += 8
        fatores.append({"fator": "IMC elevado", "detalhe": f"IMC {imc:.1f} — maior carga articular por passada.", "impacto": "medio"})
    elif imc >= 27:
        pontos += 4

    if d["tempo_pratica"] in {"menos_6_meses", "6_meses_1_ano"}:
        pontos += 6
        fatores.append({"fator": "Pouco tempo de prática", "detalhe": "Atletas iniciantes têm menor tolerância tecidual à carga.", "impacto": "medio"})

    return min(100.0, pontos / 1.51), fatores


def _bloco_carga(acwr_dados: dict) -> tuple[float | None, list[dict]]:
    acwr = acwr_dados.get("acwr")
    if acwr is None:
        return None, []

    fatores: list[dict] = []
    if acwr > 1.5:
        pontos = 85 + min(15, (acwr - 1.5) * 30)
        fatores.append({"fator": "ACWR em zona de risco", "detalhe": f"Razão aguda:crônica de {acwr:.2f}. Acima de 1,5 a probabilidade de lesão sobe de forma acentuada (Gabbett, 2016).", "impacto": "alto"})
    elif acwr > 1.3:
        pontos = 55
        fatores.append({"fator": "ACWR em zona de atenção", "detalhe": f"Razão aguda:crônica de {acwr:.2f}. Progressão de carga acima do ideal.", "impacto": "medio"})
    elif acwr >= 0.8:
        pontos = 15
        fatores.append({"fator": "ACWR na faixa ideal", "detalhe": f"Razão aguda:crônica de {acwr:.2f}, dentro da faixa protetora de 0,8 a 1,3.", "impacto": "baixo"})
    else:
        pontos = 40
        fatores.append({"fator": "ACWR baixo (subcarga)", "detalhe": f"Razão aguda:crônica de {acwr:.2f}. A carga crônica baixa reduz a tolerância do tecido e aumenta o risco quando o treino voltar a subir.", "impacto": "medio"})

    monotonia = acwr_dados.get("monotonia")
    if monotonia and monotonia > 2.0:
        pontos = min(100.0, pontos + 12)
        fatores.append({"fator": "Monotonia de treino alta", "detalhe": f"Índice de monotonia {monotonia:.2f}. Semanas sem variação de carga elevam o risco de sobrecarga.", "impacto": "medio"})

    if acwr_dados.get("total_sessoes", 0) < 6:
        fatores.append({"fator": "Histórico curto", "detalhe": "Poucas sessões no arquivo enviado — o ACWR calculado tem confiabilidade reduzida.", "impacto": "info"})

    return min(100.0, pontos), fatores


def _bloco_foto(analises: list[dict]) -> tuple[float | None, list[dict]]:
    validas = [a for a in analises if a.get("ok")]
    if not validas:
        return None, []

    fatores: list[dict] = []
    total = 0
    for a in validas:
        for alerta in a.get("alertas", []):
            if alerta["peso"] > 0:
                total += alerta["peso"]
                fatores.append({
                    "fator": alerta["titulo"],
                    "detalhe": alerta["descricao"],
                    "impacto": alerta["nivel"],
                })

    # Cada foto pode somar no máximo ~13 pontos de alerta; normaliza para 0-100.
    teto = 13 * len(validas)
    return min(100.0, total / teto * 100) if teto else 0.0, fatores


def classificar(score: float) -> str:
    if score < 30:
        return "baixo"
    if score < 55:
        return "moderado"
    if score < 75:
        return "alto"
    return "muito_alto"


def _recomendacoes(classe: str, fatores: list[dict], acwr: float | None) -> list[str]:
    recs: list[str] = []
    nomes = {f["fator"] for f in fatores}

    if classe in {"alto", "muito_alto"}:
        recs.append("Reduza o volume semanal em 20% a 30% na próxima semana e reavalie antes de retomar a progressão.")
    if classe == "muito_alto":
        recs.append("Procure avaliação presencial com fisioterapeuta ou médico do esporte antes do próximo bloco de treino.")

    if acwr is not None and acwr > 1.3:
        recs.append("Limite o aumento de carga a no máximo 10% por semana até o ACWR retornar à faixa de 0,8 a 1,3.")
    if acwr is not None and acwr < 0.8:
        recs.append("Retome o volume de forma gradual: a carga crônica baixa exige reconstrução progressiva da tolerância.")

    if "Dor limitante" in nomes or "Dor elevada" in nomes:
        recs.append("Substitua as sessões de alta intensidade por treino de baixo impacto enquanto houver dor.")
    if "Sono ruim" in nomes or "Sono irregular" in nomes:
        recs.append("Priorize de 7 a 9 horas de sono: é a intervenção de recuperação com melhor custo-benefício.")
    if "Assimetria lateral relevante" in nomes:
        recs.append("Inclua trabalho unilateral de força para reduzir a assimetria identificada nas fotografias.")
    if any(n.startswith("Aterrissagem") for n in nomes):
        recs.append("Aumente a cadência em 5% a 10% para reduzir o sobrepasso e o impacto no contato inicial.")
    if "Monotonia de treino alta" in nomes:
        recs.append("Alterne dias fortes e leves para quebrar a monotonia da semana.")

    if not recs:
        recs.append("Mantenha a rotina atual e siga registrando os treinos: o quadro está dentro dos parâmetros esperados.")
    return recs


def avaliar(dados: dict, acwr_dados: dict, analises_foto: list[dict]) -> dict:
    """Combina os três blocos em um escore final de risco de lesão."""
    s_quest, f_quest = _bloco_questionario(dados)
    s_carga, f_carga = _bloco_carga(acwr_dados)
    s_foto, f_foto = _bloco_foto(analises_foto)

    blocos = {"questionario": s_quest, "carga": s_carga, "foto": s_foto}
    disponiveis = {k: v for k, v in blocos.items() if v is not None}
    peso_total = sum(PESOS[k] for k in disponiveis)
    score = round(sum(v * PESOS[k] for k, v in disponiveis.items()) / peso_total, 1)

    fatores = f_quest + f_carga + f_foto
    ordem = {"alto": 0, "medio": 1, "baixo": 2, "ok": 3, "info": 4}
    fatores.sort(key=lambda f: ordem.get(f["impacto"], 5))

    classe = classificar(score)
    return {
        "score": score,
        "classificacao": classe,
        "blocos": {
            "questionario": round(s_quest, 1),
            "carga": round(s_carga, 1) if s_carga is not None else None,
            "foto": round(s_foto, 1) if s_foto is not None else None,
        },
        "pesos_aplicados": {k: round(PESOS[k] / peso_total, 2) for k in disponiveis},
        "fatores": fatores,
        "recomendacoes": _recomendacoes(classe, fatores, acwr_dados.get("acwr")),
        "acwr": acwr_dados,
        "analises_foto": analises_foto,
    }
