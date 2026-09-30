from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# ---------- auth ----------
class UsuarioCriar(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"nome": "Participante Teste", "email": "participante@exemplo.com", "senha": "123456"}]
    })

    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=72)


class UsuarioLogin(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"email": "participante@exemplo.com", "senha": "123456"}]
    })

    email: EmailStr
    senha: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: EmailStr


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


# ---------- avaliação ----------
class FotoMeta(BaseModel):
    modalidade: Literal["corrida", "ciclismo"]
    fase: str
    joelho_frente: Literal["esquerdo", "direito"] | None = None

    @model_validator(mode="after")
    def validar_movimento(self):
        fases = {
            "corrida": {"contato_inicial", "apoio_medio"},
            "ciclismo": {"fase_superior", "extensao_maxima"},
        }
        if self.fase not in fases[self.modalidade]:
            raise ValueError("Fase inválida para a modalidade informada")
        if self.modalidade == "corrida" and not self.joelho_frente:
            raise ValueError("Informe o joelho à frente para corrida")
        if self.modalidade == "ciclismo":
            self.joelho_frente = None
        return self


class AvaliacaoCriar(BaseModel):
    idade: int = Field(ge=10, le=90)
    sexo: Literal["masculino", "feminino", "outro"]
    esporte: Literal["corrida", "ciclismo"]
    tempo_pratica: str
    peso_kg: float = Field(gt=20, le=250)
    altura_cm: float = Field(gt=100, le=250)

    rpe: int = Field(ge=0, le=10)
    dor: int = Field(ge=0, le=10)
    fadiga: int = Field(ge=0, le=10)
    sono: int = Field(ge=0, le=10)
    recuperacao: int = Field(ge=0, le=10)
    lesao_previa: bool
    dor_limita: bool
    lesao_descricao: str | None = None
    lesao_quando: str | None = None

    consentimento_foto: bool = False
    fotos_meta: list[FotoMeta] = []


class FotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    arquivo: str
    nome_original: str
    modalidade: str
    fase: str
    joelho_frente: str | None
    analise: dict | None = None


class AvaliacaoOut(BaseModel):
    """Dados coletados e análise postural por foto, sem score de risco combinado."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    criado_em: datetime
    idade: int
    sexo: str
    esporte: str
    peso_kg: float
    altura_cm: float
    rpe: int
    dor: int
    fadiga: int
    sono: int
    recuperacao: int
    lesao_previa: bool
    dor_limita: bool
    csv_nome_original: str | None = None
    acwr: float | None = None
    carga_aguda: float | None = None
    carga_cronica: float | None = None
    detalhes: dict | None = None
    fotos: list[FotoOut] = []


class AvaliacaoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    criado_em: datetime
    esporte: str
    csv_nome_original: str | None = None
