from tkinter import ttk

from code_py import banco, organizacoes as ops, turmas as tr
from code_py.biblioteca import Biblioteca
from code_py.horarios import legivel
from code_py.user import semestre_atual

from ..estilo import CORES, TabelaRolavel, criar_card_indicador, formatar_indice
from .base import TelaBase, criar_bloco


# ============================= { TELA INICIAL / MEU PERFIL } ============================= #

class TelaInicio(TelaBase):

    def __init__(self, master, sessao, ao_status=None, ao_navegar=None):
        super().__init__(master, sessao, ao_status=ao_status, ao_navegar=ao_navegar)
        self.__conteudo = ttk.Frame(self, style='TFrame')
        self.__conteudo.pack(fill='both', expand=True)

    def atualizar(self):
        for filho in self.__conteudo.winfo_children():
            filho.destroy()

        if not self._autenticado:
            self.__montar_visitante()
        elif self._eh_discente:
            self.__montar_discente()
        elif self._eh_docente:
            self.__montar_docente()
        else:
            self.__montar_admin()

    # ========== { VISITANTE (PORTAL PÚBLICO) } ========== #

    def __montar_visitante(self):
        ano, sem = semestre_atual()
        ttk.Label(self.__conteudo, text='Bem-vindo(a) ao Portal Público — UnB FCTE', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(
            self.__conteudo,
            text=f'Campus Gama | Semestre {ano}.{sem} — Consulte serviços públicos do campus sem precisar fazer login.',
            style='Suave.TLabel',
        ).pack(anchor='w', pady=(2, 16))

        grade = ttk.Frame(self.__conteudo, style='TFrame')
        grade.pack(fill='x')
        for col in range(2):
            grade.columnconfigure(col, weight=1)

        atalhos = [
            ('Turmas do SIGAA', 'Consulte disciplinas ofertadas na FCTE, horários legíveis, docentes e vagas.', 'turmas'),
            ('Cardápio do RU — Gama', 'Veja as refeições da semana filtradas pela sua preferência alimentar.', 'cardapio'),
            ('Biblioteca FCTE', 'Pesquise livros no acervo por título, autor, área e disponibilidade.', 'biblioteca'),
            ('Campus (Organizações, Calendário e Cursos)', 'Conheça EJs, atlética, equipes de competição, calendário SAA e cursos.', 'campus'),
        ]

        for idx, (titulo, desc, destino) in enumerate(atalhos):
            bloco = criar_bloco(grade, titulo=titulo, padding=16)
            bloco.grid(row=idx // 2, column=idx % 2, sticky='nsew', padx=(0 if idx % 2 == 0 else 10, 0), pady=(0, 12))
            ttk.Label(bloco, text=desc, style='CardSuave.TLabel', wraplength=380).pack(anchor='w', pady=(0, 12))
            ttk.Button(
                bloco,
                text='Abrir módulo',
                style='Primario.TButton',
                command=lambda d=destino: self.navegar(d),
            ).pack(anchor='w')

    # ========== { DISCENTE } ========== #

    def __montar_discente(self):
        perfil = self._perfil
        matriculas = tr.turmas_do_discente(perfil)
        valor_ira = formatar_indice(tr.ira(perfil))
        valor_mp = formatar_indice(tr.mp(perfil))
        creditos = sum(m.creditos for m in matriculas if m.aprovado)

        ttk.Label(self.__conteudo, text=f'Olá, {perfil.nome}!', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(
            self.__conteudo,
            text='Resumo do seu desempenho acadêmico e dos seus dados cadastrais.',
            style='Suave.TLabel',
        ).pack(anchor='w', pady=(2, 14))

        cards = ttk.Frame(self.__conteudo, style='TFrame')
        cards.pack(fill='x', pady=(0, 14))
        for i in range(4):
            cards.columnconfigure(i, weight=1)

        c1, _, _ = criar_card_indicador(cards, 'IRA (Índice de Rendimento)', valor_ira, 'Escala UnB (0 a 5)', CORES['destaque'])
        c2, _, _ = criar_card_indicador(cards, 'MP (Média Ponderada)', valor_mp, 'Escala UnB (0 a 5)')
        c3, _, _ = criar_card_indicador(cards, 'Matrícula', perfil.id_user, f'Ingresso em {perfil.ano_entrada}.{perfil.semestre_entrada}')
        c4, _, _ = criar_card_indicador(cards, 'Créditos Concluídos', creditos, f'{len(matriculas)} disciplina(s) no histórico')

        for idx, card in enumerate((c1, c2, c3, c4)):
            card.grid(row=0, column=idx, sticky='nsew', padx=(0 if idx == 0 else 10, 0))

        self.__montar_dados_cadastrais(perfil)

        bloco_turmas = criar_bloco(self.__conteudo, titulo='Minhas Turmas e Menções')
        bloco_turmas.pack(fill='both', expand=True, pady=(12, 0))

        tabela = TabelaRolavel(
            bloco_turmas,
            colunas=(
                ('codigo', 'Código', 90, 'w'),
                ('disciplina', 'Disciplina', 250, 'w'),
                ('periodo', 'Período', 75, 'center'),
                ('creditos', 'Créd.', 55, 'center'),
                ('horario', 'Horário', 230, 'w'),
                ('resultado', 'Nota / Menção', 110, 'center'),
            ),
            altura=7,
        )
        tabela.pack(fill='both', expand=True)

        linhas = [
            (
                (
                    m.turma['codigo_disciplina'],
                    m.turma['nome_disciplina'],
                    m.turma['periodo'],
                    m.creditos,
                    legivel(m.turma.get('horario', '')),
                    'Cursando' if m.nota is None else f'{m.nota:.1f} ({m.mencao})',
                ),
                m,
            )
            for m in matriculas
        ]
        tabela.preencher(linhas)

    # ========== { DOCENTE } ========== #

    def __montar_docente(self):
        perfil = self._perfil
        ano, sem = semestre_atual()
        ofertadas = tr.turmas_do_docente(perfil)
        creditos = tr.creditos_ofertados(perfil)
        extensao = ops.listar_extensao(perfil)

        ttk.Label(self.__conteudo, text=f'Olá, Prof. {perfil.nome}!', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(
            self.__conteudo,
            text='Visão geral das suas turmas ofertadas, projetos de extensão e perfil docente.',
            style='Suave.TLabel',
        ).pack(anchor='w', pady=(2, 14))

        cards = ttk.Frame(self.__conteudo, style='TFrame')
        cards.pack(fill='x', pady=(0, 14))
        for i in range(4):
            cards.columnconfigure(i, weight=1)

        c1, _, _ = criar_card_indicador(cards, 'Matrícula Funcional', perfil.id_user, f'Ingresso em {perfil.ano_entrada}.{perfil.semestre_entrada}', CORES['destaque'])
        c2, _, _ = criar_card_indicador(cards, 'Créditos Ofertados', creditos, f'Semestre {ano}.{sem}')
        c3, _, _ = criar_card_indicador(cards, 'Turmas Vinculadas', len(ofertadas), perfil.curso_ou_area)
        c4, _, _ = criar_card_indicador(cards, 'Projetos de Extensão', len(extensao), 'Publicados no mural')

        for idx, card in enumerate((c1, c2, c3, c4)):
            card.grid(row=0, column=idx, sticky='nsew', padx=(0 if idx == 0 else 10, 0))

        self.__montar_dados_cadastrais(
            perfil,
            extras=[('Projetos de extensão', ', '.join(o.titulo for o in extensao) or 'Nenhum')],
        )

        bloco_turmas = criar_bloco(self.__conteudo, titulo='Minhas Turmas Ofertadas')
        bloco_turmas.pack(fill='both', expand=True, pady=(12, 0))

        tabela = TabelaRolavel(
            bloco_turmas,
            colunas=(
                ('codigo', 'Código', 90, 'w'),
                ('disciplina', 'Disciplina', 260, 'w'),
                ('turma', 'Turma / Período', 110, 'center'),
                ('creditos', 'Créd.', 55, 'center'),
                ('horario', 'Horário', 250, 'w'),
            ),
            altura=7,
        )
        tabela.pack(fill='both', expand=True)

        linhas = [
            (
                (
                    t['codigo_disciplina'],
                    t['nome_disciplina'],
                    f"{t['numero_turma']} ({t['periodo']})",
                    (t.get('carga_horaria') or 0) // tr.horas_por_credito,
                    legivel(t.get('horario', '')),
                ),
                t,
            )
            for t in ofertadas
        ]
        tabela.preencher(linhas)

    # ========== { ADMIN } ========== #

    def __montar_admin(self):
        discentes = banco.listar_perfis('discente')
        docentes = banco.listar_perfis('docente')
        oportunidades = ops.listar_todas(self._conta)
        livros = Biblioteca().buscar()

        ttk.Label(self.__conteudo, text='Painel Administrativo — UnB FCTE', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(
            self.__conteudo,
            text=f'Conectado como administrador ({self._conta.email}).',
            style='Suave.TLabel',
        ).pack(anchor='w', pady=(2, 14))

        cards = ttk.Frame(self.__conteudo, style='TFrame')
        cards.pack(fill='x', pady=(0, 14))
        for i in range(4):
            cards.columnconfigure(i, weight=1)

        c1, _, _ = criar_card_indicador(cards, 'Discentes', len(discentes), 'Perfis cadastrados', CORES['destaque'])
        c2, _, _ = criar_card_indicador(cards, 'Docentes', len(docentes), 'Perfis cadastrados')
        c3, _, _ = criar_card_indicador(cards, 'Oportunidades', len(oportunidades), 'No mural da FCTE')
        c4, _, _ = criar_card_indicador(cards, 'Livros no Acervo', len(livros), 'Biblioteca FCTE')

        for idx, card in enumerate((c1, c2, c3, c4)):
            card.grid(row=0, column=idx, sticky='nsew', padx=(0 if idx == 0 else 10, 0))

        bloco = criar_bloco(self.__conteudo, titulo='Ações Rápidas de Administração', padding=16)
        bloco.pack(fill='x')

        botoes = [
            ('Gerar Acesso / Listar Usuários', 'admin'),
            ('Matricular Alunos e Atualizar SIGAA', 'turmas'),
            ('Moderar Oportunidades', 'oportunidades'),
            ('Gerenciar Acervo da Biblioteca', 'biblioteca'),
            ('Entidades e Calendário SAA', 'campus'),
            ('Atualizar Cardápio do RU', 'cardapio'),
        ]

        grade = ttk.Frame(bloco, style='Card.TFrame')
        grade.pack(fill='x')
        for c in range(3):
            grade.columnconfigure(c, weight=1)

        for idx, (rotulo, destino) in enumerate(botoes):
            ttk.Button(
                grade,
                text=rotulo,
                style='Secundario.TButton',
                command=lambda d=destino: self.navegar(d),
            ).grid(row=idx // 3, column=idx % 3, sticky='ew', padx=5, pady=5)

    # ========== { BLOCO DE DADOS CADASTRAIS } ========== #

    def __montar_dados_cadastrais(self, perfil, extras=None):
        bloco = criar_bloco(self.__conteudo, titulo='Meus Dados Cadastrais')
        bloco.pack(fill='x')

        itens = [
            ('Nome completo', perfil.nome),
            ('Matrícula', perfil.id_user),
            ('Vínculo', perfil.tipo_usuario.capitalize()),
            ('Curso / Área', perfil.curso_ou_area),
            ('Ingresso', f'{perfil.ano_entrada}.{perfil.semestre_entrada}'),
            ('CPF', perfil.cpf or '—'),
            ('E-mail institucional', perfil.email),
        ]
        if extras:
            itens.extend(extras)

        grade = ttk.Frame(bloco, style='Card.TFrame')
        grade.pack(fill='x')
        grade.columnconfigure(1, weight=1)
        grade.columnconfigure(3, weight=1)

        for idx, (rotulo, valor) in enumerate(itens):
            linha = idx // 2
            col_base = (idx % 2) * 2
            ttk.Label(grade, text=f'{rotulo}:', style='CardSuave.TLabel').grid(
                row=linha, column=col_base, sticky='w', padx=(0, 6), pady=3
            )
            ttk.Label(grade, text=str(valor), style='Card.TLabel').grid(
                row=linha, column=col_base + 1, sticky='w', padx=(0, 18), pady=3
            )
