from abc import ABC, abstractmethod
import threading
from tkinter import messagebox, ttk

from ..estilo import CORES


# ============================= { TELA BASE ABSTRATA } ============================= #

class TelaBase(ttk.Frame, ABC):
    # Classe base das telas internas: concentra acesso à sessão, tratamento de erros
    # e execução de tarefas de rede em segundo plano sem travar a interface gráfica.

    def __init__(self, master, sessao, ao_status=None, ao_navegar=None):
        super().__init__(master, style='TFrame', padding=18)
        self._sessao = sessao
        self._ao_status = ao_status
        self._ao_navegar = ao_navegar

    # ========== { Propriedades da sessão } ========== #

    @property
    def _conta(self):
        return self._sessao.usuario

    @property
    def _perfil(self):
        return self._sessao.perfil

    @property
    def _eh_admin(self):
        return bool(getattr(self._conta, 'eh_admin', False))

    @property
    def _eh_discente(self):
        return getattr(self._perfil, 'tipo_usuario', None) == 'discente'

    @property
    def _eh_docente(self):
        return getattr(self._perfil, 'tipo_usuario', None) == 'docente'

    @property
    def _autenticado(self):
        return self._sessao.autenticada

    # ========== { Contrato polimórfico } ========== #

    @abstractmethod
    def atualizar(self):
        pass

    # ========== { Helpers compartilhados } ========== #

    def definir_status(self, mensagem):
        if self._ao_status:
            self._ao_status(mensagem)

    def navegar(self, destino):
        if self._ao_navegar:
            self._ao_navegar(destino)

    def tratar_erro(self, erro, titulo='Não foi possível concluir'):
        messagebox.showerror(titulo, str(erro), parent=self.winfo_toplevel())

    def mostrar_info(self, mensagem, titulo='Plataforma UnB FCTE'):
        messagebox.showinfo(titulo, mensagem, parent=self.winfo_toplevel())

    def confirmar(self, mensagem, titulo='Confirmar ação'):
        return messagebox.askyesno(titulo, mensagem, parent=self.winfo_toplevel())

    def criar_cabecalho(self, titulo, subtitulo=''):
        topo = ttk.Frame(self, style='TFrame')
        topo.pack(fill='x', pady=(0, 12))

        ttk.Label(topo, text=titulo, style='Titulo.TLabel').pack(anchor='w')
        if subtitulo:
            ttk.Label(topo, text=subtitulo, style='Suave.TLabel').pack(anchor='w', pady=(2, 0))
        return topo

    def executar_em_segundo_plano(self, tarefa, ao_sucesso, mensagem_status='Processando...',
                                  ao_erro=None, silencioso=False):
        self.definir_status(mensagem_status)

        def trabalhador():
            try:
                resultado = tarefa()
            except Exception as erro:
                def entregar_erro():
                    if not self.winfo_exists():
                        return
                    self.definir_status('')
                    if ao_erro:
                        ao_erro(erro)
                    elif not silencioso:
                        self.tratar_erro(erro)

                self.after(0, entregar_erro)
                return

            def entregar_sucesso():
                if not self.winfo_exists():
                    return
                self.definir_status('')
                ao_sucesso(resultado)

            self.after(0, entregar_sucesso)

        threading.Thread(target=trabalhador, daemon=True).start()


def criar_bloco(master, titulo=None, padding=14):
    bloco = ttk.Frame(master, style='Card.TFrame', padding=padding)
    if titulo:
        ttk.Label(bloco, text=titulo, style='Subtitulo.TLabel').pack(anchor='w', pady=(0, 8))
        ttk.Separator(bloco, orient='horizontal').pack(fill='x', pady=(0, 10))
    return bloco
