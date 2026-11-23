import tkinter as tk
from tkinter import messagebox, ttk

from code_py import banco, login
from code_py.user import cursos_disponiveis, semestre_atual

from ..estilo import CORES, DialogoBase


# ============================= { DIÁLOGO DE PRIMEIRO ACESSO } ============================= #

class DialogoTrocarSenha(DialogoBase):

    def __init__(self, master, email, senha_atual):
        super().__init__(master, 'Primeiro acesso — Trocar senha', largura=420)
        self.__email = email
        self.__senha_atual = senha_atual

        ttk.Label(
            self.corpo,
            text='Primeiro acesso detectado',
            style='Subtitulo.TLabel',
        ).pack(anchor='w')
        ttk.Label(
            self.corpo,
            text='Escolha uma nova senha com pelo menos 8 caracteres para liberar sua conta.',
            style='CardSuave.TLabel',
            wraplength=370,
        ).pack(anchor='w', pady=(4, 14))

        ttk.Label(self.corpo, text='Nova senha:', style='Card.TLabel').pack(anchor='w')
        self.__ent_nova = ttk.Entry(self.corpo, show='•')
        self.__ent_nova.pack(fill='x', pady=(3, 10))

        ttk.Label(self.corpo, text='Confirme a nova senha:', style='Card.TLabel').pack(anchor='w')
        self.__ent_conf = ttk.Entry(self.corpo, show='•')
        self.__ent_conf.pack(fill='x', pady=(3, 14))

        botoes = ttk.Frame(self.corpo, style='Card.TFrame')
        botoes.pack(fill='x')
        ttk.Button(botoes, text='Cancelar', style='Secundario.TButton', command=self.cancelar).pack(side='left')
        ttk.Button(botoes, text='Salvar nova senha', style='Primario.TButton', command=self.__salvar).pack(side='right')

        self.bind('<Return>', lambda _e: self.__salvar())
        self.__ent_nova.focus_set()
        self.finalizar_layout()

    def __salvar(self):
        nova = self.__ent_nova.get()
        conf = self.__ent_conf.get()

        if nova != conf:
            messagebox.showerror('Senhas diferentes', 'As senhas digitadas não conferem.', parent=self)
            return

        try:
            conta = login.trocar_senha(self.__email, self.__senha_atual, nova)
        except ValueError as erro:
            messagebox.showerror('Erro ao trocar senha', str(erro), parent=self)
            return

        self.resultado = conta
        messagebox.showinfo('Senha alterada', 'Senha atualizada com sucesso!', parent=self)
        self.destroy()


# ============================= { DIÁLOGO DE COMPLETAR PERFIL } ============================= #

class DialogoCompletarPerfil(DialogoBase):

    def __init__(self, master, conta):
        super().__init__(master, 'Complete seu cadastro', largura=460)
        self.__conta = conta
        ano_padrao, sem_padrao = semestre_atual()
        rotulo_curso = 'Curso' if conta.tipo_usuario == 'discente' else 'Área de atuação'

        ttk.Label(
            self.corpo,
            text=f'Cadastro de {conta.tipo_usuario.capitalize()}',
            style='Subtitulo.TLabel',
        ).pack(anchor='w')
        ttk.Label(
            self.corpo,
            text=f'E-mail institucional: {conta.email}',
            style='CardSuave.TLabel',
        ).pack(anchor='w', pady=(2, 12))

        ttk.Label(self.corpo, text='Nome completo:', style='Card.TLabel').pack(anchor='w')
        self.__ent_nome = ttk.Entry(self.corpo)
        self.__ent_nome.pack(fill='x', pady=(2, 8))

        ttk.Label(self.corpo, text='CPF (11 dígitos, somente números):', style='Card.TLabel').pack(anchor='w')
        self.__ent_cpf = ttk.Entry(self.corpo)
        self.__ent_cpf.pack(fill='x', pady=(2, 8))

        linha_periodo = ttk.Frame(self.corpo, style='Card.TFrame')
        linha_periodo.pack(fill='x', pady=(0, 8))

        col_ano = ttk.Frame(linha_periodo, style='Card.TFrame')
        col_ano.pack(side='left', fill='x', expand=True, padx=(0, 8))
        ttk.Label(col_ano, text='Ano de entrada:', style='Card.TLabel').pack(anchor='w')
        self.__ent_ano = ttk.Entry(col_ano)
        self.__ent_ano.insert(0, str(ano_padrao))
        self.__ent_ano.pack(fill='x', pady=(2, 0))

        col_sem = ttk.Frame(linha_periodo, style='Card.TFrame')
        col_sem.pack(side='left', fill='x', expand=True)
        ttk.Label(col_sem, text='Semestre de entrada:', style='Card.TLabel').pack(anchor='w')
        self.__var_sem = tk.StringVar(value=str(sem_padrao))
        ttk.Combobox(col_sem, textvariable=self.__var_sem, values=('1', '2'), state='readonly').pack(fill='x', pady=(2, 0))

        ttk.Label(self.corpo, text=f'{rotulo_curso}:', style='Card.TLabel').pack(anchor='w')
        self.__var_curso = tk.StringVar(value=cursos_disponiveis[0])
        ttk.Combobox(
            self.corpo,
            textvariable=self.__var_curso,
            values=cursos_disponiveis,
            state='readonly',
        ).pack(fill='x', pady=(2, 14))

        botoes = ttk.Frame(self.corpo, style='Card.TFrame')
        botoes.pack(fill='x')
        ttk.Button(botoes, text='Cancelar', style='Secundario.TButton', command=self.cancelar).pack(side='left')
        ttk.Button(botoes, text='Concluir cadastro', style='Destaque.TButton', command=self.__salvar).pack(side='right')

        self.bind('<Return>', lambda _e: self.__salvar())
        self.__ent_nome.focus_set()
        self.finalizar_layout()

    def __salvar(self):
        nome = self.__ent_nome.get().strip()
        cpf = ''.join(ch for ch in self.__ent_cpf.get() if ch.isdigit())
        curso = self.__var_curso.get()

        try:
            ano = int(self.__ent_ano.get().strip())
            semestre = int(self.__var_sem.get().strip())
            perfil = banco.cadastrar_perfil(self.__conta, nome, cpf, ano, semestre, curso)
        except ValueError as erro:
            messagebox.showerror('Cadastro inválido', str(erro), parent=self)
            return

        self.resultado = perfil
        messagebox.showinfo(
            'Cadastro concluído',
            f'Perfil criado com sucesso!\nSua matrícula é {perfil.id_user}.',
            parent=self,
        )
        self.destroy()


# ============================= { TELA DE LOGIN } ============================= #

class TelaLogin(ttk.Frame):

    def __init__(self, master, ao_autenticar, ao_entrar_publico):
        super().__init__(master, style='TFrame')
        self.__ao_autenticar = ao_autenticar
        self.__ao_entrar_publico = ao_entrar_publico

        container = ttk.Frame(self, style='TFrame')
        container.place(relx=0.5, rely=0.5, anchor='center')

        moldura = tk.Frame(container, bg=CORES['primaria'], padx=0, pady=0)
        moldura.pack()

        cartao = ttk.Frame(moldura, style='Card.TFrame', padding=(34, 28))
        cartao.pack(pady=(5, 0))

        # Selo institucional UnB FCTE
        selo = tk.Label(
            cartao,
            text='UnB  |  FCTE',
            bg=CORES['primaria'],
            fg='#ffffff',
            font=('Sans', 11, 'bold'),
            padx=14,
            pady=5,
        )
        selo.pack(pady=(0, 12))

        ttk.Label(cartao, text='Plataforma UnB FCTE', style='Titulo.TLabel', background=CORES['cartao']).pack()
        ttk.Label(
            cartao,
            text='Campus Gama — Portal Acadêmico Desktop',
            style='CardSuave.TLabel',
        ).pack(pady=(2, 16))

        self.__lbl_erro = tk.Label(
            cartao,
            text='',
            bg=CORES['erro_fundo'],
            fg=CORES['erro_texto'],
            font=('Sans', 9, 'bold'),
            padx=10,
            pady=6,
            wraplength=310,
            justify='left',
        )

        self.__lbl_email = ttk.Label(cartao, text='E-mail institucional', style='Card.TLabel')
        self.__lbl_email.pack(anchor='w')
        self.__ent_email = ttk.Entry(cartao, width=38)
        self.__ent_email.pack(fill='x', pady=(3, 10))

        ttk.Label(cartao, text='Senha', style='Card.TLabel').pack(anchor='w')
        self.__ent_senha = ttk.Entry(cartao, width=38, show='•')
        self.__ent_senha.pack(fill='x', pady=(3, 6))

        self.__var_mostrar = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            cartao,
            text='Mostrar senha',
            variable=self.__var_mostrar,
            style='Card.TCheckbutton',
            command=self.__alternar_senha,
        ).pack(anchor='w', pady=(0, 14))

        ttk.Button(
            cartao,
            text='Entrar no Portal',
            style='Primario.TButton',
            command=self.__entrar,
        ).pack(fill='x', pady=(0, 8))

        ttk.Separator(cartao, orient='horizontal').pack(fill='x', pady=8)

        ttk.Button(
            cartao,
            text='Acessar Portal Público (sem login)',
            style='Secundario.TButton',
            command=self.__ao_entrar_publico,
        ).pack(fill='x')

        dica = (
            'Contas de exemplo (testes):\n'
            '• Discente: aluno@exemplo.unb.br / aluno12345\n'
            '• Docente: professor@exemplo.unb.br / professor12345\n'
            '• Admin: admin@exemplo.unb.br / admin12345'
        )
        ttk.Label(
            cartao,
            text=dica,
            style='CardSuave.TLabel',
            justify='left',
        ).pack(anchor='w', pady=(14, 0))

        self.__ent_email.bind('<Return>', lambda _e: self.__ent_senha.focus_set())
        self.__ent_senha.bind('<Return>', lambda _e: self.__entrar())
        self.__ent_email.focus_set()

    def limpar(self):
        self.__ent_senha.delete(0, 'end')
        self.__esconder_erro()
        self.__ent_email.focus_set()

    def __alternar_senha(self):
        self.__ent_senha.configure(show='' if self.__var_mostrar.get() else '•')

    def __mostrar_erro(self, texto):
        self.__lbl_erro.configure(text=texto)
        if not self.__lbl_erro.winfo_ismapped():
            self.__lbl_erro.pack(fill='x', pady=(0, 12), before=self.__lbl_email)

    def __esconder_erro(self):
        if self.__lbl_erro.winfo_ismapped():
            self.__lbl_erro.pack_forget()

    def __entrar(self):
        self.__esconder_erro()
        email = self.__ent_email.get().strip()
        senha = self.__ent_senha.get()

        if not email or not senha:
            self.__mostrar_erro('Informe seu e-mail e sua senha.')
            return

        conta = login.autenticar(email, senha)
        if conta is None:
            self.__mostrar_erro('E-mail ou senha incorretos.')
            return

        # 1º acesso: obriga a trocar a senha inicial gerada pelo admin.
        if conta.precisa_trocar_senha:
            dialogo = DialogoTrocarSenha(self.winfo_toplevel(), email, senha)
            self.wait_window(dialogo)
            if dialogo.resultado is None:
                return
            conta = dialogo.resultado

        # Discentes e docentes precisam ter perfil cadastrado.
        perfil = None
        if not conta.eh_admin:
            perfil = banco.buscar_perfil(conta.email)
            if perfil is None:
                dialogo = DialogoCompletarPerfil(self.winfo_toplevel(), conta)
                self.wait_window(dialogo)
                if dialogo.resultado is None:
                    return
                perfil = dialogo.resultado

        self.__ao_autenticar(conta, perfil)
