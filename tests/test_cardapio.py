# Rodar na raiz do projeto: python -m unittest discover -s tests
import unittest

from code_py import consultas_publicas as cp
from code_py.cardapio import sanitizar_registro


class TestCardapio(unittest.TestCase):

    def test_remove_data_rotulo_e_rodape(self):
        registro = {'data': '2026-11-09', 'refeicao': 'almoco', 'itens': {
            'salada_1': ['09/11/2026', 'Alface roxa'],
            'prato_principal_vegetariano_estrito': ['Soja refogada', 'ESTRITO'],
            'bebida': ['Guaraná', 'Cardápio sujeito a alterações.'],
        }}
        itens = sanitizar_registro(registro)['itens']

        self.assertEqual(itens['salada_1'], ['Alface roxa'])
        self.assertEqual(itens['prato_principal_vegetariano_estrito'], ['Soja refogada'])
        self.assertEqual(itens['bebida'], ['Guaraná'])

    def test_jantar_saladas_e_feijao_deslocados(self):
        registro = {'data': '2026-11-09', 'refeicao': 'jantar', 'itens': {
            'salada_1': ['09/11/2026'],
            'salada_2': ['Chicória', 'Sunomono'],
            'acompanhamentos': ['Arroz branco e integral'],
            'sobremesa': ['Feijão preto', 'Melão'],
        }}
        itens = sanitizar_registro(registro)['itens']

        self.assertEqual(itens['salada_1'], ['Chicória'])
        self.assertEqual(itens['salada_2'], ['Sunomono'])
        self.assertEqual(itens['acompanhamentos'], ['Arroz branco e integral', 'Feijão preto'])
        self.assertEqual(itens['sobremesa'], ['Melão'])

    def test_cafe_desce_uma_linha_e_fruta_sai_do_rodape(self):
        registro = {'data': '2026-11-09', 'refeicao': 'cafe_da_manha', 'itens': {
            'bebidas': ['Café OU chá'],
            'gordura': ['PADRÃO', 'Frango desfiado Carne bovina moída Presunto'],
            'complemento_padrao': ['Ovos mexidos'],
            'complemento_ovolactovegetariano': ['ESTRITO Requeijão de ervas'],
            'complemento_vegetariano_estrito': ['Melancia'],
            'fruta': ['achocolatado, açúcar e adoçante. Cardápio'],
        }}
        itens = sanitizar_registro(registro)['itens']

        self.assertEqual(itens['complemento_padrao'], ['Frango desfiado', 'Carne bovina moída', 'Presunto'])
        self.assertEqual(itens['complemento_ovolactovegetariano'], ['Ovos mexidos'])
        self.assertEqual(itens['complemento_vegetariano_estrito'], ['Requeijão de ervas'])
        self.assertEqual(itens['fruta'], ['Melancia'])
        self.assertNotIn('gordura', itens)

    def test_idempotente(self):
        for registro in cp.carregar_cardapio():
            self.assertEqual(sanitizar_registro(registro), registro)

    def test_arquivo_sem_sobras(self):
        for registro in cp.carregar_cardapio():
            for lista in registro['itens'].values():
                for item in lista:
                    self.assertNotRegex(item, r'\d{2}/\d{2}/\d{4}')
                    self.assertNotIn('sujeito a alterações', item)
                    self.assertNotIn(item, ('ESTRITO', 'PADRÃO'))


class TestAtualizacaoAutomatica(unittest.TestCase):

    def setUp(self):
        import json, tempfile
        from datetime import date, timedelta
        from pathlib import Path
        from code_py import cardapio

        self.pasta = tempfile.TemporaryDirectory()
        self.arquivo = Path(self.pasta.name) / 'cardapio.json'
        self.originais = (cp.arquivo_cardapio, cp._ultima_tentativa_cardapio,
                          cp.atualizacao_automatica, cardapio.atualizar_cardapio)
        cp.arquivo_cardapio = self.arquivo
        cp._ultima_tentativa_cardapio = None
        cp.atualizacao_automatica = True

        self.chamadas = 0
        self.ontem = (date.today() - timedelta(days=1)).isoformat()
        self.amanha = (date.today() + timedelta(days=1)).isoformat()
        self.json = json
        self.cardapio = cardapio

        def baixar():
            self.chamadas += 1
            return []
        cardapio.atualizar_cardapio = baixar

    def tearDown(self):
        (cp.arquivo_cardapio, cp._ultima_tentativa_cardapio,
         cp.atualizacao_automatica, self.cardapio.atualizar_cardapio) = self.originais
        self.pasta.cleanup()

    def _gravar(self, data):
        self.arquivo.write_text(self.json.dumps(
            [{'data': data, 'refeicao': 'almoco', 'itens': {'bebida': ['Suco']}}]))

    def test_baixa_quando_cardapio_ja_passou(self):
        self._gravar(self.ontem)
        self.assertTrue(cp.garantir_cardapio_atualizado())
        self.assertEqual(self.chamadas, 1)

    def test_baixa_quando_nao_ha_arquivo(self):
        self.assertTrue(cp.garantir_cardapio_atualizado())

    def test_nao_baixa_se_ainda_vale(self):
        self._gravar(self.amanha)
        self.assertFalse(cp.garantir_cardapio_atualizado())
        self.assertEqual(self.chamadas, 0)

    def test_tenta_no_maximo_uma_vez_por_hora(self):
        self._gravar(self.ontem)
        cp.garantir_cardapio_atualizado()
        cp.garantir_cardapio_atualizado()
        self.assertEqual(self.chamadas, 1)

    def test_falha_nao_levanta_erro_e_mantem_o_antigo(self):
        self._gravar(self.ontem)

        def falhar():
            raise OSError('sem internet')
        self.cardapio.atualizar_cardapio = falhar

        self.assertFalse(cp.garantir_cardapio_atualizado())
        self.assertEqual(cp.datas_disponiveis(), [self.ontem])

    def test_respeita_o_desligamento(self):
        cp.atualizacao_automatica = False
        self.assertFalse(cp.garantir_cardapio_atualizado())
        self.assertEqual(self.chamadas, 0)
