"""Recebimento das submissões do formulário de pesquisa.

Nesta fase o objetivo é apenas **coletar e armazenar** os dados dos participantes.
As fotografias e o arquivo CSV são guardados como enviados, sem nenhum processamento.

O cálculo do score de risco (questionário, ACWR e análise de imagem) ainda será
definido e validado cientificamente pelo autor do TCC, e por isso não é executado
nem exposto aqui.
"""

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import Avaliacao, Foto, Usuario
from app.routers.auth import usuario_atual
from app.schemas import AvaliacaoCriar, AvaliacaoOut, AvaliacaoResumo

router = APIRouter(prefix="/avaliacoes", tags=["avaliacoes"])

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png"}
MAX_FOTOS = 3
MAX_BYTES = 8 * 1024 * 1024


def _dir_upload() -> Path:
    destino = Path(settings.UPLOAD_DIR).resolve()
    destino.mkdir(parents=True, exist_ok=True)
    return destino


@router.post("", response_model=AvaliacaoOut, status_code=status.HTTP_201_CREATED)
async def criar_avaliacao(
    payload: str = Form(..., description="JSON com os dados das etapas 1 e 2"),
    fotos: list[UploadFile] = File(default=[]),
    csv_treino: UploadFile | None = File(default=None),
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    """Registra uma submissão completa do formulário."""
    try:
        dados = AvaliacaoCriar.model_validate_json(payload)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, json.loads(exc.json())) from exc

    fotos = [f for f in fotos if f and f.filename]
    if len(fotos) > MAX_FOTOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Envie no máximo {MAX_FOTOS} imagens")
    if fotos and not dados.consentimento_foto:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "É necessário confirmar a autorização de uso das fotografias")
    if len(dados.fotos_meta) != len(fotos):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cada foto precisa ter modalidade e fase informadas")

    destino = _dir_upload()

    # ---- Fotografias: apenas armazenadas, com os rótulos informados ----
    salvas: list[tuple[str, str]] = []
    for arquivo in fotos:
        ext = Path(arquivo.filename).suffix.lower()
        if ext not in EXTENSOES_IMAGEM:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Formato não suportado: {ext}. Use JPG, JPEG ou PNG.")
        conteudo = await arquivo.read()
        if len(conteudo) > MAX_BYTES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"A imagem {arquivo.filename} excede 8 MB")

        nome = f"{uuid.uuid4().hex}{ext}"
        (destino / nome).write_bytes(conteudo)
        salvas.append((nome, arquivo.filename))

    # ---- Histórico de treino: guardado como veio, sem leitura do conteúdo ----
    csv_arquivo = csv_nome = None
    if csv_treino and csv_treino.filename:
        if not csv_treino.filename.lower().endswith(".csv"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "O histórico de treino precisa ser um arquivo .csv")
        conteudo = await csv_treino.read()
        if len(conteudo) > MAX_BYTES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo CSV maior que 8 MB")
        csv_arquivo = f"{uuid.uuid4().hex}.csv"
        (destino / csv_arquivo).write_bytes(conteudo)
        csv_nome = csv_treino.filename

    avaliacao = Avaliacao(
        usuario_id=usuario.id,
        **dados.model_dump(exclude={"fotos_meta"}),
        csv_arquivo=csv_arquivo,
        csv_nome_original=csv_nome,
    )
    db.add(avaliacao)
    db.flush()

    for (nome, original), meta in zip(salvas, dados.fotos_meta):
        db.add(Foto(
            avaliacao_id=avaliacao.id, arquivo=nome, nome_original=original,
            modalidade=meta.modalidade, fase=meta.fase, joelho_frente=meta.joelho_frente,
        ))

    db.commit()
    db.refresh(avaliacao)
    return avaliacao


@router.get("", response_model=list[AvaliacaoResumo])
def listar(usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    return db.scalars(
        select(Avaliacao).where(Avaliacao.usuario_id == usuario.id).order_by(Avaliacao.id.desc())
    ).all()


@router.get("/{avaliacao_id}", response_model=AvaliacaoOut)
def detalhar(avaliacao_id: int, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if not avaliacao or avaliacao.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada")
    return avaliacao


@router.delete("/{avaliacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(avaliacao_id: int, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if not avaliacao or avaliacao.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada")
    destino = _dir_upload()
    for f in avaliacao.fotos:
        (destino / f.arquivo).unlink(missing_ok=True)
    if avaliacao.csv_arquivo:
        (destino / avaliacao.csv_arquivo).unlink(missing_ok=True)
    db.delete(avaliacao)
    db.commit()
