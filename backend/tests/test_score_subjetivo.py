import unittest
from copy import deepcopy
from types import SimpleNamespace

from app.services.score_subjetivo import atualizar_score_subjetivo, calcular_icsa


FAVORAVEL = {
    "dor": 0, "fadiga": 0, "sono": 10, "recuperacao": 10,
    "dor_limita": False, "lesao_previa": False,
}


class ScoreSubjetivoTest(unittest.TestCase):
    def test_exemplo_do_documento(self):
        resultado = calcular_icsa({
            **FAVORAVEL, "dor": 6, "fadiga": 4, "sono": 7, "recuperacao": 5,
            "dor_limita": True,
        })
        self.assertEqual(resultado["score"], 0.4667)
        self.assertEqual(resultado["componentes"]["sono"], 0.3)
        self.assertEqual(resultado["componentes"]["recuperacao"], 0.5)
        self.assertEqual(resultado["versao"], 2)
        self.assertAlmostEqual(sum(resultado["pesos"].values()), 1)

    def test_extremos_da_escala(self):
        self.assertEqual(calcular_icsa(FAVORAVEL)["score"], 0)
        desfavoravel = {
            "dor": 10, "fadiga": 10, "sono": 0, "recuperacao": 0,
            "dor_limita": True, "lesao_previa": True,
        }
        self.assertEqual(calcular_icsa(desfavoravel)["score"], 1)

    def test_peso_e_sentido_de_cada_indicador(self):
        casos = [
            ("dor", 10), ("fadiga", 10), ("sono", 0), ("recuperacao", 0),
            ("dor_limita", True), ("lesao_previa", True),
        ]
        for campo, valor in casos:
            with self.subTest(campo=campo):
                resultado = calcular_icsa({**FAVORAVEL, campo: valor})
                self.assertEqual(resultado["score"], 0.1667)
                self.assertEqual(resultado["contribuicoes"][campo], 0.1667)
                self.assertEqual(resultado["pesos"][campo], 1 / 6)

    def test_nao_soma_contribuicoes_ja_arredondadas(self):
        resultado = calcular_icsa({**FAVORAVEL, "dor": 10, "fadiga": 10, "sono": 0})
        self.assertEqual(resultado["score"], 0.5)
        self.assertEqual(round(sum(resultado["contribuicoes"].values()), 4), 0.5001)

    def test_troca_de_versao_preserva_resultados_e_historico_existente(self):
        anterior = {
            "versao": 1, "status": "concluida", "score": 0.25,
            "pesos": {"dor": 0.25, "fadiga": 0.15, "sono": 0.15,
                      "recuperacao": 0.15, "dor_limita": 0.20, "lesao_previa": 0.10},
            "respostas": {**FAVORAVEL, "dor": 10},
        }
        detalhes = {
            "acwr": {"acwr": 1.8}, "score_subjetivo": anterior,
            "score_final": {"score_subjetivo": 0.25, "score_final": 0.3881},
            "historico_scores": [{"motivo": "registro_anterior"}],
        }
        original = deepcopy(detalhes)
        avaliacao = SimpleNamespace(**anterior["respostas"], detalhes=detalhes)
        self.assertTrue(atualizar_score_subjetivo(avaliacao))
        self.assertEqual(avaliacao.detalhes["score_subjetivo"]["score"], 0.1667)
        self.assertEqual(avaliacao.detalhes["acwr"], original["acwr"])
        historico = avaliacao.detalhes["historico_scores"]
        self.assertEqual(historico[0], original["historico_scores"][0])
        self.assertEqual(historico[1]["score_subjetivo"], original["score_subjetivo"])
        self.assertEqual(historico[1]["score_final"], original["score_final"])
        self.assertEqual(historico[1]["versao_icsa_destino"], 2)
        self.assertTrue(historico[1]["arquivado_em"].endswith("+00:00"))
        self.assertEqual(detalhes, original)
        self.assertFalse(atualizar_score_subjetivo(avaliacao))
        self.assertEqual(len(avaliacao.detalhes["historico_scores"]), 2)
        anterior["pesos"]["dor"] = 99
        self.assertEqual(historico[1]["score_subjetivo"]["pesos"]["dor"], 0.25)

    def test_nova_avaliacao_nao_cria_historico_artificial(self):
        avaliacao = SimpleNamespace(**FAVORAVEL, detalhes=None)
        self.assertTrue(atualizar_score_subjetivo(avaliacao))
        self.assertNotIn("historico_scores", avaliacao.detalhes)

    def test_versao_anterior_indisponivel_continua_ausente_e_e_preservada(self):
        anterior = {"versao": 1, "status": "indisponivel", "score": None}
        avaliacao = SimpleNamespace(**{**FAVORAVEL, "dor": None},
                                    detalhes={"score_subjetivo": anterior})
        atualizar_score_subjetivo(avaliacao)
        self.assertIsNone(avaliacao.detalhes["score_subjetivo"]["score"])
        self.assertEqual(avaliacao.detalhes["score_subjetivo"]["campos_ausentes"], ["dor"])
        self.assertEqual(avaliacao.detalhes["historico_scores"][0]["score_subjetivo"], anterior)

    def test_rpe_e_caracterizacao_nao_alteram_indice(self):
        resultado = calcular_icsa({
            **FAVORAVEL, "rpe": 10, "idade": 70, "peso_kg": 150,
            "altura_cm": 170, "sexo": "feminino", "lesao_quando": "menos_3_meses",
        })
        self.assertEqual(resultado, calcular_icsa(FAVORAVEL))

    def test_campos_ausentes_nao_sao_substituidos_por_zero(self):
        respostas = {**FAVORAVEL}
        del respostas["dor"]
        respostas["sono"] = None
        resultado = calcular_icsa(respostas)
        self.assertEqual(resultado["status"], "indisponivel")
        self.assertIsNone(resultado["score"])
        self.assertEqual(resultado["campos_ausentes"], ["dor", "sono"])

    def test_valores_invalidos_sao_identificados(self):
        for campo, valor in [("dor", -1), ("sono", 11), ("fadiga", True),
                             ("recuperacao", float("nan")), ("dor", "5"),
                             ("dor_limita", 1), ("lesao_previa", "Sim")]:
            with self.subTest(campo=campo, valor=valor):
                resultado = calcular_icsa({**FAVORAVEL, campo: valor})
                self.assertIsNone(resultado["score"])
                self.assertEqual(resultado["campos_invalidos"], [campo])
