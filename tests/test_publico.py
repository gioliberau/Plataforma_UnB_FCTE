# Rodar na raiz do projeto: python -m unittest discover -s tests
from datetime import date

from code_py import consultas_publicas as cp
from base import TesteComBanco


class TestConsultasPublicas(TesteComBanco):

    def test_cursos(self):
        self.assertEqual(len(cp.listar_cursos()), 5)

    def test_organizacoes(self):
        todas = cp.listar_organizacoes()
        self.assertTrue(todas)
        self.assertTrue(all(o['tipo'] == 'atletica' for o in cp.listar_organizacoes('atletica')))

        with self.assertRaises(ValueError):
            cp.listar_organizacoes('tipo_inexistente')

    def test_calendario(self):
        self.assertEqual(cp.periodos_calendario()[:2], ['2026.1', '2026.2'])

        aulas = [e for e in cp.eventos_do_periodo('2026.2') if e['descricao'] == 'Período de aulas'][0]
        self.assertIn('EM ANDAMENTO', cp.formatar_evento(aulas, date(2026, 10, 28)))
        self.assertIn('já passou', cp.formatar_evento(aulas, date(2027, 1, 1)))
        self.assertIn('daqui a 9 dia(s)', cp.formatar_evento(aulas, date(2026, 8, 1)))