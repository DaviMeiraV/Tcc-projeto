import unittest
from types import SimpleNamespace

from app.services.score_final import atualizar_score_final, calc_score_final


def foto(id, score=None, status="concluida"):
    return SimpleNamespace(id=id, analise={"score": score, "status": status})


class ScoreFinalTest(unittest.TestCase):
    def test_reune_tres_componentes_sem_combinar_fotos(self):
        avaliacao = SimpleNamespace(
            detalhes={
                "acwr": {"status": "concluida", "acwr": 1.8},
                "score_subjetivo": {"status": "concluida", "score": 0.45},
            },
            fotos=[foto(2, 0.9), foto(1, 0.7)],
        )
        resultado = calc_score_final(avaliacao)
        self.assertEqual(resultado["score_acwr"], 1.8)
        self.assertEqual(resultado["score_subjetivo"], 0.45)
        self.assertEqual(resultado["scores_posturais"], [
            {"foto_id": 1, "score": 0.7}, {"foto_id": 2, "score": 0.9},
        ])
        self.assertIsNone(resultado["score_final"])

    def test_ausencias_e_erros_nao_sao_convertidos_em_zero(self):
        avaliacao = SimpleNamespace(detalhes=None, fotos=[])
        resultado = calc_score_final(avaliacao)
        self.assertIsNone(resultado["score_acwr"])
        self.assertIsNone(resultado["score_subjetivo"])
        self.assertEqual(resultado["scores_posturais"], [])
        avaliacao.detalhes = {
            "acwr": {"status": "erro", "acwr": 2},
            "score_subjetivo": {"status": "indisponivel", "score": 0.3},
        }
        avaliacao.fotos = [foto(1, 0.9, "erro"), SimpleNamespace(id=2, analise=None)]
        resultado = calc_score_final(avaliacao)
        self.assertIsNone(resultado["score_acwr"])
        self.assertIsNone(resultado["score_subjetivo"])
        self.assertEqual(resultado["scores_posturais"], [
            {"foto_id": 1, "score": None}, {"foto_id": 2, "score": None},
        ])

    def test_zero_e_preservado_e_demais_detalhes_nao_sao_perdidos(self):
        detalhes = {
            "acwr": {"status": "concluida", "acwr": 0},
            "score_subjetivo": {"status": "concluida", "score": 0},
        }
        avaliacao = SimpleNamespace(detalhes=detalhes.copy(), fotos=[foto(1, 0)])
        self.assertTrue(atualizar_score_final(avaliacao))
        resultado = avaliacao.detalhes["score_final"]
        self.assertEqual(resultado["score_acwr"], 0)
        self.assertEqual(resultado["score_subjetivo"], 0)
        self.assertEqual(resultado["scores_posturais"][0]["score"], 0)
        self.assertEqual(avaliacao.detalhes["acwr"], detalhes["acwr"])
        self.assertFalse(atualizar_score_final(avaliacao))
        avaliacao.fotos[0].analise["score"] = 0.8
        self.assertTrue(atualizar_score_final(avaliacao))
        self.assertEqual(avaliacao.detalhes["score_final"]["scores_posturais"][0]["score"], 0.8)
