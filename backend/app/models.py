from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    avaliacoes: Mapped[list["Avaliacao"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan", order_by="Avaliacao.id.desc()"
    )


class Avaliacao(Base):
    """Uma submissão completa do formulário de 3 etapas."""

    __tablename__ = "avaliacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    # Etapa 1 — participante
    idade: Mapped[int] = mapped_column(Integer)
    sexo: Mapped[str] = mapped_column(String(20))
    esporte: Mapped[str] = mapped_column(String(20))          # corrida | ciclismo
    tempo_pratica: Mapped[str] = mapped_column(String(40))
    peso_kg: Mapped[float] = mapped_column(Float)
    altura_cm: Mapped[float] = mapped_column(Float)

    # Etapa 1 — questionário (0-10)
    rpe: Mapped[int] = mapped_column(Integer)
    dor: Mapped[int] = mapped_column(Integer)
    fadiga: Mapped[int] = mapped_column(Integer)
    sono: Mapped[int] = mapped_column(Integer)
    recuperacao: Mapped[int] = mapped_column(Integer)
    lesao_previa: Mapped[bool] = mapped_column(Boolean, default=False)
    dor_limita: Mapped[bool] = mapped_column(Boolean, default=False)
    lesao_descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    lesao_quando: Mapped[str | None] = mapped_column(String(40), nullable=True)

    consentimento_foto: Mapped[bool] = mapped_column(Boolean, default=False)

    # Etapa 2 — arquivo de historico de treino (armazenado, ainda nao analisado)
    csv_arquivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    csv_nome_original: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Resultado — reservado para a logica de score, ainda a definir pelo autor do TCC.
    # Permanece nulo enquanto o score nao for implementado.
    acwr: Mapped[float | None] = mapped_column(Float, nullable=True)
    carga_aguda: Mapped[float | None] = mapped_column(Float, nullable=True)
    carga_cronica: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_risco: Mapped[float | None] = mapped_column(Float, nullable=True)
    classificacao: Mapped[str | None] = mapped_column(String(20), nullable=True)
    detalhes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    usuario: Mapped[Usuario] = relationship(back_populates="avaliacoes")
    fotos: Mapped[list["Foto"]] = relationship(back_populates="avaliacao", cascade="all, delete-orphan")
    sessoes: Mapped[list["SessaoTreino"]] = relationship(
        back_populates="avaliacao", cascade="all, delete-orphan", order_by="SessaoTreino.data"
    )


class Foto(Base):
    __tablename__ = "fotos"

    id: Mapped[int] = mapped_column(primary_key=True)
    avaliacao_id: Mapped[int] = mapped_column(ForeignKey("avaliacoes.id", ondelete="CASCADE"), index=True)
    arquivo: Mapped[str] = mapped_column(String(255))
    nome_original: Mapped[str] = mapped_column(String(255))
    modalidade: Mapped[str] = mapped_column(String(20))
    fase: Mapped[str] = mapped_column(String(40))
    joelho_frente: Mapped[str | None] = mapped_column(String(20), nullable=True)
    analise: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    avaliacao: Mapped[Avaliacao] = relationship(back_populates="fotos")


class SessaoTreino(Base):
    """Linha do CSV de histórico de treino usada no cálculo do ACWR."""

    __tablename__ = "sessoes_treino"

    id: Mapped[int] = mapped_column(primary_key=True)
    avaliacao_id: Mapped[int] = mapped_column(ForeignKey("avaliacoes.id", ondelete="CASCADE"), index=True)
    data: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duracao_min: Mapped[float] = mapped_column(Float)
    distancia_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    rpe: Mapped[float | None] = mapped_column(Float, nullable=True)
    carga: Mapped[float] = mapped_column(Float)

    avaliacao: Mapped[Avaliacao] = relationship(back_populates="sessoes")


class Arquivo(Base):
    """Conteúdo das fotos e CSVs enviados, guardado no próprio banco.

    O disco do Render gratuito é apagado a cada deploy ou quando o serviço dorme;
    no banco (Neon) os arquivos ficam permanentes. `fotos.arquivo` e
    `avaliacoes.csv_arquivo` apontam para `arquivos.nome`.
    """

    __tablename__ = "arquivos"

    nome: Mapped[str] = mapped_column(String(255), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(100))
    tamanho_bytes: Mapped[int] = mapped_column(Integer)
    conteudo: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
