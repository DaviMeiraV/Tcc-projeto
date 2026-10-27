"""Leitura do CSV, escolha do esforço de cada sessão e cálculo do ACWR.

RPE da planilha é preservado. Quando faltar, o esforço geral do formulário
é usado como aproximação, com a origem registrada. Não é session-RPE medido.

O fluxo principal está em calcular_csv; analisar_planilha salva e registra logs.
"""

import csv
import io
import logging
import math
import unicodedata
from datetime import date, datetime, timedelta


logger = logging.getLogger("uvicorn.error")

COLUNAS = {
    "data": ("data", "date", "activity date", "start date", "inicio", "data da atividade"),
    "duracao": (
        "duration min",
        "duracao min",
        "duracao",
        "duration",
        "tempo",
        "time",
        "moving time",
        "elapsed time",
        "tempo decorrido",
        "tempo em movimento",
    ),
    "rpe": ("rpe", "perceived exertion", "esforco", "esforco percebido"),
}

SEGUNDOS = {"moving time", "elapsed time"}

DIAS_AGUDOS = 7
DIAS_CRONICOS = 28
# A rota usa esta versão para identificar resultados antigos que precisam ser recalculados.
VERSAO_ACWR = 3


def normalizar(valor: str) -> str:
    """Padroniza cabeçalhos: remove acentos e aceita espaços ou sublinhados."""
    texto = unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode().lower()
    return " ".join(texto.replace("_", " ").strip().split())


def numero(valor: str) -> float:
    """Aceita vírgula decimal, mas rejeita NaN e infinito."""
    valor_numerico = float(valor.strip().replace(",", "."))

    if not math.isfinite(valor_numerico):
        raise ValueError("Número inválido")

    return valor_numerico


def data_atividade(valor: str) -> date:
    """Extrai somente a data da atividade."""
    valor = valor.strip()

    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()
    except ValueError:
        pass

    formatos = ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%b %d, %Y, %I:%M:%S %p")

    for formato in formatos:
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue

    raise ValueError("Data inválida; use AAAA-MM-DD ou DD/MM/AAAA")


def duracao_minutos(valor: str, coluna: str) -> float:
    """Converte a duração para minutos."""
    if ":" in valor:
        partes = [numero(parte) for parte in valor.split(":")]

        if len(partes) not in (2, 3):
            raise ValueError("Duração inválida")

        if any(parte < 0 for parte in partes):
            raise ValueError("Duração inválida")

        if any(parte >= 60 for parte in partes[1:]):
            raise ValueError("Duração inválida")

        if len(partes) == 2:
            minutos = partes[0] + partes[1] / 60
        else:
            minutos = partes[0] * 60 + partes[1] + partes[2] / 60

    else:
        minutos = numero(valor)

        if coluna in SEGUNDOS:
            minutos /= 60

    if minutos <= 0:
        raise ValueError("A duração deve ser maior que zero")

    return minutos


def criar_leitor_csv(conteudo: bytes) -> csv.DictReader:
    """Abre o CSV reconhecendo codificação e separador."""
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = conteudo.decode("cp1252")

    try:
        delimitador = csv.Sniffer().sniff(texto[:4096], delimiters=",;\t").delimiter
    except csv.Error:
        delimitador = ";" if texto[:4096].count(";") > texto[:4096].count(",") else ","

    return csv.DictReader(io.StringIO(texto), delimiter=delimitador)


def mapear_colunas(cabecalhos: list[str]) -> dict:
    """Identifica as colunas de data, duração e RPE."""
    cabecalho_normalizado = {normalizar(cabecalho): cabecalho for cabecalho in cabecalhos}
    mapa = {}

    for campo, nomes_aceitos in COLUNAS.items():
        mapa[campo] = next(
            (cabecalho_normalizado[nome] for nome in nomes_aceitos if nome in cabecalho_normalizado),
            None,
        )

    if not mapa["data"] or not mapa["duracao"]:
        raise ValueError("A planilha precisa de colunas de data e duração reconhecidas.")

    return mapa


def ler_atividades(conteudo: bytes) -> list[dict]:
    """Lê e valida todas as atividades do CSV."""
    leitor = criar_leitor_csv(conteudo)
    mapa = mapear_colunas(leitor.fieldnames or [])
    atividades = []

    for linha in leitor:
        if not any(linha.values()):
            continue

        try:
            data = data_atividade(linha.get(mapa["data"]) or "")
            minutos = duracao_minutos(
                linha.get(mapa["duracao"]) or "",
                normalizar(mapa["duracao"]),
            )

            valor_rpe = (linha.get(mapa["rpe"]) or "").strip()
            rpe = numero(valor_rpe) if valor_rpe else None

            if rpe is not None and not 0 <= rpe <= 10:
                raise ValueError("RPE deve estar entre 0 e 10")

        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"Linha {leitor.line_num}: {exc}.") from exc

        atividades.append({
            "linha": leitor.line_num,
            "data": data,
            "minutos": minutos,
            "rpe": rpe,
        })

    if not atividades:
        raise ValueError("A planilha não contém atividades.")

    return atividades


def definir_carga(atividade: dict, rpe_formulario: float | None) -> dict:
    """Define o RPE utilizado e calcula a carga da sessão."""
    rpe_original = atividade["rpe"]

    if rpe_original is not None:
        rpe_utilizado = rpe_original
        origem_rpe = "planilha"

    elif rpe_formulario is not None:
        rpe_utilizado = rpe_formulario
        origem_rpe = "formulario"

    else:
        raise ValueError(
            f"Linha {atividade['linha']}: falta RPE na sessão e no formulário."
        )

    return {
        **atividade,
        "rpe_utilizado": rpe_utilizado,
        "origem_rpe": origem_rpe,
        "carga": atividade["minutos"] * rpe_utilizado,
    }


def somar_atividades(atividades: list[dict]) -> dict:
    """Soma duração e carga das atividades."""
    return {
        "atividades": len(atividades),
        "minutos": sum(atividade["minutos"] for atividade in atividades),
        "carga": sum(atividade["carga"] for atividade in atividades),
    }


def arredondar_totais(totais: dict) -> dict:
    """Arredonda somente valores exibidos."""
    return {
        "atividades": totais["atividades"],
        "minutos": round(totais["minutos"], 2),
        "carga": round(totais["carga"], 2),
    }


def montar_sessoes(atividades: list[dict]) -> list[dict]:
    """Cria o detalhamento das sessões usadas no cálculo."""
    return [
        {
            "linha": atividade["linha"],
            "data": atividade["data"].isoformat(),
            "minutos": round(atividade["minutos"], 2),
            "rpe_original": atividade["rpe"],
            "rpe_utilizado": atividade["rpe_utilizado"],
            "origem_rpe": atividade["origem_rpe"],
            "carga": round(atividade["carga"], 2),
        }
        for atividade in atividades
    ]


def calcular_csv(conteudo: bytes, rpe_formulario: float | None = None) -> dict:
    """Calcula o ACWR dos últimos 7 e 28 dias."""
    if rpe_formulario is not None and (
        not math.isfinite(rpe_formulario) or not 0 <= rpe_formulario <= 10
    ):
        raise ValueError("RPE do formulário deve estar entre 0 e 10")

    atividades = ler_atividades(conteudo)

    referencia = max(atividade["data"] for atividade in atividades)
    inicio_cronico = referencia - timedelta(days=DIAS_CRONICOS - 1)
    inicio_agudo = referencia - timedelta(days=DIAS_AGUDOS - 1)

    periodo_cronico = [
        definir_carga(atividade, rpe_formulario)
        for atividade in atividades
        if inicio_cronico <= atividade["data"] <= referencia
    ]

    periodo_agudo = [
        atividade
        for atividade in periodo_cronico
        if atividade["data"] >= inicio_agudo
    ]

    total_cronico = somar_atividades(periodo_cronico)
    total_agudo = somar_atividades(periodo_agudo)

    carga_aguda_media = total_agudo["carga"] / DIAS_AGUDOS
    carga_cronica_media = total_cronico["carga"] / DIAS_CRONICOS

    acwr = (
        round(carga_aguda_media / carga_cronica_media, 4)
        if carga_cronica_media > 0
        else None
    )

    atividades_com_rpe_formulario = sum(
        atividade["origem_rpe"] == "formulario"
        for atividade in periodo_cronico
    )

    return {
        "status": "concluida",
        "acwr": acwr,
        "carga_aguda": round(carga_aguda_media, 4),
        "carga_cronica": round(carga_cronica_media, 4),
        "metodo": "duracao_rpe",
        "referencia": referencia.isoformat(),
        "rpe_formulario": rpe_formulario,
        "atividades_com_rpe_formulario": atividades_com_rpe_formulario,
        "carga_estimada": atividades_com_rpe_formulario > 0,
        "sessoes": montar_sessoes(periodo_cronico),
        "semana": arredondar_totais(total_agudo),
        "mes": arredondar_totais(total_cronico),
        "historico_incompleto": min(
            atividade["data"] for atividade in atividades
        ) > inicio_cronico,
    }


def analisar_planilha(avaliacao, conteudo: bytes) -> None:
    """Calcula, registra e salva o resultado do ACWR."""
    try:
        resultado = calcular_csv(conteudo, rpe_formulario=avaliacao.rpe)

    except (ValueError, csv.Error, UnicodeError) as exc:
        resultado = {"status": "erro", "erro": str(exc)}
        logger.warning("ACWR atleta_id=%s: %s", avaliacao.usuario_id, exc)

    else:
        logger.info(
            "ACWR atleta_id=%s referencia=%s metodo=%s | "
            "mes_28_dias=%s | semana_7_dias=%s | score=%s | "
            "rpe_formulario=%s atividades_com_rpe_formulario=%s carga_estimada=%s",
            avaliacao.usuario_id,
            resultado["referencia"],
            resultado["metodo"],
            resultado["mes"],
            resultado["semana"],
            resultado["acwr"],
            resultado["rpe_formulario"],
            resultado["atividades_com_rpe_formulario"],
            resultado["carga_estimada"],
        )

    # Guarda a versão também em erros, evitando reprocessar o mesmo CSV a cada consulta.
    resultado["versao"] = VERSAO_ACWR
    avaliacao.acwr = resultado.get("acwr")
    avaliacao.carga_aguda = resultado.get("carga_aguda")
    avaliacao.carga_cronica = resultado.get("carga_cronica")
    avaliacao.detalhes = {**(avaliacao.detalhes or {}), "acwr": resultado}
