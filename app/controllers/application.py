import uuid
from bottle import redirect, request, template

from code_py import banco, exemplos, login, turmas
from code_py.user import semestre_atual


def _garantir_usuarios_exemplo():
    # Garante que os usuários e o histórico de exemplo existam no banco.
    try:
        exemplos.criar_exemplos()
    except (ValueError, PermissionError):
        pass


# ============================= { CONTROLADOR BMVC } ============================= #

class Application:

    def __init__(self):
        self.pages = {
            'login': self.login,
            'menu': self.menu,
        }
        self.__sessoes = {}
        _garantir_usuarios_exemplo()

    def render(self, page):
        content = self.pages.get(page, self.login)
        return content()

    def get_session_id(self):
        return request.get_cookie('session_id')

    def usuario_atual(self):
        session_id = self.get_session_id()
        return self.__sessoes.get(session_id)

    def autenticar_usuario(self, email, senha):
        conta = login.autenticar(email, senha)
        if conta is None:
            return None, 'credenciais'

        if conta.precisa_trocar_senha:
            return None, 'trocar_senha'

        perfil = None if conta.eh_admin else banco.buscar_perfil(conta.email)

        self.encerrar_sessao()
        session_id = str(uuid.uuid4())
        self.__sessoes[session_id] = self.__montar_dados_usuario(conta, perfil)
        return session_id, None

    def encerrar_sessao(self):
        session_id = self.get_session_id()
        if session_id in self.__sessoes:
            del self.__sessoes[session_id]

    @staticmethod
    def __montar_dados_usuario(conta, perfil):
        ano_atual, sem_atual = semestre_atual()
        tipo = perfil.tipo_usuario if perfil else conta.tipo_usuario

        dados = {
            'nome': perfil.nome if perfil else ('Administrador FCTE' if conta.eh_admin else conta.email),
            'email': conta.email,
            'tipo_usuario': tipo,
            'matricula': perfil.id_user if perfil else '—',
            'cpf': (perfil.cpf or '—') if perfil else '—',
            'curso_ou_area': (
                perfil.curso_ou_area
                if perfil
                else ('Administração do Sistema' if conta.eh_admin else 'Perfil não completado')
            ),
            'ingresso': (
                f'{perfil.ano_entrada}.{perfil.semestre_entrada}'
                if perfil and perfil.ano_entrada and perfil.semestre_entrada
                else '—'
            ),
            'semestre_atual': f'{ano_atual}.{sem_atual}',
            'ira': '—',
            'mp': '—',
            'creditos': 0,
            'turmas': [],
        }

        if tipo == 'discente' and perfil is not None:
            valor_mp = turmas.mp(perfil)
            valor_ira = turmas.ira(perfil)
            matriculas = turmas.turmas_do_discente(perfil)

            dados['mp'] = 'sem notas' if valor_mp is None else f'{valor_mp:.2f}'
            dados['ira'] = 'sem notas' if valor_ira is None else f'{valor_ira:.2f}'
            dados['creditos'] = sum(m.creditos for m in matriculas if m.aprovado)
            dados['turmas'] = [
                {
                    'codigo': m.turma['codigo_disciplina'],
                    'disciplina': m.turma['nome_disciplina'],
                    'periodo': m.turma['periodo'],
                    'creditos': m.creditos,
                    'resultado': 'Cursando' if m.nota is None else f'{m.nota:.1f} ({m.mencao})',
                }
                for m in matriculas
            ]

        elif tipo == 'docente' and perfil is not None:
            ofertadas = turmas.turmas_do_docente(perfil)
            dados['creditos'] = turmas.creditos_ofertados(perfil)
            dados['turmas'] = [
                {
                    'codigo': t['codigo_disciplina'],
                    'disciplina': t['nome_disciplina'],
                    'turma': f"{t['numero_turma']} ({t['periodo']})",
                    'creditos': (t.get('carga_horaria') or 0) // turmas.horas_por_credito,
                    'horario': t['horario'],
                }
                for t in ofertadas
            ]

        return dados

    # ========== { PÁGINAS } ========== #

    def login(self):
        if self.usuario_atual():
            return redirect('/menu')

        erro = request.query.get('erro')
        return template('app/views/html/login', erro=erro)

    def menu(self):
        usuario = self.usuario_atual()
        if not usuario:
            return redirect('/login')

        return template('app/views/html/menu', usuario=usuario)
