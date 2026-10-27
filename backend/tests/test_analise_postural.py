"""Testes do fluxo HTTP com banco isolado e API postural simulada."""

import base64
import io
import json
import unittest
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import baixar_arquivo
from app.models import Arquivo, Avaliacao, Foto, Usuario
from app.routers.auth import usuario_atual
from app.routers.avaliacoes import router
from app.schemas import FotoMeta
from app.services.analise_postural import ErroAnalise, analisar, montar_payload


@compiles(JSONB, "sqlite")
def jsonb_em_sqlite(tipo, compilador, **kw):
    return "JSON"


def imagem_png():
    saida = io.BytesIO()
    Image.new("RGB", (20, 30), "white").save(saida, format="PNG")
    return saida.getvalue()


PNG = imagem_png()


def resultado():
    return {
        "modalidade": "corrida", "fase_joelho": 1, "joelho_frente": "D",
        "pose_detectada": True, "score": 0.95, "resumo": "Análise concluída",
        "angulos": [], "pontos": {},
        "imagem_tratada": {
            "media_type": "image/png", "base64": base64.b64encode(PNG).decode(),
            "largura": 20, "altura": 30, "arquivo": "saida/analise_externa.png",
        },
    }


META = {"modalidade": "corrida", "fase": "contato_inicial", "joelho_frente": "direito"}
PAYLOAD = {
    "idade": 24, "sexo": "masculino", "esporte": "corrida", "tempo_pratica": "1_3_anos",
    "peso_kg": 72, "altura_cm": 178, "rpe": 6, "dor": 2, "fadiga": 4,
    "sono": 7, "recuperacao": 6, "lesao_previa": False, "dor_limita": False,
    "consentimento_foto": True,
}


class ContratoTest(unittest.TestCase):
    def test_conversao_de_todas_as_fases_e_lados(self):
        for modalidade, fases in (("corrida", ["contato_inicial", "apoio_medio"]),
                                   ("ciclismo", ["fase_superior", "extensao_maxima"])):
            for numero, fase in enumerate(fases, 1):
                for joelho, lado in (("esquerdo", "E"), ("direito", "D")):
                    with self.subTest(modalidade=modalidade, fase=fase, joelho=joelho):
                        meta = FotoMeta(modalidade=modalidade, fase=fase, joelho_frente=joelho)
                        dados = montar_payload(PNG, meta)
                        self.assertEqual(dados["modalidade"], "bike" if modalidade == "ciclismo" else "corrida")
                        self.assertEqual(dados["fase_joelho"], numero)
                        self.assertEqual(base64.b64decode(dados["imagem_base64"]), PNG)
                        if modalidade == "corrida":
                            self.assertEqual(dados["joelho_frente"], lado)
                        else:
                            self.assertNotIn("joelho_frente", dados)

    def test_fase_incompativel_e_joelho_ausente(self):
        for meta in ({**META, "fase": "fase_superior"}, {**META, "joelho_frente": None}):
            with self.assertRaises(ValidationError):
                FotoMeta(**meta)

    def test_resposta_invalida(self):
        respostas = [{}, [], {**resultado(), "score": 95}, {**resultado(), "pose_detectada": False},
                     {**resultado(), "imagem_tratada": {"media_type": "image/png", "base64": "inválido"}},
                     {**resultado(), "imagem_tratada": {"media_type": "image/png", "base64": "YWJj"}}]
        for corpo in respostas:
            with self.subTest(corpo=corpo):
                with httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, json=corpo))) as client:
                    with self.assertRaises(ErroAnalise):
                        analisar(client, PNG, FotoMeta(**META))

    def test_erros_http_e_rede(self):
        for status, detalhe in ((400, "Base64 inválido"), (413, "Imagem grande"),
                                 (422, "Nenhuma pose detectada"), (422, [{"msg": "Campo ausente"}]),
                                 (500, "Falha ao salvar PNG")):
            with self.subTest(status=status, detalhe=detalhe):
                with httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(status, json={"detail": detalhe}))) as client:
                    with self.assertRaisesRegex(ErroAnalise, str(status)):
                        analisar(client, PNG, FotoMeta(**META))
        for erro in (httpx.ReadTimeout("demora"), httpx.ConnectError("indisponível")):
            def falhar(req):
                raise erro
            with httpx.Client(transport=httpx.MockTransport(falhar)) as client:
                with self.assertRaises(ErroAnalise):
                    analisar(client, PNG, FotoMeta(**META))


class FluxoTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Usuario(id=1, nome="Teste", email="teste@example.com", senha_hash="teste"))
            db.commit()
        def banco():
            with Session(self.engine) as db:
                yield db
        app = FastAPI()
        app.include_router(router, prefix="/api")
        app.get("/uploads/{nome}")(baixar_arquivo)
        app.dependency_overrides[get_db] = banco
        app.dependency_overrides[usuario_atual] = lambda: Usuario(id=1)
        self.app = app
        self.client = TestClient(app)
        self.requisicoes = []
        self.responder = lambda req: httpx.Response(200, json=resultado())
        classe_client = httpx.Client
        def receber(req):
            self.requisicoes.append(json.loads(req.content))
            self.assertEqual(req.url.path, "/analises")
            return self.responder(req)
        self.mock = patch("app.services.analise_postural.httpx.Client",
                          side_effect=lambda **kw: classe_client(transport=httpx.MockTransport(receber), **kw))
        self.mock.start()

    def tearDown(self):
        self.mock.stop()
        self.client.close()
        self.engine.dispose()

    def enviar(self, metas=None, **campos):
        metas = [META] if metas is None else metas
        return self.client.post("/api/avaliacoes", data={"payload": json.dumps({**PAYLOAD, "fotos_meta": metas, **campos})},
                                files=[("fotos", (f"foto{i}.png", PNG, "image/png")) for i in range(len(metas))])

    def test_envio_persiste_imagem_tratada_e_exclui_arquivos(self):
        resposta = self.enviar()
        self.assertEqual(resposta.status_code, 201, resposta.text)
        envio = resposta.json()
        foto = envio["fotos"][0]
        analise = foto["analise"]
        self.assertEqual(analise["status"], "concluida")
        self.assertEqual(analise["score"], 0.95)
        self.assertNotIn("base64", analise["imagem_tratada"])
        nome = analise["imagem_tratada"]["arquivo"]
        self.assertNotIn("saida/", nome)
        download = self.client.get(f"/uploads/{nome}")
        self.assertEqual(download.content, PNG)
        self.assertEqual(download.headers["content-type"], "image/png")
        with Session(self.engine) as db:
            original = db.get(Arquivo, foto["arquivo"])
            self.assertEqual(base64.b64decode(self.requisicoes[0]["imagem_base64"]), original.conteudo)
        self.assertEqual(self.client.get(f'/api/avaliacoes/{envio["id"]}').json()["fotos"], envio["fotos"])
        self.assertEqual(self.client.delete(f'/api/avaliacoes/{envio["id"]}').status_code, 204)
        self.assertEqual(self.client.get(f"/uploads/{nome}").status_code, 404)
        with Session(self.engine) as db:
            self.assertEqual(db.scalars(select(Arquivo)).all(), [])
            self.assertEqual(db.scalars(select(Foto)).all(), [])

    def test_falha_parcial_e_nova_tentativa_sem_duplicar_envio(self):
        self.responder = lambda req: httpx.Response(422, json={"detail": "Nenhuma pose detectada"}) if len(self.requisicoes) == 1 else httpx.Response(200, json=resultado())
        resposta = self.enviar([META, {"modalidade": "ciclismo", "fase": "extensao_maxima"}])
        self.assertEqual(resposta.status_code, 201, resposta.text)
        envio = resposta.json()
        self.assertEqual([f["analise"]["status"] for f in envio["fotos"]], ["erro", "concluida"])
        self.assertEqual([f['score'] for f in envio['detalhes']['score_final']['scores_posturais']], [None, 0.95])
        self.assertEqual(self.requisicoes[1]["modalidade"], "bike")
        repetida = self.client.post(f'/api/avaliacoes/{envio["id"]}/analises')
        self.assertEqual(repetida.status_code, 200, repetida.text)
        self.assertEqual([f["analise"]["status"] for f in repetida.json()["fotos"]], ["concluida", "concluida"])
        self.assertEqual([f['score'] for f in repetida.json()['detalhes']['score_final']['scores_posturais']], [0.95, 0.95])
        self.assertEqual(len(self.requisicoes), 3)
        self.client.post(f'/api/avaliacoes/{envio["id"]}/analises')
        self.assertEqual(len(self.requisicoes), 3)
        with Session(self.engine) as db:
            self.assertEqual(len(db.scalars(select(Avaliacao)).all()), 1)
            self.assertEqual(len(db.scalars(select(Arquivo)).all()), 4)

    def test_formulario_ja_esta_salvo_ao_chamar_api(self):
        def responder(req):
            with Session(self.engine) as db:
                self.assertEqual(len(db.scalars(select(Avaliacao)).all()), 1)
                self.assertEqual(len(db.scalars(select(Foto)).all()), 1)
                self.assertEqual(len(db.scalars(select(Arquivo)).all()), 1)
            raise httpx.ConnectError("offline")
        self.responder = responder
        resposta = self.enviar()
        self.assertEqual(resposta.status_code, 201, resposta.text)
        self.assertEqual(resposta.json()["fotos"][0]["analise"]["status"], "erro")

    def test_sem_fotos_nao_chama_api(self):
        resposta = self.enviar([], consentimento_foto=False)
        self.assertEqual(resposta.status_code, 201, resposta.text)
        self.assertEqual(self.requisicoes, [])

    def test_score_subjetivo_e_salvo_sem_fotos_ou_csv(self):
        resposta = self.enviar([], dor=0, fadiga=0, sono=5, recuperacao=5,
                              dor_limita=True, lesao_previa=True)
        self.assertEqual(resposta.status_code, 201, resposta.text)
        envio = resposta.json()
        resultado = envio['detalhes']['score_subjetivo']
        self.assertEqual(resultado['score'], 0.45)
        self.assertEqual(resultado['respostas']['dor'], 0)
        self.assertTrue(resultado['respostas']['dor_limita'])
        with Session(self.engine) as db:
            avaliacao = db.get(Avaliacao, envio['id'])
            self.assertEqual(avaliacao.detalhes['score_subjetivo'], resultado)
            self.assertIsNone(avaliacao.score_risco)
            self.assertIsNone(avaliacao.classificacao)

    def test_score_subjetivo_em_envio_antigo_preserva_acwr_e_respostas(self):
        envio = self.enviar([]).json()
        acwr = {'status': 'concluida', 'acwr': 1.2}
        with Session(self.engine) as db:
            avaliacao = db.get(Avaliacao, envio['id'])
            avaliacao.detalhes = {'acwr': acwr}
            db.commit()
        consulta = self.client.get(f'/api/avaliacoes/{envio["id"]}')
        self.assertEqual(consulta.status_code, 200, consulta.text)
        dados = consulta.json()
        self.assertEqual(dados['detalhes']['acwr'], acwr)
        self.assertEqual(dados['detalhes']['score_subjetivo']['score'], 0.215)
        self.assertEqual(dados['detalhes']['score_final']['score_acwr'], 1.2)
        self.assertEqual(dados['detalhes']['score_final']['score_subjetivo'], 0.215)
        self.assertEqual(dados['dor'], envio['dor'])
        with patch('app.services.score_subjetivo.calcular_icsa') as calcular:
            self.assertEqual(self.client.get(f'/api/avaliacoes/{envio["id"]}').status_code, 200)
            calcular.assert_not_called()

    def test_csv_calcula_persiste_e_expoe_acwr_com_logs(self):
        dados = b'data,duracao,rpe\n2026-09-02,60,5\n2026-09-29,60,5'
        with self.assertLogs('uvicorn.error', level='INFO') as logs:
            resposta = self.client.post('/api/avaliacoes',
                data={'payload': json.dumps({**PAYLOAD, 'fotos_meta': []})},
                files={'csv_treino': ('treinos.csv', dados, 'text/csv')})
        self.assertEqual(resposta.status_code, 201, resposta.text)
        envio = resposta.json()
        self.assertEqual(envio['acwr'], 2)
        self.assertEqual(envio['detalhes']['score_final']['score_acwr'], 2)
        self.assertEqual(envio['detalhes']['score_final']['score_subjetivo'], envio['detalhes']['score_subjetivo']['score'])
        self.assertEqual(envio['detalhes']['acwr']['mes']['atividades'], 2)
        self.assertIn('atleta_id=1', logs.output[0])
        self.assertIn('score=2.0', logs.output[0])
        self.assertEqual(self.client.get(f'/api/avaliacoes/{envio["id"]}').json()['acwr'], 2)
        with Session(self.engine) as db:
            avaliacao = db.get(Avaliacao, envio['id'])
            self.assertEqual(db.get(Arquivo, avaliacao.csv_arquivo).conteudo, dados)
            avaliacao.detalhes = None
            avaliacao.acwr = None
            db.commit()
        self.assertEqual(self.client.get(f'/api/avaliacoes/{envio["id"]}').json()['acwr'], 2)

    def test_csv_invalido_preserva_formulario_e_analise_da_foto(self):
        resposta = self.client.post('/api/avaliacoes',
            data={'payload': json.dumps({**PAYLOAD, 'fotos_meta': [META]})},
            files=[('csv_treino', ('invalido.csv', b'invalido', 'text/csv')),
                   ('fotos', ('foto.png', PNG, 'image/png'))])
        self.assertEqual(resposta.status_code, 201, resposta.text)
        self.assertIsNone(resposta.json()['acwr'])
        self.assertEqual(resposta.json()['detalhes']['acwr']['status'], 'erro')
        self.assertEqual(resposta.json()['detalhes']['acwr']['versao'], 3)
        self.assertEqual(resposta.json()['fotos'][0]['analise']['status'], 'concluida')
        with patch('app.routers.avaliacoes.analisar_planilha') as recalcular:
            consulta = self.client.get(f'/api/avaliacoes/{resposta.json()["id"]}')
            self.assertEqual(consulta.status_code, 200)
            recalcular.assert_not_called()

    def test_csv_sem_rpe_usa_formulario_e_atualiza_resultado_antigo(self):
        resposta = self.client.post('/api/avaliacoes',
            data={'payload': json.dumps({**PAYLOAD, 'rpe': 4, 'fotos_meta': []})},
            files={'csv_treino': ('treinos.csv', b'data,duracao\n2026-09-02,60\n2026-09-29,60', 'text/csv')})
        self.assertEqual(resposta.status_code, 201, resposta.text)
        envio = resposta.json()
        self.assertEqual(envio['detalhes']['acwr']['mes']['carga'], 480)
        self.assertEqual(envio['detalhes']['acwr']['rpe_formulario'], 4)
        with Session(self.engine) as db:
            avaliacao = db.get(Avaliacao, envio['id'])
            avaliacao.detalhes = {'acwr': {'metodo': 'duracao', 'acwr': 2}}
            db.commit()
        atualizado = self.client.get(f'/api/avaliacoes/{envio["id"]}').json()['detalhes']['acwr']
        self.assertEqual(atualizado['mes']['carga'], 480)
        self.assertEqual(atualizado['atividades_com_rpe_formulario'], 2)
        self.assertEqual(atualizado['versao'], 3)
        self.assertTrue(atualizado['carga_estimada'])
        self.assertEqual(atualizado['sessoes'][0]['origem_rpe'], 'formulario')

    def test_envio_antigo_com_metadados_invalidos_preserva_dados(self):
        envio = self.enviar().json()
        with Session(self.engine) as db:
            foto = db.get(Foto, envio["fotos"][0]["id"])
            foto.fase = "fase_antiga_invalida"
            foto.analise = None
            db.commit()
        resposta = self.client.post(f'/api/avaliacoes/{envio["id"]}/analises')
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(resposta.json()["fotos"][0]["analise"]["status"], "erro")
        self.assertEqual(len(self.requisicoes), 1)

    def test_metadados_invalidos_e_falta_de_consentimento_nao_persistem(self):
        self.assertEqual(self.enviar([{**META, "fase": "fase_superior"}]).status_code, 422)
        self.assertEqual(self.enviar(consentimento_foto=False).status_code, 400)
        with Session(self.engine) as db:
            self.assertEqual(db.scalars(select(Avaliacao)).all(), [])
        self.assertEqual(self.requisicoes, [])

    def test_outro_usuario_nao_consulta_reprocessa_ou_exclui_envio(self):
        envio = self.enviar().json()
        self.app.dependency_overrides[usuario_atual] = lambda: Usuario(id=2)
        url = f'/api/avaliacoes/{envio["id"]}'
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url + "/analises").status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(len(self.requisicoes), 1)


if __name__ == "__main__":
    unittest.main()
