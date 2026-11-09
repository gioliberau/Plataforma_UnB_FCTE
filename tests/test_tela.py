# Rodar na raiz do projeto: python -m unittest discover -s tests
import io
from contextlib import closing, redirect_stdout
from datetime import datetime
from unittest.mock import patch

from code_py import banco, login, organizacoes as ops, tela, paginas
from base import TesteComBanco


class TestTela(TesteComBanco):

    def test_data_hora_e_duracao(self):
        momento = datetime(2026, 11, 8, 14, 32)
        self.assertEqual(tela.formatar_data_hora(momento), 'domingo, 08/11/2026 às 14:32')
        self.assertEqual(tela.formatar_duracao(momento, datetime(2026, 11, 8, 14, 32, 20)), 'menos de 1 min')
        self.assertEqual(tela.formatar_duracao(momento, datetime(2026, 11, 8, 14, 44)), '12 min')
        self.assertEqual(tela.formatar_duracao(momento, datetime(2026, 11, 8, 16, 5)), '1h33min')

    def test_sessao_guarda_inicio(self):
        sessao = login.Sessao()
        self.assertIsNone(sessao.iniciada_em)
        sessao.iniciar(self.admin)
        self.assertIsInstance(sessao.iniciada_em, datetime)
        sessao.encerrar()
        self.assertIsNone(sessao.iniciada_em)

    def test_menu_pausa_so_em_acao_folha(self):
        def folha():
            print('resultado da ação')

        def submenu():
            paginas.abrir_menu('SUB', lambda: [('Algo', folha)])

        opcoes = lambda: [('Folha', folha), ('Submenu', submenu)]
        # 1 = ação folha (pausa), 2 = submenu, 0 = sai do submenu, 9 = inválida, 0 = sai
        entradas = iter(['1', '2', '0', '9', '0'])

        with patch('builtins.input', lambda *a: next(entradas)), \
             patch.object(paginas, 'pausar') as pausar, \
             patch.object(paginas, 'limpar_tela') as limpar, \
             redirect_stdout(io.StringIO()) as saida:
            paginas.abrir_menu('TESTE', opcoes)

        self.assertEqual(pausar.call_count, 1)          # o submenu não gera pausa extra
        self.assertGreaterEqual(limpar.call_count, 5)   # cada tela nova limpa o terminal
        self.assertIn('Opção inválida', saida.getvalue())
        self.assertEqual(list(entradas), [])

    def test_menu_pausa_depois_de_erro(self):
        def falha():
            raise ValueError('deu ruim')

        entradas = iter(['1', '0'])

        with patch('builtins.input', lambda *a: next(entradas)), \
             patch.object(paginas, 'pausar') as pausar, \
             patch.object(paginas, 'limpar_tela'), \
             redirect_stdout(io.StringIO()) as saida:
            paginas.abrir_menu('TESTE', lambda: [('Falha', falha)])

        self.assertIn('Não foi possível concluir: deu ruim', saida.getvalue())
        self.assertEqual(pausar.call_count, 1)

    def test_sem_terminal_nao_limpa_nem_pausa(self):
        with patch.object(tela, 'interativo', return_value=False), \
             patch('builtins.input') as entrada, \
             redirect_stdout(io.StringIO()) as saida:
            tela.limpar_tela()
            tela.pausar()

        entrada.assert_not_called()
        self.assertEqual(saida.getvalue(), '')


class TestOrganizacoesDetalhadas(TesteComBanco):

    def test_banco_antigo_recebe_colunas_e_dados(self):
        # O esquema do banco.py ainda tem só 4 colunas: a migração acontece em organizacoes.py.
        lista = {e['nome']: e for e in ops.listar_entidades_fixas(None)}
        self.assertEqual(lista['Zenit']['area'], 'Engenharia Aeroespacial')
        self.assertIsNone(lista['EletroJun']['area'])

    def test_nao_sobrescreve_o_que_o_admin_editou(self):
        ops.listar_entidades_fixas(None)

        with closing(banco.conectar()) as conexao, conexao:
            conexao.execute("UPDATE entidades_fixas SET area = 'Minha área' WHERE nome = 'Zenit'")

        lista = {e['nome']: e for e in ops.listar_entidades_fixas(None)}
        self.assertEqual(lista['Zenit']['area'], 'Minha área')

    def test_cadastro_com_dados_extras(self):
        ops.cadastrar_entidade_fixa(
            self.admin, 'Nova EJ', 'empresa_junior', 'https://instagram.com/novaej/',
            area='Engenharia Eletrônica', contato='oi@novaej.com', descricao='  ', como_participar=None
        )
        nova = [e for e in ops.listar_entidades_fixas(None) if e['nome'] == 'Nova EJ'][0]
        self.assertEqual(nova['area'], 'Engenharia Eletrônica')
        self.assertIsNone(nova['descricao'])

        card = ops.formatar_entidade(nova)
        self.assertIn('@novaej', card)
        self.assertIn('oi@novaej.com', card)
        self.assertIn('Associação civil', card)         # sem descrição própria: texto padrão do tipo
        self.assertNotIn('None', card)

        with self.assertRaises(ValueError):
            ops.cadastrar_entidade_fixa(self.admin, 'X', 'atletica', 'https://instagram.com/x/', area='a' * 81)

    def test_lista_agrupada_busca_e_resumo(self):
        todas = ops.listar_entidades_fixas(None)
        texto = ops.formatar_lista_entidades(todas)
        self.assertIn('Empresa Júnior (4)', texto)
        self.assertIn(f'Total: {len(todas)} organização(ões).', texto)
        self.assertEqual(ops.formatar_lista_entidades([]), 'Nenhuma organização encontrada.')
        self.assertTrue(ops.resumo_entidades(todas).strip().startswith(f'{len(todas)} organizações'))
        self.assertEqual(texto.count('Associação civil'), 1)      # texto do tipo aparece uma vez só

        self.assertEqual([e['nome'] for e in ops.buscar_entidades('AEROESPACIAL')], ['Zenit'])
        self.assertEqual([e['nome'] for e in ops.buscar_entidades('satelites')], ['Gama CubeDesign'])
        self.assertEqual(ops.buscar_entidades('nada disso existe'), [])

        with self.assertRaises(ValueError):
            ops.buscar_entidades('   ')
