# Banco temporário para os testes: nunca toca no sistema.db real.
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import closing

from code_py import banco, login


class TesteComBanco(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.banco_original = banco.caminho_banco
        banco.caminho_banco = Path(self.pasta.name) / 'teste.db'
        self.admin = login.criar_admin_inicial('admin@unb.br', 'adminsenha')

    def tearDown(self):
        banco.caminho_banco = self.banco_original
        self.pasta.cleanup()

    def criar_perfil(self, email, tipo, cpf, curso='Engenharia de Software'):
        senha = login.gerar_acesso(self.admin, email, tipo)
        conta = login.trocar_senha(email, senha, 'senhanova123')
        return banco.cadastrar_perfil(conta, 'Pessoa Teste', cpf, 2024, 1, curso)

    def gravar_turma(self, periodo, codigo, numero, carga=60, horario='35T23'):
        # Simula uma turma já baixada do SIGAA.
        turma = {
            'codigo_disciplina': codigo, 'nome_disciplina': 'Disciplina ' + codigo,
            'numero_turma': numero, 'periodo': periodo, 'docente': 'Fulano',
            'carga_horaria': carga, 'horario': horario, 'fonte': 'teste',
        }
        chave = f'{periodo}|{codigo}|{numero}'

        with closing(banco.conectar()) as conexao, conexao:
            conexao.execute(
                'INSERT INTO dados_publicos VALUES (?, ?, ?, ?)',
                ('turma_sigaa', chave, json.dumps(turma), 'teste')
            )

        return chave
