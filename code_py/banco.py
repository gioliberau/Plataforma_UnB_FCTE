import re                       # Remover a pontuação do CPF salvo.
import sqlite3                  # Conectar e executar operações no banco SQLite.
from pathlib import Path        # Manipulação de caminhos de arquivos e pastas.
from contextlib import closing  # Fechamento da conexão após o uso.

# ----------------------------------------------- #

from .user import User, Discente, Docente

# ============================= { CONFIGURAÇÃO } ============================= #

caminho_banco = Path(__file__).resolve().parent / 'sistema.db'
# Define o caminho do banco de dados ('sistema.db') na mesma pasta deste arquivo. ('code_py')

esquema = '''
    CREATE TABLE IF NOT EXISTS acessos (
        email TEXT PRIMARY KEY COLLATE NOCASE,
        tipo_usuario TEXT NOT NULL
            CHECK (tipo_usuario IN ('discente', 'docente', 'admin')),
        senha_hash TEXT NOT NULL,
        trocar_senha INTEGER NOT NULL DEFAULT 1
    );
 
    CREATE TABLE IF NOT EXISTS usuarios (
        id_user TEXT PRIMARY KEY,
        tipo_usuario TEXT NOT NULL
            CHECK (tipo_usuario IN ('discente', 'docente')),
        nome TEXT NOT NULL,
        cpf TEXT UNIQUE,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE
            REFERENCES acessos(email),
        ano_entrada INTEGER,
        semestre_entrada INTEGER,
        curso TEXT,
        area TEXT
    );
 
    CREATE TABLE IF NOT EXISTS oportunidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        categoria TEXT NOT NULL,
        descricao TEXT NOT NULL,
        contato TEXT NOT NULL,
        prazo TEXT,
        autor_id TEXT NOT NULL,
        autor_nome TEXT NOT NULL,
        encerrada INTEGER NOT NULL DEFAULT 0,
        publicada_em TEXT NOT NULL
    );
 
    CREATE TABLE IF NOT EXISTS entidades_fixas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL,
        instagram_link TEXT NOT NULL
    );
 
    CREATE TABLE IF NOT EXISTS interesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        oportunidade_id INTEGER NOT NULL REFERENCES oportunidades(id),
        discente_id TEXT NOT NULL REFERENCES usuarios(id_user),
        criado_em TEXT NOT NULL,
        UNIQUE (oportunidade_id, discente_id)
    );
 
    CREATE TABLE IF NOT EXISTS dados_publicos (
        categoria TEXT NOT NULL,
        chave TEXT NOT NULL,
        valor TEXT NOT NULL,
        fonte TEXT NOT NULL,
        PRIMARY KEY (categoria, chave)
    );

    -- 'turma' é a mesma chave das turmas em dados_publicos: 'periodo|codigo|numero'
    CREATE TABLE IF NOT EXISTS ofertas (
        turma TEXT PRIMARY KEY,
        docente_id TEXT NOT NULL REFERENCES usuarios(id_user)
    );

    CREATE TABLE IF NOT EXISTS matriculas (
        discente_id TEXT NOT NULL REFERENCES usuarios(id_user),
        turma TEXT NOT NULL,
        nota REAL CHECK (nota BETWEEN 0 AND 10),
        PRIMARY KEY (discente_id, turma)
    );
'''

# ============================= { CONEXÃO } ============================= #

def conectar():
    #Abre uma conexão com o banco de dados.

    conexao = sqlite3.connect(caminho_banco)
    conexao.row_factory = sqlite3.Row               # Permite acessar os resultados do banco pelo nome das colunas
    
    conexao.executescript(esquema)                  # IF NOT EXISTS: só cria o que ainda não existe
    
    return conexao



# ============================= { CONSULTAS } ============================= #

def buscar_perfil(email):
    # Busca o perfil pelo e-mail e devolve o objeto (Discente/Docente), ou None se ainda não existir.

    with closing(conectar()) as conexao:
        dados = conexao.execute(
            '''
            SELECT usuarios.*, acessos.senha_hash
            FROM usuarios
            JOIN acessos ON acessos.email = usuarios.email
            WHERE usuarios.email = ?
            ''',
            (email.strip(),)
        ).fetchone()

        # fetchone() -> retorna o primeiro resultado da consulta ou None se não houver resultados.

    return __reconstruir(dados)


# ============================= { CADASTRO } ============================= #

def cadastrar_perfil(conta, nome, cpf, ano_entrada, semestre_entrada, curso_ou_area):
    # Cria o perfil de quem já tem acesso (login.py), usando o e-mail e a senha desse acesso.

    if conta.tipo_usuario not in ('discente', 'docente'):
        raise ValueError('Apenas discentes e docentes possuem perfil.')

    classe = Discente if conta.tipo_usuario == 'discente' else Docente

    usuario = classe(
        ano_entrada, semestre_entrada, nome, cpf, conta.email, curso_ou_area
    )

    for tentativa in range(3):
        try:
            with closing(conectar()) as conexao, conexao:      # 'with conexao' confirma (commit) a gravação
                conexao.execute(
                    '''
                    INSERT INTO usuarios (
                        id_user, tipo_usuario, nome, cpf, email,
                        ano_entrada, semestre_entrada, curso, area
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        usuario.id_user,
                        usuario.tipo_usuario,
                        usuario.nome,
                        usuario.cpf,
                        usuario.email,
                        usuario.ano_entrada,
                        usuario.semestre_entrada,
                        getattr(usuario, 'curso', None),
                        getattr(usuario, 'area', None)
                    )
                )
 
            return usuario

        except sqlite3.IntegrityError as erro:
            if 'id_user' in str(erro) and tentativa < 2:
                usuario.sortear_nova_matricula()
                continue  

            raise ValueError('Este e-mail ou CPF já possui perfil cadastrado.')


# ============================= { RECONSTRUÇÃO DE OBJETOS } ============================= #

def __reconstruir(dados):
    
    if dados is None:
        return None

    tipo = dados['tipo_usuario']

    # O CPF é salvo formatado (000.000.000-00); a validação espera só os dígitos.
    cpf = re.sub(r'\D', '', dados['cpf']) if dados['cpf'] else None

    comum = (
        dados['ano_entrada'], dados['semestre_entrada'], dados['nome'], cpf, dados['email']
    )

    if dados['tipo_usuario'] == 'discente':
        return Discente(*comum, dados['curso'], id_fixo=dados['id_user'])

    if dados['tipo_usuario'] == 'docente':
        return Docente(*comum, dados['area'], id_fixo=dados['id_user'])

    raise ValueError('Tipo de usuário desconhecido.')
