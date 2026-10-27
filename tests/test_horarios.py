# Rodar na raiz do projeto: python -m unittest discover -s tests
import unittest

from code_py.horarios import traduzir, descrever


class TestHorarios(unittest.TestCase):

    def test_codigos_validos(self):
        self.assertEqual(traduzir('35T23'), [(3, '14:00', '15:50'), (5, '14:00', '15:50')])
        self.assertEqual(traduzir('24M12'), [(2, '08:00', '09:50'), (4, '08:00', '09:50')])
        self.assertEqual(traduzir('6N1234'), [(6, '19:00', '22:30')])
        self.assertEqual(traduzir('7M5'), [(7, '12:00', '12:55')])

    def test_varios_blocos_e_horarios_separados(self):
        self.assertEqual(
            traduzir('2M34 4T6'),
            [(2, '10:00', '11:50'), (4, '18:00', '18:55')]
        )
        self.assertEqual(traduzir('3T13'), [(3, '12:55', '13:50'), (3, '14:55', '15:50')])

    def test_descrever(self):
        self.assertEqual(descrever('24M12'), 'segunda-feira 08:00-09:50; quarta-feira 08:00-09:50')

    def test_codigos_invalidos(self):
        for codigo in ('', '  ', None, '35X23', 'T23', '35T', '2N5', '2M6', '35T23 abc', '8M1'):
            with self.subTest(codigo=codigo), self.assertRaises(ValueError):
                traduzir(codigo)
