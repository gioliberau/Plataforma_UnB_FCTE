# Rodar na raiz do projeto: python -m unittest discover -s tests
import tempfile
import unittest
from pathlib import Path

from code_py import banco, exemplos, turmas
from code_py.horarios import legivel
from code_py.system import SistemaFCTE


class TestExemplos(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.banco_original = banco.caminho_banco
        banco.caminho_banco = Path(self.pasta.name) / 'teste.db'

    def tearDown(self):
        banco.caminho_banco = self.banco_original
        self.pasta.cleanup()

    def test_rodar_duas_vezes_nao_duplica(self):
        exemplos.criar_exemplos()
        exemplos.criar_exemplos()

        aluno = banco.buscar_perfil('aluno@exemplo.unb.br')
        professor = banco.buscar_perfil('professor@exemplo.unb.br')

        self.assertEqual(len(turmas.turmas_do_discente(aluno)), 6)
        self.assertEqual(len(turmas.turmas_do_docente(professor)), 6)
        self.assertEqual([p.nome for p in banco.listar_perfis('docente')], ['Paulo Exemplo'])
        self.assertAlmostEqual(turmas.mp(aluno), 3.5555555555555554)   # SS, MS, MM e MI nas turmas com nota

    def test_semestre_atual_tem_turmas(self):
        exemplos.criar_exemplos()
        self.assertEqual(len(SistemaFCTE().listar_turmas()), 2)

    def test_legivel(self):
        self.assertEqual(legivel('35T23'), '35T23 (terça-feira 14:00-15:50; quinta-feira 14:00-15:50)')
        self.assertEqual(legivel('a definir'), 'a definir')