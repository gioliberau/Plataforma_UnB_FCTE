# Rodar na raiz do projeto: python -m unittest discover -s tests
from code_py import organizacoes as ops
from base import TesteComBanco


class TestOrganizacoes(TesteComBanco):

    def setUp(self):
        super().setUp()
        self.aluno = self.criar_perfil('ana@aluno.unb.br', 'discente', '52998224725')
        self.prof = self.criar_perfil('prof@unb.br', 'docente', '11144477735')

    def test_monitoria_e_interesse(self):
        vaga = ops.publicar(self.prof, 'Monitoria de OO', 'monitoria', 'Ajudar a turma', 'prof@unb.br')

        self.assertEqual(vaga.autor_id, self.prof.id_user)
        self.assertEqual([o.id for o in ops.listar_para_discente(self.aluno, 'monitoria')], [vaga.id])

        ops.demonstrar_interesse(self.aluno, vaga.id)
        self.assertEqual(ops.contar_interessados(vaga.id), 1)
        self.assertEqual(len(ops.listar_interessados(self.prof, vaga.id)), 1)

    def test_extensao_e_admin(self):
        ops.publicar(self.prof, 'Extensão', 'projeto_extensao', 'Projeto', 'prof@unb.br')
        ops.publicar(self.admin, 'Estágio', 'estagio', 'Vaga', 'rh@unb.br')

        self.assertEqual([o.titulo for o in ops.listar_extensao(self.prof)], ['Extensão'])
        self.assertEqual(len(ops.listar_todas(self.admin)), 2)

        editada = ops.editar(self.prof, ops.listar_minhas(self.prof)[0].id, titulo='Extensão 2')
        self.assertEqual(editada.titulo, 'Extensão 2')

    def test_entidade_fixa(self):
        with self.assertRaises(PermissionError):
            ops.cadastrar_entidade_fixa(self.prof, 'X', 'atletica', 'https://instagram.com/x/')

        ops.cadastrar_entidade_fixa(self.admin, 'X', 'atletica', 'https://instagram.com/x/')
        self.assertIn('X', [e['nome'] for e in ops.listar_entidades_fixas(self.aluno, 'atletica')])
