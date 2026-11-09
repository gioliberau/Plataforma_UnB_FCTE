# Rodar na raiz do projeto: python -m unittest discover -s tests
import tempfile
from datetime import date, timedelta
from pathlib import Path

from code_py import biblioteca
from base import TesteComBanco


class TestBiblioteca(TesteComBanco):

    def setUp(self):
        super().setUp()
        self.aluno = self.criar_perfil('ana@aluno.unb.br', 'discente', '52998224725')
        self.outro = self.criar_perfil('bia@aluno.unb.br', 'discente', '39053344705')
        self.prof = self.criar_perfil('prof@unb.br', 'docente', '11144477735')

        self.dia = date(2026, 11, 2)
        self.lib = biblioteca.Biblioteca(hoje=lambda: self.dia)

    def livro(self, termo):
        return self.lib.buscar(termo)[0]

    def test_busca_sem_acento_e_por_autor(self):
        self.assertTrue(self.lib.buscar('calculo stewart'))
        self.assertTrue(self.lib.buscar('SOMMERVILLE'))
        self.assertEqual(self.lib.buscar('livro que nao existe'), [])
        self.assertTrue(all(l.area == 'Software' for l in self.lib.buscar(area='Software')))

    def test_reserva_e_prazo(self):
        livro = self.livro('Sommerville')
        _, prazo = self.lib.reservar(self.aluno, livro.id)
        self.assertEqual(prazo, self.dia + timedelta(days=15))       # discente: 15 dias

        _, prazo_prof = self.lib.reservar(self.prof, livro.id)
        self.assertEqual(prazo_prof, self.dia + timedelta(days=30))  # docente: 30 dias

        self.assertEqual(self.lib.obter_livro(livro.id).disponiveis, livro.exemplares - 2)

    def test_reserva_invalida(self):
        livro = self.livro('Anderson')                                # 1 exemplar
        self.lib.reservar(self.aluno, livro.id)

        with self.assertRaises(ValueError):
            self.lib.reservar(self.aluno, livro.id)                   # repetido
        with self.assertRaises(ValueError):
            self.lib.reservar(self.outro, livro.id)                   # sem exemplar
        with self.assertRaises(ValueError):
            self.lib.reservar(self.aluno, 99999)                      # inexistente
        with self.assertRaises(PermissionError):
            self.lib.reservar(self.admin, livro.id)                   # admin não tem perfil

    def test_limite_de_livros(self):
        for livro in self.lib.buscar()[:10]:
            self.lib.reservar(self.aluno, livro.id)

        with self.assertRaises(ValueError):
            self.lib.reservar(self.aluno, self.lib.buscar()[10].id)

    def test_renovacao(self):
        livro = self.livro('Stewart')
        self.lib.reservar(self.aluno, livro.id)
        id_emp = self.lib.emprestimos_ativos(self.aluno)[0].id

        self.dia += timedelta(days=10)
        self.assertEqual(self.lib.renovar(self.aluno, id_emp), self.dia + timedelta(days=15))

        for _ in range(biblioteca.max_renovacoes - 1):
            self.lib.renovar(self.aluno, id_emp)

        with self.assertRaises(ValueError):
            self.lib.renovar(self.aluno, id_emp)                      # passou de 5

        with self.assertRaises(ValueError):
            self.lib.renovar(self.outro, id_emp)                      # não é dele

    def test_atraso_multa_e_bloqueio(self):
        livro = self.livro('Sommerville')
        self.lib.reservar(self.aluno, livro.id)
        id_emp = self.lib.emprestimos_ativos(self.aluno)[0].id

        self.dia += timedelta(days=15 + 4)                            # 4 dias de atraso
        atrasado = self.lib.emprestimos_ativos(self.aluno)[0]
        self.assertTrue(atrasado.atrasado)
        self.assertAlmostEqual(atrasado.multa, 4 * 0.90)

        with self.assertRaises(ValueError):
            self.lib.renovar(self.aluno, id_emp)
        with self.assertRaises(ValueError):
            self.lib.reservar(self.aluno, self.livro('Stewart').id)   # bloqueado com atraso

        self.assertAlmostEqual(self.lib.devolver(self.aluno, id_emp), 3.60)
        self.lib.reservar(self.aluno, self.livro('Stewart').id)       # liberado depois de devolver

    def test_historico(self):
        a, b = self.livro('Sommerville'), self.livro('Stewart')
        self.lib.reservar(self.aluno, a.id)
        id_a = self.lib.emprestimos_ativos(self.aluno)[0].id
        self.lib.devolver(self.aluno, id_a)

        self.dia += timedelta(days=1)
        self.lib.reservar(self.aluno, b.id)

        historico = self.lib.historico(self.aluno)
        self.assertEqual([e.livro_id for e in historico], [b.id, a.id])   # mais recente primeiro
        self.assertTrue(historico[0].ativo)
        self.assertFalse(historico[1].ativo)
        self.assertEqual(self.lib.historico(self.outro), [])

    def test_admin(self):
        self.lib.cadastrar_livro(self.admin, 'Livro Novo', 'Autor X', 'Geral', 2)
        self.assertTrue(self.lib.buscar('livro novo'))

        with self.assertRaises(ValueError):
            self.lib.cadastrar_livro(self.admin, 'Livro Novo', 'Autor X', 'Geral', 2)   # duplicado
        with self.assertRaises(PermissionError):
            self.lib.cadastrar_livro(self.prof, 'Y', 'Z', 'Geral', 1)

    def test_devolucao_devolve_ao_estoque(self):
        livro = self.livro('Anderson')                                # 1 exemplar
        self.assertEqual(self.lib.obter_livro(livro.id).disponiveis, 1)
 
        self.lib.reservar(self.aluno, livro.id)
        self.assertEqual(self.lib.obter_livro(livro.id).disponiveis, 0)
 
        self.lib.devolver(self.aluno, self.lib.emprestimos_ativos(self.aluno)[0].id)
        self.assertEqual(self.lib.obter_livro(livro.id).disponiveis, 1)     # voltou
        self.lib.reservar(self.outro, livro.id)                             # outro já pode pegar
 
    def _csv(self, texto, codificacao='utf-8-sig'):
        caminho = Path(tempfile.mkdtemp()) / 'acervo.csv'
        caminho.write_text(texto, encoding=codificacao)
        return caminho
 
 
    def test_importar_csv(self):
        antes = len(self.lib.buscar())
        caminho = self._csv('titulo;autores;area;exemplares\nLivro CSV;Autor Y;Geral;3\nEngenharia de Software;Ian Sommerville;Software;9\n')
        self.assertEqual(self.lib.importar_csv(self.admin, caminho), (1, 1))     # 1 novo, 1 atualizado
        self.assertEqual(len(self.lib.buscar()), antes + 1)
        self.assertEqual(self.livro('Livro CSV').exemplares, 3)
        self.assertEqual(self.livro('Sommerville').exemplares, 9)
 

    def test_importar_csv_virgula_e_excel(self):
        caminho = self._csv('Título,Autores,Área,Exemplares\nCálculo Z,João,Matemática,2\n', 'latin-1')
        self.assertEqual(self.lib.importar_csv(self.admin, caminho), (1, 0))
 

    def test_importar_csv_invalido(self):
        antes = len(self.lib.buscar())
        ruim = self._csv('titulo;autores;area;exemplares\nOK;A;G;1\nSem numero;A;G;muitos\n')
 
        with self.assertRaises(ValueError):
            self.lib.importar_csv(self.admin, ruim)
        self.assertEqual(len(self.lib.buscar()), antes)                  # tudo ou nada
 
        with self.assertRaises(ValueError):
            self.lib.importar_csv(self.admin, self._csv('a;b\n1;2\n'))  # faltam colunas
        with self.assertRaises(ValueError):
            self.lib.importar_csv(self.admin, '/nao/existe.csv')
        with self.assertRaises(PermissionError):
            self.lib.importar_csv(self.prof, ruim)