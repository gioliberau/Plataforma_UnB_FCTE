# Rodar na raiz do projeto: python3 -m unittest discover -s tests
from io import BytesIO, StringIO
import unittest
from urllib.parse import urlencode

from code_py import banco, biblioteca, login, organizacoes as ops, turmas
from tests.base import TesteComBanco


def _bottle_disponivel():
    try:
        import bottle  # noqa: F401
        return True
    except ModuleNotFoundError:
        return False


class TestBackendCrudExtensoes(TesteComBanco):
    # Valida todas as novas operações CRUD adicionadas ao backend (independe do Bottle).

    def setUp(self):
        super().setUp()
        self.aluno = self.criar_perfil('ana@aluno.unb.br', 'discente', '52998224725')
        self.prof = self.criar_perfil('prof@unb.br', 'docente', '11144477735')

    def test_crud_oportunidades_docente_e_admin(self):
        vaga = ops.publicar(self.prof, 'Monitoria OO', 'monitoria', 'Desc', 'prof@unb.br')

        # Admin também pode editar e remover qualquer oportunidade.
        editada = ops.editar(self.admin, vaga.id, titulo='Monitoria OO Editada')
        self.assertEqual(editada.titulo, 'Monitoria OO Editada')

        # Docente também pode remover a própria publicação.
        ops.remover(self.prof, vaga.id)
        self.assertIsNone(ops.buscar(vaga.id))

    def test_crud_entidades_fixas(self):
        ent_id = ops.cadastrar_entidade_fixa(
            self.admin, 'Equipe Teste', 'equipe_competicao', 'https://instagram.com/equipeteste/'
        )
        ent = ops.buscar_entidade_fixa(ent_id)
        self.assertEqual(ent['nome'], 'Equipe Teste')

        atualizada = ops.editar_entidade_fixa(
            self.admin, ent_id, 'Equipe Editada', 'empresa_junior',
            'https://instagram.com/equipeeditada/', area='Software'
        )
        self.assertEqual(atualizada['nome'], 'Equipe Editada')
        self.assertEqual(atualizada['area'], 'Software')

        ops.remover_entidade_fixa(self.admin, ent_id)
        self.assertIsNone(ops.buscar_entidade_fixa(ent_id))

    def test_crud_livros_biblioteca(self):
        lib = biblioteca.Biblioteca()
        lib.cadastrar_livro(self.admin, 'Livro CRUD', 'Autor Teste', 'Software', 2)
        livro = lib.buscar('Livro CRUD')[0]

        editado = lib.editar_livro(self.admin, livro.id, 'Livro CRUD v2', 'Autor Teste', 'Engenharia', 3)
        self.assertEqual(editado.titulo, 'Livro CRUD v2')
        self.assertEqual(editado.exemplares, 3)

        # Empréstimo ativo bloqueia remoção e redução abaixo dos emprestados.
        lib.reservar(self.aluno, livro.id)
        with self.assertRaises(ValueError):
            lib.remover_livro(self.admin, livro.id)

        emp_id = lib.emprestimos_ativos(self.aluno)[0].id
        lib.devolver(self.aluno, emp_id)

        lib.remover_livro(self.admin, livro.id)
        self.assertEqual(lib.buscar('Livro CRUD v2'), [])

    def test_crud_usuarios_e_perfis(self):
        # Próprio usuário atualiza nome e curso.
        atualizado = banco.atualizar_perfil(
            self.aluno, self.aluno.email, nome='Ana Atualizada', curso_ou_area='Engenharia Aeroespacial'
        )
        self.assertEqual(atualizado.nome, 'Ana Atualizada')
        self.assertEqual(atualizado.curso, 'Engenharia Aeroespacial')

        # Discente não pode editar outro perfil.
        with self.assertRaises(PermissionError):
            banco.atualizar_perfil(self.aluno, self.prof.email, nome='Hack')

        # Admin lista acessos e remove usuário (mas não a si mesmo).
        acessos = login.listar_acessos(self.admin)
        self.assertEqual(len(acessos), 3)

        with self.assertRaises(ValueError):
            banco.remover_usuario(self.admin, self.admin.email)

        banco.remover_usuario(self.admin, self.aluno.email)
        self.assertIsNone(banco.buscar_perfil(self.aluno.email))
        self.assertEqual(len(login.listar_acessos(self.admin)), 2)

    def test_turmas_desmatricular_e_remover_oferta(self):
        chave = self.gravar_turma('2026.2', 'FGA0170', '01')
        turmas.atribuir_docente(self.admin, self.prof.id_user, chave)
        turmas.matricular(self.admin, self.aluno.id_user, chave)

        self.assertEqual(len(turmas.listar_matriculas_admin(self.admin)), 1)
        self.assertEqual(len(turmas.listar_ofertas_admin(self.admin)), 1)

        turmas.desmatricular(self.admin, self.aluno.id_user, chave)
        turmas.remover_oferta(self.admin, chave)

        self.assertEqual(turmas.listar_matriculas_admin(self.admin), [])
        self.assertEqual(turmas.listar_ofertas_admin(self.admin), [])


@unittest.skipUnless(_bottle_disponivel(), 'bottle não instalado')
class TestRotasBMVC(TesteComBanco):
    # Testa rotas WSGI reais do Bottle: login, acesso restrito e CRUDs completos.

    def setUp(self):
        super().setUp()
        import route
        from app.controllers.application import Application

        self.route = route
        self._ctl_original = route.ctl
        route.ctl = Application(garantir_exemplos=False)
        self.cookies = {}

        self.aluno = self.criar_perfil('ana@aluno.unb.br', 'discente', '52998224725')
        self.prof = self.criar_perfil('prof@unb.br', 'docente', '11144477735')
        self.chave_turma = self.gravar_turma('2026.2', 'FGA0170', '01')

    def tearDown(self):
        self.route.ctl = self._ctl_original
        super().tearDown()

    def _requisicao(self, metodo, caminho, dados=None, query=''):
        corpo = urlencode(dados or {}).encode('utf-8') if metodo == 'POST' else b''
        ambiente = {
            'REQUEST_METHOD': metodo,
            'PATH_INFO': caminho,
            'QUERY_STRING': query,
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8080',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': BytesIO(corpo),
            'wsgi.errors': StringIO(),
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'CONTENT_LENGTH': str(len(corpo)),
        }
        if metodo == 'POST':
            ambiente['CONTENT_TYPE'] = 'application/x-www-form-urlencoded; charset=utf-8'
        if self.cookies:
            ambiente['HTTP_COOKIE'] = '; '.join(f'{k}={v}' for k, v in self.cookies.items())

        status_holder = {}
        headers_holder = {}

        def start_response(status, headers, _exc_info=None):
            status_holder['code'] = int(status.split()[0])
            headers_holder['list'] = headers

        partes = list(self.route.app(ambiente, start_response))
        headers = headers_holder.get('list', [])
        for nome, valor in headers:
            if nome.lower() == 'set-cookie':
                par = valor.split(';', 1)[0]
                if '=' in par:
                    k, v = par.split('=', 1)
                    if 'max-age=0' in valor.lower() or v == '':
                        self.cookies.pop(k, None)
                    else:
                        self.cookies[k] = v

        local = next((v for n, v in headers if n.lower() == 'location'), '')
        html = b''.join(partes).decode('utf-8', errors='replace')
        return status_holder['code'], local, html

    def _fazer_login(self, email, senha):
        self.cookies.clear()
        return self._requisicao('POST', '/login', {'email': email, 'senha': senha})

    def test_acesso_restrito_sem_login_redireciona(self):
        for rota in ('/menu', '/perfil', '/oportunidades', '/organizacoes', '/biblioteca', '/turmas', '/usuarios', '/cardapio'):
            status, local, _ = self._requisicao('GET', rota)
            self.assertEqual(status, 303, f'{rota} deveria redirecionar sem login')
            self.assertTrue(local.endswith('/login'))

    def test_controle_de_acesso_admin_bloqueia_discente(self):
        self._fazer_login('ana@aluno.unb.br', 'senhanova123')
        status, local, _ = self._requisicao('GET', '/usuarios')
        self.assertEqual(status, 303)
        self.assertTrue(local.endswith('/menu'))

        # Discente consegue abrir menu e editar próprio perfil.
        status, _, html = self._requisicao('GET', '/menu')
        self.assertEqual(status, 200)
        self.assertIn('Pessoa Teste', html)

        status, local, _ = self._requisicao('POST', '/perfil/editar', {
            'nome': 'Ana Web',
            'curso_ou_area': 'Engenharia Eletrônica',
        })
        self.assertEqual(status, 303)
        self.assertEqual(banco.buscar_perfil('ana@aluno.unb.br').nome, 'Ana Web')

    def test_crud_completo_admin_via_http(self):
        status, local, _ = self._fazer_login('admin@unb.br', 'adminsenha')
        self.assertEqual(status, 303)
        self.assertTrue(local.endswith('/menu'))

        # 1) CRUD Oportunidades
        self._requisicao('POST', '/oportunidades/novo', {
            'titulo': 'Estágio Web',
            'categoria': 'estagio',
            'descricao': 'Vaga de estágio na FCTE',
            'contato': 'estagio@unb.br',
            'prazo': '',
        })
        status, _, html = self._requisicao('GET', '/oportunidades')
        self.assertEqual(status, 200)
        self.assertIn('Estágio Web', html)
        op = ops.listar_todas(self.admin)[0]
        status, _, _ = self._requisicao('GET', f'/oportunidades/{op.id}/editar')
        self.assertEqual(status, 200)
        self._requisicao('POST', f'/oportunidades/{op.id}/editar', {
            'titulo': 'Estágio Web Editado',
            'descricao': 'Descrição atualizada',
            'contato': 'estagio@unb.br',
            'prazo': '',
        })
        self.assertEqual(ops.buscar(op.id).titulo, 'Estágio Web Editado')
        self._requisicao('POST', f'/oportunidades/{op.id}/excluir')
        self.assertIsNone(ops.buscar(op.id))

        # 2) CRUD Organizações
        self._requisicao('POST', '/organizacoes/novo', {
            'nome': 'Equipe Web',
            'tipo': 'equipe_competicao',
            'instagram_link': 'https://instagram.com/equipeweb/',
            'area': 'Software',
        })
        status, _, html = self._requisicao('GET', '/organizacoes')
        self.assertEqual(status, 200)
        self.assertIn('Equipe Web', html)
        ent = [e for e in ops.listar_entidades_fixas(None) if e['nome'] == 'Equipe Web'][0]
        status, _, _ = self._requisicao('GET', f'/organizacoes/{ent["id"]}/editar')
        self.assertEqual(status, 200)
        self._requisicao('POST', f'/organizacoes/{ent["id"]}/editar', {
            'nome': 'Equipe Web v2',
            'tipo': 'empresa_junior',
            'instagram_link': 'https://instagram.com/equipeweb2/',
        })
        self.assertEqual(ops.buscar_entidade_fixa(ent['id'])['nome'], 'Equipe Web v2')
        self._requisicao('POST', f'/organizacoes/{ent["id"]}/excluir')
        self.assertIsNone(ops.buscar_entidade_fixa(ent['id']))

        # 3) CRUD Biblioteca
        self._requisicao('POST', '/biblioteca/novo', {
            'titulo': 'Arquitetura Limpa',
            'autores': 'Robert Martin',
            'area': 'Software',
            'exemplares': '4',
        })
        status, _, html = self._requisicao('GET', '/biblioteca')
        self.assertEqual(status, 200)
        self.assertIn('Arquitetura Limpa', html)
        lib = biblioteca.Biblioteca()
        livro = lib.buscar('Arquitetura Limpa')[0]
        status, _, _ = self._requisicao('GET', f'/biblioteca/{livro.id}/editar')
        self.assertEqual(status, 200)
        self._requisicao('POST', f'/biblioteca/{livro.id}/editar', {
            'titulo': 'Arquitetura Limpa 2ed',
            'autores': 'Robert Martin',
            'area': 'Software',
            'exemplares': '5',
        })
        self.assertEqual(lib.obter_livro(livro.id).exemplares, 5)
        self._requisicao('POST', f'/biblioteca/{livro.id}/excluir')
        self.assertEqual(lib.buscar('Arquitetura Limpa 2ed'), [])

        # 4) CRUD Turmas (matricular, atribuir docente, nota pelo docente, desmatricular, remover oferta)
        self._requisicao('POST', '/turmas/atribuir-docente', {
            'id_docente': self.prof.id_user,
            'chave': self.chave_turma,
        })
        self._requisicao('POST', '/turmas/matricular', {
            'matricula': self.aluno.id_user,
            'chave': self.chave_turma,
        })
        status, _, _ = self._requisicao('GET', '/turmas')
        self.assertEqual(status, 200)
        self.assertEqual(len(turmas.listar_matriculas_admin(self.admin)), 1)

        # Docente acessa /turmas e lança nota
        self._fazer_login('prof@unb.br', 'senhanova123')
        status, _, html = self._requisicao('GET', '/turmas')
        self.assertEqual(status, 200)
        self.assertIn('FGA0170', html)
        self._requisicao('POST', '/turmas/nota', {
            'chave': self.chave_turma,
            'matricula': self.aluno.id_user,
            'nota': '9.0',
        })
        self.assertEqual(turmas.alunos_da_turma(self.prof, self.chave_turma)[0]['nota'], 9.0)

        # Discente testa reserva, renovação e devolução na biblioteca + perfil
        self._fazer_login('ana@aluno.unb.br', 'senhanova123')
        status, _, _ = self._requisicao('GET', '/perfil')
        self.assertEqual(status, 200)
        primeiro_livro = lib.buscar()[0]
        self._requisicao('POST', f'/biblioteca/{primeiro_livro.id}/reservar')
        emp = lib.emprestimos_ativos(self.aluno)[0]
        self._requisicao('POST', f'/biblioteca/emprestimo/{emp.id}/renovar')
        self._requisicao('POST', f'/biblioteca/emprestimo/{emp.id}/devolver')
        self.assertEqual(lib.emprestimos_ativos(self.aluno), [])

        # Admin conclui desmatrícula, remoção de oferta e CRUD de usuários
        self._fazer_login('admin@unb.br', 'adminsenha')
        self._requisicao('POST', '/turmas/desmatricular', {
            'matricula': self.aluno.id_user,
            'chave': self.chave_turma,
        })
        self._requisicao('POST', '/turmas/remover-oferta', {'chave': self.chave_turma})
        self.assertEqual(turmas.listar_matriculas_admin(self.admin), [])

        # 5) CRUD Usuários
        self._requisicao('POST', '/usuarios/novo', {
            'email': 'novo@aluno.unb.br',
            'tipo': 'discente',
        })
        status, _, html = self._requisicao('GET', '/usuarios')
        self.assertEqual(status, 200)
        self.assertIn('novo@aluno.unb.br', html)

        status, _, _ = self._requisicao('GET', '/usuarios/editar', query='email=ana@aluno.unb.br')
        self.assertEqual(status, 200)
        self._requisicao('POST', '/usuarios/editar', {
            'email': 'ana@aluno.unb.br',
            'nome': 'Ana Editada Admin',
            'curso_ou_area': 'Engenharia Automotiva',
        })
        self.assertEqual(banco.buscar_perfil('ana@aluno.unb.br').nome, 'Ana Editada Admin')

        self._requisicao('POST', '/usuarios/excluir', {'email': 'novo@aluno.unb.br'})
        self.assertNotIn('novo@aluno.unb.br', [a.email for a in login.listar_acessos(self.admin)])

        # Renderização de /cardapio
        status, _, _ = self._requisicao('GET', '/cardapio')
        self.assertEqual(status, 200)

    def test_fluxo_primeiro_acesso_e_completar_perfil_web(self):
        senha_temp = login.gerar_acesso(self.admin, 'calouro@unb.br', 'discente')

        status, local, _ = self._fazer_login('calouro@unb.br', senha_temp)
        self.assertEqual(status, 303)
        self.assertTrue(local.endswith('/primeiro-acesso'))

        # Tentar burlar indo direto ao /menu deve redirecionar para /primeiro-acesso.
        status, local, _ = self._requisicao('GET', '/menu')
        self.assertEqual(status, 303)
        self.assertTrue(local.endswith('/primeiro-acesso'))

        # Troca senha na web -> redireciona para /completar-perfil.
        status, local, _ = self._requisicao('POST', '/primeiro-acesso', {
            'nova_senha': 'novasenha123',
            'confirmacao': 'novasenha123',
        })
        self.assertEqual(status, 303)
        self.assertTrue(local.endswith('/completar-perfil'))

        # Completa perfil na web -> redireciona para /menu.
        status, local, _ = self._requisicao('POST', '/completar-perfil', {
            'nome': 'Carlos Calouro',
            'cpf': '39053344705',
            'ano_entrada': '2026',
            'semestre_entrada': '1',
            'curso_ou_area': 'Engenharia de Software',
        })
        self.assertEqual(status, 303)
        self.assertTrue(local.endswith('/menu'))
        self.assertEqual(banco.buscar_perfil('calouro@unb.br').nome, 'Carlos Calouro')


if __name__ == '__main__':
    unittest.main()
