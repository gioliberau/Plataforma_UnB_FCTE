# ============================= { CLASSE SESSAO } ============================= #

class Sessao:
    def __init__(self):
        self.__usuario = None   # Inicialmente sem nenhum usuario conectado

    # ========== { GETTER } ========== #

    @property
    def usuario(self):
        return self.__usuario   # Usuario conectado

    @property
    def autenticada(self):      # Verificação
        return self.__usuario is not None

    # ========== { CONTROLE DA SESSAO } ========== #

    def iniciar(self, usuario):

        if usuario is None:
            raise ValueError('Não é possível iniciar uma sessão sem usuário.')

        # Impede substituir uma sessão já ativa.
        if self.autenticada:
            raise ValueError('Já existe um usuário conectado.')

        self.__usuario = usuario

    def encerrar(self):
        self.__usuario = None