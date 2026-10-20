# ============================= { CLASSE SESSAO } ============================= #

class Sessao:
    def __init__(self):
        self.__usuario = None   # Inicialmente sem nenhum usuario conectado
        self.__perfil = None    # Discente/Docente do usuário (admin não tem perfil)

    # ========== { GETTER } ========== #

    @property
    def usuario(self):
        return self.__usuario   # Usuario conectado

    @property
    def perfil(self):
        return self.__perfil

    @property
    def autenticada(self):      # Verificação
        return self.__usuario is not None

    # ========== { CONTROLE DA SESSAO } ========== #

    def iniciar(self, usuario, perfil=None):

        if usuario is None:
            raise ValueError('Não é possível iniciar uma sessão sem usuário.')

        # Impede substituir uma sessão já ativa.
        if self.autenticada:
            raise ValueError('Já existe um usuário conectado.')

        self.__usuario = usuario
        self.__perfil = perfil

    def encerrar(self):
        self.__usuario = None
        self.__perfil = None