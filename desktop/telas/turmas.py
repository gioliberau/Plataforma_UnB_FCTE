import tkinter as tk
from tkinter import messagebox, ttk

from code_py import banco, turmas as tr
from code_py.horarios import legivel
from code_py.system import SistemaFCTE
from code_py.user import semestre_atual

from ..estilo import CORES, DialogoBase, TabelaRolavel, formatar_indice, parsear_periodo
from .base import TelaBase, criar_bloco


# ============================= { DIÁLOGO DE LANÇAMENTO DE NOTA } ============================= #

class DialogoLancarNota(DialogoBase):

    def __init__(self, master, docente, chave_turma, aluno):
        super().__init__(master, 'Lançar Nota', largura=380)
        self.__docente = docente
        self.__chave = chave_turma
        self.__aluno = aluno

        ttk.Label(self.corpo, text=aluno['nome'], style='Subtitulo.TLabel').pack(anchor='w')
        ttk.Label(self.corpo, text=f"Matrícula: {aluno['matricula']}", style='CardSuave.TLabel').pack(anchor='w', pady=(2, 12))

        ttk.Label(self.corpo, text='Nota (0 a 10):', style='Card.TLabel').pack(anchor='w')
        self.__ent_nota = ttk.Entry(self.corpo)
        if aluno['nota'] is not None:
            self.__ent_nota.insert(0, f"{aluno['nota']:.1f}")
        self.__ent_nota.pack(fill='x', pady=(3, 14))

        botoes = ttk.Frame(self.corpo, style='Card.TFrame')
        botoes.pack(fill='x')
        ttk.Button(botoes, text='Cancelar', style='Secundario.TButton', command=self.cancelar).pack(side='left')
        ttk.Button(botoes, text='Salvar nota', style='Primario.TButton', command=self.__salvar).pack(side='right')

        self.bind('<Return>', lambda _e: self.__salvar())
        self.__ent_nota.focus_set()
        self.finalizar_layout()

    def __salvar(self):
        texto = self.__ent_nota.get().strip().replace(',', '.')
        try:
            nota = float(texto)
            tr.lancar_nota(self.__docente, self.__chave, self.__aluno['matricula'], nota)
        except (ValueError, PermissionError) as erro:
            messagebox.showerror('Nota inválida', str(erro), parent=self)
            return

        self.resultado = nota
        self.destroy()


# ============================= { TELA DE TURMAS DO SIGAA } ============================= #

class TelaTurmas(TelaBase):

    def __init__(self, master, sessao, ao_status=None, ao_navegar=None):
        super().__init__(master, sessao, ao_status=ao_status, ao_navegar=ao_navegar)
        self.__sistema = SistemaFCTE()
        self.__docente_turmas_mapa = {}
        self.__admin_discentes_mapa = {}
        self.__admin_docentes_mapa = {}
        self.__admin_turmas_mapa = {}

        self.criar_cabecalho(
            'Turmas do SIGAA — FCTE',
            'Consulta de ofertas de disciplinas, horários traduzidos, matrículas e lançamento de notas.',
        )

        self.__abas = ttk.Notebook(self)
        self.__abas.pack(fill='both', expand=True)

        self.__montar_aba_consulta()
        if self._eh_discente:
            self.__montar_aba_discente()
        if self._eh_docente:
            self.__montar_aba_docente()
        if self._eh_admin:
            self.__montar_aba_admin()

    def atualizar(self):
        self.__buscar_turmas()
        if self._eh_discente:
            self.__carregar_minhas_discente()
        if self._eh_docente:
            self.__carregar_turmas_docente()
        if self._eh_admin:
            self.__carregar_listas_admin()

    # ========== { ABA: CONSULTA PÚBLICA } ========== #

    def __montar_aba_consulta(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Consultar Turmas (SIGAA)')

        ano, sem = semestre_atual()
        filtros = criar_bloco(aba, padding=10)
        filtros.pack(fill='x', pady=(0, 10))

        linha = ttk.Frame(filtros, style='Card.TFrame')
        linha.pack(fill='x')

        ttk.Label(linha, text='Buscar (disciplina, código ou docente):', style='Card.TLabel').pack(side='left')
        self.__ent_filtro = ttk.Entry(linha, width=28)
        self.__ent_filtro.pack(side='left', padx=(6, 12))
        self.__ent_filtro.bind('<Return>', lambda _e: self.__buscar_turmas())

        ttk.Label(linha, text='Período (AAAA.S):', style='Card.TLabel').pack(side='left')
        self.__ent_periodo = ttk.Entry(linha, width=10)
        self.__ent_periodo.insert(0, f'{ano}.{sem}')
        self.__ent_periodo.pack(side='left', padx=(6, 12))
        self.__ent_periodo.bind('<Return>', lambda _e: self.__buscar_turmas())

        ttk.Button(linha, text='Buscar', style='Primario.TButton', command=self.__buscar_turmas).pack(side='left', padx=(0, 6))
        ttk.Button(linha, text='Limpar', style='Secundario.TButton', command=self.__limpar_busca).pack(side='left')

        self.__lbl_contagem = ttk.Label(aba, text='', style='Suave.TLabel')
        self.__lbl_contagem.pack(anchor='w', pady=(0, 6))

        self.__tab_consulta = TabelaRolavel(
            aba,
            colunas=(
                ('codigo', 'Código', 80, 'w'),
                ('disciplina', 'Disciplina', 220, 'w'),
                ('turma', 'Turma', 55, 'center'),
                ('periodo', 'Período', 70, 'center'),
                ('docente', 'Docente', 160, 'w'),
                ('horario', 'Horário', 200, 'w'),
                ('local', 'Local', 95, 'w'),
                ('vagas', 'Vagas', 75, 'center'),
            ),
            altura=11,
            ao_selecionar=self.__mostrar_detalhe_turma,
        )
        self.__tab_consulta.pack(fill='both', expand=True)

        detalhe = criar_bloco(aba, padding=10)
        detalhe.pack(fill='x', pady=(10, 0))
        self.__lbl_detalhe = ttk.Label(
            detalhe,
            text='Selecione uma turma na tabela para ver detalhes completos.',
            style='CardSuave.TLabel',
            wraplength=820,
            justify='left',
        )
        self.__lbl_detalhe.pack(anchor='w')

    def __limpar_busca(self):
        ano, sem = semestre_atual()
        self.__ent_filtro.delete(0, 'end')
        self.__ent_periodo.delete(0, 'end')
        self.__ent_periodo.insert(0, f'{ano}.{sem}')
        self.__buscar_turmas()

    def __buscar_turmas(self):
        try:
            ano, sem = parsear_periodo(self.__ent_periodo.get())
        except ValueError as erro:
            self.tratar_erro(erro)
            return

        filtro = self.__ent_filtro.get().strip() or None
        turmas = self.__sistema.listar_turmas(ano, sem, filtro)

        linhas = [
            (
                (
                    t.get('codigo_disciplina', ''),
                    t.get('nome_disciplina', ''),
                    t.get('numero_turma', ''),
                    t.get('periodo', ''),
                    t.get('docente', ''),
                    legivel(t.get('horario', '')),
                    t.get('local', '—'),
                    f"{t.get('vagas_ocupadas', '?')}/{t.get('vagas_ofertadas', '?')}",
                ),
                t,
            )
            for t in turmas
        ]
        self.__tab_consulta.preencher(linhas)
        self.__lbl_contagem.configure(text=f'{len(turmas)} turma(s) encontrada(s).')

    def __mostrar_detalhe_turma(self, turma):
        if not turma:
            return
        carga = f"{turma['carga_horaria']}h" if turma.get('carga_horaria') else 'não informada'
        texto = (
            f"{turma.get('codigo_disciplina')} — {turma.get('nome_disciplina')} "
            f"(Turma {turma.get('numero_turma')} | Período {turma.get('periodo')})\n"
            f"Docente: {turma.get('docente')}  |  Carga horária: {carga}  |  Local: {turma.get('local', '—')}\n"
            f"Horário: {legivel(turma.get('horario', ''))}  |  "
            f"Vagas ocupadas: {turma.get('vagas_ocupadas', '?')} de {turma.get('vagas_ofertadas', '?')}"
        )
        self.__lbl_detalhe.configure(text=texto, style='Card.TLabel')

    # ========== { ABA: DISCENTE } ========== #

    def __montar_aba_discente(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Minhas Turmas e Notas')

        self.__lbl_indices = ttk.Label(aba, text='', style='Subtitulo.TLabel', background=CORES['fundo'])
        self.__lbl_indices.pack(anchor='w', pady=(0, 8))

        self.__tab_discente = TabelaRolavel(
            aba,
            colunas=(
                ('codigo', 'Código', 85, 'w'),
                ('disciplina', 'Disciplina', 230, 'w'),
                ('turma', 'Turma', 55, 'center'),
                ('periodo', 'Período', 75, 'center'),
                ('creditos', 'Créd.', 55, 'center'),
                ('horario', 'Horário', 230, 'w'),
                ('resultado', 'Nota / Menção', 115, 'center'),
            ),
            altura=13,
        )
        self.__tab_discente.pack(fill='both', expand=True)

    def __carregar_minhas_discente(self):
        matriculas = tr.turmas_do_discente(self._perfil)
        valor_mp = formatar_indice(tr.mp(self._perfil))
        valor_ira = formatar_indice(tr.ira(self._perfil))
        self.__lbl_indices.configure(text=f'MP: {valor_mp}   |   IRA: {valor_ira}   |   {len(matriculas)} disciplina(s)')

        linhas = [
            (
                (
                    m.turma['codigo_disciplina'],
                    m.turma['nome_disciplina'],
                    m.turma['numero_turma'],
                    m.turma['periodo'],
                    m.creditos,
                    legivel(m.turma.get('horario', '')),
                    'Sem nota' if m.nota is None else f'{m.nota:.1f} ({m.mencao})',
                ),
                m,
            )
            for m in matriculas
        ]
        self.__tab_discente.preencher(linhas)

    # ========== { ABA: DOCENTE } ========== #

    def __montar_aba_docente(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Minhas Turmas e Notas')

        topo = criar_bloco(aba, padding=10)
        topo.pack(fill='x', pady=(0, 10))

        linha = ttk.Frame(topo, style='Card.TFrame')
        linha.pack(fill='x')

        ttk.Label(linha, text='Selecione uma turma:', style='Card.TLabel').pack(side='left')
        self.__var_turma_doc = tk.StringVar()
        self.__cmb_turma_doc = ttk.Combobox(linha, textvariable=self.__var_turma_doc, state='readonly', width=55)
        self.__cmb_turma_doc.pack(side='left', padx=(8, 10), fill='x', expand=True)
        self.__cmb_turma_doc.bind('<<ComboboxSelected>>', lambda _e: self.__carregar_alunos_docente())

        ttk.Button(linha, text='Lançar Nota', style='Destaque.TButton', command=self.__lancar_nota).pack(side='right')

        self.__lbl_turma_doc_info = ttk.Label(aba, text='', style='Suave.TLabel')
        self.__lbl_turma_doc_info.pack(anchor='w', pady=(0, 6))

        self.__tab_alunos = TabelaRolavel(
            aba,
            colunas=(
                ('matricula', 'Matrícula', 120, 'center'),
                ('nome', 'Discente', 320, 'w'),
                ('nota', 'Nota', 90, 'center'),
                ('mencao', 'Menção', 90, 'center'),
            ),
            altura=12,
        )
        self.__tab_alunos.pack(fill='both', expand=True)

    def __carregar_turmas_docente(self):
        turmas = tr.turmas_do_docente(self._perfil)
        self.__docente_turmas_mapa = {}
        rotulos = []
        for t in turmas:
            rotulo = f"{t['periodo']} | {t['codigo_disciplina']} - {t['nome_disciplina']} (Turma {t['numero_turma']})"
            self.__docente_turmas_mapa[rotulo] = t
            rotulos.append(rotulo)

        self.__cmb_turma_doc['values'] = rotulos
        if rotulos:
            if self.__var_turma_doc.get() not in self.__docente_turmas_mapa:
                self.__var_turma_doc.set(rotulos[0])
            self.__carregar_alunos_docente()
        else:
            self.__var_turma_doc.set('')
            self.__tab_alunos.preencher([])
            self.__lbl_turma_doc_info.configure(text='Nenhuma turma vinculada a você. Peça a um admin para atribuir.')

    def __carregar_alunos_docente(self):
        turma = self.__docente_turmas_mapa.get(self.__var_turma_doc.get())
        if not turma:
            return
        chave = tr.chave_turma(turma)
        alunos = tr.alunos_da_turma(self._perfil, chave)
        self.__lbl_turma_doc_info.configure(
            text=f"Horário: {legivel(turma.get('horario', ''))}  |  Local: {turma.get('local', '—')}  |  {len(alunos)} aluno(s)"
        )
        linhas = [
            (
                (
                    a['matricula'],
                    a['nome'],
                    '—' if a['nota'] is None else f"{a['nota']:.1f}",
                    '—' if a['nota'] is None else tr.mencao(a['nota']),
                ),
                a,
            )
            for a in alunos
        ]
        self.__tab_alunos.preencher(linhas)

    def __lancar_nota(self):
        turma = self.__docente_turmas_mapa.get(self.__var_turma_doc.get())
        aluno = self.__tab_alunos.selecionado()
        if not turma or not aluno:
            self.tratar_erro('Selecione um aluno na tabela para lançar ou alterar a nota.')
            return

        chave = tr.chave_turma(turma)
        dialogo = DialogoLancarNota(self.winfo_toplevel(), self._perfil, chave, aluno)
        self.wait_window(dialogo)
        if dialogo.resultado is not None:
            self.__carregar_alunos_docente()
            self.mostrar_info(f"Nota {dialogo.resultado:.1f} ({tr.mencao(dialogo.resultado)}) salva com sucesso!")

    # ========== { ABA: GESTÃO ADMIN } ========== #

    def __montar_aba_admin(self):
        aba = ttk.Frame(self.__abas, style='TFrame', padding=12)
        self.__abas.add(aba, text='Gestão Acadêmica (Admin)')

        # 1) Atualizar SIGAA
        bloco_sigaa = criar_bloco(aba, titulo='Atualizar Turmas a partir do SIGAA', padding=12)
        bloco_sigaa.pack(fill='x', pady=(0, 12))

        ano, sem = semestre_atual()
        linha_s = ttk.Frame(bloco_sigaa, style='Card.TFrame')
        linha_s.pack(fill='x')
        ttk.Label(linha_s, text='Período (AAAA.S):', style='Card.TLabel').pack(side='left')
        self.__ent_periodo_sigaa = ttk.Entry(linha_s, width=10)
        self.__ent_periodo_sigaa.insert(0, f'{ano}.{sem}')
        self.__ent_periodo_sigaa.pack(side='left', padx=(6, 12))
        self.__btn_atualizar_sigaa = ttk.Button(
            linha_s,
            text='Consultar e Gravar Turmas do SIGAA',
            style='Primario.TButton',
            command=self.__atualizar_sigaa,
        )
        self.__btn_atualizar_sigaa.pack(side='left')

        # 2) Matricular discente
        bloco_mat = criar_bloco(aba, titulo='Matricular Discente em Turma', padding=12)
        bloco_mat.pack(fill='x', pady=(0, 12))

        g_mat = ttk.Frame(bloco_mat, style='Card.TFrame')
        g_mat.pack(fill='x')
        g_mat.columnconfigure(1, weight=1)

        ttk.Label(g_mat, text='Discente:', style='Card.TLabel').grid(row=0, column=0, sticky='w', pady=4, padx=(0, 8))
        self.__var_admin_discente = tk.StringVar()
        self.__cmb_admin_discente = ttk.Combobox(g_mat, textvariable=self.__var_admin_discente, state='readonly')
        self.__cmb_admin_discente.grid(row=0, column=1, sticky='ew', pady=4)

        ttk.Label(g_mat, text='Turma (semestre atual):', style='Card.TLabel').grid(row=1, column=0, sticky='w', pady=4, padx=(0, 8))
        self.__var_admin_turma_m = tk.StringVar()
        self.__cmb_admin_turma_m = ttk.Combobox(g_mat, textvariable=self.__var_admin_turma_m, state='readonly')
        self.__cmb_admin_turma_m.grid(row=1, column=1, sticky='ew', pady=4)

        ttk.Button(g_mat, text='Matricular', style='Destaque.TButton', command=self.__matricular_discente).grid(
            row=2, column=1, sticky='e', pady=(8, 0)
        )

        # 3) Atribuir docente
        bloco_doc = criar_bloco(aba, titulo='Ligar Turma a Docente', padding=12)
        bloco_doc.pack(fill='x')

        g_doc = ttk.Frame(bloco_doc, style='Card.TFrame')
        g_doc.pack(fill='x')
        g_doc.columnconfigure(1, weight=1)

        ttk.Label(g_doc, text='Docente:', style='Card.TLabel').grid(row=0, column=0, sticky='w', pady=4, padx=(0, 8))
        self.__var_admin_docente = tk.StringVar()
        self.__cmb_admin_docente = ttk.Combobox(g_doc, textvariable=self.__var_admin_docente, state='readonly')
        self.__cmb_admin_docente.grid(row=0, column=1, sticky='ew', pady=4)

        ttk.Label(g_doc, text='Turma (semestre atual):', style='Card.TLabel').grid(row=1, column=0, sticky='w', pady=4, padx=(0, 8))
        self.__var_admin_turma_d = tk.StringVar()
        self.__cmb_admin_turma_d = ttk.Combobox(g_doc, textvariable=self.__var_admin_turma_d, state='readonly')
        self.__cmb_admin_turma_d.grid(row=1, column=1, sticky='ew', pady=4)

        ttk.Button(g_doc, text='Atribuir Docente', style='Primario.TButton', command=self.__atribuir_docente).grid(
            row=2, column=1, sticky='e', pady=(8, 0)
        )

    def __carregar_listas_admin(self):
        discentes = banco.listar_perfis('discente')
        docentes = banco.listar_perfis('docente')
        turmas = self.__sistema.listar_turmas()

        self.__admin_discentes_mapa = {f'{d.nome} ({d.id_user}) — {d.curso}': d.id_user for d in discentes}
        self.__admin_docentes_mapa = {f'{d.nome} ({d.id_user}) — {d.area}': d.id_user for d in docentes}
        self.__admin_turmas_mapa = {
            f"{t['periodo']} | {t['codigo_disciplina']} - {t['nome_disciplina']} (Turma {t['numero_turma']})": tr.chave_turma(t)
            for t in turmas
        }

        self.__cmb_admin_discente['values'] = list(self.__admin_discentes_mapa)
        self.__cmb_admin_docente['values'] = list(self.__admin_docentes_mapa)
        rotulos_turmas = list(self.__admin_turmas_mapa)
        self.__cmb_admin_turma_m['values'] = rotulos_turmas
        self.__cmb_admin_turma_d['values'] = rotulos_turmas

        if self.__admin_discentes_mapa and not self.__var_admin_discente.get():
            self.__var_admin_discente.set(next(iter(self.__admin_discentes_mapa)))
        if self.__admin_docentes_mapa and not self.__var_admin_docente.get():
            self.__var_admin_docente.set(next(iter(self.__admin_docentes_mapa)))
        if rotulos_turmas:
            if not self.__var_admin_turma_m.get():
                self.__var_admin_turma_m.set(rotulos_turmas[0])
            if not self.__var_admin_turma_d.get():
                self.__var_admin_turma_d.set(rotulos_turmas[0])

    def __atualizar_sigaa(self):
        try:
            ano, sem = parsear_periodo(self.__ent_periodo_sigaa.get())
        except ValueError as erro:
            self.tratar_erro(erro)
            return

        if not self.confirmar('Consultar o site público do SIGAA agora? Isso pode levar alguns segundos.'):
            return

        self.__btn_atualizar_sigaa.configure(state='disabled')

        def tarefa():
            return self.__sistema.atualizar_turmas_sigaa(self._conta, ano, sem)

        def ao_sucesso(total):
            self.__btn_atualizar_sigaa.configure(state='normal')
            self.atualizar()
            self.mostrar_info(f'Turmas atualizadas com sucesso ({total} turmas gravadas).')

        def ao_erro(erro):
            self.__btn_atualizar_sigaa.configure(state='normal')
            self.tratar_erro(erro)

        self.executar_em_segundo_plano(tarefa, ao_sucesso, 'Consultando turmas no SIGAA...', ao_erro=ao_erro)

    def __matricular_discente(self):
        id_aluno = self.__admin_discentes_mapa.get(self.__var_admin_discente.get())
        chave = self.__admin_turmas_mapa.get(self.__var_admin_turma_m.get())
        if not id_aluno or not chave:
            self.tratar_erro('Selecione o discente e a turma.')
            return

        try:
            tr.matricular(self._conta, id_aluno, chave)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.mostrar_info('Discente matriculado(a) com sucesso!')

    def __atribuir_docente(self):
        id_doc = self.__admin_docentes_mapa.get(self.__var_admin_docente.get())
        chave = self.__admin_turmas_mapa.get(self.__var_admin_turma_d.get())
        if not id_doc or not chave:
            self.tratar_erro('Selecione o docente e a turma.')
            return

        try:
            tr.atribuir_docente(self._conta, id_doc, chave)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.mostrar_info('Docente vinculado(a) à turma com sucesso!')
