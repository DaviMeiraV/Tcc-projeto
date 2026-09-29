"""Atualizações explícitas e aditivas para bancos de versões anteriores."""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db import Base

logger = logging.getLogger(__name__)


def inicializar_banco(engine: Engine) -> None:
    import app.models  # noqa: F401 registra as tabelas no metadata

    with engine.begin() as conexao:
        # Evita que duas instâncias alterem o mesmo esquema durante a subida.
        if conexao.dialect.name == "postgresql":
            conexao.execute(text("SELECT pg_advisory_xact_lock(20260929, 1)"))
        Base.metadata.create_all(bind=conexao)

        # create_all cria tabelas novas, mas não adiciona colunas às existentes.
        # Estas colunas são opcionais: registros antigos continuam válidos.
        colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("avaliacoes")}
        for nome in ("csv_arquivo", "csv_nome_original"):
            if nome not in colunas:
                conexao.execute(text(f"ALTER TABLE avaliacoes ADD COLUMN {nome} VARCHAR(255)"))
                logger.info("Banco atualizado: adicionada avaliacoes.%s", nome)
