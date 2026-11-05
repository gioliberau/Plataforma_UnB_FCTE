# Testa a leitura dos PDFs da SAA e a atualização do calendário (sem internet: downloads simulados).
import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from code_py import calendario, consultas_publicas as cp

# Texto real do PDF "Calendário de Matrícula 2026.2" (SAA/UnB, 25/06/2026), com a ordem bagunçada de sempre.
TEXTO_2026_2 = """
Período para solicitação de matrícula de 07h do dia 27/07 até 23h59 do dia 29/07/2026 no SIGAA > Portal Discente > Ensino > Matrícula on27/07 a 29/07/2026 Estudante line > Realizar Matrícula.
03/08 e 04/08/2026 Coordenação Solicitação de rematrícula em turmas que não permitem matrícula on-line de 07h do dia 03/08 até 23h59 do dia 04/08/2026.
31/07/2026 STI Resultado da matrícula até às 12h do dia 31/07/2026.
Período para solicitação de rematrícula de 07h do dia 03/08 até 23h59 do dia 04/08/2026 no SIGAA > Portal Discente > Ensino > Matrícula
on-line > Realizar Matrícula.
06/08/2026
STI
Resultado da rematrícula até às 12h do dia 06/08/2026.
Matrícula Extraordinária de 10h do dia 07/08 até 23h59 do dia 14/08/2026 no SIGAA > Portal Discente > Ensino > Matrícula on-line >
CALENDÁRIO DE MATRÍCULA EM DISCIPLINA 2026.2
Período de aulas:
Início: 10/08/2026
Término: 14/12/2026
"""

HTML_SAA = """
<a href="/wp-content/uploads/a.pdf">Calendário de Matrícula 2026.1 (23/02/2026)</a>
<a href="/wp-content/uploads/b15.pdf">Calendário de Matrícula 2026.2 (15/06/2026)</a>
<a href="/wp-content/uploads/b25.pdf">Calendário de Matrícula 2026.2 (25/06/2026)</a>
<a href="/wp-content/uploads/c.pdf">Calendário por Atividades 2026.2 (15/06/2026)</a>
<a href="/outra-pagina">Calendário de Matrícula 2026.3</a>
"""


class TestCalendario(unittest.TestCase):

    def setUp(self):
        # Trabalha numa cópia do JSON para não mexer no arquivo real.
        self.pasta = Path(tempfile.mkdtemp())
        self.json = self.pasta / 'calendario.json'
        shutil.copy(cp.arquivo_calendario, self.json)

        self.originais = (calendario.arquivo_calendario, cp.arquivo_calendario,
                          calendario.baixar_conteudo, calendario.extrair_texto_pdf)
        calendario.arquivo_calendario = cp.arquivo_calendario = self.json

    def tearDown(self):
        (calendario.arquivo_calendario, cp.arquivo_calendario,
         calendario.baixar_conteudo, calendario.extrair_texto_pdf) = self.originais

    def simular_site(self, texto_pdf):
        # Só o PDF de 2026.2 (b25.pdf) traz o texto dado; o de 2026.1 vem sem datas legíveis.
        calendario.baixar_conteudo = lambda url: HTML_SAA.encode() if url == calendario.pag_calendario else url.encode()
        calendario.extrair_texto_pdf = lambda conteudo: texto_pdf if conteudo.endswith(b'b25.pdf') else 'sem datas'

    def test_ler_eventos(self):
        periodo, eventos = calendario.ler_eventos(TEXTO_2026_2)
        por_descricao = {e['descricao']: (e['inicio'], e['fim']) for e in eventos}

        self.assertEqual(periodo, '2026.2')
        self.assertEqual(por_descricao['Solicitação de matrícula (SIGAA)'], ('2026-07-27', '2026-07-29'))
        self.assertEqual(por_descricao['Rematrícula (SIGAA)'], ('2026-08-03', '2026-08-04'))
        self.assertEqual(por_descricao['Matrícula extraordinária'], ('2026-08-07', '2026-08-14'))
        self.assertEqual(por_descricao['Resultado da matrícula (até 12h)'], ('2026-07-31', None))
        self.assertEqual(por_descricao['Resultado da rematrícula (até 12h)'], ('2026-08-06', None))
        self.assertEqual(por_descricao['Período de aulas'], ('2026-08-10', '2026-12-14'))

    def test_ler_eventos_texto_desconhecido(self):
        self.assertEqual(calendario.ler_eventos('texto qualquer sem datas'), (None, []))

    def test_escolhe_pdf_mais_novo(self):
        pdfs = calendario.encontrar_pdfs_matricula(HTML_SAA)
        self.assertEqual(set(pdfs), {'2026.1', '2026.2'})
        self.assertTrue(pdfs['2026.2'].endswith('/wp-content/uploads/b25.pdf'))   # versão de 25/06, não a de 15/06

    def test_atualizar_troca_so_o_que_leu(self):
        # Muda uma data no JSON, para ver o PDF corrigir. A "menção final" não está no PDF e deve continuar.
        dados = json.loads(self.json.read_text(encoding='utf-8'))
        for e in dados['eventos']:
            if e['periodo'] == '2026.2' and e['descricao'] == 'Período de aulas':
                e['fim'] = '2026-01-01'
        self.json.write_text(json.dumps(dados), encoding='utf-8')

        self.simular_site(TEXTO_2026_2)
        self.assertEqual(calendario.atualizar_calendario(), 6)

        eventos = cp.eventos_do_periodo('2026.2')
        aulas = [e for e in eventos if e['descricao'] == 'Período de aulas'][0]
        self.assertEqual(aulas['fim'], '2026-12-14')
        self.assertTrue(any('menção final' in e['descricao'] for e in eventos))
        self.assertEqual(len(eventos), 7)                                       # sem duplicar
        self.assertIn('atualizado_em', json.loads(self.json.read_text(encoding='utf-8')))

    def test_layout_mudou_mantem_arquivo_antigo(self):
        antes = self.json.read_text(encoding='utf-8')
        self.simular_site('PDF com outro layout, sem as frases de sempre')

        with self.assertRaises(RuntimeError):
            calendario.atualizar_calendario()

        self.assertEqual(self.json.read_text(encoding='utf-8'), antes)

    def test_so_admin_atualiza(self):
        with self.assertRaises(PermissionError):
            cp.atualizar_calendario(None)

    def test_formatar_evento_continua_funcionando(self):
        evento = cp.eventos_do_periodo('2026.2')[0]
        self.assertIn('já passou', cp.formatar_evento(evento, date(2027, 1, 1)))

    @unittest.skipUnless(__import__('importlib').util.find_spec('reportlab'), 'reportlab não instalado')
    def test_pdf_de_verdade(self):
        # Cria um PDF com o texto acima e passa pelo pdfplumber, para testar a extração de ponta a ponta.
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        caminho = self.pasta / 'teste.pdf'
        pdf = canvas.Canvas(str(caminho), pagesize=A4)
        y = 800
        for linha in TEXTO_2026_2.strip().splitlines():
            pdf.setFont('Helvetica', 6)
            pdf.drawString(10, y, linha)
            y -= 10
        pdf.save()

        periodo, eventos = calendario.ler_eventos(calendario.extrair_texto_pdf(caminho.read_bytes()))
        self.assertEqual(periodo, '2026.2')
        self.assertEqual(len(eventos), 6)