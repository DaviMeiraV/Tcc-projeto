import unittest

from sqlalchemy import create_engine, inspect, text

# O projeto usa JSONB no PostgreSQL; os testes isolados usam JSON no SQLite.
from test_analise_postural import jsonb_em_sqlite  # noqa: F401
from app.migracoes import inicializar_banco


class MigracoesTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")

    def tearDown(self):
        self.engine.dispose()

    def test_banco_antigo_preserva_registros_e_adiciona_colunas(self):
        with self.engine.begin() as conexao:
            conexao.execute(text("CREATE TABLE avaliacoes (id INTEGER PRIMARY KEY, idade INTEGER)"))
            conexao.execute(text("INSERT INTO avaliacoes (id, idade) VALUES (1, 21)"))
        inicializar_banco(self.engine)
        inicializar_banco(self.engine)
        with self.engine.begin() as conexao:
            self.assertEqual(conexao.execute(text(
                "SELECT id, idade, csv_arquivo, csv_nome_original FROM avaliacoes"
            )).one(), (1, 21, None, None))
            conexao.execute(text(
                "UPDATE avaliacoes SET csv_arquivo = 'treino.csv', csv_nome_original = 'Activities.csv' WHERE id = 1"
            ))
        inicializar_banco(self.engine)
        with self.engine.connect() as conexao:
            self.assertEqual(conexao.execute(text(
                "SELECT csv_arquivo, csv_nome_original FROM avaliacoes WHERE id = 1"
            )).one(), ("treino.csv", "Activities.csv"))

    def test_banco_novo_e_inicializacao_repetida(self):
        inicializar_banco(self.engine)
        inicializar_banco(self.engine)
        colunas = {c["name"] for c in inspect(self.engine).get_columns("avaliacoes")}
        self.assertTrue({"csv_arquivo", "csv_nome_original"} <= colunas)

    def test_banco_com_apenas_uma_coluna_csv(self):
        with self.engine.begin() as conexao:
            conexao.execute(text("CREATE TABLE avaliacoes (id INTEGER PRIMARY KEY, csv_arquivo VARCHAR(255))"))
            conexao.execute(text("INSERT INTO avaliacoes VALUES (1, 'preservado.csv')"))
        inicializar_banco(self.engine)
        with self.engine.connect() as conexao:
            self.assertEqual(conexao.execute(text(
                "SELECT csv_arquivo, csv_nome_original FROM avaliacoes"
            )).one(), ("preservado.csv", None))
