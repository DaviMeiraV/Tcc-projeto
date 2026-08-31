from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db import Base, engine
from app.routers import auth, avaliacoes

@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    # Para um MVP, criar as tabelas na subida basta; em produção, use Alembic.
    import app.models  # noqa: F401  garante o registro dos modelos no metadata

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=ciclo_de_vida,
    title="Sistema de Predição de Risco de Lesão",
    description=(
        "API do TCC: coleta questionário de prontidão, histórico de treino (ACWR) "
        "e fotografias da prática esportiva para estimar o risco de lesão."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(avaliacoes.router)

uploads = Path(settings.UPLOAD_DIR).resolve()
uploads.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads)), name="uploads")


@app.get("/saude", tags=["infra"])
def saude() -> dict:
    return {"status": "ok"}
