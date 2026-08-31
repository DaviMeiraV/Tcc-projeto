"""Hash de senha (bcrypt) e emissão/leitura de JWT.

Usa bcrypt e PyJWT diretamente: passlib depende do módulo `crypt`, removido
da biblioteca padrão no Python 3.13.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

# bcrypt trunca a senha em 72 bytes; o limite é validado no schema de entrada.
LIMITE_SENHA = 72


def hash_senha(senha: str) -> str:
    bruto = senha.encode("utf-8")[:LIMITE_SENHA]
    return bcrypt.hashpw(bruto, bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8")[:LIMITE_SENHA], hashed.encode("utf-8"))
    except ValueError:
        return False


def criar_token(subject: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": subject, "exp": expira}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def ler_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
    return payload.get("sub")
