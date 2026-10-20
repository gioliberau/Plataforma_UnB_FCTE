from .user import User      # Importa a classe abstrata 'User' de 'user.py'

cursos_disponiveis = (
    'Engenharia Aeroespacial',
    'Engenharia Automotiva',
    'Engenharia de Energia',
    'Engenharia Eletrônica',
    'Engenharia de Software'
)

areas_disponiveis = cursos_disponiveis      # As áreas dos docentes são os mesmos cursos.

# ============================= { CLASSE DISCENTE } ============================= #

class Discente(User):

    def __init__(self, ano_entrada, semestre_entrada, nome, cpf, email, senha, curso, id_fixo = None, senha_hash = None):

        # Pega os atributos de User
        super().__init__(ano_entrada, semestre_entrada, nome, cpf, email, senha, id_fixo = id_fixo, senha_hash = senha_hash)
        self.__curso = None     # atributo privado

        self.curso = curso      # chama o setter


    # ========== { Getters } ========== #

    @property
    def tipo_usuario(self):     # método abstrato da classe User
        return 'discente'

    @property
    def curso(self):
        return self.__curso

    # ========== { Setters } ========== #

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

    def __init__(self, ano_entrada, semestre_entrada, nome, cpf, email, senha, area, id_fixo = None, senha_hash = None):

        super().__init__(ano_entrada, semestre_entrada, nome, cpf, email, senha, id_fixo = id_fixo, senha_hash = senha_hash)
        self.__area = None

        self.area = area

    # ========== { Getters } ========== #

    @property
    def area(self):
        return self.__area

    @property
    def tipo_usuario(self):
        return 'docente'

    # ========== { Setters } ========== #

    @area.setter
    def area(self, v_area):
        if not isinstance(v_area, str) or not v_area.strip():
            raise ValueError('A área deve ser informada.')

        v_area = v_area.strip()

        if v_area not in areas_disponiveis:
            raise ValueError('Área acadêmica indisponível.')

        self.__area = v_area

# ============================= { CLASSE ADMIN } ============================= #

class Admin(User):

    def __init__(self, nome, email, senha, id_admin = None, senha_hash = None):
        super().__init__(
            None, None, nome, None, email, senha,
            id_fixo=id_admin, senha_hash=senha_hash
        )

    @property
    def tipo_usuario(self):
        return 'admin'

    @property
    def acesso_total(self):
        return True