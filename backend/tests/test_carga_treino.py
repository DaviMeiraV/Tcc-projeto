import unittest
from datetime import date, timedelta
from pathlib import Path

from app.services.carga_treino import calcular_csv


class CargaTreinoTest(unittest.TestCase):
    def test_carga_constante_resulta_em_um_e_conta_dias_sem_treino(self):
        inicio = date(2026, 9, 1)
        linhas = [f'{inicio + timedelta(days=i)},30,5' for i in range(28)]
        resultado = calcular_csv(('data,duracao,rpe\n' + '\n'.join(linhas)).encode())
        self.assertEqual(resultado['acwr'], 1)
        self.assertEqual(resultado['semana']['atividades'], 7)
        self.assertEqual(resultado['mes']['minutos'], 840)
        self.assertEqual(resultado['carga_aguda'], 150)
        self.assertFalse(resultado['historico_incompleto'])

    def test_limites_das_janelas_e_multiplas_atividades_no_mesmo_dia(self):
        # 01/09 fica fora da janela; 02/09 entra nos 28 dias; 23/09 inicia os 7 dias.
        dados = b'data,duracao\n2026-09-01,9999\n2026-09-02,100\n2026-09-22,100\n2026-09-23,50\n2026-09-29,50\n2026-09-29,100'
        resultado = calcular_csv(dados, rpe_formulario=1)
        self.assertEqual(resultado['acwr'], 2)
        self.assertEqual(resultado['mes']['minutos'], 400)
        self.assertEqual(resultado['semana']['minutos'], 200)
        self.assertEqual(resultado['semana']['atividades'], 3)

    def test_segundos_strava_e_duracao_garmin(self):
        for dados in (b'Activity Date,Elapsed Time\n2026-09-29,300',
                      'Data;Tempo\n29/09/2026;00:05:00'.encode(),
                      b'data,duracao_min\n2026-09-29,5'):
            with self.subTest(dados=dados):
                resultado = calcular_csv(dados, rpe_formulario=1)
                self.assertEqual(resultado['mes']['minutos'], 5)
                self.assertEqual(resultado['acwr'], 4)
                self.assertTrue(resultado['historico_incompleto'])

    def test_sem_rpe_no_formulario_nao_descarta_rpes_da_planilha(self):
        with self.assertRaisesRegex(ValueError, 'falta RPE na sessão e no formulário'):
            calcular_csv(b'data,duracao,rpe\n2026-09-02,60,10\n2026-09-29,60,')

    def test_carga_zero_nao_divide_por_zero(self):
        resultado = calcular_csv(b'data,duracao,rpe\n2026-09-29,30,0')
        self.assertIsNone(resultado['acwr'])
        self.assertEqual(resultado['carga_cronica'], 0)

    def test_rpe_formulario_completa_apenas_sessoes_sem_rpe(self):
        resultado = calcular_csv(b'data,duracao,rpe\n2026-09-02,60,10\n2026-09-29,60,', rpe_formulario=5)
        self.assertEqual(resultado['metodo'], 'duracao_rpe')
        self.assertEqual(resultado['mes']['carga'], 900)
        self.assertEqual(resultado['semana']['carga'], 300)
        self.assertEqual(resultado['acwr'], 1.3333)
        self.assertEqual(resultado['atividades_com_rpe_formulario'], 1)
        self.assertTrue(resultado['carga_estimada'])
        self.assertEqual(resultado['sessoes'][0]['rpe_original'], 10)
        self.assertEqual(resultado['sessoes'][0]['rpe_utilizado'], 10)
        self.assertEqual(resultado['sessoes'][0]['origem_rpe'], 'planilha')
        self.assertIsNone(resultado['sessoes'][1]['rpe_original'])
        self.assertEqual(resultado['sessoes'][1]['rpe_utilizado'], 5)
        self.assertEqual(resultado['sessoes'][1]['origem_rpe'], 'formulario')
        self.assertEqual(resultado['sessoes'][1]['linha'], 3)

    def test_rpe_constante_multiplica_cargas_e_preserva_razao(self):
        dados = b'data,duracao\n2026-09-02,60\n2026-09-29,60'
        resultado = calcular_csv(dados, rpe_formulario=6)
        self.assertEqual(resultado['mes']['carga'], 720)
        self.assertEqual(resultado['semana']['carga'], 360)
        self.assertEqual(resultado['acwr'], calcular_csv(dados, rpe_formulario=1)['acwr'])
        self.assertEqual(resultado['atividades_com_rpe_formulario'], 2)
        self.assertIsNone(calcular_csv(dados, rpe_formulario=0)['acwr'])

    def test_rpe_zero_da_sessao_nao_e_substituido(self):
        resultado = calcular_csv(b'data,duracao,rpe\n2026-09-29,30,0', rpe_formulario=6)
        self.assertEqual(resultado['mes']['carga'], 0)
        self.assertEqual(resultado['atividades_com_rpe_formulario'], 0)
        self.assertFalse(resultado['carga_estimada'])
        self.assertEqual(resultado['sessoes'][0]['origem_rpe'], 'planilha')

    def test_dados_invalidos_nao_produzem_score_parcial(self):
        for dados in (b'data,duracao\n', b'coluna\nvalor',
                      b'data,duracao\n2026-09-29,NaN',
                      b'data,duracao,rpe\n2026-09-29,30,11',
                      b'data,duracao\n2026-09-29,30\ninvalida,30'):
            with self.subTest(dados=dados), self.assertRaises(ValueError):
                calcular_csv(dados)

    def test_planilha_de_exemplo_do_projeto(self):
        resultado = calcular_csv((Path(__file__).resolve().parents[2] / 'exemplo_treinos.csv').read_bytes(), rpe_formulario=5)
        self.assertEqual(resultado['status'], 'concluida')
        self.assertEqual(resultado['metodo'], 'duracao_rpe')
        self.assertTrue(resultado['carga_estimada'])
        self.assertGreater(resultado['mes']['atividades'], 0)
