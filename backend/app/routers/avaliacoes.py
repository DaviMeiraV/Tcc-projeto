import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import Avaliacao, Foto, SessaoTreino, Usuario
from app.routers.auth import usuario_atual
from app.schemas import AvaliacaoCriar, AvaliacaoOut, AvaliacaoResumo
from app.services import acwr as acwr_svc
from app.services import foto as foto_svc
from app.services import risco as risco_svc

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
    """Recebe o formulário completo, calcula o ACWR, analisa as fotos e gera o risco."""
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

    # ---- 1. Histórico de treino -> ACWR ----
    sessoes: list[acwr_svc.Sessao] = []
    if csv_treino and csv_treino.filename:
        conteudo = await csv_treino.read()
        if len(conteudo) > MAX_BYTES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo CSV maior que 8 MB")
        try:
            sessoes = acwr_svc.ler_csv(conteudo)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
        if not sessoes:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nenhuma sessão de treino válida foi encontrada no CSV")
    acwr_dados = acwr_svc.calcular_acwr(sessoes)

    # ---- 2. Fotografias -> análise postural ----
    destino = _dir_upload()
    salvas: list[tuple[str, str, dict]] = []
    analises: list[dict] = []
    for arquivo, meta in zip(fotos, dados.fotos_meta):
        ext = Path(arquivo.filename).suffix.lower()
        if ext not in EXTENSOES_IMAGEM:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Formato não suportado: {ext}. Use JPG, JPEG ou PNG.")
        conteudo = await arquivo.read()
        if len(conteudo) > MAX_BYTES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"A imagem {arquivo.filename} excede 8 MB")

        nome = f"{uuid.uuid4().hex}{ext}"
        (destino / nome).write_bytes(conteudo)
        analise = foto_svc.analisar_imagem(str(destino / nome), meta.modalidade, meta.fase, meta.joelho_frente)
        analises.append(analise)
        salvas.append((nome, arquivo.filename, analise))

    # ---- 3. Escore final ----
    resultado = risco_svc.avaliar(dados.model_dump(), acwr_dados, analises)

    avaliacao = Avaliacao(
        usuario_id=usuario.id,
        **dados.model_dump(exclude={"fotos_meta"}),
        acwr=acwr_dados["acwr"],
        carga_aguda=acwr_dados["carga_aguda"],
        carga_cronica=acwr_dados["carga_cronica"],
        score_risco=resultado["score"],
        classificacao=resultado["classificacao"],
        detalhes=resultado,
    )
    db.add(avaliacao)
    db.flush()

    for (nome, original, analise), meta in zip(salvas, dados.fotos_meta):
        db.add(Foto(
            avaliacao_id=avaliacao.id, arquivo=nome, nome_original=original,
            modalidade=meta.modalidade, fase=meta.fase,
            joelho_frente=meta.joelho_frente, analise=analise,
        ))
    for s in sessoes:
        db.add(SessaoTreino(
            avaliacao_id=avaliacao.id, data=s.data, duracao_min=s.duracao_min,
            distancia_km=s.distancia_km, rpe=s.rpe, carga=s.carga,
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
    db.delete(avaliacao)
    db.commit()
