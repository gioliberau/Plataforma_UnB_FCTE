from datetime import date, datetime, timedelta
import json
import re
from urllib.parse import quote
import uuid

from bottle import redirect, request, template

from code_py import (
    banco,
    biblioteca as bib,
    consultas_publicas as cp,
    exemplos,
    login,
    organizacoes as ops,
    turmas as tr,
)
from code_py.horarios import legivel
from code_py.system import SistemaFCTE
from code_py.user import cursos_disponiveis, semestre_atual


# ============================= { AUXILIARES } ============================= #

def _garantir_usuarios_exemplo():
    # Garante que os usuários e o histórico de exemplo existam no banco.
    try:
        exemplos.criar_exemplos()
    except (ValueError, PermissionError):
        pass


def _converter_data_iso(texto):
    # Aceita 'AAAA-MM-DD' (input type="date") ou 'DD/MM/AAAA'. Vazio -> None.
    valor = (texto or '').strip()
    if not valor:
        return None
    for formato in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue
    raise ValueError('Data inválida. Use AAAA-MM-DD ou DD/MM/AAAA.')


def _parsear_periodo(texto):
    valor = (texto or '').strip()
    if not valor:
        return None, None
    match = re.fullmatch(r'(\d{4})\.([12])', valor)
    if not match:
        raise ValueError('Período inválido. Use o formato AAAA.S (ex.: 2026.2).')
    return int(match.group(1)), int(match.group(2))


def _data_br(valor):
    if not valor:
        return '—'
    if isinstance(valor, date):
        return valor.strftime('%d/%m/%Y')
    texto = str(valor).strip()[:10]
    try:
        return date.fromisoformat(texto).strftime('%d/%m/%Y')
    except ValueError:
        return texto


# ============================= { CONTROLADOR BMVC } ============================= #

class Application:

    def __init__(self, garantir_exemplos=True):
        self.__sessoes = {}
        self.__clientes_ws = set()
        self.__sistema = SistemaFCTE()
        self.__biblioteca = bib.Biblioteca()
        if garantir_exemplos:
            _garantir_usuarios_exemplo()

    # ========== { WEBSOCKET TEMPO REAL } ========== #

    def sessao_valida_ws(self):
        return self.usuario_atual() is not None

    def registrar_ws(self, ws):
        self.__clientes_ws.add(ws)

    def remover_ws(self, ws):
        self.__clientes_ws.discard(ws)

    def notificar_ws(self, canal, mensagem):
        carga = json.dumps({'canal': canal, 'mensagem': mensagem}, ensure_ascii=False)
        desconectados = []
        for ws in list(self.__clientes_ws):
            try:
                ws.send(carga)
            except Exception:
                desconectados.append(ws)
        for ws in desconectados:
            self.__clientes_ws.discard(ws)

    # ========== { SESSÃO E FLASH } ========== #

    duracao_sessao = timedelta(hours=1)

    def get_session_id(self):
        return request.get_cookie('session_id')

    def _limpar_sessoes_vencidas(self):
        agora = datetime.now()
        vencidas = [sid for sid, item in self.__sessoes.items() if item['expira_em'] <= agora]
        for sid in vencidas:
            del self.__sessoes[sid]

    def _sessao_bruta(self):
        session_id = self.get_session_id()
        if not session_id:
            return None
        sessao = self.__sessoes.get(session_id)
        if not sessao:
            return None
        if sessao['expira_em'] <= datetime.now():
            del self.__sessoes[session_id]
            return None
        return sessao

    def revogar_sessoes_email(self, email):
        alvo = (email or '').strip().casefold()
        remover = [
            sid for sid, item in self.__sessoes.items()
            if item['conta'].email.casefold() == alvo
        ]
        for sid in remover:
            del self.__sessoes[sid]

    def definir_flash(self, tipo, texto):
        sessao = self._sessao_bruta()
        if sessao is not None:
            sessao['flash'] = {'tipo': tipo, 'texto': texto}

    def consumir_flash(self):
        sessao = self._sessao_bruta()
        if sessao is None:
            return None
        flash = sessao.get('flash')
        sessao['flash'] = None
        return flash

    def usuario_atual(self):
        sessao = self._sessao_bruta()
        if not sessao:
            return None
        conta = sessao['conta']
        if conta.precisa_trocar_senha:
            return None
        perfil = None if conta.eh_admin else banco.buscar_perfil(conta.email)
        if not conta.eh_admin and perfil is None:
            return None
        return self.__montar_dados_usuario(conta, perfil)

    def _exigir_sessao_ativa(self):
        sessao = self._sessao_bruta()
        if not sessao:
            redirect('/login')

        conta = sessao['conta']
        if conta.precisa_trocar_senha:
            redirect('/primeiro-acesso')

        perfil = None if conta.eh_admin else banco.buscar_perfil(conta.email)
        if not conta.eh_admin and perfil is None:
            redirect('/completar-perfil')

        return conta, perfil, self.__montar_dados_usuario(conta, perfil)

    def _exigir_admin_web(self):
        conta, perfil, usuario = self._exigir_sessao_ativa()
        if not conta.eh_admin:
            self.definir_flash('erro', 'Acesso restrito a administradores.')
            redirect('/menu')
        return conta, perfil, usuario

    def _contexto_base(self, usuario, pagina_ativa):
        return {
            'usuario': usuario,
            'pagina_ativa': pagina_ativa,
            'flash': self.consumir_flash(),
            'data_br': _data_br,
            'quote_url': lambda valor: quote(str(valor), safe=''),
        }

    # ========== { AUTENTICAÇÃO } ========== #

    def autenticar_usuario(self, email, senha):
        conta = login.autenticar(email, senha)
        if conta is None:
            return None, 'credenciais', None

        self.encerrar_sessao()
        self._limpar_sessoes_vencidas()
        session_id = str(uuid.uuid4())
        self.__sessoes[session_id] = {
            'conta': conta,
            'expira_em': datetime.now() + self.duracao_sessao,
            'flash': None,
        }

        if conta.precisa_trocar_senha:
            return session_id, None, '/primeiro-acesso'

        if not conta.eh_admin and banco.buscar_perfil(conta.email) is None:
            return session_id, None, '/completar-perfil'

        return session_id, None, '/menu'

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
            'eh_admin': conta.eh_admin,
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
            valor_mp = tr.mp(perfil)
            valor_ira = tr.ira(perfil)
            matriculas = tr.turmas_do_discente(perfil)

            dados['mp'] = 'sem notas' if valor_mp is None else f'{valor_mp:.2f}'
            dados['ira'] = 'sem notas' if valor_ira is None else f'{valor_ira:.2f}'
            dados['creditos'] = sum(m.creditos for m in matriculas if m.aprovado)
            dados['turmas'] = [
                {
                    'codigo': m.turma['codigo_disciplina'],
                    'disciplina': m.turma['nome_disciplina'],
                    'periodo': m.turma['periodo'],
                    'creditos': m.creditos,
                    'horario': legivel(m.turma.get('horario', '')),
                    'resultado': 'Cursando' if m.nota is None else f'{m.nota:.1f} ({m.mencao})',
                }
                for m in matriculas
            ]

        elif tipo == 'docente' and perfil is not None:
            ofertadas = tr.turmas_do_docente(perfil)
            dados['creditos'] = tr.creditos_ofertados(perfil)
            dados['turmas'] = [
                {
                    'codigo': t['codigo_disciplina'],
                    'disciplina': t['nome_disciplina'],
                    'turma': f"{t['numero_turma']} ({t['periodo']})",
                    'creditos': (t.get('carga_horaria') or 0) // tr.horas_por_credito,
                    'horario': legivel(t.get('horario', '')),
                }
                for t in ofertadas
            ]

        return dados

    # ========== { PÁGINAS DE ACESSO } ========== #

    def login(self):
        sessao = self._sessao_bruta()
        if sessao:
            conta = sessao['conta']
            if conta.precisa_trocar_senha:
                return redirect('/primeiro-acesso')
            if not conta.eh_admin and banco.buscar_perfil(conta.email) is None:
                return redirect('/completar-perfil')
            return redirect('/menu')

        erro = request.query.getunicode('erro')
        return template('app/views/html/login', erro=erro)

    def form_primeiro_acesso(self):
        sessao = self._sessao_bruta()
        if not sessao:
            return redirect('/login')
        conta = sessao['conta']
        if not conta.precisa_trocar_senha:
            return redirect('/menu')
        return template(
            'app/views/html/primeiro_acesso',
            email=conta.email,
            flash=self.consumir_flash(),
        )

    def acao_primeiro_acesso(self):
        sessao = self._sessao_bruta()
        if not sessao:
            return redirect('/login')
        conta = sessao['conta']
        nova = request.forms.getunicode('nova_senha') or ''
        conf = request.forms.getunicode('confirmacao') or ''

        if nova != conf:
            self.definir_flash('erro', 'As senhas digitadas não conferem.')
            return redirect('/primeiro-acesso')

        try:
            nova_conta = login.definir_nova_senha_primeiro_acesso(conta, nova)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/primeiro-acesso')

        sessao['conta'] = nova_conta

        if not nova_conta.eh_admin and banco.buscar_perfil(nova_conta.email) is None:
            self.definir_flash('sucesso', 'Senha atualizada! Complete seu cadastro para continuar.')
            return redirect('/completar-perfil')

        self.definir_flash('sucesso', 'Senha atualizada com sucesso!')
        return redirect('/menu')

    def form_completar_perfil(self):
        sessao = self._sessao_bruta()
        if not sessao:
            return redirect('/login')
        conta = sessao['conta']
        if conta.precisa_trocar_senha:
            return redirect('/primeiro-acesso')
        if conta.eh_admin or banco.buscar_perfil(conta.email) is not None:
            return redirect('/menu')

        ano_padrao, sem_padrao = semestre_atual()
        return template(
            'app/views/html/completar_perfil',
            conta=conta,
            cursos=cursos_disponiveis,
            ano_padrao=ano_padrao,
            sem_padrao=sem_padrao,
            flash=self.consumir_flash(),
        )

    def acao_completar_perfil(self):
        sessao = self._sessao_bruta()
        if not sessao:
            return redirect('/login')
        conta = sessao['conta']
        nome = request.forms.getunicode('nome') or ''
        cpf = ''.join(ch for ch in (request.forms.getunicode('cpf') or '') if ch.isdigit())
        curso_ou_area = request.forms.getunicode('curso_ou_area') or ''

        try:
            ano = int((request.forms.getunicode('ano_entrada') or '').strip())
            semestre = int((request.forms.getunicode('semestre_entrada') or '').strip())
            perfil = banco.cadastrar_perfil(conta, nome, cpf, ano, semestre, curso_ou_area)
        except ValueError as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/completar-perfil')

        self.definir_flash('sucesso', f'Cadastro concluído! Sua matrícula é {perfil.id_user}.')
        return redirect('/menu')

    # ========== { MENU PRINCIPAL } ========== #

    def menu(self):
        conta, perfil, usuario = self._exigir_sessao_ativa()
        ctx = self._contexto_base(usuario, 'menu')
        if conta.eh_admin:
            ctx['resumo_admin'] = {
                'discentes': len(banco.listar_perfis('discente')),
                'docentes': len(banco.listar_perfis('docente')),
                'oportunidades': len(ops.listar_todas(conta)),
                'livros': len(self.__biblioteca.buscar()),
            }
        return template('app/views/html/menu', **ctx)

    # ========== { CRUD: MEU PERFIL } ========== #

    def perfil(self):
        conta, perfil, usuario = self._exigir_sessao_ativa()
        ctx = self._contexto_base(usuario, 'perfil')
        ctx.update({
            'perfil': perfil,
            'cursos': cursos_disponiveis,
        })
        return template('app/views/html/perfil', **ctx)

    def editar_perfil(self):
        conta, perfil, _ = self._exigir_sessao_ativa()
        if conta.eh_admin or perfil is None:
            self.definir_flash('erro', 'Contas de administrador não possuem perfil acadêmico editável.')
            return redirect('/perfil')

        nome = request.forms.getunicode('nome') or ''
        curso_ou_area = request.forms.getunicode('curso_ou_area') or ''
        try:
            banco.atualizar_perfil(conta, conta.email, nome=nome, curso_ou_area=curso_ou_area)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/perfil')

        self.definir_flash('sucesso', 'Dados cadastrais atualizados com sucesso!')
        return redirect('/perfil')

    def trocar_senha_perfil(self):
        conta, _, _ = self._exigir_sessao_ativa()
        senha_atual = request.forms.getunicode('senha_atual') or ''
        nova = request.forms.getunicode('nova_senha') or ''
        conf = request.forms.getunicode('confirmacao') or ''

        if nova != conf:
            self.definir_flash('erro', 'A confirmação da nova senha não confere.')
            return redirect('/perfil')

        try:
            nova_conta = login.trocar_senha(conta.email, senha_atual, nova)
        except ValueError as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/perfil')

        self._sessao_bruta()['conta'] = nova_conta
        self.definir_flash('sucesso', 'Senha alterada com sucesso!')
        return redirect('/perfil')

    # ========== { CRUD: OPORTUNIDADES } ========== #

    def oportunidades(self):
        conta, perfil, usuario = self._exigir_sessao_ativa()
        ctx = self._contexto_base(usuario, 'oportunidades')

        categoria = (request.query.getunicode('categoria') or '').strip() or None
        ver_int = request.query.getunicode('interessados')
        interessados_lista = None
        oportunidade_foco = None

        if conta.eh_admin:
            lista = ops.listar_todas(conta)
            if categoria:
                lista = [o for o in lista if o.categoria == categoria]
            autor = conta
        elif perfil.tipo_usuario == 'docente':
            lista = ops.listar_minhas(perfil)
            if categoria:
                lista = [o for o in lista if o.categoria == categoria]
            autor = perfil
        else:
            lista = ops.listar_para_discente(perfil, categoria)
            autor = None

        contagens = {o.id: ops.contar_interessados(o.id) for o in lista}
        meus_interesses = ops.listar_meus_interesses(perfil) if usuario['tipo_usuario'] == 'discente' else []
        ids_meus_interesses = {o.id for o in meus_interesses}

        if autor is not None and ver_int and ver_int.isdigit():
            try:
                id_foco = int(ver_int)
                interessados_lista = ops.listar_interessados(autor, id_foco)
                oportunidade_foco = ops.buscar(id_foco)
            except (ValueError, PermissionError) as erro:
                ctx['flash'] = {'tipo': 'erro', 'texto': str(erro)}

        ctx.update({
            'oportunidades': lista,
            'contagens': contagens,
            'categorias': ops.categorias_oportunidades,
            'categoria_atual': categoria or '',
            'meus_interesses': meus_interesses,
            'ids_meus_interesses': ids_meus_interesses,
            'pode_gerenciar': autor is not None,
            'interessados_lista': interessados_lista,
            'oportunidade_foco': oportunidade_foco,
        })
        return template('app/views/html/oportunidades', **ctx)

    def criar_oportunidade(self):
        conta, perfil, _ = self._exigir_sessao_ativa()
        autor = conta if conta.eh_admin else perfil

        titulo = request.forms.getunicode('titulo') or ''
        categoria = request.forms.getunicode('categoria') or ''
        descricao = request.forms.getunicode('descricao') or ''
        contato = request.forms.getunicode('contato') or ''

        try:
            prazo = _converter_data_iso(request.forms.getunicode('prazo'))
            nova = ops.publicar(autor, titulo, categoria, descricao, contato, prazo)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/oportunidades')

        self.notificar_ws('oportunidades', f'Nova oportunidade publicada: {nova.titulo}')
        self.definir_flash('sucesso', f'Oportunidade #{nova.id} publicada com sucesso!')
        return redirect('/oportunidades')

    def form_editar_oportunidade(self, id_oportunidade):
        conta, perfil, usuario = self._exigir_sessao_ativa()
        autor = conta if conta.eh_admin else perfil
        oportunidade = ops.buscar(id_oportunidade)

        if oportunidade is None:
            self.definir_flash('erro', 'Publicação não encontrada.')
            return redirect('/oportunidades')

        if not conta.eh_admin and (perfil is None or perfil.tipo_usuario != 'docente' or oportunidade.autor_id != perfil.id_user):
            self.definir_flash('erro', 'Você não tem permissão para editar esta publicação.')
            return redirect('/oportunidades')

        ctx = self._contexto_base(usuario, 'oportunidades')
        ctx['oportunidade'] = oportunidade
        return template('app/views/html/oportunidade_editar', **ctx)

    def editar_oportunidade(self, id_oportunidade):
        conta, perfil, _ = self._exigir_sessao_ativa()
        autor = conta if conta.eh_admin else perfil

        titulo = request.forms.getunicode('titulo') or ''
        descricao = request.forms.getunicode('descricao') or ''
        contato = request.forms.getunicode('contato') or ''

        try:
            prazo = _converter_data_iso(request.forms.getunicode('prazo'))
            ops.editar(autor, id_oportunidade, titulo=titulo, descricao=descricao, contato=contato, prazo=prazo)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect(f'/oportunidades/{id_oportunidade}/editar')

        self.notificar_ws('oportunidades', f'Oportunidade #{id_oportunidade} atualizada.')
        self.definir_flash('sucesso', f'Oportunidade #{id_oportunidade} atualizada com sucesso!')
        return redirect('/oportunidades')

    def encerrar_oportunidade(self, id_oportunidade):
        conta, perfil, _ = self._exigir_sessao_ativa()
        autor = conta if conta.eh_admin else perfil

        try:
            ops.encerrar(autor, id_oportunidade)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/oportunidades')

        self.notificar_ws('oportunidades', f'Oportunidade #{id_oportunidade} encerrada.')
        self.definir_flash('sucesso', f'Oportunidade #{id_oportunidade} encerrada.')
        return redirect('/oportunidades')

    def excluir_oportunidade(self, id_oportunidade):
        conta, perfil, _ = self._exigir_sessao_ativa()
        autor = conta if conta.eh_admin else perfil

        try:
            ops.remover(autor, id_oportunidade)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/oportunidades')

        self.notificar_ws('oportunidades', f'Oportunidade #{id_oportunidade} removida.')
        self.definir_flash('sucesso', f'Oportunidade #{id_oportunidade} removida definitivamente.')
        return redirect('/oportunidades')

    def demonstrar_interesse(self, id_oportunidade):
        _, perfil, _ = self._exigir_sessao_ativa()
        try:
            oportunidade = ops.demonstrar_interesse(perfil, id_oportunidade)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/oportunidades')

        self.notificar_ws('oportunidades', f'Novo interesse em "{oportunidade.titulo}".')
        self.definir_flash('sucesso', f'Interesse registrado em "{oportunidade.titulo}"!')
        return redirect('/oportunidades')

    def retirar_interesse(self, id_oportunidade):
        _, perfil, _ = self._exigir_sessao_ativa()
        try:
            ops.retirar_interesse(perfil, id_oportunidade)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/oportunidades')

        self.notificar_ws('oportunidades', f'Interesse retirado na oportunidade #{id_oportunidade}.')
        self.definir_flash('sucesso', 'Interesse removido com sucesso.')
        return redirect('/oportunidades')

    # ========== { CRUD: ORGANIZAÇÕES ESTUDANTIS } ========== #

    def organizacoes(self):
        _, _, usuario = self._exigir_sessao_ativa()
        ctx = self._contexto_base(usuario, 'organizacoes')

        tipo = (request.query.getunicode('tipo') or '').strip() or None
        busca = (request.query.getunicode('busca') or '').strip()

        try:
            if busca:
                lista = cp.buscar_organizacoes(busca)
                if tipo:
                    lista = [e for e in lista if e['tipo'] == tipo]
            else:
                lista = cp.listar_organizacoes(tipo)
        except ValueError as erro:
            ctx['flash'] = {'tipo': 'erro', 'texto': str(erro)}
            lista = cp.listar_organizacoes()

        ctx.update({
            'entidades': lista,
            'tipos': ops.tipos_entidades_fixas,
            'tipo_atual': tipo or '',
            'busca': busca,
            'resumo': cp.resumo_organizacoes().replace('\n', ' ').strip(),
        })
        return template('app/views/html/organizacoes', **ctx)

    def criar_organizacao(self):
        conta, _, _ = self._exigir_admin_web()
        try:
            ops.cadastrar_entidade_fixa(
                conta,
                request.forms.getunicode('nome') or '',
                request.forms.getunicode('tipo') or '',
                request.forms.getunicode('instagram_link') or '',
                area=request.forms.getunicode('area'),
                descricao=request.forms.getunicode('descricao'),
                como_participar=request.forms.getunicode('como_participar'),
                contato=request.forms.getunicode('contato'),
            )
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/organizacoes')

        self.definir_flash('sucesso', 'Organização estudantil cadastrada com sucesso!')
        return redirect('/organizacoes')

    def form_editar_organizacao(self, id_entidade):
        _, _, usuario = self._exigir_admin_web()
        entidade = ops.buscar_entidade_fixa(id_entidade)
        if entidade is None:
            self.definir_flash('erro', 'Organização não encontrada.')
            return redirect('/organizacoes')

        ctx = self._contexto_base(usuario, 'organizacoes')
        ctx.update({
            'entidade': entidade,
            'tipos': ops.tipos_entidades_fixas,
        })
        return template('app/views/html/organizacao_editar', **ctx)

    def editar_organizacao(self, id_entidade):
        conta, _, _ = self._exigir_admin_web()
        try:
            ops.editar_entidade_fixa(
                conta,
                id_entidade,
                request.forms.getunicode('nome') or '',
                request.forms.getunicode('tipo') or '',
                request.forms.getunicode('instagram_link') or '',
                area=request.forms.getunicode('area'),
                descricao=request.forms.getunicode('descricao'),
                como_participar=request.forms.getunicode('como_participar'),
                contato=request.forms.getunicode('contato'),
            )
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect(f'/organizacoes/{id_entidade}/editar')

        self.definir_flash('sucesso', 'Organização atualizada com sucesso!')
        return redirect('/organizacoes')

    def excluir_organizacao(self, id_entidade):
        conta, _, _ = self._exigir_admin_web()
        try:
            removida = ops.remover_entidade_fixa(conta, id_entidade)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/organizacoes')

        self.definir_flash('sucesso', f'Organização "{removida["nome"]}" removida.')
        return redirect('/organizacoes')

    # ========== { CRUD: BIBLIOTECA FCTE } ========== #

    def biblioteca(self):
        conta, perfil, usuario = self._exigir_sessao_ativa()
        ctx = self._contexto_base(usuario, 'biblioteca')

        busca = (request.query.getunicode('busca') or '').strip()
        area = (request.query.getunicode('area') or '').strip() or None
        so_disp = request.query.getunicode('disponiveis') == '1'

        livros = self.__biblioteca.buscar(busca, area=area, so_disponiveis=so_disp)
        tem_perfil = perfil is not None and perfil.tipo_usuario in bib.regras

        ctx.update({
            'livros': livros,
            'areas': self.__biblioteca.areas(),
            'busca': busca,
            'area_atual': area or '',
            'so_disp': so_disp,
            'tem_perfil': tem_perfil,
            'emprestimos': self.__biblioteca.emprestimos_ativos(perfil) if tem_perfil else [],
            'historico': self.__biblioteca.historico(perfil) if tem_perfil else [],
            'max_renovacoes': bib.max_renovacoes,
            'multa_por_dia': bib.multa_por_dia,
        })
        return template('app/views/html/biblioteca', **ctx)

    def criar_livro(self):
        conta, _, _ = self._exigir_admin_web()
        try:
            exemplares = int((request.forms.getunicode('exemplares') or '').strip())
            self.__biblioteca.cadastrar_livro(
                conta,
                request.forms.getunicode('titulo') or '',
                request.forms.getunicode('autores') or '',
                request.forms.getunicode('area') or '',
                exemplares,
            )
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/biblioteca')

        self.notificar_ws('biblioteca', 'Novo livro cadastrado no acervo.')
        self.definir_flash('sucesso', 'Livro cadastrado no acervo com sucesso!')
        return redirect('/biblioteca')

    def form_editar_livro(self, id_livro):
        _, _, usuario = self._exigir_admin_web()
        try:
            livro = self.__biblioteca.obter_livro(id_livro)
        except ValueError as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/biblioteca')

        ctx = self._contexto_base(usuario, 'biblioteca')
        ctx['livro'] = livro
        return template('app/views/html/livro_editar', **ctx)

    def editar_livro(self, id_livro):
        conta, _, _ = self._exigir_admin_web()
        try:
            exemplares = int((request.forms.getunicode('exemplares') or '').strip())
            self.__biblioteca.editar_livro(
                conta,
                id_livro,
                request.forms.getunicode('titulo') or '',
                request.forms.getunicode('autores') or '',
                request.forms.getunicode('area') or '',
                exemplares,
            )
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect(f'/biblioteca/{id_livro}/editar')

        self.notificar_ws('biblioteca', f'Livro #{id_livro} atualizado no acervo.')
        self.definir_flash('sucesso', 'Livro atualizado com sucesso!')
        return redirect('/biblioteca')

    def excluir_livro(self, id_livro):
        conta, _, _ = self._exigir_admin_web()
        try:
            removido = self.__biblioteca.remover_livro(conta, id_livro)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/biblioteca')

        self.notificar_ws('biblioteca', f'Livro "{removido.titulo}" removido do acervo.')
        self.definir_flash('sucesso', f'Livro "{removido.titulo}" removido do acervo.')
        return redirect('/biblioteca')

    def reservar_livro(self, id_livro):
        _, perfil, _ = self._exigir_sessao_ativa()
        try:
            livro, devolver_ate = self.__biblioteca.reservar(perfil, id_livro)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/biblioteca')

        self.notificar_ws('biblioteca', f'Livro reservado: "{livro.titulo}".')
        self.definir_flash(
            'sucesso',
            f'Reserva de "{livro.titulo}" concluída! Devolver até {bib.formatar_data(devolver_ate)}.',
        )
        return redirect('/biblioteca')

    def renovar_emprestimo(self, id_emprestimo):
        _, perfil, _ = self._exigir_sessao_ativa()
        try:
            nova_data = self.__biblioteca.renovar(perfil, id_emprestimo)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/biblioteca')

        self.notificar_ws('biblioteca', f'Empréstimo #{id_emprestimo} renovado.')
        self.definir_flash('sucesso', f'Empréstimo renovado! Novo prazo: {bib.formatar_data(nova_data)}.')
        return redirect('/biblioteca')

    def devolver_emprestimo(self, id_emprestimo):
        _, perfil, _ = self._exigir_sessao_ativa()
        try:
            multa = self.__biblioteca.devolver(perfil, id_emprestimo)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/biblioteca')

        self.notificar_ws('biblioteca', f'Livro devolvido (empréstimo #{id_emprestimo}).')
        msg = 'Livro devolvido com sucesso!'
        if multa:
            msg += f' Multa por atraso: R$ {multa:.2f}.'
        self.definir_flash('sucesso', msg)
        return redirect('/biblioteca')

    # ========== { CRUD: TURMAS, MATRÍCULAS E NOTAS } ========== #

    def turmas(self):
        conta, perfil, usuario = self._exigir_sessao_ativa()
        ctx = self._contexto_base(usuario, 'turmas')

        ano_padrao, sem_padrao = semestre_atual()
        periodo_str = (request.query.getunicode('periodo') or f'{ano_padrao}.{sem_padrao}').strip()
        filtro = (request.query.getunicode('filtro') or '').strip()

        try:
            ano, sem = _parsear_periodo(periodo_str)
            lista_turmas = self.__sistema.listar_turmas(ano, sem, filtro or None)
        except ValueError as erro:
            ctx['flash'] = {'tipo': 'erro', 'texto': str(erro)}
            lista_turmas = self.__sistema.listar_turmas()

        turmas_formatadas = [
            {
                **t,
                'chave': tr.chave_turma(t),
                'horario_legivel': legivel(t.get('horario', '')),
            }
            for t in lista_turmas
        ]

        docente_turmas = []
        if usuario['tipo_usuario'] == 'docente' and perfil is not None:
            for t in tr.turmas_do_docente(perfil):
                chave = tr.chave_turma(t)
                alunos = tr.alunos_da_turma(perfil, chave)
                for a in alunos:
                    a['mencao'] = None if a['nota'] is None else tr.mencao(a['nota'])
                docente_turmas.append({
                    'chave': chave,
                    'turma': t,
                    'horario_legivel': legivel(t.get('horario', '')),
                    'alunos': alunos,
                })

        ctx.update({
            'turmas_sigaa': turmas_formatadas,
            'periodo_atual': periodo_str,
            'filtro': filtro,
            'docente_turmas': docente_turmas,
            'discentes_admin': banco.listar_perfis('discente') if conta.eh_admin else [],
            'docentes_admin': banco.listar_perfis('docente') if conta.eh_admin else [],
            'turmas_semestre': [
                {'chave': tr.chave_turma(t), 'turma': t}
                for t in self.__sistema.listar_turmas()
            ] if conta.eh_admin else [],
            'matriculas_admin': tr.listar_matriculas_admin(conta) if conta.eh_admin else [],
            'ofertas_admin': tr.listar_ofertas_admin(conta) if conta.eh_admin else [],
        })
        return template('app/views/html/turmas', **ctx)

    def matricular_discente(self):
        conta, _, _ = self._exigir_admin_web()
        matricula = (request.forms.getunicode('matricula') or '').strip()
        chave = (request.forms.getunicode('chave') or '').strip()
        try:
            tr.matricular(conta, matricula, chave)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/turmas')

        self.definir_flash('sucesso', 'Discente matriculado(a) com sucesso!')
        return redirect('/turmas')

    def desmatricular_discente(self):
        conta, _, _ = self._exigir_admin_web()
        matricula = (request.forms.getunicode('matricula') or '').strip()
        chave = (request.forms.getunicode('chave') or '').strip()
        try:
            tr.desmatricular(conta, matricula, chave)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/turmas')

        self.definir_flash('sucesso', 'Matrícula removida com sucesso.')
        return redirect('/turmas')

    def atribuir_docente(self):
        conta, _, _ = self._exigir_admin_web()
        id_docente = (request.forms.getunicode('id_docente') or '').strip()
        chave = (request.forms.getunicode('chave') or '').strip()
        try:
            tr.atribuir_docente(conta, id_docente, chave)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/turmas')

        self.definir_flash('sucesso', 'Docente atribuído(a) à turma com sucesso!')
        return redirect('/turmas')

    def remover_oferta(self):
        conta, _, _ = self._exigir_admin_web()
        chave = (request.forms.getunicode('chave') or '').strip()
        try:
            tr.remover_oferta(conta, chave)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/turmas')

        self.definir_flash('sucesso', 'Vínculo de oferta removido.')
        return redirect('/turmas')

    def lancar_nota(self):
        _, perfil, _ = self._exigir_sessao_ativa()
        chave = (request.forms.getunicode('chave') or '').strip()
        matricula = (request.forms.getunicode('matricula') or '').strip()
        texto_nota = (request.forms.getunicode('nota') or '').strip().replace(',', '.')

        try:
            nota = float(texto_nota)
            tr.lancar_nota(perfil, chave, matricula, nota)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/turmas')

        self.definir_flash('sucesso', f'Nota {nota:.1f} ({tr.mencao(nota)}) lançada com sucesso!')
        return redirect('/turmas')

    # ========== { CRUD: USUÁRIOS (RESTRITO A ADMIN) } ========== #

    def usuarios(self):
        conta, _, usuario = self._exigir_admin_web()
        ctx = self._contexto_base(usuario, 'usuarios')

        acessos = login.listar_acessos(conta)
        registros = []
        for acc in acessos:
            perf = None if acc.eh_admin else banco.buscar_perfil(acc.email)
            registros.append({
                'email': acc.email,
                'tipo_usuario': acc.tipo_usuario,
                'precisa_trocar_senha': acc.precisa_trocar_senha,
                'eh_proprio': acc.email.casefold() == conta.email.casefold(),
                'tem_perfil': perf is not None,
                'nome': perf.nome if perf else ('Administrador' if acc.eh_admin else 'Perfil pendente'),
                'matricula': perf.id_user if perf else '—',
                'curso_ou_area': perf.curso_ou_area if perf else '—',
            })

        ctx.update({
            'registros': registros,
            'tipos_usuario': login.tipos_usuario,
        })
        return template('app/views/html/usuarios', **ctx)

    def criar_usuario(self):
        conta, _, _ = self._exigir_admin_web()
        email = (request.forms.getunicode('email') or '').strip()
        tipo = (request.forms.getunicode('tipo') or '').strip().lower()

        try:
            senha_inicial = login.gerar_acesso(conta, email, tipo)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/usuarios')

        self.definir_flash(
            'sucesso',
            f'Acesso criado para {email} ({tipo}). Senha inicial temporária: {senha_inicial}',
        )
        return redirect('/usuarios')

    def form_editar_usuario(self):
        _, _, usuario = self._exigir_admin_web()
        email = (request.query.getunicode('email') or '').strip()
        perfil = banco.buscar_perfil(email)

        if perfil is None:
            self.definir_flash('erro', 'Perfil não encontrado para este e-mail.')
            return redirect('/usuarios')

        ctx = self._contexto_base(usuario, 'usuarios')
        ctx.update({
            'alvo': perfil,
            'cursos': cursos_disponiveis,
        })
        return template('app/views/html/usuario_editar', **ctx)

    def editar_usuario(self):
        conta, _, _ = self._exigir_admin_web()
        email = (request.forms.getunicode('email') or '').strip()
        nome = request.forms.getunicode('nome') or ''
        curso_ou_area = request.forms.getunicode('curso_ou_area') or ''

        try:
            banco.atualizar_perfil(conta, email, nome=nome, curso_ou_area=curso_ou_area)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect(f"/usuarios/editar?email={quote(email, safe='')}")

        self.definir_flash('sucesso', f'Perfil de {email} atualizado com sucesso!')
        return redirect('/usuarios')

    def excluir_usuario(self):
        conta, _, _ = self._exigir_admin_web()
        email = (request.forms.getunicode('email') or '').strip()

        try:
            banco.remover_usuario(conta, email)
        except (ValueError, PermissionError) as erro:
            self.definir_flash('erro', str(erro))
            return redirect('/usuarios')

        self.revogar_sessoes_email(email)
        self.definir_flash('sucesso', f'Usuário {email} removido com sucesso.')
        return redirect('/usuarios')

    # ========== { CARDÁPIO DO RU } ========== #

    def cardapio(self):
        _, _, usuario = self._exigir_sessao_ativa()
        ctx = self._contexto_base(usuario, 'cardapio')

        try:
            datas = cp.datas_disponiveis()
        except RuntimeError as erro:
            ctx['flash'] = {'tipo': 'erro', 'texto': str(erro)}
            datas = []

        hoje_iso = date.today().isoformat()
        dia = (request.query.getunicode('dia') or '').strip()
        if dia not in datas:
            dia = hoje_iso if hoje_iso in datas else (datas[-1] if datas else '')

        dieta = (request.query.getunicode('dieta') or 'padrao').strip()
        if dieta not in cp.dietas:
            dieta = 'padrao'

        refeicoes_formatadas = []
        if dia:
            for chave, itens in cp.cardapio_do_dia(dia).items():
                refeicoes_formatadas.append({
                    'nome': cp.refeicoes[chave],
                    'itens': cp.formatar_refeicao(itens, dieta),
                })

        ctx.update({
            'datas': [
                {'iso': d, 'rotulo': f'{_data_br(d)} ({cp.nome_dia_semana(d)})'}
                for d in datas
            ],
            'dia_atual': dia,
            'dietas': cp.dietas,
            'dieta_atual': dieta,
            'refeicoes': refeicoes_formatadas,
            'desatualizado': bool(datas and datas[-1] < hoje_iso),
            'ultima_data': _data_br(datas[-1]) if datas else None,
        })
        return template('app/views/html/cardapio', **ctx)
