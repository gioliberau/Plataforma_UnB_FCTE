import tkinter as tk
from tkinter import filedialog, ttk

from code_py import biblioteca as bib

from ..estilo import TabelaRolavel, formatar_data_br
from .base import TelaBase, criar_bloco


# ============================= { TELA DA BIBLIOTECA FCTE } ============================= #

class TelaBiblioteca(TelaBase):

    def __init__(self, master, sessao, ao_status=None, ao_navegar=None):
        super().__init__(master, sessao, ao_status=ao_status, ao_navegar=ao_navegar)
        self.__bib = bib.Biblioteca()
        self.__tem_perfil = self._eh_discente or self._eh_docente

        self.criar_cabecalho(
            'Biblioteca FCTE',
            'Pesquise o acervo, reserve exemplares, acompanhe prazos de devolução e renove empréstimos.',
        )

        self.__abas = ttk.Notebook(self)
        self.__abas.pack(fill='both', expand=True)

        self.__montar_aba_acervo()
        if self.__tem_perfil:
            self.__montar_aba_emprestimos()
            self.__montar_aba_historico()
        if self._eh_admin:
            self.__montar_aba_admin()

    def atualizar(self):
        self.__atualizar_areas()
        self.__buscar_livros()
        if self.__tem_perfil:
            self.__carregar_emprestimos()
            self.__carregar_historico()

    # ========== { ABA: ACERVO } ========== #

    def __montar_aba_acervo(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Acervo')

        barra = criar_bloco(aba, padding=10)
        barra.pack(fill='x', pady=(0, 10))

        linha = ttk.Frame(barra, style='Card.TFrame')
        linha.pack(fill='x')

        ttk.Label(linha, text='Buscar:', style='Card.TLabel').pack(side='left')
        self.__ent_busca = ttk.Entry(linha, width=26)
        self.__ent_busca.pack(side='left', padx=(6, 12))
        self.__ent_busca.bind('<Return>', lambda _e: self.__buscar_livros())

        ttk.Label(linha, text='Área:', style='Card.TLabel').pack(side='left')
        self.__var_area = tk.StringVar(value='Todas')
        self.__cmb_area = ttk.Combobox(linha, textvariable=self.__var_area, state='readonly', width=22)
        self.__cmb_area.pack(side='left', padx=(6, 12))
        self.__cmb_area.bind('<<ComboboxSelected>>', lambda _e: self.__buscar_livros())

        self.__var_disp = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            linha,
            text='Só disponíveis',
            variable=self.__var_disp,
            style='Card.TCheckbutton',
            command=self.__buscar_livros,
        ).pack(side='left', padx=(0, 12))

        ttk.Button(linha, text='Pesquisar', style='Primario.TButton', command=self.__buscar_livros).pack(side='left')

        if self.__tem_perfil:
            ttk.Button(
                linha,
                text='Reservar Selecionado',
                style='Destaque.TButton',
                command=self.__reservar,
            ).pack(side='right')

        self.__lbl_total_livros = ttk.Label(aba, text='', style='Suave.TLabel')
        self.__lbl_total_livros.pack(anchor='w', pady=(0, 6))

        self.__tab_acervo = TabelaRolavel(
            aba,
            colunas=(
                ('id', '#', 50, 'center'),
                ('titulo', 'Título', 300, 'w'),
                ('autores', 'Autor(es)', 220, 'w'),
                ('area', 'Área', 150, 'w'),
                ('disp', 'Disponibilidade', 120, 'center'),
            ),
            altura=13,
        )
        self.__tab_acervo.pack(fill='both', expand=True)

    def __atualizar_areas(self):
        areas = ['Todas'] + self.__bib.areas()
        self.__cmb_area['values'] = areas
        if self.__var_area.get() not in areas:
            self.__var_area.set('Todas')

    def __buscar_livros(self):
        termo = self.__ent_busca.get().strip()
        area = None if self.__var_area.get() == 'Todas' else self.__var_area.get()
        livros = self.__bib.buscar(termo, area=area, so_disponiveis=self.__var_disp.get())

        self.__lbl_total_livros.configure(text=f'{len(livros)} livro(s) encontrado(s).')
        self.__tab_acervo.preencher([
            (
                (
                    f'#{l.id}',
                    l.titulo,
                    l.autores,
                    l.area,
                    f'{l.disponiveis}/{l.exemplares} disp.' if l.disponiveis else 'Indisponível',
                ),
                l,
            )
            for l in livros
        ])

    def __reservar(self):
        livro = self.__tab_acervo.selecionado()
        if not livro:
            self.tratar_erro('Selecione um livro no acervo para reservar.')
            return

        if not self.confirmar(f'Reservar "{livro.titulo}" ({livro.autores})?'):
            return

        try:
            _, devolver_ate = self.__bib.reservar(self._perfil, livro.id)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.atualizar()
        self.mostrar_info(
            f'Reserva concluída!\nRetire na Biblioteca FCTE e devolva até {bib.formatar_data(devolver_ate)}.'
        )

    # ========== { ABA: MEUS EMPRÉSTIMOS } ========== #

    def __montar_aba_emprestimos(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Meus Empréstimos')

        regra = bib.regras[self._perfil.tipo_usuario]
        topo = ttk.Frame(aba, style='TFrame')
        topo.pack(fill='x', pady=(0, 8))

        ttk.Label(
            topo,
            text=(
                f"Limite: {regra['limite']} livros  |  Prazo: {regra['prazo_dias']} dias  |  "
                f"Até {bib.max_renovacoes} renovações  |  Multa: R$ {bib.multa_por_dia:.2f}/dia"
            ),
            style='Suave.TLabel',
        ).pack(side='left')

        ttk.Button(topo, text='Devolver Livro', style='Perigo.TButton', command=self.__devolver).pack(side='right')
        ttk.Button(topo, text='Renovar Empréstimo', style='Primario.TButton', command=self.__renovar).pack(side='right', padx=(0, 8))

        self.__tab_emp = TabelaRolavel(
            aba,
            colunas=(
                ('id', '#', 50, 'center'),
                ('titulo', 'Livro', 280, 'w'),
                ('retirado', 'Retirado em', 95, 'center'),
                ('prazo', 'Devolver até', 95, 'center'),
                ('renov', 'Renovações', 90, 'center'),
                ('status', 'Situação', 250, 'w'),
            ),
            altura=13,
        )
        self.__tab_emp.pack(fill='both', expand=True)

    def __carregar_emprestimos(self):
        ativos = self.__bib.emprestimos_ativos(self._perfil)
        self.__tab_emp.preencher([
            (
                (
                    f'#{e.id}',
                    e.titulo,
                    formatar_data_br(e.retirado_em),
                    formatar_data_br(e.devolver_ate),
                    f'{e.renovacoes}/{bib.max_renovacoes}',
                    e.status,
                ),
                e,
            )
            for e in ativos
        ])

    def __renovar(self):
        emp = self.__tab_emp.selecionado()
        if not emp:
            self.tratar_erro('Selecione um empréstimo ativo para renovar.')
            return

        try:
            nova_data = self.__bib.renovar(self._perfil, emp.id)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.atualizar()
        self.mostrar_info(f'Empréstimo renovado! Novo prazo: {bib.formatar_data(nova_data)}.')

    def __devolver(self):
        emp = self.__tab_emp.selecionado()
        if not emp:
            self.tratar_erro('Selecione um empréstimo ativo para devolver.')
            return

        if not self.confirmar(f'Confirmar devolução de "{emp.titulo}"?'):
            return

        try:
            multa = self.__bib.devolver(self._perfil, emp.id)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.atualizar()
        mensagem = 'Livro devolvido com sucesso!'
        if multa:
            mensagem += f'\nMulta por atraso: R$ {multa:.2f}'
        self.mostrar_info(mensagem)

    # ========== { ABA: HISTÓRICO } ========== #

    def __montar_aba_historico(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Histórico')

        self.__tab_hist = TabelaRolavel(
            aba,
            colunas=(
                ('id', '#', 50, 'center'),
                ('titulo', 'Livro', 280, 'w'),
                ('retirado', 'Retirado em', 95, 'center'),
                ('devolvido', 'Devolvido em', 95, 'center'),
                ('renov', 'Renovações', 85, 'center'),
                ('status', 'Situação', 250, 'w'),
            ),
            altura=14,
        )
        self.__tab_hist.pack(fill='both', expand=True)

    def __carregar_historico(self):
        hist = self.__bib.historico(self._perfil)
        self.__tab_hist.preencher([
            (
                (
                    f'#{e.id}',
                    e.titulo,
                    formatar_data_br(e.retirado_em),
                    formatar_data_br(e.devolvido_em) if e.devolvido_em else 'Em aberto',
                    f'{e.renovacoes}/{bib.max_renovacoes}',
                    e.status,
                ),
                e,
            )
            for e in hist
        ])

    # ========== { ABA: ADMINISTRAÇÃO DO ACERVO } ========== #

    def __montar_aba_admin(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Administração do Acervo')

        bloco_cad = criar_bloco(aba, titulo='Cadastrar Novo Livro', padding=14)
        bloco_cad.pack(fill='x', pady=(0, 12))

        grade = ttk.Frame(bloco_cad, style='Card.TFrame')
        grade.pack(fill='x')
        grade.columnconfigure(1, weight=1)

        ttk.Label(grade, text='Título:', style='Card.TLabel').grid(row=0, column=0, sticky='w', pady=4, padx=(0, 8))
        self.__ent_titulo = ttk.Entry(grade)
        self.__ent_titulo.grid(row=0, column=1, sticky='ew', pady=4)

        ttk.Label(grade, text='Autor(es):', style='Card.TLabel').grid(row=1, column=0, sticky='w', pady=4, padx=(0, 8))
        self.__ent_autores = ttk.Entry(grade)
        self.__ent_autores.grid(row=1, column=1, sticky='ew', pady=4)

        ttk.Label(grade, text='Área:', style='Card.TLabel').grid(row=2, column=0, sticky='w', pady=4, padx=(0, 8))
        self.__ent_area = ttk.Entry(grade)
        self.__ent_area.grid(row=2, column=1, sticky='ew', pady=4)

        ttk.Label(grade, text='Exemplares:', style='Card.TLabel').grid(row=3, column=0, sticky='w', pady=4, padx=(0, 8))
        self.__ent_exemplares = ttk.Entry(grade, width=10)
        self.__ent_exemplares.insert(0, '1')
        self.__ent_exemplares.grid(row=3, column=1, sticky='w', pady=4)

        ttk.Button(grade, text='Cadastrar Livro', style='Destaque.TButton', command=self.__cadastrar_livro).grid(
            row=4, column=1, sticky='e', pady=(8, 0)
        )

        bloco_lote = criar_bloco(aba, titulo='Importação em Lote', padding=14)
        bloco_lote.pack(fill='x')

        ttk.Label(
            bloco_lote,
            text='Importe livros a partir de um CSV (colunas: titulo;autores;area;exemplares) ou recarregue o JSON padrão.',
            style='CardSuave.TLabel',
        ).pack(anchor='w', pady=(0, 10))

        linha_b = ttk.Frame(bloco_lote, style='Card.TFrame')
        linha_b.pack(fill='x')
        ttk.Button(linha_b, text='Importar arquivo CSV...', style='Primario.TButton', command=self.__importar_csv).pack(side='left', padx=(0, 10))
        ttk.Button(linha_b, text='Recarregar acervo_biblioteca.json', style='Secundario.TButton', command=self.__recarregar_json).pack(side='left')

    def __cadastrar_livro(self):
        try:
            exemplares = int(self.__ent_exemplares.get().strip())
        except ValueError:
            self.tratar_erro('Número de exemplares deve ser um inteiro.')
            return

        try:
            self.__bib.cadastrar_livro(
                self._conta,
                self.__ent_titulo.get(),
                self.__ent_autores.get(),
                self.__ent_area.get(),
                exemplares,
            )
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.__ent_titulo.delete(0, 'end')
        self.__ent_autores.delete(0, 'end')
        self.__ent_area.delete(0, 'end')
        self.__ent_exemplares.delete(0, 'end')
        self.__ent_exemplares.insert(0, '1')
        self.atualizar()
        self.mostrar_info('Livro cadastrado com sucesso!')

    def __importar_csv(self):
        caminho = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title='Selecionar arquivo CSV do acervo',
            filetypes=[('Arquivos CSV', '*.csv'), ('Todos os arquivos', '*.*')],
        )
        if not caminho:
            return

        try:
            novos, atualizados = self.__bib.importar_csv(self._conta, caminho)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.atualizar()
        self.mostrar_info(f'Acervo importado: {novos} livro(s) novo(s) e {atualizados} atualizado(s).')

    def __recarregar_json(self):
        if not self.confirmar('Reler o arquivo data/acervo_biblioteca.json e atualizar o acervo?'):
            return

        try:
            total = self.__bib.recarregar_acervo(self._conta)
        except (ValueError, PermissionError, OSError) as erro:
            self.tratar_erro(erro)
            return

        self.atualizar()
        self.mostrar_info(f'Acervo recarregado com sucesso ({total} livros no arquivo JSON).')
