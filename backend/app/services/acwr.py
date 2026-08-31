"""Cálculo de carga de treino e ACWR (Acute:Chronic Workload Ratio).

Carga da sessão = duração (min) x RPE  (método de Foster, sRPE).
Quando o CSV não traz RPE, estima-se a partir do ritmo ou da frequência cardíaca.

ACWR = carga aguda (média diária dos últimos 7 dias)
     / carga crônica (média diária dos últimos 28 dias)

Faixas de referência (Gabbett, 2016):
    < 0.80        -> subcarga (destreino)
    0.80 - 1.30   -> "sweet spot"
    1.31 - 1.50   -> zona de atenção
    > 1.50        -> zona de risco elevado
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

JANELA_AGUDA = 7
JANELA_CRONICA = 28

_COLUNAS = {
    "data": ["date", "data", "activity date", "start", "start_date", "datetime", "inicio", "incio"],
    "duracao": ["duration", "moving time", "elapsed time", "tempo", "duracao", "durao", "time"],
    "distancia": ["distance", "distancia", "distncia", "dist"],
    "rpe": ["rpe", "perceived exertion", "esforco", "esforo", "effort"],
    "fc": ["average heart rate", "avg hr", "heart rate", "fc media", "fc", "hr"],
    "tipo": ["activity type", "type", "sport", "esporte", "tipo"],
}


@dataclass
class Sessao:
    data: datetime
    duracao_min: float
    distancia_km: float | None
    rpe: float | None
    carga: float


def _norm(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.strip().lower())


def _mapear_colunas(cabecalho: list[str]) -> dict[str, int]:
    mapa: dict[str, int] = {}
    normalizado = [_norm(c) for c in cabecalho]
    for campo, apelidos in _COLUNAS.items():
        for i, col in enumerate(normalizado):
            if col and any(a in col for a in apelidos):
                mapa.setdefault(campo, i)
                break
    return mapa


def _parse_data(valor: str) -> datetime | None:
    valor = valor.strip().strip('"')
    formatos = [
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y",
        "%b %d, %Y, %I:%M:%S %p", "%d %b %Y %H:%M:%S",
    ]
    for f in formatos:
        try:
            return datetime.strptime(valor, f).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _parse_duracao(valor: str) -> float | None:
    """Aceita minutos ("45"), segundos ("2700") ou "HH:MM:SS"."""
    valor = valor.strip()
    if not valor:
        return None
    if ":" in valor:
        try:
            partes = [float(p or 0) for p in valor.split(":")]
        except ValueError:
            return None
        while len(partes) < 3:
            partes.insert(0, 0.0)
        h, m, s = partes[-3:]
        total = h * 60 + m + s / 60
        return total if total > 0 else None
    try:
        n = float(valor.replace(",", "."))
    except ValueError:
        return None
    if n <= 0:
        return None
    # Heurística: valores grandes vêm em segundos (padrão Strava/Garmin).
    return n / 60 if n > 600 else n


def _num(valor: str) -> float | None:
    try:
        n = float(valor.strip().replace(",", "."))
    except (ValueError, AttributeError):
        return None
    return n if n > 0 else None


def _rpe_estimado(duracao_min: float, distancia_km: float | None, fc: float | None) -> float:
    """Estima RPE 1-10 quando o arquivo não informa esforço percebido."""
    if fc and fc > 60:
        # Percentual aproximado da FC máxima estimada (200 bpm) mapeado em 1-10.
        return max(1.0, min(10.0, (fc / 200) * 12 - 2))
    if distancia_km and duracao_min > 0:
        vel = distancia_km / (duracao_min / 60)  # km/h
        if vel >= 25:
            return 7.0
        if vel >= 15:
            return 6.0
        if vel >= 11:
            return 6.0
        if vel >= 8:
            return 5.0
        return 4.0
    return 5.0


def ler_csv(conteudo: bytes) -> list[Sessao]:
    """Lê um CSV de histórico de treino (Strava, Garmin ou planilha própria)."""
    texto = conteudo.decode("utf-8-sig", errors="replace")
    amostra = texto[:4096]
    try:
        delim = csv.Sniffer().sniff(amostra, delimiters=",;\t").delimiter
    except csv.Error:
        delim = ";" if amostra.count(";") > amostra.count(",") else ","

    linhas = [l for l in csv.reader(io.StringIO(texto), delimiter=delim) if any(c.strip() for c in l)]
    if len(linhas) < 2:
        return []

    mapa = _mapear_colunas(linhas[0])
    if "data" not in mapa or "duracao" not in mapa:
        raise ValueError(
            "CSV sem colunas reconhecidas. É necessário ao menos uma coluna de data "
            "e uma de duração (ex.: 'date' e 'duration')."
        )

    sessoes: list[Sessao] = []
    for linha in linhas[1:]:
        def campo(nome: str) -> str:
            i = mapa.get(nome)
            return linha[i] if i is not None and i < len(linha) else ""

        data = _parse_data(campo("data"))
        duracao = _parse_duracao(campo("duracao"))
        if not data or not duracao:
            continue

        distancia = _num(campo("distancia"))
        if distancia and distancia > 1000:  # metros -> km
            distancia = distancia / 1000

        rpe = _num(campo("rpe"))
        if rpe and rpe > 10:
            rpe = rpe / 10
        if not rpe:
            rpe = _rpe_estimado(duracao, distancia, _num(campo("fc")))

        sessoes.append(
            Sessao(
                data=data,
                duracao_min=round(duracao, 1),
                distancia_km=round(distancia, 2) if distancia else None,
                rpe=round(rpe, 1),
                carga=round(duracao * rpe, 1),
            )
        )

    sessoes.sort(key=lambda s: s.data)
    return sessoes


def faixa_acwr(acwr: float | None) -> str | None:
    if acwr is None:
        return None
    if acwr < 0.8:
        return "subcarga"
    if acwr <= 1.3:
        return "ideal"
    if acwr <= 1.5:
        return "atencao"
    return "risco"


def calcular_acwr(sessoes: list[Sessao], referencia: datetime | None = None) -> dict:
    """Retorna carga aguda, crônica, ACWR, monotonia e a série diária de carga."""
    vazio = {
        "acwr": None, "carga_aguda": None, "carga_cronica": None, "faixa": None,
        "serie_diaria": [], "total_sessoes": 0, "monotonia": None,
    }
    if not sessoes:
        return vazio

    ref = referencia or max(s.data for s in sessoes)
    inicio_agudo = ref - timedelta(days=JANELA_AGUDA)
    inicio_cronico = ref - timedelta(days=JANELA_CRONICA)

    carga_aguda = sum(s.carga for s in sessoes if inicio_agudo < s.data <= ref) / JANELA_AGUDA
    carga_cronica = sum(s.carga for s in sessoes if inicio_cronico < s.data <= ref) / JANELA_CRONICA
    acwr = round(carga_aguda / carga_cronica, 2) if carga_cronica > 0 else None

    # Monotonia de Foster: média / desvio-padrão das cargas diárias da semana.
    diarias = [0.0] * JANELA_AGUDA
    for s in sessoes:
        if inicio_agudo < s.data <= ref:
            atras = min(JANELA_AGUDA - 1, (ref.date() - s.data.date()).days)
            diarias[JANELA_AGUDA - 1 - atras] += s.carga
    media = sum(diarias) / JANELA_AGUDA
    desvio = (sum((d - media) ** 2 for d in diarias) / JANELA_AGUDA) ** 0.5
    monotonia = round(media / desvio, 2) if desvio > 0 else None

    # Série diária dos últimos 28 dias, para o gráfico do resultado.
    por_dia = {
        (ref - timedelta(days=JANELA_CRONICA - 1 - i)).date().isoformat(): 0.0
        for i in range(JANELA_CRONICA)
    }
    for s in sessoes:
        chave = s.data.date().isoformat()
        if chave in por_dia:
            por_dia[chave] += s.carga

    return {
        "acwr": acwr,
        "carga_aguda": round(carga_aguda, 1),
        "carga_cronica": round(carga_cronica, 1),
        "faixa": faixa_acwr(acwr),
        "monotonia": monotonia,
        "total_sessoes": len(sessoes),
        "serie_diaria": [{"data": d, "carga": round(c, 1)} for d, c in por_dia.items()],
    }
