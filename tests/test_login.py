# Rodar na raiz do projeto: python -m unittest discover -s tests
from code_py import banco, login
from base import TesteComBanco


class TestLogin(TesteComBanco):

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

    def test_perfil_gravado(self):
        perfil = self.criar_perfil('ana@aluno.unb.br', 'discente', '52998224725')
        self.assertEqual(banco.buscar_perfil('ana@aluno.unb.br').id_user, perfil.id_user)
