from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import engine, get_db
from app.migracoes import inicializar_banco
from app.models import Arquivo
from app.routers import auth, avaliacoes


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    inicializar_banco(engine)
    yield


DESCRICAO = """
API do TCC **Sistema de Predição de Risco de Lesão** — coleta de dados e cálculo de indicadores experimentais.

Recebe e armazena, para cada participante:

* dados pessoais e prática esportiva;
* questionário de prontidão (escalas de 0 a 10);
* até 3 fotografias da prática esportiva;
* arquivo CSV com o histórico de treino.

As fotografias são enviadas à API postural externa, e o PNG tratado e o score
postural (0 a 1) ficam associados a cada foto. O CSV alimenta o cálculo de ACWR
(média diária de carga de 7 dias / média diária de 28 dias). O questionário gera o
ICSA versão 2, média de seis componentes normalizados com pesos iguais (1/6).
O IMCA combina ACWR normalizado, ICSA e score postural invertido com peso 1/3 cada,
quando os três componentes atendem às regras de disponibilidade.

Os cálculos ficam em `detalhes.acwr`, `detalhes.score_subjetivo` e `detalhes.score_final`.
Dados ausentes ou inválidos não são substituídos por zero. Histórico marcado como
incompleto ou várias fotos sem protocolo de seleção deixam o IMCA indisponível.
Esses índices são experimentais, não representam probabilidade clínica de lesão
e não recebem classificação clínica de risco. A API postural é hospedada separadamente.

## Como testar por aqui

1. Em **auth**, chame `POST /api/auth/cadastro` (ou `/login`) e copie o `access_token`.
2. Clique em **Authorize** (cadeado, no topo) e cole o token.
3. As rotas de **avaliacoes** passam a funcionar com o seu usuário.
"""

TAGS = [
    {"name": "auth", "description": "Cadastro, login e dados do usuário autenticado (JWT)."},
    {"name": "avaliacoes", "description": "Envio e consulta dos formulários de coleta. Exige token."},
    {"name": "infra", "description": "Verificação de saúde do serviço."},
]

app = FastAPI(
    lifespan=ciclo_de_vida,
    title="Predição de Risco de Lesão — API",
    description=DESCRICAO,
    version="1.0.0",
    openapi_tags=TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={"persistAuthorization": True, "defaultModelsExpandDepth": 0},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(avaliacoes.router, prefix="/api")


@app.get("/api/saude", tags=["infra"], summary="Status do serviço")
def saude() -> dict:
    """Usado pelo Render para saber se o container está de pé."""
    return {"status": "ok"}


@app.get(
    "/uploads/{nome}",
    tags=["avaliacoes"],
    summary="Baixar foto ou CSV enviado",
    response_class=Response,
    responses={
        200: {"content": {"image/jpeg": {}, "image/png": {}, "text/csv": {}}, "description": "Conteúdo do arquivo"},
        404: {"description": "Arquivo inexistente"},
    },
)
def baixar_arquivo(nome: str, db: Session = Depends(get_db)):
    """Devolve um arquivo guardado no banco. O nome vem de `fotos.arquivo` ou `csv_arquivo`.

    Não exige token para que a foto possa ser exibida numa tag `<img>`; os nomes são
    aleatórios e impossíveis de adivinhar.
    """
    arquivo = db.get(Arquivo, nome)
    if arquivo is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return Response(
        content=arquivo.conteudo,
        media_type=arquivo.tipo,
        # O conteúdo de um nome nunca muda, então o navegador pode guardar em cache.
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )


# ---------------------------------------------------------------------------
# Frontend (React compilado). Só é ativado quando existe o build — no Docker e
# no deploy. Em desenvolvimento o Vite serve o frontend na porta 5173.
# ---------------------------------------------------------------------------
estatico = settings.static_path
if (estatico / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=str(estatico / "assets")), name="assets")

    @app.get("/{caminho:path}", include_in_schema=False)
    def spa(caminho: str):
        # Rotas de API inexistentes devem responder 404 em JSON, não a página do React.
        if caminho.startswith("api/"):
            raise HTTPException(status_code=404, detail="Rota não encontrada")
        arquivo = (estatico / caminho).resolve()
        if caminho and arquivo.is_file() and arquivo.is_relative_to(estatico):
            return FileResponse(arquivo)
        # Qualquer outra rota (/login, /formulario...) é resolvida pelo React Router.
        return FileResponse(estatico / "index.html")
