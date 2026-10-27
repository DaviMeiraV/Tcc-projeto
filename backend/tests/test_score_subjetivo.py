import unittest

from app.services.score_subjetivo import calcular_icsa


FAVORAVEL = {
    "dor": 0, "fadiga": 0, "sono": 10, "recuperacao": 10,
    "dor_limita": False, "lesao_previa": False,
}


class ScoreSubjetivoTest(unittest.TestCase):
    def test_exemplo_do_documento(self):
        resultado = calcular_icsa({
            **FAVORAVEL, "sono": 5, "recuperacao": 5,
            "dor_limita": True, "lesao_previa": True,
        })
        self.assertEqual(resultado["score"], 0.45)
        self.assertEqual(resultado["componentes"]["sono"], 0.5)
        self.assertEqual(resultado["componentes"]["recuperacao"], 0.5)
        self.assertEqual(resultado["versao"], 1)
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
            ("dor", 10, 0.25), ("fadiga", 10, 0.15),
            ("sono", 0, 0.15), ("recuperacao", 0, 0.15),
            ("dor_limita", True, 0.20), ("lesao_previa", True, 0.10),
        ]
        for campo, valor, esperado in casos:
            with self.subTest(campo=campo):
                resultado = calcular_icsa({**FAVORAVEL, campo: valor})
                self.assertEqual(resultado["score"], esperado)
                self.assertEqual(resultado["contribuicoes"][campo], esperado)

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
