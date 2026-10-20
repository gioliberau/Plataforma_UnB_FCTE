from abc import ABC, abstractmethod
import random
from datetime import date

# ----------------------------------------------- #

from .seguranca import gerar_hash_senha

# ============================= { SEMESTRE ATUAL } ============================= #

def semestre_atual():
    # Retorna (ano, semestre) de hoje. Usada na matrícula e nas consultas ao SIGAA.
    hoje = date.today()

    if hoje.month < 7:
        return (hoje.year, 1)

    return (hoje.year, 2)

# ============================= { VALIDAÇÃO DE E-MAIL } ============================= #

def validar_email(email):
    # Usada pela classe User e pelo login (login.py).

    if not isinstance(email, str):
        raise ValueError('O e-mail deve ser um texto.')

    parte_local, separador, dominio = email.strip().partition('@')

    if not parte_local or not separador:
        raise ValueError('E-mail inválido.')

    if '.' not in dominio:
        raise ValueError('E-mail inválido.')

    if dominio.startswith('.') or dominio.endswith('.'):
        raise ValueError('E-mail inválido.')

    return email.strip()

# ============================= { CLASSE USER } ============================= #

class User(ABC):
    def __init__(self, ano_entrada, semestre_entrada, nome, cpf, email, senha=None, id_fixo=None, senha_hash=None):

        self.__ano_entrada = ano_entrada
        self.__semestre_entrada = semestre_entrada

        if senha_hash is not None:
            if not isinstance(senha_hash, str) or not senha_hash:
                raise ValueError('Hash de senha inválido.')

            self.__senha = None
            self.__hash_senha = senha_hash
        else:
            self.__senha = self.__validar_senha(senha)
            self.__hash_senha = None


        if id_fixo is not None:
            if not isinstance(id_fixo, str) or not id_fixo:
                raise ValueError('O ID deve ser um texto não vazio.')

            self.__id_user = id_fixo

        elif ano_entrada is not None and semestre_entrada is not None:
            self.__id_user = self.__gerar_id(
                ano_entrada, semestre_entrada
            )

        else:
            raise ValueError(
                'Ano e semestre devem ser informados juntos, '
                'ou um ID fixo deve ser fornecido.'
            )

        # Valida o CPF quando ele for informado.
        if cpf is None:
            self.__cpf = None
        else:
            self.__cpf = self.__formatar_cpf(cpf)

        self._email = self.__validar_email(email)
        self._nome = self.__validar_nome(nome)

    # ========== { Tipo de usuário } ========== #

    @property
    @abstractmethod
    def tipo_usuario(self):
        pass
    
    # ========== { Getters } ========== #

    @property
    def ano_entrada(self):
        return self.__ano_entrada

    @property
    def semestre_entrada(self):
        return self.__semestre_entrada

    @property
    def id_user(self):
        return self.__id_user

    @property
    def cpf(self):
        return self.__cpf

    @property
    def email(self):
        return self._email

    @property
    def nome(self):
        return self._nome

    # ======================== { método estáticos } ======================== #


    # === { SENHA } === #
    @staticmethod
    def __validar_senha(senha):
        if not isinstance(senha, str) or not senha.strip():
            raise ValueError('A senha não pode estar vazia.')

        if len(senha) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres.')

        return senha       # A senha não é alterada (espaços podem fazer parte da senha válida)


    # === { ID } === #

    @staticmethod
    def __gerar_id(ano, semestre):      # Gera ID do Docente / Discente

        if type(ano) is not int:
            raise ValueError(
                'O ano deve ser um número inteiro.'
            )

        if semestre not in (1,2):
            raise ValueError (
                'O semestre deve ser 1 ou 2.'
            )

        semestre_min = (2008, 2)
        semestre_max = semestre_atual()
        entrada = (ano, semestre)

        if not semestre_min <= entrada <= semestre_max:
            raise ValueError(
                'Período de entrada inválido.'
            )

        ano = str(ano)[-2:]         # Pega os 2 últimos dígitos do ano
        semestre = str(semestre)
        resto = str(random.randint(0,999999)).zfill(6)      #gera um inteiro aleatório de 6 dígitos

        return ano + semestre + resto       # Gera um número de matrícula


    def sortear_nova_matricula(self):
        # Usado pelo banco quando a matrícula sorteada já existe.
        self.__id_user = self.__gerar_id(self.__ano_entrada, self.__semestre_entrada)


    # === { CPF } === #
    @staticmethod
    def __validar_cpf(cpf):

        if cpf == cpf[0] * 11:
            return False
        
        # == { 1º digito verificador } == #
        soma = 0

        for i in range(9):
            soma += int(cpf[i]) * (10 - i)

        resto = soma % 11

        if resto < 2:
            digito1 = 0
        else:
            digito1 = 11 - resto

        # == { 2º digito verificador } == #
        soma = 0

        for i in range(10):
            if i < 9:
                numero = int(cpf[i])
            else:
                numero = digito1

            soma += numero * (11 - i)

        resto = soma % 11

        if resto < 2:
            digito2 = 0
        else:
            digito2 = 11 - resto

        return (digito1 == int(cpf[9]) and digito2 == int(cpf[10]))


    @staticmethod
    def __formatar_cpf(cpf):
        cpf = str(cpf)

        if len(cpf) != 11 or not cpf.isdigit():
            raise ValueError(
                'CPF inválido: O CPF deve conter exatamente 11 dígitos.'
            )

        if not User.__validar_cpf(cpf):         # chama o método __validar_cpf
            raise ValueError('CPF inválido.')

        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'


    # === { EMAIL } === #
    @staticmethod
    def __validar_email(email):
        return validar_email(email)


    # === { NOME } === #
    @staticmethod
    def __validar_nome(nome):
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError('O nome não pode estar vazio.')

        return nome.strip()


    def get_hash_senha(self):
        if self.__hash_senha is not None:
            return self.__hash_senha

        # Gera o hash na primeira utilização.
        self.__hash_senha = gerar_hash_senha(self.__senha)
        self.__senha = None

        return self.__hash_senha