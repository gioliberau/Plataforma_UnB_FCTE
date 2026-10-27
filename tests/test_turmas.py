# Rodar na raiz do projeto: python -m unittest discover -s tests
from code_py import turmas
from base import TesteComBanco


class TestTurmas(TesteComBanco):

    def setUp(self):
        super().setUp()
        self.aluno = self.criar_perfil('ana@aluno.unb.br', 'discente', '52998224725')
        self.prof = self.criar_perfil('prof@unb.br', 'docente', '11144477735')
        self.outro_prof = self.criar_perfil('outro@unb.br', 'docente', '39053344705')

        self.oo = self.gravar_turma('2024.1', 'FGA0158', '01', carga=60)      # 4 créditos
        self.calc = self.gravar_turma('2024.2', 'FGA0160', '01', carga=90)    # 6 créditos

        turmas.atribuir_docente(self.admin, self.prof.id_user, self.oo)
        turmas.atribuir_docente(self.admin, self.prof.id_user, self.calc)
        turmas.matricular(self.admin, self.aluno.id_user, self.oo)
        turmas.matricular(self.admin, self.aluno.id_user, self.calc)

    def test_mencao(self):
        self.assertEqual(
            [turmas.mencao(n) for n in (10, 9, 8.9, 7, 5, 4.9, 3, 2.9, 0.1, 0)],
            ['SS', 'SS', 'MS', 'MS', 'MM', 'MI', 'MI', 'II', 'II', 'SR']
        )

    def test_matricula(self):
        self.assertEqual(len(turmas.turmas_do_discente(self.aluno)), 2)
        self.assertEqual(len(turmas.turmas_do_docente(self.prof)), 2)

        with self.assertRaises(ValueError):
            turmas.matricular(self.admin, self.aluno.id_user, self.oo)          # repetida

        with self.assertRaises(ValueError):
            turmas.matricular(self.admin, '999999999', self.oo)                 # aluno inexistente

        with self.assertRaises(ValueError):
            turmas.matricular(self.admin, self.prof.id_user, self.oo)           # docente não é aluno

        with self.assertRaises(ValueError):
            turmas.matricular(self.admin, self.aluno.id_user, '2024.1|FGA9999|01')  # turma inexistente

        with self.assertRaises(PermissionError):
            turmas.matricular(self.prof, self.aluno.id_user, self.oo)           # só admin

    def test_notas_e_medias(self):
        self.assertIsNone(turmas.mp(self.aluno))

        turmas.lancar_nota(self.prof, self.oo, self.aluno.id_user, 9.5)        # SS, peso 5
        turmas.lancar_nota(self.prof, self.calc, self.aluno.id_user, 6)        # MM, peso 3

        # MP = (5*4 + 3*6) / 10; IRA pesa também o semestre (1º e 2º): (5*4*1 + 3*6*2) / (4 + 12)
        self.assertAlmostEqual(turmas.mp(self.aluno), 3.8)
        self.assertAlmostEqual(turmas.ira(self.aluno), 3.5)

        aprovacoes = {m.turma['codigo_disciplina']: m.aprovado for m in turmas.turmas_do_discente(self.aluno)}
        self.assertEqual(aprovacoes, {'FGA0158': True, 'FGA0160': True})

        alunos = turmas.alunos_da_turma(self.prof, self.oo)
        self.assertEqual([(a['matricula'], a['nota']) for a in alunos], [(self.aluno.id_user, 9.5)])

    def test_nota_recusada(self):
        with self.assertRaises(PermissionError):
            turmas.lancar_nota(self.outro_prof, self.oo, self.aluno.id_user, 8)    # turma de outro

        for nota in (-1, 10.5, '8', True):
            with self.assertRaises(ValueError):
                turmas.lancar_nota(self.prof, self.oo, self.aluno.id_user, nota)

    def test_creditos_ofertados(self):
        self.assertEqual(turmas.creditos_ofertados(self.prof, 2024, 1), 4)
        self.assertEqual(turmas.creditos_ofertados(self.prof, 2024, 2), 6)
        self.assertEqual(turmas.creditos_ofertados(self.outro_prof, 2024, 1), 0)
