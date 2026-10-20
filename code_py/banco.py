import sqlite3                  # Conectar e executar operações no banco SQLite.
from pathlib import Path        # Manipulação de caminhos de arquivos e pastas.
from contextlib import closing  # Fechamento da conexão após o uso.

# ----------------------------------------------- #

from .user import User
from .user_types import Discente, Docente, Admin
from .seguranca import verificar_senha

# ============================= { CONFIGURAÇÃO } ============================= #

caminho_banco = Path(__file__).resolve().parent / 'sistema.db'
# Define o caminho do banco de dados ('sistema.db') na mesma pasta deste arquivo. ('code_py')

# ============================= { CONEXÃO } ============================= #

def conectar():
    #Abre uma conexão com o banco de dados.

    conexao = sqlite3.connect(caminho_banco)
    conexao.row_factory = sqlite3.Row               # Permite acessar os resultados do banco pelo nome das colunas
    return conexao


# ============================= { CRIAÇÃO DAS TABELAS } ============================= #

def criar_tabelas():
    #Cria a tabela de usuários caso ela ainda não exista.

    with conectar() as conexao:
        conexao.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id_user TEXT PRIMARY KEY,
                tipo_usuario TEXT NOT NULL
                    CHECK (tipo_usuario IN ('discente', 'docente', 'admin')),
                nome TEXT NOT NULL,
                cpf TEXT UNIQUE,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                senha_hash TEXT NOT NULL,
                ano_entrada INTEGER,
                semestre_entrada INTEGER,
                curso TEXT,
                area TEXT
            )
        ''')
        # exectute() -> executa um comando SQL no banco de dados.


# ============================= { CONSULTAS } ============================= #

def buscar_usuario_por_id(id_user):
    # Busca um usuário pelo ID.

    with conectar() as conexao:
        usuario = conexao.execute(
            '''
            SELECT *
            FROM usuarios
            WHERE id_user = ?
            ''',
            (id_user,)
        ).fetchone()

        # fetchone() -> retorna o primeiro resultado da consulta ou None se não houver resultados.

    return usuario


def buscar_usuario_por_email(email):
    #Busca um usuário pelo e-mail.

    with conectar() as conexao:
        usuario = conexao.execute(
            '''
            SELECT *
            FROM usuarios
            WHERE email = ?
            ''',
            (email,)
        ).fetchone()

    return usuario

# ============================= { CADASTRO } ============================= #

def cadastrar_usuario(usuario):

    if not isinstance(usuario, User):
        raise TypeError('O usuário deve ser um objeto da classe User.')

    # Gera o hash da senha sem armazenar a senha original.
    senha_hash = usuario.get_hash_senha()

    # Obtém os dados comuns a todos os tipos de usuário.
    dados = (
        usuario.id_user,
        usuario.tipo_usuario,
        usuario.nome,
        usuario.cpf,
        usuario.email,
        senha_hash,
        getattr(usuario, 'ano_entrada', None),
        getattr(usuario, 'semestre_entrada', None),
        getattr(usuario, 'curso', None),
        getattr(usuario, 'area', None)
    )

    criar_tabelas()

    # Abre uma conexão com o banco e garante que ela seja fechada ao final.
    with closing(conectar()) as conexao:
        with conexao:
            conexao.execute(
                '''
                INSERT INTO usuarios (
                    id_user,
                    tipo_usuario,
                    nome,
                    cpf,
                    email,
                    senha_hash,
                    ano_entrada,
                    semestre_entrada,
                    curso,
                    area
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                dados
            )

    
    return usuario.id_user

# ============================= { RECONSTRUÇÃO DE OBJETOS } ============================= #

def reconstruir_usuario(dados):
    
    if dados is None:
        return None

    tipo = dados['tipo_usuario']


    # Reconstrói o objeto correspondente ao tipo.
    if tipo == 'discente':
        return Discente(
            dados['ano_entrada'],
            dados['semestre_entrada'],
            dados['nome'],
            dados['cpf'],
            dados['email'],
            'SenhaTemporaria123',
            dados['curso']
        )

    if tipo == 'docente':
        return Docente(
            dados['ano_entrada'],
            dados['semestre_entrada'],
            dados['nome'],
            dados['cpf'],
            dados['email'],
            'SenhaTemporaria123',
            dados['area']
        )

    if tipo == 'admin':
        return Admin(
            dados['nome'],
            dados['email'],
            'SenhaTemporaria123',
            dados['id_user']
        )

    raise ValueError('Tipo de usuário desconhecido.')

# ============================= { AUTENTICAÇÃO } ============================= #

def autenticar_usuario(email, senha):
    
    if not isinstance(email, str) or not email.strip():
        return None

    if not isinstance(senha, str) or not senha:
        return None

    usuario = buscar_usuario_por_email(email.strip())

    if usuario is None:     # Se o usuário não existir a autenticação falha.
        return None

    if not verificar_senha(senha, usuario['senha_hash']):
        return None

    return reconstruir_usuario(usuario)
