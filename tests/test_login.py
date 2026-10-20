# Rodar na raiz do projeto: python -m unittest discover -s tests
import tempfile
import unittest
from pathlib import Path

from code_py import banco, login
from code_py.user_types import Discente
from code_py.seguranca import verificar_senha


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


class TestPerfilLigadoAoLogin(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.banco_original = banco.caminho_banco
        banco.caminho_banco = Path(self.pasta.name) / 'teste.db'

        admin = login.criar_admin_inicial('admin@unb.br', 'adminsenha')
        self.admin = admin
        senha_inicial = login.gerar_acesso(admin, 'ana@aluno.unb.br', 'discente')
        self.conta = login.trocar_senha('ana@aluno.unb.br', senha_inicial, 'minhasenha')

    def tearDown(self):
        banco.caminho_banco = self.banco_original
        self.pasta.cleanup()

    def test_primeiro_acesso_cria_perfil(self):
        self.assertIsNone(banco.buscar_perfil('ana@aluno.unb.br'))

        criado = banco.cadastrar_perfil(
            self.conta, 'Ana', '52998224725', 2024, 1, 'Engenharia de Software'
        )
        perfil = banco.buscar_perfil('ANA@aluno.unb.br')

        self.assertEqual(perfil.id_user, criado.id_user)
        self.assertEqual(perfil.nome, 'Ana')
        self.assertEqual(perfil.cpf, '529.982.247-25')
        self.assertEqual(perfil.curso, 'Engenharia de Software')

        # A senha do perfil é a mesma do login (uma única senha por pessoa).
        self.assertTrue(verificar_senha('minhasenha', perfil.get_hash_senha()))

    def test_perfil_acompanha_troca_de_senha(self):
        banco.cadastrar_perfil(self.conta, 'Ana', '52998224725', 2024, 1, 'Engenharia de Software')
        login.trocar_senha('ana@aluno.unb.br', 'minhasenha', 'outrasenha')

        perfil = banco.buscar_perfil('ana@aluno.unb.br')
        self.assertTrue(verificar_senha('outrasenha', perfil.get_hash_senha()))

    def test_perfil_recusa_repeticao_e_admin(self):
        banco.cadastrar_perfil(self.conta, 'Ana', '52998224725', 2024, 1, 'Engenharia de Software')

        with self.assertRaises(ValueError):
            banco.cadastrar_perfil(self.conta, 'Ana', '11144477735', 2024, 1, 'Engenharia de Software')

        senha = login.gerar_acesso(self.admin, 'bia@aluno.unb.br', 'discente')
        bia = login.trocar_senha('bia@aluno.unb.br', senha, 'senhadabia')
        with self.assertRaises(ValueError):    # CPF já usado pela Ana
            banco.cadastrar_perfil(bia, 'Bia', '52998224725', 2024, 1, 'Engenharia de Software')

        with self.assertRaises(ValueError):
            banco.cadastrar_perfil(self.admin, 'Admin', '11144477735', 2024, 1, 'Engenharia de Software')

    def test_docente_com_area_invalida(self):
        senha = login.gerar_acesso(self.admin, 'prof@unb.br', 'docente')
        prof = login.trocar_senha('prof@unb.br', senha, 'senhaprof')

        with self.assertRaises(ValueError):
            banco.cadastrar_perfil(prof, 'Prof', '11144477735', 2015, 2, 'Medicina')

        perfil = banco.cadastrar_perfil(prof, 'Prof', '11144477735', 2015, 2, 'Engenharia de Energia')
        self.assertEqual(perfil.area, 'Engenharia de Energia')


if __name__ == '__main__':
    unittest.main()
