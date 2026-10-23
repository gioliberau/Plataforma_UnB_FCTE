from contextlib import closing
from datetime import date, datetime
import sqlite3

# ----------------------------------------------- #

from .banco import conectar
from .login import exigir_admin

# ============================= { CONFIGURAÇÃO } ============================= #

# Categorias dinâmicas do mural de vagas (gerenciadas por docentes)
categorias_oportunidades = {
    'projeto_extensao': 'Projeto de extensão',
    'projeto_pesquisa': 'Projeto de pesquisa científica',
    'estagio': 'Estágio',
}

# Tipos de entidades fixas da instituição (consultadas apenas por discentes)
tipos_entidades_fixas = {
    'empresa_junior': 'Empresa Júnior',
    'atletica': 'Atlética / Equipe Esportiva',
    'equipe_competicao': 'Equipe de Competição',
}

# Categorias de oportunidades que cada perfil enxerga no mural
categorias_por_perfil = {
    'discente': tuple(categorias_oportunidades),
    'docente': ('estagio', 'projeto_extensao', 'projeto_pesquisa'),
    'admin' : tuple(categorias_oportunidades)
}

campos_editaveis = ('titulo', 'descricao', 'contato', 'prazo')

# Lista de entidades fixas da UnB FGA pré-cadastradas no sistema
entidades_fixas_iniciais = [
    {
        'nome': "Orc'estra",
        'tipo': 'empresa_junior',
        'instagram_link': 'https://instagram.com/ser.orcestra/',
    },
    {
        'nome': "Zenit",
        'tipo': 'empresa_junior',
        'instagram_link': 'https://instagram.com/zenitaerospace/',
    },
    {
        'nome': "Matriz",
        'tipo': 'empresa_junior',
        'instagram_link': 'https://instagram.com/matrizenergia/',
    },
    {
        'nome': "EletroJun",
        'tipo': 'empresa_junior',
        'instagram_link': 'https://instagram.com/equipe.eletrojun/',
    },
    {
        'nome': 'Atlética Pesadelo',
        'tipo': 'atletica',
        'instagram_link': 'https://instagram.com/atleticapesadelo/',
    },
    {
        'nome': 'UnBaja',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/unbaja/',
    },
    {
        'nome': 'Mamutes do Cerrado',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/mmtsdocerrado/',
    },
    {
        'nome': 'Gama CubeDesign',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/gamacubedesign/',
    },
    {
        'nome': 'FGR',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/fgr.unb/',
    },
    {
        'nome': 'EDRA',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/edraunb/',
    },
    {
        'nome': 'Ares',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/ares.unb/',
    },
    {
        'nome': 'Titans',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/robotictitans/',
    },
    {
        'nome': 'Capital Rocket Team',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/capitalrocketteam/',
    },
]


def categorias_do_perfil(perfil):
    # Categorias visíveis para o tipo do perfil no mural de oportunidades.
    return categorias_por_perfil.get(perfil.tipo_usuario, ())


# ============================= { CLASSE OPORTUNIDADE } ============================= #

class Oportunidade:

    def __init__(self, titulo, categoria, descricao, contato, prazo=None,
                 autor_id=None, autor_nome=None, id_oportunidade=None,
                 encerrada=False, publicada_em=None):

        if categoria not in categorias_oportunidades:
            raise ValueError('Categoria de oportunidade inválida.')

        self.__categoria = categoria
        self.__autor_id = autor_id
        self.__autor_nome = autor_nome
        self.__id = id_oportunidade
        self.__encerrada = bool(encerrada)
        self.__publicada_em = (
            publicada_em or datetime.now().isoformat(timespec='seconds')
        )

        # Passam pelos setters (validação).
        self.titulo = titulo
        self.descricao = descricao
        self.contato = contato
        self.prazo = prazo

    # ========== { Getters } ========== #

    @property
    def id(self):
        return self.__id

    @property
    def categoria(self):
        return self.__categoria

    @property
    def nome_categoria(self):
        return categorias_oportunidades[self.__categoria]

    @property
    def autor_id(self):
        return self.__autor_id

    @property
    def autor_nome(self):
        return self.__autor_nome

    @property
    def encerrada(self):
        return self.__encerrada

    @property
    def publicada_em(self):
        return self.__publicada_em

    @property
    def titulo(self):
        return self.__titulo

    @property
    def descricao(self):
        return self.__descricao

    @property
    def contato(self):
        return self.__contato

    @property
    def prazo(self):
        return self.__prazo

    # ========== { Setters } ========== #

    @titulo.setter
    def titulo(self, valor):
        self.__titulo = self.__validar_texto(valor, 'O título', 100)

    @descricao.setter
    def descricao(self, valor):
        self.__descricao = self.__validar_texto(valor, 'A descrição', 1000)

    @contato.setter
    def contato(self, valor):
        self.__contato = self.__validar_texto(valor, 'O contato', 150)

    @prazo.setter
    def prazo(self, valor):
        if valor is not None and not isinstance(valor, date):
            raise ValueError('O prazo deve ser uma data.')

        self.__prazo = valor

    # ========== { Comportamento } ========== #

    def definir_id(self, novo_id):
        # Usado pelo repositório depois do INSERT.
        self.__id = novo_id

    def encerrar(self):
        self.__encerrada = True

    def inscricoes_abertas(self, hoje=None):
        hoje = hoje or date.today()

        if self.__encerrada:
            return False

        return self.__prazo is None or self.__prazo >= hoje


    @staticmethod
    def __validar_texto(valor, rotulo, limite):
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f'{rotulo} não pode estar vazio.')

        valor = valor.strip()

        if len(valor) > limite:
            raise ValueError(f'{rotulo} deve ter no máximo {limite} caracteres.')

        return valor


    def __str__(self):
        prazo = self.__prazo.strftime('%d/%m/%Y') if self.__prazo else 'sem prazo'
        situacao = 'ENCERRADA' if self.__encerrada else 'aberta'

        return (
            f'[#{self.__id}] {self.__titulo} ({self.nome_categoria} - {situacao})\n'
            f'    {self.__descricao}\n'
            f'    Publicado por: {self.__autor_nome} | Contato: {self.__contato}\n'
            f'    Prazo: {prazo}'
        )


# ============================= { ENTIDADES FIXAS } ============================= #

def cadastrar_entidade_fixa(nome, tipo, instagram_link):
    # Cadastra manualmente uma nova entidade fixa no catálogo (se necessário).
    exigir_admin(conta)

    if tipo not in tipos_entidades_fixas:
        raise ValueError('Tipo de entidade fixa inválido.')

    if not isinstance(nome, str) or not nome.strip():
        raise ValueError('O nome não pode estar vazio.')

    if not isinstance(instagram_link, str) or not instagram_link.strip().startswith(
        ('https://instagram.com/', 'https://www.instagram.com/')
    ):
        raise ValueError('Informe um link do Instagram (https://instagram.com/...).')

    nome = nome.strip()

    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute(
            '''
            INSERT INTO entidades_fixas (nome, tipo, instagram_link)
            VALUES (?, ?, ?)
            ''',
            (nome, tipo, instagram_link.strip())
        )
        return cursor.lastrowid


def _popular_entidades_fixas():
    # Insere as entidades padrão caso a tabela esteja limpa.
    with closing(conectar()) as conexao:
        total = conexao.execute('SELECT COUNT(*) FROM entidades_fixas').fetchone()[0]

        if total == 0:
            with conexao:
                conexao.executemany(
                    '''
                    INSERT INTO entidades_fixas (nome, tipo, instagram_link)
                    VALUES (:nome, :tipo, :instagram_link)
                    ''',
                    entidades_fixas_iniciais
                )


def listar_entidades_fixas(perfil, tipo=None):
    # Retorna as entidades fixas da instituição. Apenas alunos (discentes) podem consultar.
    
    if tipo is not None and tipo not in tipos_entidades_fixas:
        raise ValueError('Tipo de entidade inválido.')
 
    _popular_entidades_fixas()
 
    if tipo:
        linhas = _consultar(
            'SELECT * FROM entidades_fixas WHERE tipo = ? ORDER BY nome ASC', (tipo,)
        )
    else:
        linhas = _consultar('SELECT * FROM entidades_fixas ORDER BY tipo ASC, nome ASC')
 
    return [dict(linha) for linha in linhas]


# ============================= { FUNÇÕES AUXILIARES } ============================= #

def _exigir_tipo(perfil, tipo):
    if perfil is None or perfil.tipo_usuario != tipo:
        raise PermissionError(f'Ação permitida apenas para {tipo}s.')

def _consultar(sql, parametros=()):
    with closing(conectar()) as conexao:
        return conexao.execute(sll, parametros).fetchall()

def _reconstruir(linha):
    return Oportunidade(
        linha['titulo'],
        linha['categoria'],
        linha['descricao'],
        linha['contato'],
        date.fromisoformat(linha['prazo']) if linha['prazo'] else None,
        autor_id=linha['autor_id'],
        autor_nome=linha['autor_nome'],
        id_oportunidade=linha['id'],
        encerrada=linha['encerrada'],
        publicada_em=linha['publicada_em']
    )


def _inserir(oportunidade):
    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute(
            '''
            INSERT INTO oportunidades (
                titulo, categoria, descricao, contato, prazo,
                autor_id, autor_nome, encerrada, publicada_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                oportunidade.titulo,
                oportunidade.categoria,
                oportunidade.descricao,
                oportunidade.contato,
                oportunidade.prazo.isoformat() if oportunidade.prazo else None,
                oportunidade.autor_id,
                oportunidade.autor_nome,
                int(oportunidade.encerrada),
                oportunidade.publicada_em
            )
        )
 
    oportunidade.definir_id(cursor.lastrowid)
    return oportunidade
 
 
def _exigir_gestor(usuario):
    if usuario is None or usuario.tipo_usuario not in ('docente', 'admin'):
        raise PermissionError('Ação permitida apenas para docentes e admins.')
 
 
def _buscar_gerenciavel(usuario, id_oportunidade):
    # Garante que a publicação existe e que o usuário pode gerenciá-la:
    # admin gerencia qualquer uma; docente, só as suas.
    _exigir_gestor(usuario)
 
    oportunidade = buscar(id_oportunidade)
 
    if oportunidade is None:
        raise ValueError('Publicação não encontrada.')
 
    if usuario.tipo_usuario == 'docente' and oportunidade.autor_id != usuario.id_user:
        raise ValueError('Publicação não encontrada entre as suas.')
 
    return oportunidade

# ============================= { CONSULTAS } ============================= #

 
def buscar(id_oportunidade):
    # Devolve a Oportunidade ou None.
    linhas = _consultar('SELECT * FROM oportunidades WHERE id = ?', (id_oportunidade,))
    return _reconstruir(linhas[0]) if linhas else None
 
 
def listar_para_discente(perfil, categoria=None):
    # Só oportunidades abertas e dentro do prazo, nas categorias que o discente enxerga.
    _exigir_tipo(perfil, 'discente')
 
    permitidas = categorias_do_perfil(perfil)
 
    if categoria is not None and categoria not in permitidas:
        raise PermissionError('Categoria não disponível para o seu perfil.')
 
    alvo = (categoria,) if categoria else permitidas
    marcadores = ', '.join('?' for _ in alvo)
 
    linhas = _consultar(
        f'''
        SELECT * FROM oportunidades
        WHERE encerrada = 0 AND categoria IN ({marcadores})
        ORDER BY publicada_em DESC, id DESC
        ''',
        alvo
    )
 
    oportunidades = [_reconstruir(linha) for linha in linhas]
 
    return [o for o in oportunidades if o.inscricoes_abertas()]
 
 
def listar_minhas(perfil):
    _exigir_tipo(perfil, 'docente')
 
    linhas = _consultar(
        '''
        SELECT * FROM oportunidades
        WHERE autor_id = ?
        ORDER BY publicada_em DESC, id DESC
        ''',
        (perfil.id_user,)
    )
 
    return [_reconstruir(linha) for linha in linhas]
 
 
def listar_todas(conta):
    # Todas as oportunidades, de qualquer categoria e situação (uso do admin).
    exigir_admin(conta)
 
    linhas = _consultar('SELECT * FROM oportunidades ORDER BY publicada_em DESC, id DESC')
    return [_reconstruir(linha) for linha in linhas]
 


# ============================= { DOCENTE/ADMIN: PUBLICAR / GERENCIAR } ============================= #

def publicar(autor, titulo, categoria, descricao, contato, prazo=None):
    
    _exigir_gestor(autor)

    if categoria not in categorias_do_perfil(autor):
        raise PermissionError('Categoria não disponível para o seu perfil.')

    if prazo is not None and prazo < date.today():
        raise ValueError('O prazo não pode estar no passado.')

    if autor.tipo_usuario == 'admin':
        autor_id, autor_nome = f'admin:{autor.email}', 'Administração'
    else:
        autor_id, autor_nome = autor.id_user, autor.nome

    return _inserir(Oportunidade(
        titulo, categoria, descricao, contato, prazo,
        autor_id=perfil.id_user, autor_nome=perfil.nome
    ))


def editar(perfil, id_oportunidade, **campos):
    # Campos aceitos: titulo, descricao, contato, prazo (date ou None).
    _exigir_tipo(perfil, 'docente')

    if not campos or any(nome not in campos_editaveis for nome in campos):
        raise ValueError('Informe apenas campos editáveis: ' + ', '.join(campos_editaveis))

    oportunidade = _buscar_do_autor(perfil, id_oportunidade)

    if oportunidade.encerrada:
        raise ValueError('Publicações encerradas não podem ser editadas.')

    if campos.get('prazo') is not None and campos['prazo'] < date.today():
        raise ValueError('O prazo não pode estar no passado.')

    for nome, valor in campos.items():
        setattr(oportunidade, nome, valor)     # passa pelos setters (validação)

    with closing(conectar()) as conexao, conexao:
        conexao.execute(
            '''
            UPDATE oportunidades
            SET titulo = ?, descricao = ?, contato = ?, prazo = ?
            WHERE id = ? AND autor_id = ?
            ''',
            (
                oportunidade.titulo,
                oportunidade.descricao,
                oportunidade.contato,
                oportunidade.prazo.isoformat() if oportunidade.prazo else None,
                oportunidade.id,
                perfil.id_user
            )
        )

    return oportunidade


def encerrar(perfil, id_oportunidade):
    oportunidade = _buscar_gerenciavel(perfil, id_oportunidade)

    if oportunidade.encerrada:
        raise ValueError('Esta publicação já está encerrada.')

    oportunidade.encerrar()

    with closing(conectar()) as conexao, conexao:
        conexao.execute(
            'UPDATE oportunidades SET encerrada = 1 WHERE id = ?',
            (oportunidade.id,)
        )

    return oportunidade


def remover(conta, id_oportunidade):
    # Remove a publicação e os interesses ligados a ela. Só admin.
    exigir_admin(conta)
 
    oportunidade = buscar(id_oportunidade)
 
    if oportunidade is None:
        raise ValueError('Publicação não encontrada.')
 
    with closing(conectar()) as conexao, conexao:
        conexao.execute(
            'DELETE FROM interesses WHERE oportunidade_id = ?',
            (oportunidade.id,)
        )
        conexao.execute(
            'DELETE FROM oportunidades WHERE id = ?',
            (oportunidade.id,)
        )
 
    return oportunidade

# ============================= { INTERESSES } ============================= #

def demonstrar_interesse(perfil, id_oportunidade):
    _exigir_tipo(perfil, 'discente')
 
    oportunidade = buscar(id_oportunidade)
 
    if (
        oportunidade is None
        or oportunidade.categoria not in categorias_do_perfil(perfil)
        or not oportunidade.inscricoes_abertas()
    ):
        raise ValueError('Oportunidade não encontrada ou não está mais aberta.')
 
    # Um discente só pode demonstrar interesse uma vez por oportunidade (UNIQUE na tabela).
    try:
        with closing(conectar()) as conexao, conexao:
            conexao.execute(
                '''
                INSERT INTO interesses (oportunidade_id, discente_id, criado_em)
                VALUES (?, ?, ?)
                ''',
                (
                    oportunidade.id,
                    perfil.id_user,
                    datetime.now().isoformat(timespec='seconds')
                )
            )
    except sqlite3.IntegrityError:
        raise ValueError('Você já demonstrou interesse nesta oportunidade.')
 
    return oportunidade
 
 
def retirar_interesse(perfil, id_oportunidade):
    _exigir_tipo(perfil, 'discente')
 
    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute(
            'DELETE FROM interesses WHERE oportunidade_id = ? AND discente_id = ?',
            (id_oportunidade, perfil.id_user)
        )
 
    if cursor.rowcount == 0:
        raise ValueError('Você não tinha interesse registrado nesta oportunidade.')
 
 
def listar_meus_interesses(perfil):
    _exigir_tipo(perfil, 'discente')
 
    linhas = _consultar(
        '''
        SELECT oportunidade_id
        FROM interesses
        WHERE discente_id = ?
        ORDER BY criado_em DESC, id DESC
        ''',
        (perfil.id_user,)
    )
 
    oportunidades = [buscar(linha['oportunidade_id']) for linha in linhas]
 
    return [o for o in oportunidades if o is not None]
 
 
def contar_interessados(id_oportunidade):
    return _consultar(
        'SELECT COUNT(*) FROM interesses WHERE oportunidade_id = ?',
        (id_oportunidade,)
    )[0][0]
 
 
def listar_interessados(usuario, id_oportunidade):
    #Vale para docente (só as suas publicações) e admin (qualquer uma).
    _buscar_gerenciavel(usuario, id_oportunidade)
 
    linhas = _consultar(
        '''
        SELECT usuarios.id_user AS matricula,
               usuarios.nome,
               usuarios.email,
               usuarios.curso,
               interesses.criado_em
        FROM interesses
        JOIN usuarios ON usuarios.id_user = interesses.discente_id
        WHERE interesses.oportunidade_id = ?
        ORDER BY interesses.criado_em
        ''',
        (id_oportunidade,)
    )
 
    return [dict(linha) for linha in linhas]

# ============================= { DISCENTE: CONSULTAR MURAL } ============================= #

def listar_para_discente(perfil, categoria=None):
    # Só oportunidades abertas e dentro do prazo, nas categorias que o discente enxerga.
    _exigir_tipo(perfil, 'discente')

    permitidas = categorias_do_perfil(perfil)

    if categoria is not None and categoria not in permitidas:
        raise PermissionError('Categoria não disponível para o seu perfil.')

    criar_tabela()

    alvo = (categoria,) if categoria else permitidas
    marcadores = ', '.join('?' for _ in alvo)

    with closing(conectar()) as conexao:
        linhas = conexao.execute(
            f'''
            SELECT * FROM oportunidades
            WHERE encerrada = 0 AND categoria IN ({marcadores})
            ORDER BY publicada_em DESC, id DESC
            ''',
            alvo
        ).fetchall()

    oportunidades = [_reconstruir(linha) for linha in linhas]

    return [o for o in oportunidades if o.inscricoes_abertas()]


# ============================= { API PARA OUTROS MÓDULOS } ============================= #

def buscar(id_oportunidade):
    # Devolve a Oportunidade ou None.
    return _buscar(id_oportunidade)


def listar_todas():
    # Todas as oportunidades, de qualquer categoria e situação (uso do admin).
    criar_tabela()

    with closing(conectar()) as conexao:
        linhas = conexao.execute(
            'SELECT * FROM oportunidades ORDER BY publicada_em DESC, id DESC'
        ).fetchall()

    return [_reconstruir(linha) for linha in linhas]


def inserir(oportunidade):
    # Grava uma Oportunidade nova e preenche o id gerado.
    criar_tabela()

    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute(
            '''
            INSERT INTO oportunidades (
                titulo, categoria, descricao, contato, prazo,
                autor_id, autor_nome, encerrada, publicada_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                oportunidade.titulo,
                oportunidade.categoria,
                oportunidade.descricao,
                oportunidade.contato,
                oportunidade.prazo.isoformat() if oportunidade.prazo else None,
                oportunidade.autor_id,
                oportunidade.autor_nome,
                int(oportunidade.encerrada),
                oportunidade.publicada_em
            )
        )

    oportunidade.definir_id(cursor.lastrowid)
    return oportunidade