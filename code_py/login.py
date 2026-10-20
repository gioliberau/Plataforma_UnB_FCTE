import sqlite3                  # Erro de e-mail duplicado (IntegrityError).
from contextlib import closing  # Fechamento da conexão após o uso.
from getpass import getpass     # Lê a senha no terminal sem exibi-la.

# ----------------------------------------------- #

from . import banco
from .user import validar_email
from .seguranca import gerar_hash_senha, verificar_senha, gerar_senha_aleatoria

# ============================= { CONFIGURAÇÃO } ============================= #

tipos_usuario = ('discente', 'docente', 'admin')
tamanho_minimo_senha = 8

# ============================= { CLASSE CONTA } ============================= #

class Conta:
    # Representa as credenciais de quem fez login (sem dados de perfil).

    def __init__(self, email, tipo_usuario, precisa_trocar_senha):
        self.__email = email
        self.__tipo_usuario = tipo_usuario
        self.__precisa_trocar_senha = bool(precisa_trocar_senha)

    # ========== { Getters } ========== #

    @property
    def email(self):
        return self.__email

    @property
    def tipo_usuario(self):
        return self.__tipo_usuario

    @property
    def precisa_trocar_senha(self):
        return self.__precisa_trocar_senha

    @property
    def eh_admin(self):
        return self.__tipo_usuario == 'admin'


# ============================= { CRIAÇÃO DA TABELA } ============================= #

def criar_tabela_acessos():
    # Cria a tabela de credenciais caso ela ainda não exista.

    with closing(banco.conectar()) as conexao:
        with conexao:
            conexao.execute('''
                CREATE TABLE IF NOT EXISTS acessos (
                    email TEXT PRIMARY KEY COLLATE NOCASE,
                    tipo_usuario TEXT NOT NULL
                        CHECK (tipo_usuario IN ('discente', 'docente', 'admin')),
                    senha_hash TEXT NOT NULL,
                    trocar_senha INTEGER NOT NULL DEFAULT 1
                )
            ''')


# ============================= { FUNÇÕES AUXILIARES } ============================= #

def _validar_nova_senha(senha):
    # Único requisito da senha: pelo menos 8 caracteres.

    if not isinstance(senha, str) or len(senha) < tamanho_minimo_senha:
        raise ValueError(
            f'A senha deve ter pelo menos {tamanho_minimo_senha} caracteres.'
        )

    return senha


def _buscar_acesso(email):
    # Busca as credenciais de um e-mail (sem diferenciar maiúsculas).

    criar_tabela_acessos()

    with closing(banco.conectar()) as conexao:
        return conexao.execute(
            '''
            SELECT *
            FROM acessos
            WHERE email = ?
            ''',
            (email.strip(),)
        ).fetchone()


def _inserir_acesso(email, tipo, senha_hash, trocar_senha):

    try:
        with closing(banco.conectar()) as conexao:
            with conexao:
                conexao.execute(
                    '''
                    INSERT INTO acessos (email, tipo_usuario, senha_hash, trocar_senha)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (email, tipo, senha_hash, trocar_senha)
                )

    except sqlite3.IntegrityError:
        raise ValueError('Este e-mail já possui acesso cadastrado.')


# ============================= { CADASTRO } ============================= #

def criar_admin_inicial(email, senha):
    # Cria o primeiro admin. Só funciona enquanto não houver nenhum admin no banco.

    email = validar_email(email)
    _validar_nova_senha(senha)

    criar_tabela_acessos()

    with closing(banco.conectar()) as conexao:
        existe_admin = conexao.execute(
            '''
            SELECT 1
            FROM acessos
            WHERE tipo_usuario = 'admin'
            '''
        ).fetchone()

    if existe_admin:
        raise PermissionError('Já existe um admin cadastrado.')

    # O próprio admin escolheu a senha, então não precisa trocá-la.
    _inserir_acesso(email, 'admin', gerar_hash_senha(senha), 0)

    return Conta(email, 'admin', False)


def gerar_acesso(admin, email, tipo):
    # O admin libera um e-mail e recebe a senha inicial para repassar ao usuário.

    if not isinstance(admin, Conta) or not admin.eh_admin:
        raise PermissionError('Apenas um admin pode gerar acessos.')

    if admin.precisa_trocar_senha:
        raise PermissionError('O admin precisa trocar a própria senha antes.')

    email = validar_email(email)

    if tipo not in tipos_usuario:
        raise ValueError('Tipo de usuário inválido.')

    criar_tabela_acessos()

    senha_inicial = gerar_senha_aleatoria()
    _inserir_acesso(email, tipo, gerar_hash_senha(senha_inicial), 1)

    # A senha em texto só existe aqui; no banco fica apenas o hash.
    return senha_inicial


# ============================= { AUTENTICAÇÃO } ============================= #

def autenticar(email, senha):
    # Retorna a Conta se e-mail e senha conferirem, senão None.

    if not isinstance(email, str) or not email.strip():
        return None

    if not isinstance(senha, str) or not senha:
        return None

    acesso = _buscar_acesso(email)

    if acesso is None:
        return None

    if not verificar_senha(senha, acesso['senha_hash']):
        return None

    return Conta(acesso['email'], acesso['tipo_usuario'], acesso['trocar_senha'])


def trocar_senha(email, senha_atual, nova_senha):
    # Troca a senha (obrigatório no primeiro acesso) e libera a conta.

    if autenticar(email, senha_atual) is None:
        raise ValueError('E-mail ou senha atual incorretos.')

    _validar_nova_senha(nova_senha)

    with closing(banco.conectar()) as conexao:
        with conexao:
            conexao.execute(
                '''
                UPDATE acessos
                SET senha_hash = ?, trocar_senha = 0
                WHERE email = ?
                ''',
                (gerar_hash_senha(nova_senha), email.strip())
            )

    return autenticar(email, nova_senha)


# ============================= { EXECUÇÃO } ============================= #

def main():
    # Bootstrap: cria o primeiro admin pelo terminal (python -m code_py.login).

    print('===== CRIAR ADMIN INICIAL =====')
    email = input('E-mail do admin: ').strip()
    senha = getpass('Senha (mínimo 8 caracteres): ')
    confirmacao = getpass('Confirme a senha: ')

    if senha != confirmacao:
        print('As senhas não conferem.')
        return

    try:
        criar_admin_inicial(email, senha)
        print('Admin criado com sucesso!')
    except (ValueError, PermissionError) as erro:
        print(f'Não foi possível criar o admin: {erro}')


if __name__ == '__main__':
    main()
