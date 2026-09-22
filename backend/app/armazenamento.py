"""Armazenamento das fotos e CSVs enviados, dentro do PostgreSQL.

Os arquivos ficam na tabela `arquivos` em vez do disco: no Render gratuito o
disco é apagado a cada deploy ou quando o serviço dorme, e o banco (Neon) é
permanente.

As fotos são reduzidas antes de gravar: fotos de celular chegam com vários MB e
o plano gratuito do Neon tem 0,5 GB. Com no máximo 1920 px de lado, cada foto
ocupa algumas centenas de KB e continua nítida para avaliar postura.
"""

import io
import uuid

from fastapi import HTTPException, status
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import Arquivo

LADO_MAXIMO_PX = 1920
QUALIDADE_JPEG = 85


def preparar_imagem(conteudo: bytes, nome_original: str) -> bytes:
    """Valida que o arquivo é mesmo uma imagem e devolve um JPEG reduzido."""
    try:
        with Image.open(io.BytesIO(conteudo)) as bruta:
            imagem = ImageOps.exif_transpose(bruta)  # respeita a rotação do celular
            imagem = imagem.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"O arquivo {nome_original} não é uma imagem válida"
        ) from exc

    imagem.thumbnail((LADO_MAXIMO_PX, LADO_MAXIMO_PX))
    saida = io.BytesIO()
    imagem.save(saida, format="JPEG", quality=QUALIDADE_JPEG, optimize=True)
    return saida.getvalue()


def salvar(db: Session, conteudo: bytes, extensao: str, tipo: str) -> str:
    """Grava o arquivo e devolve o nome gerado, usado na URL `/uploads/{nome}`."""
    nome = f"{uuid.uuid4().hex}{extensao}"
    db.add(Arquivo(nome=nome, tipo=tipo, tamanho_bytes=len(conteudo), conteudo=conteudo))
    return nome


def remover(db: Session, nomes: list[str]) -> None:
    if nomes:
        db.execute(delete(Arquivo).where(Arquivo.nome.in_(nomes)))
