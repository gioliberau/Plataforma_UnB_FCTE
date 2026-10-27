from abc import ABC, abstractmethod
import random
from datetime import date
# ----------------------------------------------- #

cursos_disponiveis = (
    'Engenharia Aeroespacial',
    'Engenharia Automotiva',
    'Engenharia de Energia',
    'Engenharia Eletrônica',
    'Engenharia de Software',
)

areas_disponiveis = cursos_disponiveis # As áreas dos docentes são os mesmos cursos

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


# ============================= { VALIDAÇÃO DE CPF / FORMATAÇÃO } ============================= #

def _cpf_valido(cpf):

    if cpf == cpf[0] * 11:
        return False

    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = 0 if soma % 11 < 2 else 11 - soma % 11

        if digito != int(cpf[tamanho]):
            return False
    
    return True

def _formatar_cpf(cpf):
    cpf = str(cpf)

    if len(cpf) != 11 or not cpf.isdigit():
        raise ValueError(
            'CPF inválido: O CPF deve conter exatamente 11 dígitos.'
        )

    if not _cpf_valido(cpf):
        raise ValueError('CPF inválido.')

    return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'



# ============================= { CLASSE USER } ============================= #

class User(ABC):
    def __init__(self, ano_entrada, semestre_entrada, nome, cpf, email, id_fixo=None):

        self.__ano_entrada = ano_entrada
        self.__semestre_entrada = semestre_entrada

       
        if id_fixo is not None:
            if not isinstance(id_fixo, str) or not id_fixo:
                raise ValueError('O ID deve ser um texto não vazio.')

            self.__id_user = id_fixo

        elif ano_entrada is not None and semestre_entrada is not None:
            self.__id_user = self.__gerar_id(ano_entrada, semestre_entrada)

        else:
            raise ValueError(
                'Ano e semestre devem ser informados juntos, '
                'ou um ID fixo deve ser fornecido.'
            )

        # Valida o CPF quando ele for informado.
        self.__cpf = None if cpf is None else _formatar_cpf(cpf)

        self.__email = validar_email(email)

        if not isinstance(nome, str) or not nome.strip():
                raise ValueError('O nome não pode estar vazio.')

        self.__nome = nome.strip()

    # ========== { Tipo de usuário } ========== #

    @property
    @abstractmethod
    def tipo_usuario(self):
        pass

    @property
    @abstractmethod
    def curso_ou_area(self):
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
        return self.__email

    @property
    def nome(self):
        return self.__nome


    # === { ID } === #

    @staticmethod
    def __gerar_id(ano, semestre):      # Gera ID do Docente / Discente

        if type(ano) is not int:
            raise ValueError('O ano deve ser um número inteiro.')

        if semestre not in (1,2):
            raise ValueError ('O semestre deve ser 1 ou 2.')

        if not (2008, 2) <= (ano, semestre) <= semestre_atual():
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



# ============================= { CLASSE DICENTE } ============================= #

class Discente(User):
    def __init__(self, ano_entrada, semestre_entrada, nome, cpf, email, curso, id_fixo=None):
        
        super().__init__(ano_entrada, semestre_entrada, nome, cpf, email, id_fixo=id_fixo)

        self.__curso = None

        self.curso = curso

    @property
    def tipo_usuario(self):
        return 'discente'

    @property
    def curso(self):
        return self.__curso

    @property
    def curso_ou_area(self):
        return self.__curso

    @curso.setter
    def curso(self, v_curso):
        if not isinstance(v_curso, str) or not v_curso.strip():
            raise ValueError('O curso deve ser informado.')

        v_curso = v_curso.strip()

        if v_curso not in cursos_disponiveis:
            raise ValueError('Curso indisponível.')

        self.__curso = v_curso


# ============================= { CLASSE DOCENTE } ============================= #

class Docente(User):
    def __init__(self, ano_entrada, semestre_entrada, nome, cpf, email, area, id_fixo=None):
        
        super().__init__(ano_entrada, semestre_entrada, nome, cpf, email, id_fixo=id_fixo)
        
        self.__area = None
        self.area = area

    @property
    def tipo_usuario(self):
        return 'docente'

    @property
    def area(self):
        return self.__area

    @property
    def curso_ou_area(self):
        return self.__area

    @area.setter
    def area(self, v_area):
        if not isinstance(v_area, str) or not v_area.strip():
            raise ValueError('A área deve ser informada.')

        v_area = v_area.strip()

        if v_area not in areas_disponiveis:
            raise ValueError('Área acadêmica indisponível.')

        self.__area = v_area