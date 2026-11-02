"""Testes de autorização e conteúdo do painel administrativo."""

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.models import Arquivo, Avaliacao, Foto, Usuario
from app.main import baixar_arquivo
from app.core.security import hash_senha
from app.routers.auth import router as auth_router
from app.routers.auth import usuario_atual
from app.routers.avaliacoes import router


@compiles(JSONB, "sqlite")
def jsonb_em_sqlite(tipo, compilador, **kw):
    return "JSON"


class PainelAdminTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            participante = Usuario(
                id=1,
                nome="Participante",
                email="participante@example.com",
                senha_hash="hash",
            )
            db.add(participante)
            avaliacao = Avaliacao(
                usuario=participante,
                idade=24,
                sexo="masculino",
                esporte="corrida",
                tempo_pratica="1_3_anos",
                peso_kg=72,
                altura_cm=178,
                rpe=6,
                dor=2,
                fadiga=4,
                sono=7,
                recuperacao=6,
                lesao_previa=False,
                dor_limita=False,
                detalhes={
                    "acwr": {"status": "concluida", "acwr": 1.5},
                    "score_subjetivo": {"status": "concluida", "score": 0.4},
                    "score_final": {
                        "status": "concluida",
                        "score_acwr_normalizado": 0.2857,
                        "score_final": 0.5,
                    },
                },
            )
            avaliacao.fotos.append(Foto(
                arquivo="original.jpg",
                nome_original="foto.jpg",
                modalidade="corrida",
                fase="contato_inicial",
                joelho_frente="direito",
                analise={
                    "status": "concluida",
                    "score": 0.8,
                    "imagem_tratada": {"arquivo": "tratada.png"},
                },
            ))
            db.add(avaliacao)
            db.commit()

        def banco():
            with Session(self.engine) as db:
                yield db

        self.usuario = Usuario(
            id=1,
            nome="Participante",
            email="participante@example.com",
            senha_hash="hash",
        )
        app = FastAPI()
        app.include_router(router, prefix="/api")
        app.include_router(auth_router, prefix="/api")
        app.add_api_route("/uploads/{nome}", baixar_arquivo)
        app.dependency_overrides[get_db] = banco
        app.dependency_overrides[usuario_atual] = lambda: self.usuario
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_usuario_comum_nao_acessa_resultados_de_todos(self):
        resposta = self.client.get("/api/avaliacoes/admin")

        self.assertEqual(resposta.status_code, 403)

    def test_admin_consulta_total_scores_e_foto_tratada_sem_dados_extras(self):
        self.usuario.email = "ANDREVOLIMAJP@GMAIL.COM"

        resposta = self.client.get("/api/avaliacoes/admin")

        self.assertEqual(resposta.status_code, 200)
        dados = resposta.json()
        self.assertEqual(dados["total_avaliacoes"], 1)
        avaliacao = dados["avaliacoes"][0]
        self.assertEqual(avaliacao["usuario_email"], "participante@example.com")
        self.assertEqual(avaliacao["score_acwr"], 1.5)
        self.assertEqual(avaliacao["score_acwr_normalizado"], 0.2857)
        self.assertEqual(avaliacao["score_subjetivo"], 0.2167)
        self.assertEqual(avaliacao["score_final"], 0.2341)
        self.assertEqual(avaliacao["fotos"][0]["score_postural"], 0.8)
        self.assertEqual(avaliacao["fotos"][0]["imagem_tratada"], "tratada.png")
        self.assertNotIn("idade", avaliacao)

    def test_sem_login_nao_acessa_painel(self):
        self.client.app.dependency_overrides.pop(usuario_atual)
        self.assertEqual(self.client.get("/api/avaliacoes/admin").status_code, 401)

    def test_login_real_do_admin_acessa_resultados_de_outro_usuario(self):
        with Session(self.engine) as db:
            db.add(Usuario(nome="Admin", email="andrevolimajp@gmail.com", senha_hash=hash_senha("senha-teste")))
            db.commit()
        self.client.app.dependency_overrides.pop(usuario_atual)
        login = self.client.post("/api/auth/login", json={"email": "andrevolimajp@gmail.com", "senha": "senha-teste"})
        self.assertEqual(login.status_code, 200)
        resposta = self.client.get("/api/avaliacoes/admin", headers={"Authorization": "Bearer " + login.json()["access_token"]})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["total_avaliacoes"], 1)
        self.assertEqual(resposta.json()["avaliacoes"][0]["usuario_email"], "participante@example.com")

    def test_foto_tratada_pode_ser_baixada_pelo_link_retornado(self):
        self.usuario.email = "andrevolimajp@gmail.com"
        with Session(self.engine) as db:
            db.add(Arquivo(nome="tratada.png", conteudo=b"png-teste", tipo="image/png", tamanho_bytes=9))
            db.commit()
        foto = self.client.get("/api/avaliacoes/admin").json()["avaliacoes"][0]["fotos"][0]
        resposta = self.client.get("/uploads/" + foto["imagem_tratada"])
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.content, b"png-teste")
        self.assertEqual(resposta.headers["content-type"], "image/png")

    def test_resultados_atualizados_persistem_sem_duplicar_historico(self):
        self.usuario.email = "andrevolimajp@gmail.com"
        self.client.get("/api/avaliacoes/admin")
        self.client.get("/api/avaliacoes/admin")
        with Session(self.engine) as db:
            detalhes = db.get(Avaliacao, 1).detalhes
            self.assertEqual(detalhes["score_subjetivo"]["versao"], 2)
            self.assertEqual(len(detalhes["historico_scores"]), 1)

    def test_falha_postural_nao_vira_zero_e_exibe_motivo(self):
        self.usuario.email = "andrevolimajp@gmail.com"
        with Session(self.engine) as db:
            db.get(Foto, 1).analise = {"status": "erro"}
            db.commit()
        avaliacao = self.client.get("/api/avaliacoes/admin").json()["avaliacoes"][0]
        self.assertIsNone(avaliacao["score_final"])
        self.assertIsNone(avaliacao["fotos"][0]["score_postural"])
        self.assertTrue(avaliacao["motivos_score_final"])


if __name__ == "__main__":
    unittest.main()
