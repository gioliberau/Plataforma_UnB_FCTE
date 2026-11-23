import os
import unittest
from datetime import date

from code_py import banco, exemplos, login
from desktop.estilo import converter_data_br, formatar_data_br, formatar_indice, parsear_periodo
from tests.base import TesteComBanco


def _tk_disponivel():
    try:
        import tkinter as tk
    except ModuleNotFoundError:
        return False

    if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        return False

    try:
        raiz = tk.Tk()
        raiz.withdraw()
        raiz.destroy()
        return True
    except Exception:
        return False


class TestHelpersDesktop(unittest.TestCase):

    def test_converter_data_br(self):
        self.assertIsNone(converter_data_br(''))
        self.assertEqual(converter_data_br('25/11/2026'), date(2026, 11, 25))
        with self.assertRaises(ValueError):
            converter_data_br('2026-11-25')

    def test_formatar_data_br(self):
        self.assertEqual(formatar_data_br(None), '—')
        self.assertEqual(formatar_data_br(date(2026, 5, 9)), '09/05/2026')
        self.assertEqual(formatar_data_br('2026-05-09T14:30:00'), '09/05/2026')

    def test_parsear_periodo(self):
        self.assertEqual(parsear_periodo(''), (None, None))
        self.assertEqual(parsear_periodo('2026.2'), (2026, 2))
        with self.assertRaises(ValueError):
            parsear_periodo('2026.3')

    def test_formatar_indice(self):
        self.assertEqual(formatar_indice(None), 'sem notas')
        self.assertEqual(formatar_indice(4.256), '4.26')


@unittest.skipUnless(_tk_disponivel(), 'tkinter ou servidor gráfico indisponível')
class TestAppDesktop(TesteComBanco):

    def setUp(self):
        super().setUp()
        from code_py import consultas_publicas as cp
        self._auto_original = cp.atualizacao_automatica
        cp.atualizacao_automatica = False
        self.app = None

    def tearDown(self):
        from code_py import consultas_publicas as cp
        cp.atualizacao_automatica = self._auto_original
        if self.app is not None:
            try:
                self.app.destroy()
            except Exception:
                pass
        super().tearDown()

    def _criar_app(self):
        from desktop.app import AppFCTE
        self.app = AppFCTE(garantir_exemplos=False)
        self.app.withdraw()
        self.app.update_idletasks()
        return self.app

    def test_navegacao_portal_publico(self):
        app = self._criar_app()
        app.entrar_como_visitante()
        principal = app.tela_ativa

        for chave in ('inicio', 'turmas', 'cardapio', 'biblioteca', 'campus'):
            principal.abrir_tela(chave)
            app.update_idletasks()

        self.assertFalse(app.sessao.autenticada)

    def test_navegacao_perfis_autenticados(self):
        self.criar_perfil('aluno@unb.br', 'discente', '52998224725')
        self.criar_perfil('docente@unb.br', 'docente', '11144477735')
        self.gravar_turma('2026.2', 'FGA0170', '01')

        app = self._criar_app()

        # Discente
        conta_aluno = login.autenticar('aluno@unb.br', 'senhanova123')
        perfil_aluno = banco.buscar_perfil('aluno@unb.br')
        app.ao_autenticar(conta_aluno, perfil_aluno)
        for chave in ('inicio', 'turmas', 'cardapio', 'oportunidades', 'biblioteca', 'campus'):
            app.tela_ativa.abrir_tela(chave)
            app.update_idletasks()
        app.fazer_logout(exibir_aviso=False)
        self.assertFalse(app.sessao.autenticada)

        # Docente
        conta_doc = login.autenticar('docente@unb.br', 'senhanova123')
        perfil_doc = banco.buscar_perfil('docente@unb.br')
        app.ao_autenticar(conta_doc, perfil_doc)
        for chave in ('inicio', 'turmas', 'cardapio', 'oportunidades', 'biblioteca', 'campus'):
            app.tela_ativa.abrir_tela(chave)
            app.update_idletasks()
        app.fazer_logout(exibir_aviso=False)

        # Admin
        app.ao_autenticar(self.admin, None)
        for chave in ('inicio', 'turmas', 'cardapio', 'oportunidades', 'biblioteca', 'campus', 'admin'):
            app.tela_ativa.abrir_tela(chave)
            app.update_idletasks()
        app.fazer_logout(exibir_aviso=False)

    def test_exemplos_e_arranque_padrao(self):
        # Garante que iniciar com banco contendo exemplos funciona sem erro.
        banco.caminho_banco.unlink(missing_ok=True)
        exemplos.criar_exemplos()
        app = self._criar_app()
        conta = login.autenticar(*exemplos.admin_exemplo)
        self.assertIsNotNone(conta)
        app.ao_autenticar(conta, None)
        app.tela_ativa.abrir_tela('admin')
        app.update_idletasks()


if __name__ == '__main__':
    unittest.main()
