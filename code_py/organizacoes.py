from contextlib import closing
from datetime import date, datetime
import sqlite3
import textwrap
import unicodedata

# ----------------------------------------------- #

from .banco import conectar
from .login import exigir_admin
from . import tela

# ============================= { CONFIGURAÇÃO } ============================= #

# Categorias dinâmicas do mural de vagas (gerenciadas por docentes)
categorias_oportunidades = {
    'projeto_extensao': 'Projeto de extensão',
    'projeto_pesquisa': 'Projeto de pesquisa científica',
    'estagio': 'Estágio',
    'monitoria': 'Monitoria',
}

# Tipos de entidades fixas da instituição (consultadas apenas por discentes)
tipos_entidades_fixas = {
    'empresa_junior': 'Empresa Júnior',
    'atletica': 'Atlética / Equipe Esportiva',
    'equipe_competicao': 'Equipe de Competição',
}

# Texto padrão de cada tipo: usado quando a entidade não tem descrição / "como participar" próprios.
info_tipos = {
    'empresa_junior': {
        'sobre': 'Associação civil sem fins lucrativos, gerida por estudantes de graduação, '
                 'que presta serviços e consultoria na área do curso, com orientação de professores.',
        'como_participar': 'Costuma ser por processo seletivo; acompanhe o Instagram para saber quando abre.',
    },
    'atletica': {
        'sobre': 'Entidade estudantil esportiva e social: organiza times, treinos, torneios e eventos para os alunos.',
        'como_participar': 'Procure a atlética no Instagram para saber como entrar nos times e nos eventos.',
    },
    'equipe_competicao': {
        'sobre': 'Grupo de estudantes que projeta, constrói e testa protótipos para competições universitárias de engenharia.',
        'como_participar': 'Em geral por processo seletivo divulgado nas redes; veja o Instagram da equipe.',
    },
}

# Colunas opcionais da tabela entidades_fixas (além de nome, tipo e instagram_link).
campos_extras = ('area', 'descricao', 'como_participar', 'contato')


# Categorias de oportunidades que cada perfil enxerga no mural
categorias_por_perfil = {
    'discente': tuple(categorias_oportunidades),
    'docente': ('estagio', 'projeto_extensao', 'projeto_pesquisa', 'monitoria'),
    'admin' : tuple(categorias_oportunidades)
}

campos_editaveis = ('titulo', 'descricao', 'contato', 'prazo')

# Lista de entidades fixas da UnB FGA pré-cadastradas no sistema
entidades_fixas_iniciais = [
    {
        'nome': "Orc'estra",
        'tipo': 'empresa_junior',
        'instagram_link': 'https://instagram.com/ser.orcestra/',
        'area': 'Gamificação',
    },
    {
        'nome': "Zenit",
        'tipo': 'empresa_junior',
        'instagram_link': 'https://instagram.com/zenitaerospace/',
        'area': 'Engenharia Aeroespacial',
        'descricao': 'Serviços como modelagem 2D/3D, consultoria e cursos de pilotagem de drones.',

    },
    {
        'nome': "Matriz",
        'tipo': 'empresa_junior',
        'instagram_link': 'https://instagram.com/matrizenergia/',
        'area': 'Engenharia de Energia',
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
        'descricao': 'Projeta e constrói um veículo off-road para a competição Baja SAE.',
    },
    {
        'nome': 'Mamutes do Cerrado',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/mmtsdocerrado/',
        'descricao': 'Equipe de aeromodelismo.',
    },
    {
        'nome': 'Gama CubeDesign',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/gamacubedesign/',
        'descricao': 'Equipe de desenvolvimento de satélites.',
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
        'descricao': 'Equipe de drones.',
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
        'descricao': 'Equipe de robótica.',
    },
    {
        'nome': 'Capital Rocket Team',
        'tipo': 'equipe_competicao',
        'instagram_link': 'https://instagram.com/capitalrocketteam/',
        'descricao': 'Equipe de foguetes de sondagem.',
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

def cadastrar_entidade_fixa(conta, nome, tipo, instagram_link, area=None, descricao=None, como_participar=None, contato=None):
    # Cadastra manualmente uma nova entidade fixa no catálogo (se necessário).
    exigir_admin(conta)
    _popular_entidades_fixas()      # senão a lista padrão nunca entraria depois do primeiro cadastro

    if tipo not in tipos_entidades_fixas:
        raise ValueError('Tipo de entidade fixa inválido.')

    if not isinstance(nome, str) or not nome.strip():
        raise ValueError('O nome não pode estar vazio.')

    if not isinstance(instagram_link, str) or not instagram_link.strip().startswith(
        ('https://instagram.com/', 'https://www.instagram.com/')
    ):
        raise ValueError('Informe um link do Instagram (https://instagram.com/...).')

    nome = nome.strip()


    # Dados extras são opcionais: vazio vira None
    area = _limpar_opcional(area, 'A área', 80)
    descricao = _limpar_opcional(descricao, 'A descrição', 300)
    como_participar = _limpar_opcional(como_participar, 'O campo "como participar"', 300)
    contato = _limpar_opcional(contato, 'O contato', 120)


    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute(
            '''
            INSERT INTO entidades_fixas (nome, tipo, instagram_link, area, descricao, como_participar, contato)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (nome, tipo, instagram_link.strip(), area, descricao, como_participar, contato)
        )
        return cursor.lastrowid


def _popular_entidades_fixas():
    # 1) Cria as colunas extras em bancos antigos; 
    # 2) insere o catálogo se a tabela estiver vazia;
    # 3) completa só os campos VAZIOS das entidades padrão (o que o admin cadastrou nunca é sobrescrito).

    with closing(conectar()) as conexao, conexao:
        colunas = {coluna['name'] for coluna in conexao.execute('PRAGMA table_info(entidades_fixas)')}

        for campo in campos_extras:
            if campo not in colunas:
                conexao.execute(f'ALTER TABLE entidades_fixas ADD COLUMN {campo} TEXT')

        total = conexao.execute('SELECT COUNT(*) FROM entidades_fixas').fetchone()[0]

        if total == 0:
            conexao.executemany(
                '''
                INSERT INTO entidades_fixas
                    (nome, tipo, instagram_link, area, descricao, como_participar, contato)
                VALUES (:nome, :tipo, :instagram_link, :area, :descricao, :como_participar, :contato)
                ''',
                [{campo: None for campo in campos_extras} | entidade for entidade in entidades_fixas_iniciais]
            )
            return

        for entidade in entidades_fixas_iniciais:
            for campo in campos_extras:
                if entidade.get(campo):
                    conexao.execute(
                        f"UPDATE entidades_fixas SET {campo} = ? "
                        f"WHERE nome = ? AND ({campo} IS NULL OR {campo} = '')",
                        (entidade[campo], entidade['nome'])
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

def _sem_acento(texto):
    texto = unicodedata.normalize('NFD', str(texto))
    return ''.join(c for c in texto if not unicodedata.combining(c)).casefold()


def _limpar_opcional(valor, rotulo, limite):
    if valor is None or not str(valor).strip():
        return None

    valor = str(valor).strip()

    if len(valor) > limite:
        raise ValueError(f'{rotulo} deve ter no máximo {limite} caracteres.')

    return valor


def _exigir_tipo(perfil, tipo):
    if perfil is None or perfil.tipo_usuario != tipo:
        raise PermissionError(f'Ação permitida apenas para {tipo}s.')

def _consultar(sql, parametros=()):
    with closing(conectar()) as conexao, conexao:
        return conexao.execute(sql, parametros).fetchall()

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


def listar_extensao(perfil):
    # Atividades de extensão publicadas pelo docente (dados do perfil).
    return [o for o in listar_minhas(perfil) if o.categoria == 'projeto_extensao']
 
 
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
        autor_id=autor_id, autor_nome=autor_nome
    ))


def editar(perfil, id_oportunidade, **campos):
    # Campos aceitos: titulo, descricao, contato, prazo (date ou None).
    _exigir_tipo(perfil, 'docente')

    if not campos or any(nome not in campos_editaveis for nome in campos):
        raise ValueError('Informe apenas campos editáveis: ' + ', '.join(campos_editaveis))

    oportunidade = _buscar_gerenciavel(perfil, id_oportunidade)

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

def buscar_entidades(texto):
    # Busca sem acento/maiúsculas no nome, tipo, área e descrição.
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError('Digite um termo para buscar.')

    termo = _sem_acento(texto.strip())

    def alvo(entidade):
        partes = [entidade['nome'], tipos_entidades_fixas.get(entidade['tipo'], ''),
                    entidade.get('area'), entidade.get('descricao')]
        return _sem_acento(' '.join(parte for parte in partes if parte))

    return [entidade for entidade in listar_entidades_fixas(None) if termo in alvo(entidade)]


# ========== { Apresentação das entidades } ========== #

def _usuario_instagram(link):
    # https://instagram.com/unbaja/  ->  @unbaja
    return '@' + link.rstrip('/').rsplit('/', 1)[-1]


def formatar_entidade(entidade, incluir_padrao=True):
    # Card de uma entidade; campos vazios são omitidos (nada de "None" na tela).
    # incluir_padrao=False: só o que é da entidade (nas listas, o texto do tipo aparece uma vez no grupo).
    padrao = info_tipos.get(entidade['tipo'], {}) if incluir_padrao else {}
    tipo = tipos_entidades_fixas.get(entidade['tipo'], entidade['tipo'])

    linhas = [f"  ▸ {entidade['nome']}"]

    if incluir_padrao:
        linhas.append(tela.campo('Tipo', tipo))

    if entidade.get('area'):
        linhas.append(tela.campo('Área', entidade['area']))

    sobre = entidade.get('descricao') or padrao.get('sobre')
    if sobre:
        linhas.append(tela.campo('Sobre', sobre))

    participar = entidade.get('como_participar') or padrao.get('como_participar')
    if participar:
        linhas.append(tela.campo('Como participar', participar))

    linhas.append(tela.campo(
        'Instagram', f"{_usuario_instagram(entidade['instagram_link'])}  ({entidade['instagram_link']})"
    ))

    if entidade.get('contato'):
        linhas.append(tela.campo('Contato', entidade['contato']))

    return '\n'.join(linhas)


def formatar_lista_entidades(lista):
    # Grupos por tipo: título com contagem + texto geral do tipo (uma vez) + cards. Total no fim.
    if not lista:
        return 'Nenhuma organização encontrada.'

    blocos = []

    for tipo, rotulo in tipos_entidades_fixas.items():
        do_tipo = [entidade for entidade in lista if entidade['tipo'] == tipo]

        if not do_tipo:
            continue

        padrao = info_tipos.get(tipo, {})
        titulo = f'── {rotulo} ({len(do_tipo)}) '
        cabecalho = [titulo + '─' * max(tela.largura - len(titulo), 3)]

        if padrao.get('sobre'):
            cabecalho.append(tela.campo('O que é', padrao['sobre'], recuo=2))

        if padrao.get('como_participar'):
            cabecalho.append(tela.campo('Como participar', padrao['como_participar'], recuo=2))

        cards = '\n\n'.join(formatar_entidade(entidade, incluir_padrao=False) for entidade in do_tipo)
        blocos.append('\n'.join(cabecalho) + '\n\n' + cards)

    return '\n\n'.join(blocos) + f'\n\nTotal: {len(lista)} organização(ões).'


def resumo_entidades(lista):
    # Ex.: "13 organizações · Empresa Júnior: 4 · ..." (quebrado na largura da tela)
    contagens = [
        f"{rotulo}: {sum(1 for entidade in lista if entidade['tipo'] == tipo)}"
        for tipo, rotulo in tipos_entidades_fixas.items()
    ]
    texto = f'{len(lista)} organizações  ·  ' + '  ·  '.join(contagens)

    return textwrap.fill(texto, width=tela.largura, initial_indent='  ', subsequent_indent='  ')

