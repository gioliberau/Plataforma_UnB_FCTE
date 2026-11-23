import tkinter as tk
from tkinter import messagebox, ttk

from code_py import exemplos
from code_py.login import Sessao
from code_py.tela import formatar_data_hora, formatar_duracao
from code_py.user import semestre_atual

from .estilo import CORES, configurar_estilo
from .telas.admin import TelaAdmin
from .telas.biblioteca import TelaBiblioteca
from .telas.campus import TelaCampus
from .telas.cardapio import TelaCardapio
from .telas.inicio import TelaInicio
from .telas.login import TelaLogin
from .telas.oportunidades import TelaOportunidades
from .telas.turmas import TelaTurmas


# ============================= { CONFIGURAÇÃO } ============================= #

def _garantir_exemplos():
    # Garante usuários e histórico de exemplo sem sobrescrever nem duplicar dados.
    try:
        exemplos.criar_exemplos()
    except (ValueError, PermissionError):
        pass


# ============================= { TELA PRINCIPAL } ============================= #

class TelaPrincipal(ttk.Frame):
    # Layout autenticado ou de visitante: cabeçalho, barra lateral, área de conteúdo e rodapé.

    def __init__(self, master, sessao, ao_sair):
        super().__init__(master, style='TFrame')
        self.__sessao = sessao
        self.__ao_sair = ao_sair
        self.__telas = {}
        self.__botoes_menu = {}
        self.__tela_atual = None

        self.__montar_topo()

        meio = ttk.Frame(self, style='TFrame')
        meio.pack(fill='both', expand=True)

        self.__montar_barra_lateral(meio)

        self.__area_conteudo = ttk.Frame(meio, style='TFrame')
        self.__area_conteudo.pack(side='left', fill='both', expand=True)

        self.__montar_rodape()
        self.abrir_tela('inicio')

    def __montar_topo(self):
        ano, sem = semestre_atual()
        topo = tk.Frame(self, bg=CORES['primaria'], height=58)
        topo.pack(fill='x')
        topo.pack_propagate(False)

        esquerda = tk.Frame(topo, bg=CORES['primaria'])
        esquerda.pack(side='left', padx=18)

        tk.Label(
            esquerda,
            text='Plataforma UnB FCTE',
            bg=CORES['primaria'],
            fg='#ffffff',
            font=('Sans', 13, 'bold'),
        ).pack(anchor='w')
        tk.Label(
            esquerda,
            text=f'Campus Gama  |  Semestre {ano}.{sem}',
            bg=CORES['primaria'],
            fg='#cbd5e1',
            font=('Sans', 9),
        ).pack(anchor='w')

        direita = tk.Frame(topo, bg=CORES['primaria'])
        direita.pack(side='right', padx=18)

        if self.__sessao.autenticada:
            tipo = self.__sessao.usuario.tipo_usuario.upper()
            nome = self.__sessao.perfil.nome if self.__sessao.perfil else self.__sessao.usuario.email
            texto_btn = 'Sair da conta'
        else:
            tipo = 'PORTAL PÚBLICO'
            nome = 'Visitante'
            texto_btn = 'Fazer login'

        tk.Label(
            direita,
            text=nome,
            bg=CORES['primaria'],
            fg='#ffffff',
            font=('Sans', 9, 'bold'),
        ).pack(side='left', padx=(0, 10))

        tk.Label(
            direita,
            text=tipo,
            bg=CORES['destaque'],
            fg='#ffffff',
            font=('Sans', 8, 'bold'),
            padx=10,
            pady=4,
        ).pack(side='left', padx=(0, 12))

        tk.Button(
            direita,
            text=texto_btn,
            bg='#1e4e79',
            fg='#ffffff',
            activebackground='#2c6699',
            activeforeground='#ffffff',
            relief='flat',
            font=('Sans', 9, 'bold'),
            padx=12,
            pady=5,
            cursor='hand2',
            command=self.__ao_sair,
        ).pack(side='left')

    def __itens_navegacao(self):
        autenticado = self.__sessao.autenticada
        eh_admin = bool(getattr(self.__sessao.usuario, 'eh_admin', False))

        itens = [
            ('inicio', 'Início / Perfil' if autenticado else 'Início (Público)', TelaInicio),
            ('turmas', 'Turmas do SIGAA', TelaTurmas),
            ('cardapio', 'Cardápio do RU', TelaCardapio),
        ]

        if autenticado:
            itens.append(('oportunidades', 'Oportunidades', TelaOportunidades))

        itens.extend([
            ('biblioteca', 'Biblioteca FCTE', TelaBiblioteca),
            ('campus', 'Campus (Org / Cal / Cursos)', TelaCampus),
        ])

        if eh_admin:
            itens.append(('admin', 'Administração', TelaAdmin))

        return itens

    def __montar_barra_lateral(self, pai):
        barra = tk.Frame(pai, bg=CORES['sidebar_fundo'], width=225)
        barra.pack(side='left', fill='y')
        barra.pack_propagate(False)

        tk.Label(
            barra,
            text='NAVEGAÇÃO',
            bg=CORES['sidebar_fundo'],
            fg='#9fb3c8',
            font=('Sans', 8, 'bold'),
            anchor='w',
            padx=16,
            pady=12,
        ).pack(fill='x')

        self.__classes_telas = {}

        for chave, rotulo, classe in self.__itens_navegacao():
            self.__classes_telas[chave] = classe
            btn = tk.Button(
                barra,
                text=f'  {rotulo}',
                bg=CORES['sidebar_fundo'],
                fg='#e2e8f0',
                activebackground=CORES['sidebar_hover'],
                activeforeground='#ffffff',
                relief='flat',
                anchor='w',
                font=('Sans', 10),
                padx=14,
                pady=10,
                cursor='hand2',
                command=lambda c=chave: self.abrir_tela(c),
            )
            btn.pack(fill='x', padx=8, pady=2)
            self.__botoes_menu[chave] = btn

    def __montar_rodape(self):
        rodape = tk.Frame(self, bg='#dde5ef', height=28)
        rodape.pack(fill='x', side='bottom')
        rodape.pack_propagate(False)

        if self.__sessao.autenticada:
            info = (
                f'Conectado: {self.__sessao.usuario.email}  |  '
                f'Sessão iniciada em {formatar_data_hora(self.__sessao.iniciada_em)}'
            )
        else:
            info = 'Modo visitante — Portal Público da UnB FCTE'

        tk.Label(
            rodape,
            text=info,
            bg='#dde5ef',
            fg=CORES['texto_suave'],
            font=('Sans', 8),
            padx=14,
        ).pack(side='left')

        self.__lbl_status = tk.Label(
            rodape,
            text='',
            bg='#dde5ef',
            fg=CORES['primaria'],
            font=('Sans', 8, 'bold'),
            padx=14,
        )
        self.__lbl_status.pack(side='right')

    def definir_status(self, mensagem):
        self.__lbl_status.configure(text=mensagem)

    def abrir_tela(self, chave):
        if chave not in self.__classes_telas:
            return

        if chave not in self.__telas:
            classe = self.__classes_telas[chave]
            self.__telas[chave] = classe(
                self.__area_conteudo,
                self.__sessao,
                ao_status=self.definir_status,
                ao_navegar=self.abrir_tela,
            )

        if self.__tela_atual is not None:
            self.__tela_atual.pack_forget()

        self.__tela_atual = self.__telas[chave]
        self.__tela_atual.pack(fill='both', expand=True)
        self.__tela_atual.atualizar()

        for k, btn in self.__botoes_menu.items():
            if k == chave:
                btn.configure(bg=CORES['sidebar_ativo'], fg='#ffffff', font=('Sans', 10, 'bold'))
            else:
                btn.configure(bg=CORES['sidebar_fundo'], fg='#e2e8f0', font=('Sans', 10))


# ============================= { APLICAÇÃO PRINCIPAL } ============================= #

class AppFCTE(tk.Tk):
    # Janela principal do aplicativo Desktop; compõe Sessao e alterna entre Login e TelaPrincipal.

    def __init__(self, garantir_exemplos=True):
        super().__init__()
        self.title('Plataforma UnB FCTE — Desktop')
        self.geometry('1140x720')
        self.minsize(940, 600)
        self.configure(bg=CORES['fundo'])

        configurar_estilo(self)

        if garantir_exemplos:
            _garantir_exemplos()

        self.__sessao = Sessao()
        self.__tela_ativa = None
        self.__mostrar_login()

    @property
    def sessao(self):
        return self.__sessao

    @property
    def tela_ativa(self):
        return self.__tela_ativa

    def __trocar_tela(self, nova_tela):
        if self.__tela_ativa is not None:
            self.__tela_ativa.destroy()
        self.__tela_ativa = nova_tela
        self.__tela_ativa.pack(fill='both', expand=True)

    def __mostrar_login(self):
        tela = TelaLogin(
            self,
            ao_autenticar=self.ao_autenticar,
            ao_entrar_publico=self.entrar_como_visitante,
        )
        self.__trocar_tela(tela)

    def ao_autenticar(self, conta, perfil=None):
        if self.__sessao.autenticada:
            self.__sessao.encerrar()
        self.__sessao.iniciar(conta, perfil)
        self.__trocar_tela(TelaPrincipal(self, self.__sessao, ao_sair=self.fazer_logout))

    def entrar_como_visitante(self):
        if self.__sessao.autenticada:
            self.__sessao.encerrar()
        self.__trocar_tela(TelaPrincipal(self, self.__sessao, ao_sair=self.__voltar_para_login))

    def __voltar_para_login(self):
        self.__mostrar_login()

    def fazer_logout(self, exibir_aviso=True):
        duracao = formatar_duracao(self.__sessao.iniciada_em) if self.__sessao.iniciada_em else None
        self.__sessao.encerrar()
        self.__mostrar_login()
        if exibir_aviso and duracao:
            messagebox.showinfo('Logout', f'Logout realizado com sucesso! Sessão de {duracao}.', parent=self)


def main():
    app = AppFCTE()
    app.mainloop()


if __name__ == '__main__':
    main()
