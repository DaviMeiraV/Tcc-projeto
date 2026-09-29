"""Comunicação com a API de postura e armazenamento do resultado por fotografia."""

import base64
import binascii
import io

import httpx
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import armazenamento
from app.core.config import settings
from app.models import Arquivo, Avaliacao
from app.schemas import FotoMeta

FASES = {"contato_inicial": 1, "apoio_medio": 2, "fase_superior": 1, "extensao_maxima": 2}


class ErroAnalise(Exception):
    """Falha recuperável: o formulário e a foto continuam salvos."""


def montar_payload(conteudo: bytes, foto) -> dict:
    try:
        foto = FotoMeta.model_validate(foto, from_attributes=True)
    except ValidationError as exc:
        raise ErroAnalise("Os dados desta foto estão incompletos ou incompatíveis. Envie um novo formulário com os dados corrigidos.") from exc
    payload = {
        "modalidade": "bike" if foto.modalidade == "ciclismo" else "corrida",
        "fase_joelho": FASES[foto.fase],
        "imagem_base64": base64.b64encode(conteudo).decode("ascii"),
    }
    if foto.modalidade == "corrida":
        payload["joelho_frente"] = {"esquerdo": "E", "direito": "D"}[foto.joelho_frente]
    return payload


def analisar(client: httpx.Client, conteudo: bytes, foto) -> tuple[dict, bytes]:
    try:
        resposta = client.post(
            f"{settings.ANALISE_API_URL.rstrip('/')}/analises",
            json=montar_payload(conteudo, foto),
        )
    except httpx.TimeoutException as exc:
        raise ErroAnalise("A análise excedeu o tempo de espera. Tente novamente.") from exc
    except httpx.RequestError as exc:
        raise ErroAnalise("Não foi possível conectar à API de análise. Tente novamente mais tarde.") from exc

    if not resposta.is_success:
        try:
            detalhe = resposta.json().get("detail")
        except (ValueError, AttributeError):
            detalhe = None
        if isinstance(detalhe, list):
            detalhe = "; ".join(str(e.get("msg", "Dados inválidos")) for e in detalhe if isinstance(e, dict))
        mensagem = detalhe if isinstance(detalhe, str) and detalhe else "Serviço indisponível ou dados rejeitados."
        raise ErroAnalise(f"API de análise (HTTP {resposta.status_code}): {mensagem}")

    try:
        resultado = resposta.json()
        imagem = resultado["imagem_tratada"]
        score = resultado["score"]
        if (resultado["pose_detectada"] is not True or isinstance(score, bool)
                or not isinstance(score, (int, float)) or not 0 <= score <= 1
                or imagem["media_type"] != "image/png"):
            raise ValueError("Resultado inválido")
        png = base64.b64decode(imagem["base64"], validate=True)
        with Image.open(io.BytesIO(png)) as verificada:
            if verificada.format != "PNG":
                raise ValueError("Formato inválido")
            verificada.verify()
        # O caminho `saida/...` pertence ao servidor externo. Usamos o PNG retornado.
        resultado["imagem_tratada"] = {
            "media_type": "image/png",
            "largura": verificada.width,
            "altura": verificada.height,
        }
        return resultado, png
    except (ValueError, KeyError, TypeError, OSError, binascii.Error,
            UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ErroAnalise("A API retornou uma resposta ou imagem inválida. Tente novamente.") from exc


def processar_fotos(db: Session, avaliacao_id: int) -> Avaliacao:
    # Serializa novas tentativas do mesmo envio e preserva as análises já concluídas.
    avaliacao = db.scalar(select(Avaliacao).where(Avaliacao.id == avaliacao_id).with_for_update())
    if avaliacao is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    with httpx.Client(timeout=settings.ANALISE_API_TIMEOUT) as client:
        for foto in avaliacao.fotos:
            if (foto.analise or {}).get("status") == "concluida":
                continue
            arquivo = db.get(Arquivo, foto.arquivo)
            try:
                if arquivo is None:
                    raise ErroAnalise("A fotografia não está disponível para análise.")
                resultado, png = analisar(client, arquivo.conteudo, foto)
                nome = armazenamento.salvar(db, png, ".png", "image/png")
                resultado["imagem_tratada"]["arquivo"] = nome
                foto.analise = {**resultado, "status": "concluida"}
            except ErroAnalise as exc:
                foto.analise = {"status": "erro", "erro": str(exc)}
    db.commit()
    db.refresh(avaliacao)
    return avaliacao
