import unittest
from types import SimpleNamespace

from app.services.score_final import atualizar_score_final, calc_score_final, normalizar_acwr, normalizar_postural


def foto(id, score=None, status="concluida"):
    return SimpleNamespace(id=id, analise={"score": score, "status": status})


class ScoreFinalTest(unittest.TestCase):
    def test_normalizacao_acwr(self):
        for bruto, esperado in [(0, 0), (0.8, 0), (1, 0), (1.2, 0), (1.3, 0),
                                (1.4, 0.1429), (1.5, 0.2857), (1.7, 0.5714),
                                (1.8, 0.7143), (2, 1), (4, 1)]:
            with self.subTest(bruto=bruto):
                self.assertEqual(round(normalizar_acwr(bruto), 4), esperado)
        for invalido in [None, -1, float('nan'), float('inf'), -float('inf'), True, '1.8', {}, []]:
            with self.subTest(invalido=invalido):
                self.assertIsNone(normalizar_acwr(invalido))

    def test_normalizacao_postural(self):
        for bruto, esperado in [(0, 1), (0.5, 0.5), (1, 0)]:
            self.assertEqual(normalizar_postural(bruto), esperado)
        for invalido in [None, -0.1, 1.1, float('nan'), float('inf'), True, '0.8', {}]:
            self.assertIsNone(normalizar_postural(invalido))

    def avaliacao_completa(self):
        return SimpleNamespace(detalhes={
            'acwr': {'status': 'concluida', 'acwr': 1.8},
            'score_subjetivo': {'status': 'concluida', 'score': 0.45},
        }, fotos=[foto(1, 0.8)])

    def test_exemplo_e_precisao_intermediaria(self):
        avaliacao = self.avaliacao_completa()
        resultado = calc_score_final(avaliacao)
        self.assertEqual(resultado['score_final'], 0.4548)
        self.assertEqual(resultado['score_acwr'], 1.8)
        self.assertEqual(resultado['score_acwr_normalizado'], 0.7143)
        self.assertEqual(resultado['score_subjetivo'], 0.45)
        self.assertEqual(resultado['score_postural_original'], 0.8)
        self.assertEqual(resultado['score_postural_normalizado'], 0.2)
        self.assertEqual(resultado['foto_id'], 1)
        self.assertEqual(resultado['motivos'], [])
        # Arredondar C antes da média produziria 0.3001 em vez de 0.3000.
        avaliacao.detalhes['acwr']['acwr'] = 1.4
        avaliacao.detalhes['score_subjetivo']['score'] = 0.55729
        self.assertEqual(calc_score_final(avaliacao)['score_final'], 0.3)

    def test_ausencia_de_cada_componente_e_subjetivo_invalido(self):
        for campo in ['acwr', 'score_subjetivo', 'fotos']:
            avaliacao = self.avaliacao_completa()
            if campo == 'fotos':
                avaliacao.fotos = []
            else:
                del avaliacao.detalhes[campo]
            self.assertIsNone(calc_score_final(avaliacao)['score_final'])
        for invalido in [None, -1, 2, True, '0.5', float('nan'), float('inf')]:
            avaliacao = self.avaliacao_completa()
            avaliacao.detalhes['score_subjetivo']['score'] = invalido
            self.assertIsNone(calc_score_final(avaliacao)['score_final'])

    def test_historico_incompleto_e_multiplas_fotos(self):
        avaliacao = self.avaliacao_completa()
        avaliacao.detalhes['acwr']['historico_incompleto'] = True
        self.assertIsNone(calc_score_final(avaliacao)['score_final'])
        avaliacao.detalhes['acwr']['historico_incompleto'] = False
        avaliacao.fotos.append(foto(2, None, 'erro'))
        resultado = calc_score_final(avaliacao)
        self.assertIsNone(resultado['score_final'])
        self.assertIsNone(resultado['foto_id'])
        self.assertIn('várias fotos', resultado['motivos'][0])

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
            {"foto_id": 1, "score": 0.7, "score_normalizado": 0.3},
            {"foto_id": 2, "score": 0.9, "score_normalizado": 0.1},
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
            {"foto_id": 1, "score": None, "score_normalizado": None},
            {"foto_id": 2, "score": None, "score_normalizado": None},
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
