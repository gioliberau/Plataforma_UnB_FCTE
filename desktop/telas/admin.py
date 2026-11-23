import tkinter as tk
from tkinter import ttk

from code_py import banco, login

from ..estilo import CORES, TabelaRolavel
from .base import TelaBase, criar_bloco


# ============================= { TELA DE ADMINISTRAÇÃO } ============================= #

class TelaAdmin(TelaBase):

    def __init__(self, master, sessao, ao_status=None, ao_navegar=None):
        super().__init__(master, sessao, ao_status=ao_status, ao_navegar=ao_navegar)
        self.__ultima_senha = ''

        self.criar_cabecalho(
            'Administração — Acessos e Usuários',
            'Libere novos e-mails com senha inicial temporária e consulte os perfis cadastrados.',
        )

        # Bloco 1: Gerar acesso
        bloco_acesso = criar_bloco(self, titulo='Gerar Acesso para um Novo E-mail', padding=14)
        bloco_acesso.pack(fill='x', pady=(0, 12))

        linha = ttk.Frame(bloco_acesso, style='Card.TFrame')
        linha.pack(fill='x')

        ttk.Label(linha, text='E-mail:', style='Card.TLabel').pack(side='left')
        self.__ent_email = ttk.Entry(linha, width=32)
        self.__ent_email.pack(side='left', padx=(6, 14))

        ttk.Label(linha, text='Tipo:', style='Card.TLabel').pack(side='left')
        self.__var_tipo = tk.StringVar(value='discente')
        ttk.Combobox(
            linha,
            textvariable=self.__var_tipo,
            values=login.tipos_usuario,
            state='readonly',
            width=14,
        ).pack(side='left', padx=(6, 14))

        ttk.Button(linha, text='Gerar Acesso', style='Destaque.TButton', command=self.__gerar_acesso).pack(side='left')

        # Resultado da senha gerada
        self.__frame_senha = ttk.Frame(bloco_acesso, style='Card.TFrame')
        self.__lbl_senha_info = tk.Label(
            self.__frame_senha,
            text='',
            bg=CORES['sucesso_fundo'],
            fg=CORES['sucesso_texto'],
            font=('Sans', 9, 'bold'),
            padx=10,
            pady=6,
        )
        self.__lbl_senha_info.pack(side='left', fill='x', expand=True)
        ttk.Button(
            self.__frame_senha,
            text='Copiar Senha',
            style='Secundario.TButton',
            command=self.__copiar_senha,
        ).pack(side='right', padx=(8, 0))

        # Bloco 2: Lista de usuários
        bloco_lista = criar_bloco(self, titulo='Discentes e Docentes Cadastrados', padding=14)
        bloco_lista.pack(fill='both', expand=True)

        filtros = ttk.Frame(bloco_lista, style='Card.TFrame')
        filtros.pack(fill='x', pady=(0, 8))

        ttk.Label(filtros, text='Filtrar por vínculo:', style='Card.TLabel').pack(side='left')
        self.__var_filtro_tipo = tk.StringVar(value='Todos')
        cmb = ttk.Combobox(
            filtros,
            textvariable=self.__var_filtro_tipo,
            values=('Todos', 'Discente', 'Docente'),
            state='readonly',
            width=14,
        )
        cmb.pack(side='left', padx=(6, 14))
        cmb.bind('<<ComboboxSelected>>', lambda _e: self.__carregar_usuarios())

        ttk.Label(filtros, text='Buscar:', style='Card.TLabel').pack(side='left')
        self.__ent_busca_usr = ttk.Entry(filtros, width=26)
        self.__ent_busca_usr.pack(side='left', padx=(6, 8))
        self.__ent_busca_usr.bind('<Return>', lambda _e: self.__carregar_usuarios())
        ttk.Button(filtros, text='Filtrar', style='Primario.TButton', command=self.__carregar_usuarios).pack(side='left')

        self.__tab_usuarios = TabelaRolavel(
            bloco_lista,
            colunas=(
                ('tipo', 'Vínculo', 90, 'center'),
                ('matricula', 'Matrícula', 105, 'center'),
                ('nome', 'Nome', 210, 'w'),
                ('curso', 'Curso / Área', 200, 'w'),
                ('email', 'E-mail', 210, 'w'),
            ),
            altura=10,
        )
        self.__tab_usuarios.pack(fill='both', expand=True)

    def atualizar(self):
        self.__carregar_usuarios()

    def __gerar_acesso(self):
        email = self.__ent_email.get().strip()
        tipo = self.__var_tipo.get()

        try:
            senha_inicial = login.gerar_acesso(self._conta, email, tipo)
        except (ValueError, PermissionError) as erro:
            self.tratar_erro(erro)
            return

        self.__ultima_senha = senha_inicial
        self.__lbl_senha_info.configure(
            text=f'Acesso criado para {email} ({tipo}) — Senha inicial: {senha_inicial}  (repassar ao usuário)'
        )
        if not self.__frame_senha.winfo_ismapped():
            self.__frame_senha.pack(fill='x', pady=(10, 0))

        self.__ent_email.delete(0, 'end')

    def __copiar_senha(self):
        if not self.__ultima_senha:
            return
        raiz = self.winfo_toplevel()
        raiz.clipboard_clear()
        raiz.clipboard_append(self.__ultima_senha)
        self.definir_status('Senha inicial copiada para a área de transferência.')

    def __carregar_usuarios(self):
        filtro = self.__var_filtro_tipo.get()
        termo = self.__ent_busca_usr.get().strip().casefold()

        perfis = []
        if filtro in ('Todos', 'Discente'):
            perfis.extend(banco.listar_perfis('discente'))
        if filtro in ('Todos', 'Docente'):
            perfis.extend(banco.listar_perfis('docente'))

        if termo:
            perfis = [
                p for p in perfis
                if termo in f'{p.nome} {p.id_user} {p.email} {p.curso_ou_area}'.casefold()
            ]

        self.__tab_usuarios.preencher([
            (
                (
                    p.tipo_usuario.capitalize(),
                    p.id_user,
                    p.nome,
                    p.curso_ou_area,
                    p.email,
                ),
                p,
            )
            for p in perfis
        ])
