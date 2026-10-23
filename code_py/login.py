import sqlite3                  # Erro de e-mail duplicado (IntegrityError).
from contextlib import closing  # Fechamento da conexão após o uso.
from getpass import getpass     # Lê a senha no terminal sem exibi-la.
import hashlib
import secrets

# ----------------------------------------------- #

from . import banco
from .user import validar_email

# ============================= { CONFIGURAÇÃO } ============================= #

tipos_usuario = ('discente', 'docente', 'admin')
tamanho_minimo_senha = 8

iteracoes = 600_000

caracteres_senha = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'

# ============================= { SEGURANÇA } ============================= #

def gerar_hash_senha(senha):
    # Gera um hash seguro para a senha
    if not isinstance(senha, str) or not senha:
        raise ValueError('A senha deve ser informada.')

    sal = secrets.tocken_bytes(16)

    hash_senha = hashlib.pdkdf2_hmac(
        'sha258',
        senha.encode('utf-8'),
        sal,
        iteracoes
    )

    # Monta uma string com todas as informações necessárias para verificar a senha posteriormente:
    # algoritmo, número de iterações, sal e hash gerado.
    return f'pbkdf2_sha256${iteracoes}${sal.hex()}${hash_senha.hex()}'

def verificar_senha(senha_digitada, hash_armazenado):
    # Verifica se a senha digitada corresponde ao hash armazenado.
 
    if not isinstance(senha_digitada, str):
        return False
 
    if not isinstance(hash_armazenado, str):
        return False
 
    try:
        # Separa as quatro partes do hash usando o caractere '$'.
        algoritmo, iteracoes_hash, sal_hex, hash_original = hash_armazenado.split('$')
 
        if algoritmo != 'pbkdf2_sha256':
            return False
 
        iteracoes_hash = int(iteracoes_hash)
        if not 1 <= iteracoes_hash <= 2_000_000:
            return False
 
        sal = bytes.fromhex(sal_hex)
        hash_original = bytes.fromhex(hash_original)
 
        hash_teste = hashlib.pbkdf2_hmac(
            'sha256',
            senha_digitada.encode('utf-8'),
            sal,
            iteracoes_hash
        )
 
        # compare_digest() é apropriado para comparações sensíveis a tempo. Ajuda a reduzir vazamentos de informação.
        return secrets.compare_digest(hash_teste, hash_original)
 
    except (ValueError, TypeError):
        return False
 
 
def gerar_senha_aleatoria(tamanho=10):
    # Gera uma senha inicial aleatória para ser repassada pelo admin.
    if type(tamanho) is not int or tamanho < tamanho_minimo_senha:
        raise ValueError(f'A senha gerada deve ter pelo menos {tamanho_minimo_senha} caracteres.')
 
    return ''.join(secrets.choice(caracteres_senha) for _ in range(tamanho))


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

def exigir_admin(conta):
    # 'conta' é a Conta de quem está logado; admin não tem perfil.
    if conta is None or not getattr(conta, 'eh_admin', False):
        raise PermissionError('Ação permitida apenas para ADMs')

# ============================= { CLASSE SESSAO } ============================= #

class Sessao:
    def __init__(self):
        self.__usuario = None   # Inicialmente sem nenhum usuario conectado (é a Conta)
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


# ============================= { FUNÇÕES AUXILIARES } ============================= #

def _validar_nova_senha(senha):
    # Único requisito da senha: pelo menos 8 caracteres.

    if not isinstance(senha, str) or len(senha) < tamanho_minimo_senha:
        raise ValueError(
            f'A senha deve ter pelo menos {tamanho_minimo_senha} caracteres.'
        )

    return senha


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

    with closing(banco.conectar()) as conexao:
        existe_admin = conexao.execute("SELECT 1 FROM acessos WHERE tipo_usuario = 'admin'"
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

    # Busca as credenciais de um e-mail (sem diferenciar maiúsculas).
    with closing(conectar()) as conexao:
        acesso = conexao.execute(
            'SELECT * FROM acessos WHERE email = ?',
            (email.strip(),)
        ).fetchone()


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
