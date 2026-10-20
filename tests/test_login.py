# Rodar na raiz do projeto: python -m unittest discover -s tests
import tempfile
import unittest
from pathlib import Path

from code_py import banco, login
from code_py.user_types import Discente


class TestLogin(unittest.TestCase):

    def setUp(self):
        # Banco temporário: nunca toca no sistema.db real.
        self.pasta = tempfile.TemporaryDirectory()
        self.banco_original = banco.caminho_banco
        banco.caminho_banco = Path(self.pasta.name) / 'teste.db'
        self.admin = login.criar_admin_inicial('admin@unb.br', 'adminsenha')

    def tearDown(self):
        banco.caminho_banco = self.banco_original
        self.pasta.cleanup()

    def test_fluxo_primeiro_acesso(self):
        senha_inicial = login.gerar_acesso(self.admin, 'aluno@aluno.unb.br', 'discente')

        conta = login.autenticar('aluno@aluno.unb.br', senha_inicial)
        self.assertTrue(conta.precisa_trocar_senha)

        with self.assertRaises(ValueError):
            login.trocar_senha('aluno@aluno.unb.br', senha_inicial, '1234567')

        conta = login.trocar_senha('aluno@aluno.unb.br', senha_inicial, 'minhasenha')
        self.assertFalse(conta.precisa_trocar_senha)

        self.assertIsNone(login.autenticar('aluno@aluno.unb.br', senha_inicial))
        self.assertIsNotNone(login.autenticar('ALUNO@aluno.unb.br', 'minhasenha'))

    def test_apenas_um_admin_inicial(self):
        with self.assertRaises(PermissionError):
            login.criar_admin_inicial('outro@unb.br', 'outrasenha')

    def test_gerar_acesso_recusa_entradas_invalidas(self):
        login.gerar_acesso(self.admin, 'aluno@aluno.unb.br', 'discente')

        with self.assertRaises(ValueError):
            login.gerar_acesso(self.admin, 'Aluno@aluno.unb.br', 'docente')   # e-mail repetido
        with self.assertRaises(ValueError):
            login.gerar_acesso(self.admin, 'x@unb.br', 'chefe')
        with self.assertRaises(ValueError):
            login.gerar_acesso(self.admin, 'semarroba', 'docente')

        nao_admin = login.Conta('x@unb.br', 'discente', False)
        with self.assertRaises(PermissionError):
            login.gerar_acesso(nao_admin, 'y@unb.br', 'docente')


class TestPerfil(unittest.TestCase):

    def test_cpf(self):
        with self.assertRaises(ValueError):
            Discente(2024, 1, 'Ana', '12345678900', 'ana@unb.br', 'senha1234', 'Engenharia de Software')

        aluna = Discente(2024, 1, 'Ana', '52998224725', 'ana@unb.br', 'senha1234', 'Engenharia de Software')
        self.assertEqual(aluna.cpf, '529.982.247-25')

    def test_cadastro_e_reconstrucao(self):
        with tempfile.TemporaryDirectory() as pasta:
            original = banco.caminho_banco
            banco.caminho_banco = Path(pasta) / 'teste.db'

            try:
                aluna = Discente(2024, 1, 'Ana', '52998224725', 'ana@unb.br', 'senha1234', 'Engenharia de Software')
                matricula = banco.cadastrar_usuario(aluna)

                recriada = banco.reconstruir_usuario(banco.buscar_usuario_por_id(matricula))
                self.assertEqual(recriada.id_user, matricula)
                self.assertEqual(recriada.cpf, '529.982.247-25')
                self.assertEqual(recriada.get_hash_senha(), aluna.get_hash_senha())
            finally:
                banco.caminho_banco = original


if __name__ == '__main__':
    unittest.main()
