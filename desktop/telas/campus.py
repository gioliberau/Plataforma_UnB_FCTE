from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from code_py import consultas_publicas as cp, organizacoes as ops

from ..estilo import DialogoBase, TabelaRolavel, formatar_data_br
from .base import TelaBase, criar_bloco


# ============================= { DIÁLOGO DE CADASTRO DE ENTIDADE } ============================= #

class DialogoCadastrarEntidade(DialogoBase):

    def __init__(self, master, conta):
        super().__init__(master, 'Cadastrar Entidade Estudantil', largura=480)
        self.__conta = conta
        self.__mapa_tipos = {rotulo: chave for chave, rotulo in ops.tipos_entidades_fixas.items()}

        ttk.Label(self.corpo, text='Tipo de entidade:', style='Card.TLabel').pack(anchor='w')
        self.__var_tipo = tk.StringVar(value=next(iter(self.__mapa_tipos)))
        ttk.Combobox(
            self.corpo,
            textvariable=self.__var_tipo,
            values=list(self.__mapa_tipos),
            state='readonly',
        ).pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Nome:', style='Card.TLabel').pack(anchor='w')
        self.__ent_nome = ttk.Entry(self.corpo)
        self.__ent_nome.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Link do Instagram (https://instagram.com/...):', style='Card.TLabel').pack(anchor='w')
        self.__ent_insta = ttk.Entry(self.corpo)
        self.__ent_insta.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Área / Curso de atuação (opcional):', style='Card.TLabel').pack(anchor='w')
        self.__ent_area = ttk.Entry(self.corpo)
        self.__ent_area.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Descrição (opcional):', style='Card.TLabel').pack(anchor='w')
        self.__ent_desc = ttk.Entry(self.corpo)
        self.__ent_desc.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Como participar (opcional):', style='Card.TLabel').pack(anchor='w')
        self.__ent_part = ttk.Entry(self.corpo)
        self.__ent_part.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Contato / E-mail (opcional):', style='Card.TLabel').pack(anchor='w')
        self.__ent_contato = ttk.Entry(self.corpo)
        self.__ent_contato.pack(fill='x', pady=(2, 14))

        botoes = ttk.Frame(self.corpo, style='Card.TFrame')
        botoes.pack(fill='x')
        ttk.Button(botoes, text='Cancelar', style='Secundario.TButton', command=self.cancelar).pack(side='left')
        ttk.Button(botoes, text='Cadastrar', style='Destaque.TButton', command=self.__salvar).pack(side='right')

        self.__ent_nome.focus_set()
        self.finalizar_layout()

    def __salvar(self):
        tipo = self.__mapa_tipos[self.__var_tipo.get()]
        try:
            ops.cadastrar_entidade_fixa(
                self.__conta,
                self.__ent_nome.get(),
                tipo,
                self.__ent_insta.get(),
                area=self.__ent_area.get(),
                descricao=self.__ent_desc.get(),
                como_participar=self.__ent_part.get(),
                contato=self.__ent_contato.get(),
            )
        except (ValueError, PermissionError) as erro:
            messagebox.showerror('Cadastro inválido', str(erro), parent=self)
            return

        self.resultado = True
        self.destroy()


# ============================= { TELA DO CAMPUS (ORG, CALENDÁRIO, CURSOS) } ============================= #

class TelaCampus(TelaBase):

    def __init__(self, master, sessao, ao_status=None, ao_navegar=None):
        super().__init__(master, sessao, ao_status=ao_status, ao_navegar=ao_navegar)
        self.__link_org_atual = None

        self.criar_cabecalho(
            'Campus UnB FCTE — Informações Públicas',
            'Organizações estudantis, calendário acadêmico oficial (SAA) e cursos de graduação.',
        )

        self.__abas = ttk.Notebook(self)
        self.__abas.pack(fill='both', expand=True)

        self.__montar_aba_organizacoes()
        self.__montar_aba_calendario()
        self.__montar_aba_cursos()

    def atualizar(self):
        self.__carregar_organizacoes()
        self.__carregar_calendario()

    # ========== { ABA: ORGANIZAÇÕES ESTUDANTIS } ========== #

    def __montar_aba_organizacoes(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Organizações Estudantis')

        self.__lbl_resumo_org = ttk.Label(aba, text='', style='Suave.TLabel')
        self.__lbl_resumo_org.pack(anchor='w', pady=(0, 6))

        barra = criar_bloco(aba, padding=10)
        barra.pack(fill='x', pady=(0, 10))
        linha = ttk.Frame(barra, style='Card.TFrame')
        linha.pack(fill='x')

        self.__mapa_tipo_org = {'Todas': None}
        for chave, rotulo in cp.tipos_organizacoes.items():
            self.__mapa_tipo_org[rotulo] = chave

        ttk.Label(linha, text='Tipo:', style='Card.TLabel').pack(side='left')
        self.__var_tipo_org = tk.StringVar(value='Todas')
        cmb = ttk.Combobox(linha, textvariable=self.__var_tipo_org, values=list(self.__mapa_tipo_org), state='readonly', width=25)
        cmb.pack(side='left', padx=(6, 12))
        cmb.bind('<<ComboboxSelected>>', lambda _e: self.__carregar_organizacoes())

        ttk.Label(linha, text='Buscar:', style='Card.TLabel').pack(side='left')
        self.__ent_busca_org = ttk.Entry(linha, width=22)
        self.__ent_busca_org.pack(side='left', padx=(6, 8))
        self.__ent_busca_org.bind('<Return>', lambda _e: self.__carregar_organizacoes())

        ttk.Button(linha, text='Filtrar', style='Primario.TButton', command=self.__carregar_organizacoes).pack(side='left')

        if self._eh_admin:
            ttk.Button(
                linha,
                text='+ Cadastrar Entidade',
                style='Destaque.TButton',
                command=self.__cadastrar_entidade,
            ).pack(side='right')

        self.__tab_org = TabelaRolavel(
            aba,
            colunas=(
                ('nome', 'Organização', 190, 'w'),
                ('tipo', 'Tipo', 175, 'w'),
                ('area', 'Área', 180, 'w'),
                ('instagram', 'Instagram', 250, 'w'),
            ),
            altura=10,
            ao_selecionar=self.__mostrar_detalhe_org,
        )
        self.__tab_org.pack(fill='both', expand=True)

        detalhe = criar_bloco(aba, padding=10)
        detalhe.pack(fill='x', pady=(10, 0))

        self.__lbl_detalhe_org = ttk.Label(
            detalhe,
            text='Selecione uma organização para ver descrição, como participar e contato.',
            style='CardSuave.TLabel',
            wraplength=800,
            justify='left',
        )
        self.__lbl_detalhe_org.pack(anchor='w')

        self.__btn_insta = ttk.Button(
            detalhe,
            text='Abrir Instagram no navegador',
            style='Secundario.TButton',
            command=self.__abrir_instagram,
            state='disabled',
        )
        self.__btn_insta.pack(anchor='w', pady=(8, 0))

    def __carregar_organizacoes(self):
        self.__lbl_resumo_org.configure(text=cp.resumo_organizacoes().replace('\n', ' ').strip())
        termo = self.__ent_busca_org.get().strip()
        tipo = self.__mapa_tipo_org.get(self.__var_tipo_org.get())

        if termo:
            lista = cp.buscar_organizacoes(termo)
            if tipo:
                lista = [e for e in lista if e['tipo'] == tipo]
        else:
            lista = cp.listar_organizacoes(tipo)

        self.__tab_org.preencher([
            (
                (
                    e['nome'],
                    cp.tipos_organizacoes.get(e['tipo'], e['tipo']),
                    e.get('area') or '—',
                    e.get('instagram_link', ''),
                ),
                e,
            )
            for e in lista
        ])

    def __mostrar_detalhe_org(self, entidade):
        if not entidade:
            self.__link_org_atual = None
            self.__btn_insta.configure(state='disabled')
            return

        padrao = ops.info_tipos.get(entidade['tipo'], {})
        tipo = cp.tipos_organizacoes.get(entidade['tipo'], entidade['tipo'])
        sobre = entidade.get('descricao') or padrao.get('sobre') or '—'
        participar = entidade.get('como_participar') or padrao.get('como_participar') or '—'
        contato = entidade.get('contato') or 'Via Instagram'

        texto = (
            f"{entidade['nome']} ({tipo})\n"
            f"Sobre: {sobre}\n"
            f"Como participar: {participar}\n"
            f"Contato: {contato}  |  Instagram: {entidade['instagram_link']}"
        )
        self.__lbl_detalhe_org.configure(text=texto, style='Card.TLabel')
        self.__link_org_atual = entidade.get('instagram_link')
        self.__btn_insta.configure(state='normal' if self.__link_org_atual else 'disabled')

    def __abrir_instagram(self):
        if self.__link_org_atual:
            webbrowser.open(self.__link_org_atual)

    def __cadastrar_entidade(self):
        dialogo = DialogoCadastrarEntidade(self.winfo_toplevel(), self._conta)
        self.wait_window(dialogo)
        if dialogo.resultado:
            self.__carregar_organizacoes()
            self.mostrar_info('Entidade cadastrada com sucesso!')

    # ========== { ABA: CALENDÁRIO ACADÊMICO } ========== #

    def __montar_aba_calendario(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Calendário Acadêmico')

        barra = criar_bloco(aba, padding=10)
        barra.pack(fill='x', pady=(0, 10))
        linha = ttk.Frame(barra, style='Card.TFrame')
        linha.pack(fill='x')

        ttk.Label(linha, text='Período:', style='Card.TLabel').pack(side='left')
        self.__var_per_cal = tk.StringVar()
        self.__cmb_per_cal = ttk.Combobox(linha, textvariable=self.__var_per_cal, state='readonly', width=14)
        self.__cmb_per_cal.pack(side='left', padx=(6, 12))
        self.__cmb_per_cal.bind('<<ComboboxSelected>>', lambda _e: self.__mostrar_eventos_periodo())

        ttk.Button(
            linha,
            text='Abrir site da SAA',
            style='Secundario.TButton',
            command=lambda: webbrowser.open('https://saa.unb.br/calendario-academico-graduacao/'),
        ).pack(side='left')

        if self._eh_admin:
            self.__btn_atualizar_cal = ttk.Button(
                linha,
                text='Atualizar Calendário (SAA)',
                style='Primario.TButton',
                command=self.__atualizar_calendario,
            )
            self.__btn_atualizar_cal.pack(side='right')

        self.__tab_cal = TabelaRolavel(
            aba,
            colunas=(
                ('datas', 'Datas', 170, 'center'),
                ('descricao', 'Evento', 380, 'w'),
                ('situacao', 'Situação', 180, 'center'),
            ),
            altura=13,
        )
        self.__tab_cal.pack(fill='both', expand=True)

    def __carregar_calendario(self):
        try:
            periodos = cp.periodos_calendario()
        except RuntimeError as erro:
            self.tratar_erro(erro)
            periodos = []

        self.__cmb_per_cal['values'] = periodos
        if periodos:
            if self.__var_per_cal.get() not in periodos:
                self.__var_per_cal.set(periodos[-1])
            self.__mostrar_eventos_periodo()
        else:
            self.__var_per_cal.set('')
            self.__tab_cal.preencher([])

    def __mostrar_eventos_periodo(self):
        periodo = self.__var_per_cal.get()
        if not periodo:
            return
        hoje = date.today()
        eventos = cp.eventos_do_periodo(periodo)

        linhas = []
        for e in eventos:
            inicio = date.fromisoformat(e['inicio'])
            fim = date.fromisoformat(e['fim']) if e.get('fim') else inicio
            datas = formatar_data_br(inicio) if fim == inicio else f"{inicio.strftime('%d/%m')} a {formatar_data_br(fim)}"
            if fim < hoje:
                sit = 'Já passou'
            elif inicio <= hoje:
                sit = 'EM ANDAMENTO'
            else:
                sit = f'Daqui a {(inicio - hoje).days} dia(s)'
            linhas.append(((datas, e['descricao'], sit), e))

        self.__tab_cal.preencher(linhas)

    def __atualizar_calendario(self):
        if not self.confirmar('Consultar os PDFs oficiais no site da SAA/UnB agora?'):
            return

        self.__btn_atualizar_cal.configure(state='disabled')

        def tarefa():
            return cp.atualizar_calendario(self._conta)

        def ao_sucesso(total):
            self.__btn_atualizar_cal.configure(state='normal')
            self.__carregar_calendario()
            self.mostrar_info(f'Calendário atualizado com sucesso ({total} datas lidas).')

        def ao_erro(erro):
            self.__btn_atualizar_cal.configure(state='normal')
            self.tratar_erro(erro)

        self.executar_em_segundo_plano(tarefa, ao_sucesso, 'Atualizando calendário da SAA...', ao_erro=ao_erro)

    # ========== { ABA: CURSOS DA FCTE } ========== #

    def __montar_aba_cursos(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Cursos da FCTE')

        bloco = criar_bloco(aba, titulo='Cursos de Graduação — Campus Gama (FCTE)', padding=16)
        bloco.pack(fill='x')

        for numero, curso in enumerate(cp.listar_cursos(), start=1):
            linha = ttk.Frame(bloco, style='Card.TFrame')
            linha.pack(fill='x', pady=5)
            ttk.Label(linha, text=f'{numero}.  {curso}', style='Subtitulo.TLabel').pack(anchor='w')

        ttk.Separator(bloco, orient='horizontal').pack(fill='x', pady=12)
        ttk.Label(bloco, text=f'Portal oficial da unidade: {cp.site_fcte}', style='CardSuave.TLabel').pack(anchor='w', pady=(0, 8))
        ttk.Button(
            bloco,
            text='Abrir site da FCTE no navegador',
            style='Primario.TButton',
            command=lambda: webbrowser.open(cp.site_fcte),
        ).pack(anchor='w')
