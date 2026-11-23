import tkinter as tk
from tkinter import messagebox, ttk

from code_py import organizacoes as ops

from ..estilo import DialogoBase, TabelaRolavel, converter_data_br, formatar_data_br
from .base import TelaBase, criar_bloco


# ============================= { DIÁLOGOS DE OPORTUNIDADES } ============================= #

class DialogoPublicarOportunidade(DialogoBase):

    def __init__(self, master, autor):
        super().__init__(master, 'Publicar Oportunidade', largura=480)
        self.__autor = autor
        permitidas = ops.categorias_do_perfil(autor)
        self.__mapa_cat = {ops.categorias_oportunidades[c]: c for c in permitidas}

        ttk.Label(self.corpo, text='Categoria:', style='Card.TLabel').pack(anchor='w')
        self.__var_cat = tk.StringVar(value=next(iter(self.__mapa_cat)))
        ttk.Combobox(
            self.corpo,
            textvariable=self.__var_cat,
            values=list(self.__mapa_cat),
            state='readonly',
        ).pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Título (máx. 100 caracteres):', style='Card.TLabel').pack(anchor='w')
        self.__ent_titulo = ttk.Entry(self.corpo)
        self.__ent_titulo.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Descrição (máx. 1000 caracteres):', style='Card.TLabel').pack(anchor='w')
        self.__txt_desc = tk.Text(self.corpo, height=5, width=48, wrap='word', relief='solid', borderwidth=1)
        self.__txt_desc.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Contato (e-mail ou sala):', style='Card.TLabel').pack(anchor='w')
        self.__ent_contato = ttk.Entry(self.corpo)
        self.__ent_contato.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Prazo (DD/MM/AAAA — deixe vazio se não houver):', style='Card.TLabel').pack(anchor='w')
        self.__ent_prazo = ttk.Entry(self.corpo)
        self.__ent_prazo.pack(fill='x', pady=(2, 14))

        botoes = ttk.Frame(self.corpo, style='Card.TFrame')
        botoes.pack(fill='x')
        ttk.Button(botoes, text='Cancelar', style='Secundario.TButton', command=self.cancelar).pack(side='left')
        ttk.Button(botoes, text='Publicar', style='Destaque.TButton', command=self.__salvar).pack(side='right')

        self.__ent_titulo.focus_set()
        self.finalizar_layout()

    def __salvar(self):
        categoria = self.__mapa_cat[self.__var_cat.get()]
        titulo = self.__ent_titulo.get()
        descricao = self.__txt_desc.get('1.0', 'end').strip()
        contato = self.__ent_contato.get()

        try:
            prazo = converter_data_br(self.__ent_prazo.get())
            nova = ops.publicar(self.__autor, titulo, categoria, descricao, contato, prazo)
        except (ValueError, PermissionError) as erro:
            messagebox.showerror('Não foi possível publicar', str(erro), parent=self)
            return

        self.resultado = nova
        self.destroy()


class DialogoEditarOportunidade(DialogoBase):

    def __init__(self, master, docente, oportunidade):
        super().__init__(master, f'Editar Oportunidade #{oportunidade.id}', largura=480)
        self.__docente = docente
        self.__oportunidade = oportunidade

        ttk.Label(self.corpo, text='Título:', style='Card.TLabel').pack(anchor='w')
        self.__ent_titulo = ttk.Entry(self.corpo)
        self.__ent_titulo.insert(0, oportunidade.titulo)
        self.__ent_titulo.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Descrição:', style='Card.TLabel').pack(anchor='w')
        self.__txt_desc = tk.Text(self.corpo, height=5, width=48, wrap='word', relief='solid', borderwidth=1)
        self.__txt_desc.insert('1.0', oportunidade.descricao)
        self.__txt_desc.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Contato:', style='Card.TLabel').pack(anchor='w')
        self.__ent_contato = ttk.Entry(self.corpo)
        self.__ent_contato.insert(0, oportunidade.contato)
        self.__ent_contato.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='Prazo (DD/MM/AAAA — deixe vazio para remover o prazo):', style='Card.TLabel').pack(anchor='w')
        self.__ent_prazo = ttk.Entry(self.corpo)
        if oportunidade.prazo:
            self.__ent_prazo.insert(0, oportunidade.prazo.strftime('%d/%m/%Y'))
        self.__ent_prazo.pack(fill='x', pady=(2, 14))

        botoes = ttk.Frame(self.corpo, style='Card.TFrame')
        botoes.pack(fill='x')
        ttk.Button(botoes, text='Cancelar', style='Secundario.TButton', command=self.cancelar).pack(side='left')
        ttk.Button(botoes, text='Salvar alterações', style='Primario.TButton', command=self.__salvar).pack(side='right')

        self.finalizar_layout()

    def __salvar(self):
        try:
            prazo = converter_data_br(self.__ent_prazo.get())
            atualizada = ops.editar(
                self.__docente,
                self.__oportunidade.id,
                titulo=self.__ent_titulo.get(),
                descricao=self.__txt_desc.get('1.0', 'end').strip(),
                contato=self.__ent_contato.get(),
                prazo=prazo,
            )
        except (ValueError, PermissionError) as erro:
            messagebox.showerror('Não foi possível salvar', str(erro), parent=self)
            return

        self.resultado = atualizada
        self.destroy()


class DialogoInteressados(DialogoBase):

    def __init__(self, master, oportunidade, lista):
        super().__init__(master, f'Interessados — #{oportunidade.id} {oportunidade.titulo}', largura=680, altura=380)

        ttk.Label(
            self.corpo,
            text=f'{len(lista)} discente(s) interessado(s) em "{oportunidade.titulo}"',
            style='Subtitulo.TLabel',
        ).pack(anchor='w', pady=(0, 10))

        tabela = TabelaRolavel(
            self.corpo,
            colunas=(
                ('nome', 'Nome', 190, 'w'),
                ('matricula', 'Matrícula', 100, 'center'),
                ('curso', 'Curso', 170, 'w'),
                ('email', 'E-mail', 170, 'w'),
                ('data', 'Data', 90, 'center'),
            ),
            altura=10,
        )
        tabela.pack(fill='both', expand=True)
        tabela.preencher([
            ((a['nome'], a['matricula'], a['curso'], a['email'], formatar_data_br(a['criado_em'])), a)
            for a in lista
        ])

        ttk.Button(self.corpo, text='Fechar', style='Secundario.TButton', command=self.cancelar).pack(anchor='e', pady=(10, 0))
        self.finalizar_layout()


# ============================= { TELA DE OPORTUNIDADES } ============================= #

class TelaOportunidades(TelaBase):

    def __init__(self, master, sessao, ao_status=None, ao_navegar=None):
        super().__init__(master, sessao, ao_status=ao_status, ao_navegar=ao_navegar)

        self.criar_cabecalho(
            'Mural de Oportunidades — FCTE',
            'Projetos de extensão, iniciação científica, estágios e monitorias do campus.',
        )

        self.__abas = ttk.Notebook(self)
        self.__abas.pack(fill='both', expand=True)

        if self._eh_discente:
            self.__montar_discente()
        elif self._eh_docente:
            self.__montar_gestao(eh_admin=False)
        elif self._eh_admin:
            self.__montar_gestao(eh_admin=True)

    @property
    def __autor(self):
        return self._conta if self._eh_admin else self._perfil

    def atualizar(self):
        if self._eh_discente:
            self.__carregar_abertas()
            self.__carregar_interesses()
        elif self._eh_docente or self._eh_admin:
            self.__carregar_gestao()

    # ========== { DISCENTE } ========== #

    def __montar_discente(self):
        aba_abertas = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba_abertas, text='Oportunidades Abertas')

        self.__mapa_filtro_cat = {'Todas as categorias': None}
        for chave in ops.categorias_do_perfil(self._perfil):
            self.__mapa_filtro_cat[ops.categorias_oportunidades[chave]] = chave

        topo = criar_bloco(aba_abertas, padding=10)
        topo.pack(fill='x', pady=(0, 10))
        linha = ttk.Frame(topo, style='Card.TFrame')
        linha.pack(fill='x')

        ttk.Label(linha, text='Categoria:', style='Card.TLabel').pack(side='left')
        self.__var_cat = tk.StringVar(value='Todas as categorias')
        cmb = ttk.Combobox(linha, textvariable=self.__var_cat, values=list(self.__mapa_filtro_cat), state='readonly', width=30)
        cmb.pack(side='left', padx=(6, 12))
        cmb.bind('<<ComboboxSelected>>', lambda _e: self.__carregar_abertas())

        ttk.Button(
            linha,
            text='Demonstrar Interesse',
            style='Destaque.TButton',
            command=self.__demonstrar_interesse,
        ).pack(side='right')

        self.__tab_abertas = TabelaRolavel(
            aba_abertas,
            colunas=(
                ('id', '#', 50, 'center'),
                ('titulo', 'Título', 250, 'w'),
                ('categoria', 'Categoria', 175, 'w'),
                ('autor', 'Publicado por', 160, 'w'),
                ('prazo', 'Prazo', 95, 'center'),
            ),
            altura=10,
            ao_selecionar=self.__mostrar_detalhe_discente,
        )
        self.__tab_abertas.pack(fill='both', expand=True)

        detalhe = criar_bloco(aba_abertas, padding=10)
        detalhe.pack(fill='x', pady=(10, 0))
        self.__lbl_detalhe_disc = ttk.Label(
            detalhe,
            text='Selecione uma oportunidade para ler a descrição completa e o contato.',
            style='CardSuave.TLabel',
            wraplength=820,
            justify='left',
        )
        self.__lbl_detalhe_disc.pack(anchor='w')

        # Aba Meus Interesses
        aba_int = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba_int, text='Meus Interesses')

        topo_i = ttk.Frame(aba_int, style='TFrame')
        topo_i.pack(fill='x', pady=(0, 8))
        ttk.Label(topo_i, text='Oportunidades em que você registrou interesse:', style='Suave.TLabel').pack(side='left')
        ttk.Button(topo_i, text='Retirar Interesse', style='Perigo.TButton', command=self.__retirar_interesse).pack(side='right')

        self.__tab_interesses = TabelaRolavel(
            aba_int,
            colunas=(
                ('id', '#', 50, 'center'),
                ('titulo', 'Título', 240, 'w'),
                ('categoria', 'Categoria', 165, 'w'),
                ('contato', 'Contato', 180, 'w'),
                ('situacao', 'Situação', 95, 'center'),
                ('prazo', 'Prazo', 90, 'center'),
            ),
            altura=12,
        )
        self.__tab_interesses.pack(fill='both', expand=True)

    def __carregar_abertas(self):
        categoria = self.__mapa_filtro_cat.get(self.__var_cat.get())
        lista = ops.listar_para_discente(self._perfil, categoria)
        self.__tab_abertas.preencher([
            (
                (
                    f'#{o.id}',
                    o.titulo,
                    o.nome_categoria,
                    o.autor_nome,
                    formatar_data_br(o.prazo) if o.prazo else 'Sem prazo',
                ),
                o,
            )
            for o in lista
        ])

    def __mostrar_detalhe_discente(self, o):
        if not o:
            return
        prazo = formatar_data_br(o.prazo) if o.prazo else 'sem prazo'
        texto = (
            f'[#{o.id}] {o.titulo} ({o.nome_categoria})\n'
            f'{o.descricao}\n'
            f'Publicado por: {o.autor_nome}  |  Contato: {o.contato}  |  Prazo: {prazo}'
        )
        self.__lbl_detalhe_disc.configure(text=texto, style='Card.TLabel')

    def __demonstrar_interesse(self):
        o = self.__tab_abertas.selecionado()
        if not o:
            self.tratar_erro('Selecione uma oportunidade na lista.')
            return

        if not self.confirmar(
            f'Confirmar interesse em "{o.titulo}"?\n\n'
            'Seu nome, matrícula, curso e e-mail ficarão visíveis para quem publicou.'
        ):
            return

        try:
            ops.demonstrar_interesse(self._perfil, o.id)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.__carregar_interesses()
        self.mostrar_info(f'Interesse registrado em "{o.titulo}"!')

    def __carregar_interesses(self):
        lista = ops.listar_meus_interesses(self._perfil)
        self.__tab_interesses.preencher([
            (
                (
                    f'#{o.id}',
                    o.titulo,
                    o.nome_categoria,
                    o.contato,
                    'Encerrada' if o.encerrada else 'Aberta',
                    formatar_data_br(o.prazo) if o.prazo else 'Sem prazo',
                ),
                o,
            )
            for o in lista
        ])

    def __retirar_interesse(self):
        o = self.__tab_interesses.selecionado()
        if not o:
            self.tratar_erro('Selecione uma oportunidade na aba Meus Interesses.')
            return

        if not self.confirmar(f'Retirar seu interesse de "{o.titulo}"?'):
            return

        try:
            ops.retirar_interesse(self._perfil, o.id)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.__carregar_interesses()
        self.mostrar_info('Interesse removido com sucesso.')

    # ========== { DOCENTE / ADMIN } ========== #

    def __montar_gestao(self, eh_admin):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        titulo_aba = 'Todas as Publicações (Moderação)' if eh_admin else 'Minhas Publicações'
        self.__abas.add(aba, text=titulo_aba)

        acoes = ttk.Frame(aba, style='TFrame')
        acoes.pack(fill='x', pady=(0, 10))

        ttk.Button(acoes, text='+ Publicar Oportunidade', style='Destaque.TButton', command=self.__publicar).pack(side='left', padx=(0, 8))
        ttk.Button(acoes, text='Ver Interessados', style='Primario.TButton', command=self.__ver_interessados).pack(side='left', padx=(0, 8))
        if not eh_admin:
            ttk.Button(acoes, text='Editar', style='Secundario.TButton', command=self.__editar).pack(side='left', padx=(0, 8))
        ttk.Button(acoes, text='Encerrar', style='Secundario.TButton', command=self.__encerrar).pack(side='left', padx=(0, 8))
        if eh_admin:
            ttk.Button(acoes, text='Remover Definitivamente', style='Perigo.TButton', command=self.__remover).pack(side='right')

        self.__tab_gestao = TabelaRolavel(
            aba,
            colunas=(
                ('id', '#', 50, 'center'),
                ('titulo', 'Título', 230, 'w'),
                ('categoria', 'Categoria', 155, 'w'),
                ('autor', 'Autor', 140, 'w'),
                ('situacao', 'Situação', 85, 'center'),
                ('prazo', 'Prazo', 90, 'center'),
                ('interessados', 'Interessados', 95, 'center'),
            ),
            altura=11,
            ao_selecionar=self.__mostrar_detalhe_gestao,
        )
        self.__tab_gestao.pack(fill='both', expand=True)

        detalhe = criar_bloco(aba, padding=10)
        detalhe.pack(fill='x', pady=(10, 0))
        self.__lbl_detalhe_gestao = ttk.Label(
            detalhe,
            text='Selecione uma publicação para ver os detalhes.',
            style='CardSuave.TLabel',
            wraplength=820,
            justify='left',
        )
        self.__lbl_detalhe_gestao.pack(anchor='w')

    def __carregar_gestao(self):
        lista = ops.listar_todas(self._conta) if self._eh_admin else ops.listar_minhas(self._perfil)
        self.__tab_gestao.preencher([
            (
                (
                    f'#{o.id}',
                    o.titulo,
                    o.nome_categoria,
                    o.autor_nome,
                    'Encerrada' if o.encerrada else 'Aberta',
                    formatar_data_br(o.prazo) if o.prazo else 'Sem prazo',
                    ops.contar_interessados(o.id),
                ),
                o,
            )
            for o in lista
        ])

    def __mostrar_detalhe_gestao(self, o):
        if not o:
            return
        self.__lbl_detalhe_gestao.configure(
            text=f'[#{o.id}] {o.titulo}\n{o.descricao}\nContato: {o.contato}',
            style='Card.TLabel',
        )

    def __publicar(self):
        dialogo = DialogoPublicarOportunidade(self.winfo_toplevel(), self.__autor)
        self.wait_window(dialogo)
        if dialogo.resultado is not None:
            self.__carregar_gestao()
            self.mostrar_info(f'Oportunidade publicada! Código: #{dialogo.resultado.id}')

    def __editar(self):
        o = self.__tab_gestao.selecionado()
        if not o:
            self.tratar_erro('Selecione uma publicação para editar.')
            return
        if o.encerrada:
            self.tratar_erro('Publicações encerradas não podem ser editadas.')
            return

        dialogo = DialogoEditarOportunidade(self.winfo_toplevel(), self._perfil, o)
        self.wait_window(dialogo)
        if dialogo.resultado is not None:
            self.__carregar_gestao()
            self.mostrar_info('Publicação atualizada com sucesso!')

    def __ver_interessados(self):
        o = self.__tab_gestao.selecionado()
        if not o:
            self.tratar_erro('Selecione uma publicação.')
            return

        try:
            lista = ops.listar_interessados(self.__autor, o.id)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        dialogo = DialogoInteressados(self.winfo_toplevel(), o, lista)
        self.wait_window(dialogo)

    def __encerrar(self):
        o = self.__tab_gestao.selecionado()
        if not o:
            self.tratar_erro('Selecione uma publicação para encerrar.')
            return
        if not self.confirmar(f'Encerrar a publicação #{o.id} ("{o.titulo}")?'):
            return

        try:
            ops.encerrar(self.__autor, o.id)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.__carregar_gestao()
        self.mostrar_info('Publicação encerrada.')

    def __remover(self):
        o = self.__tab_gestao.selecionado()
        if not o:
            self.tratar_erro('Selecione uma publicação para remover.')
            return
        if not self.confirmar(
            f'Remover DEFINITIVAMENTE #{o.id} ("{o.titulo}") e todos os interesses ligados a ela?'
        ):
            return

        try:
            ops.remover(self._conta, o.id)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.__carregar_gestao()
        self.mostrar_info('Publicação removida definitivamente.')
