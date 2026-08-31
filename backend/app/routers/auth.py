from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import criar_token, hash_senha, ler_token, verificar_senha
from app.db import get_db
from app.models import Usuario
from app.schemas import TokenOut, UsuarioCriar, UsuarioLogin, UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])
esquema = HTTPBearer(auto_error=False)


def usuario_atual(
    credencial: HTTPAuthorizationCredentials | None = Depends(esquema),
    db: Session = Depends(get_db),
) -> Usuario:
    if credencial is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Não autenticado")
    email = ler_token(credencial.credentials)
    if not email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada ou token inválido")
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    if not usuario:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário não encontrado")
    return usuario


@router.post("/cadastro", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: UsuarioCriar, db: Session = Depends(get_db)):
    email = dados.email.lower()
    if db.scalar(select(Usuario).where(Usuario.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com este e-mail")

    usuario = Usuario(nome=dados.nome.strip(), email=email, senha_hash=hash_senha(dados.senha))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return TokenOut(access_token=criar_token(usuario.email), usuario=UsuarioOut.model_validate(usuario))


@router.post("/login", response_model=TokenOut)
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email.lower()))
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha incorretos")
    return TokenOut(access_token=criar_token(usuario.email), usuario=UsuarioOut.model_validate(usuario))


@router.get("/eu", response_model=UsuarioOut)
def eu(usuario: Usuario = Depends(usuario_atual)):
    return usuario
