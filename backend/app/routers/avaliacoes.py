"""Recebimento das submissões do formulário de pesquisa.

Nesta fase o objetivo é apenas **coletar e armazenar** os dados dos participantes.
As fotografias (reduzidas para economizar espaço) e o arquivo CSV são guardados no
próprio banco, sem nenhuma análise do conteúdo.

O cálculo do score de risco (questionário, ACWR e análise de imagem) ainda será
definido e validado cientificamente pelo autor do TCC, e por isso não é executado
nem exposto aqui.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import armazenamento
from app.db import get_db
from app.models import Avaliacao, Foto, Usuario
from app.routers.auth import usuario_atual
from app.schemas import AvaliacaoCriar, AvaliacaoOut, AvaliacaoResumo

router = APIRouter(
    prefix="/avaliacoes",
    tags=["avaliacoes"],
    responses={401: {"description": "Token ausente, inválido ou expirado"}},
)

# Exemplo exibido no Swagger: o campo `payload` já vem preenchido para teste.
EXEMPLO_PAYLOAD = json.dumps(
    {
        "idade": 24,
        "sexo": "masculino",
        "esporte": "corrida",
        "tempo_pratica": "1_3_anos",
        "peso_kg": 72.5,
        "altura_cm": 178,
        "rpe": 6,
        "dor": 2,
        "fadiga": 4,
        "sono": 7,
        "recuperacao": 6,
        "lesao_previa": True,
        "dor_limita": False,
        "lesao_descricao": "Canelite na perna direita",
        "lesao_quando": "6_12_meses",
        "consentimento_foto": False,
        "fotos_meta": [],
    },
    ensure_ascii=False,
)

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png"}
MAX_FOTOS = 3
MAX_BYTES = 8 * 1024 * 1024


@router.post(
    "",
    response_model=AvaliacaoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar formulário",
    responses={
        400: {"description": "Arquivo inválido, fotos sem rótulo ou sem consentimento"},
        422: {"description": "Algum campo do `payload` fora do formato esperado"},
    },
)
async def criar_avaliacao(
    payload: str = Form(
        ...,
        description="JSON com os dados das etapas 1 e 2 (formato no exemplo).",
        examples=[EXEMPLO_PAYLOAD],
    ),
    fotos: list[UploadFile] = File(
        default=[],
        description="Até 3 imagens JPG, JPEG ou PNG, de até 8 MB cada.",
    ),
    csv_treino: UploadFile | None = File(
        default=None,
        description="Histórico de treino em CSV (opcional), até 8 MB.",
    ),
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    """Registra uma submissão completa do formulário (requisição `multipart/form-data`).

    **Regras de validação**

    * `fotos_meta` precisa ter **um item por foto**, na mesma ordem dos arquivos.
    * Com fotos, `consentimento_foto` precisa ser `true`.
    * `joelho_frente` é esperado apenas quando `modalidade` é `corrida`.

    **Valores aceitos**

    | Campo | Valores |
    |---|---|
    | `sexo` | `masculino`, `feminino`, `outro` |
    | `esporte` / `modalidade` | `corrida`, `ciclismo` |
    | `tempo_pratica` | `menos_6_meses`, `6_meses_1_ano`, `1_3_anos`, `3_5_anos`, `mais_5_anos` |
    | `lesao_quando` | `menos_3_meses`, `3_6_meses`, `6_12_meses`, `mais_1_ano` |
    | `fase` (corrida) | `contato_inicial`, `apoio_medio` |
    | `fase` (ciclismo) | `fase_superior`, `extensao_maxima` |
    | `rpe`, `dor`, `fadiga`, `sono`, `recuperacao` | inteiro de 0 a 10 |

    Fotos e CSV são guardados no banco, **sem nenhuma análise**. As fotos são convertidas
    para JPEG com no máximo 1920 px de lado.
    """
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

    # ---- Fotografias: validadas, reduzidas e guardadas com os rótulos informados ----
    salvas: list[tuple[str, str]] = []
    for arquivo in fotos:
        ext = Path(arquivo.filename).suffix.lower()
        if ext not in EXTENSOES_IMAGEM:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Formato não suportado: {ext}. Use JPG, JPEG ou PNG.")
        conteudo = await arquivo.read()
        if len(conteudo) > MAX_BYTES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"A imagem {arquivo.filename} excede 8 MB")

        jpeg = armazenamento.preparar_imagem(conteudo, arquivo.filename)
        salvas.append((armazenamento.salvar(db, jpeg, ".jpg", "image/jpeg"), arquivo.filename))

    # ---- Histórico de treino: guardado como veio, sem leitura do conteúdo ----
    csv_arquivo = csv_nome = None
    if csv_treino and csv_treino.filename:
        if not csv_treino.filename.lower().endswith(".csv"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "O histórico de treino precisa ser um arquivo .csv")
        conteudo = await csv_treino.read()
        if len(conteudo) > MAX_BYTES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo CSV maior que 8 MB")
        csv_arquivo = armazenamento.salvar(db, conteudo, ".csv", "text/csv")
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


@router.get("", response_model=list[AvaliacaoResumo], summary="Listar meus envios")
def listar(usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    """Formulários enviados pelo usuário autenticado, do mais recente para o mais antigo."""
    return db.scalars(
        select(Avaliacao).where(Avaliacao.usuario_id == usuario.id).order_by(Avaliacao.id.desc())
    ).all()


@router.get(
    "/{avaliacao_id}",
    response_model=AvaliacaoOut,
    summary="Detalhar um envio",
    responses={404: {"description": "Envio inexistente ou de outro usuário"}},
)
def detalhar(avaliacao_id: int, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    """Todos os dados de um envio. As fotos ficam acessíveis em `/uploads/{arquivo}`."""
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if not avaliacao or avaliacao.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada")
    return avaliacao


@router.delete(
    "/{avaliacao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir um envio",
    responses={404: {"description": "Envio inexistente ou de outro usuário"}},
)
def remover(avaliacao_id: int, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    """Apaga o envio, as fotos e o CSV associados. Não pode ser desfeito."""
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if not avaliacao or avaliacao.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada")
    arquivos = [f.arquivo for f in avaliacao.fotos]
    if avaliacao.csv_arquivo:
        arquivos.append(avaliacao.csv_arquivo)
    armazenamento.remover(db, arquivos)
    db.delete(avaliacao)
    db.commit()
