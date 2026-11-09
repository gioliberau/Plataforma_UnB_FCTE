import csv                      # Importação do acervo
import json
import sqlite3                  # Erro de livro duplicado (IntegrityError).
import unicodedata              # Busca sem acento.
from contextlib import closing  # Fechamento da conexão após o uso.
from datetime import date, timedelta
from pathlib import Path

# ----------------------------------------------- #

from .banco import conectar
from .login import exigir_admin
from .paginas import PaginaPerfil

# ============================= { CONFIGURAÇÃO } ============================= #

caminho_acervo = Path(__file__).resolve().parent.parent / 'data' / 'acervo_biblioteca.json'

#   discente de graduação: 10 livros por 15 dias | docente: 15 livros por 30 dias
#   renovação online: até 5 vezes | multa: R$ 0,90 por dia de atraso, por livro

regras = {
    'discente': {'limite': 10, 'prazo_dias': 15},
    'docente': {'limite': 15, 'prazo_dias': 30},
}

max_renovacoes = 5
multa_por_dia = 0.90
limite_exibicao = 20

esquema_biblioteca = '''
    CREATE TABLE IF NOT EXISTS livros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        autores TEXT NOT NULL,
        area TEXT NOT NULL,
        exemplares INTEGER NOT NULL CHECK (exemplares >= 0),
        UNIQUE (titulo, autores)
    );

    CREATE TABLE IF NOT EXISTS emprestimos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        livro_id INTEGER NOT NULL REFERENCES livros(id),
        usuario_id TEXT NOT NULL REFERENCES usuarios(id_user),
        retirado_em TEXT NOT NULL,
        devolver_ate TEXT NOT NULL,
        devolvido_em TEXT,
        renovacoes INTEGER NOT NULL DEFAULT 0
    );
'''

# ============================= { CONEXÃO E ACERVO } ============================= #

def _conectar():
    # Usa a conexão do banco.py, garante as tabelas da biblioteca e carrega o acervo na 1ª vez.
    conexao = conectar()
    conexao.executescript(esquema_biblioteca)

    with conexao:
        if conexao.execute('SELECT COUNT(*) FROM livros').fetchone()[0] == 0:
            _carregar_json(conexao)

    return conexao


sql_inserir_ou_atualizar = '''
    INSERT INTO livros (titulo, autores, area, exemplares) VALUES (?, ?, ?, ?)
    ON CONFLICT (titulo, autores) DO UPDATE SET
        area = excluded.area, exemplares = excluded.exemplares
'''


def _carregar_json(conexao):
    # Insere livros novos e atualiza a área/quantidade dos que já existem. Devolve quantos mudaram.
    with open(caminho_acervo, encoding='utf-8') as arquivo:
        livros = json.load(arquivo)['livros']

    for livro in livros:
        conexao.execute(
            '''
            INSERT INTO livros (titulo, autores, area, exemplares) VALUES (?, ?, ?, ?)
            ON CONFLICT (titulo, autores) DO UPDATE SET
                area = excluded.area, exemplares = excluded.exemplares
            ''',
            (livro['titulo'], livro['autores'], livro['area'], livro['exemplares'])
        )

    return len(livros)


def _ler_csv(caminho):
    # Lê o CSV (colunas: titulo, autores, area, exemplares). Aceita ';' ou ',' e UTF-8 ou Excel (latin-1).
    arquivo = Path(str(caminho).strip().strip('"'))
 
    if not arquivo.is_file():
        raise ValueError('Arquivo não encontrado.')
 
    try:
        texto = arquivo.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        texto = arquivo.read_text(encoding='latin-1')
 
    linhas = texto.splitlines()
 
    if not linhas:
        raise ValueError('O arquivo está vazio.')
 
    delimitador = ';' if linhas[0].count(';') >= linhas[0].count(',') else ','
    leitor = csv.DictReader(linhas, delimiter=delimitador)
    leitor.fieldnames = [_normalizar(coluna).strip() for coluna in (leitor.fieldnames or [])]
 
    faltando = [c for c in ('titulo', 'autores', 'area', 'exemplares') if c not in leitor.fieldnames]
 
    if faltando:
        raise ValueError(f"Faltam as colunas: {', '.join(faltando)}. Cabeçalho esperado: titulo;autores;area;exemplares")
 
    livros, erros = [], []
 
    for numero, linha in enumerate(leitor, start=2):        # linha 1 = cabeçalho
        titulo = (linha['titulo'] or '').strip()
        autores = (linha['autores'] or '').strip()
        area = (linha['area'] or '').strip()
 
        try:
            exemplares = int((linha['exemplares'] or '').strip())
            if exemplares < 0:
                raise ValueError
        except ValueError:
            erros.append(f'linha {numero}: exemplares deve ser um número inteiro (0 ou mais)')
            continue
 
        if not titulo or not autores or not area:
            erros.append(f'linha {numero}: título, autores e área são obrigatórios')
            continue
 
        livros.append((titulo, autores, area, exemplares))
 
    if erros:
        resto = f' (e mais {len(erros) - 5})' if len(erros) > 5 else ''
        raise ValueError('Nada foi importado. Corrija o arquivo:\n  ' + '\n  '.join(erros[:5]) + resto)
 
    if not livros:
        raise ValueError('O arquivo não tem nenhum livro.')
 
    return livros


def _normalizar(texto):
    # Minúsculas e sem acento: 'Cálculo' e 'calculo' passam a ser iguais na busca.
    decomposto = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in decomposto if not unicodedata.combining(c)).lower()


def formatar_data(data):
    return data.strftime('%d/%m/%Y')


# ============================= { CLASSE LIVRO } ============================= #

class Livro:

    def __init__(self, id_livro, titulo, autores, area, exemplares, emprestados):
        self.__id = id_livro
        self.__titulo = titulo
        self.__autores = autores
        self.__area = area
        self.__exemplares = exemplares
        self.__emprestados = emprestados

    # ========== { Getters } ========== #

    @property
    def id(self):
        return self.__id

    @property
    def titulo(self):
        return self.__titulo

    @property
    def autores(self):
        return self.__autores

    @property
    def area(self):
        return self.__area

    @property
    def exemplares(self):
        return self.__exemplares

    @property
    def disponiveis(self):
        return max(0, self.__exemplares - self.__emprestados)

    def __str__(self):
        situacao = f'{self.disponiveis}/{self.__exemplares} disponíveis' if self.disponiveis else 'indisponível'

        return f'[{self.__id}] {self.__titulo}\n     {self.__autores} | {self.__area} | {situacao}'


# ============================= { CLASSE EMPRESTIMO } ============================= #

class Emprestimo:
    # Uma reserva/empréstimo de um livro por um usuário. As datas são calculadas em relação a 'hoje'.

    def __init__(self, dados, hoje):
        self.__id = dados['id']
        self.__livro_id = dados['livro_id']
        self.__titulo = dados['titulo']
        self.__retirado_em = date.fromisoformat(dados['retirado_em'])
        self.__devolver_ate = date.fromisoformat(dados['devolver_ate'])
        self.__devolvido_em = date.fromisoformat(dados['devolvido_em']) if dados['devolvido_em'] else None
        self.__renovacoes = dados['renovacoes']
        self.__hoje = hoje

    # ========== { Getters } ========== #

    @property
    def id(self):
        return self.__id

    @property
    def livro_id(self):
        return self.__livro_id

    @property
    def titulo(self):
        return self.__titulo

    @property
    def retirado_em(self):
        return self.__retirado_em

    @property
    def devolver_ate(self):
        return self.__devolver_ate

    @property
    def devolvido_em(self):
        return self.__devolvido_em

    @property
    def renovacoes(self):
        return self.__renovacoes

    @property
    def ativo(self):
        return self.__devolvido_em is None

    @property
    def dias_atraso(self):
        # Para quem ainda está com o livro conta até hoje; para quem devolveu, até a data da devolução.
        referencia = self.__devolvido_em or self.__hoje
        return max(0, (referencia - self.__devolver_ate).days)

    @property
    def atrasado(self):
        return self.dias_atraso > 0

    @property
    def multa(self):
        return self.dias_atraso * multa_por_dia

    @property
    def status(self):
        if self.ativo:
            if self.atrasado:
                return f'ATRASADO há {self.dias_atraso} dia(s) | multa até agora: R$ {self.multa:.2f}'

            restantes = (self.__devolver_ate - self.__hoje).days
            return f'Devolver até {formatar_data(self.__devolver_ate)} (faltam {restantes} dia(s))'

        texto = f'Devolvido em {formatar_data(self.__devolvido_em)}'

        if self.atrasado:
            texto += f' com {self.dias_atraso} dia(s) de atraso | multa: R$ {self.multa:.2f}'

        return texto

    def __str__(self):
        return (
            f'#{self.__id} {self.__titulo}\n'
            f'     Retirado em {formatar_data(self.__retirado_em)} | '
            f'Renovações: {self.__renovacoes}/{max_renovacoes}\n'
            f'     {self.status}'
        )


# ============================= { CLASSE BIBLIOTECA } ============================= #

class Biblioteca:

    def __init__(self, hoje=date.today):
        # 'hoje' é uma função: nos testes dá para trocar por uma data falsa e simular atrasos.
        self.__hoje = hoje

    # ========== { Consulta ao acervo } ========== #

    _consulta_livros = '''
        SELECT livros.*,
               (SELECT COUNT(*) FROM emprestimos
                WHERE emprestimos.livro_id = livros.id AND emprestimos.devolvido_em IS NULL) AS emprestados
        FROM livros
    '''

    @staticmethod
    def _montar_livro(linha):
        return Livro(
            linha['id'], linha['titulo'], linha['autores'],
            linha['area'], linha['exemplares'], linha['emprestados']
        )

    def areas(self):
        with closing(_conectar()) as conexao:
            linhas = conexao.execute('SELECT DISTINCT area FROM livros ORDER BY area').fetchall()

        return [linha['area'] for linha in linhas]

    def buscar(self, termo='', area=None, so_disponiveis=False):
        # Todas as palavras do termo precisam aparecer no título, nos autores ou na área.
        with closing(_conectar()) as conexao:
            linhas = conexao.execute(self._consulta_livros + ' ORDER BY livros.titulo').fetchall()

        palavras = _normalizar(termo).split()
        resultado = []

        for linha in linhas:
            livro = self._montar_livro(linha)
            alvo = _normalizar(f'{livro.titulo} {livro.autores} {livro.area}')

            if area and livro.area != area:
                continue

            if so_disponiveis and not livro.disponiveis:
                continue

            if all(palavra in alvo for palavra in palavras):
                resultado.append(livro)

        return resultado

    def obter_livro(self, id_livro):
        with closing(_conectar()) as conexao:
            linha = conexao.execute(
                self._consulta_livros + ' WHERE livros.id = ?', (id_livro,)
            ).fetchone()

        if linha is None:
            raise ValueError('Livro não encontrado.')

        return self._montar_livro(linha)

    # ========== { Empréstimos do usuário } ========== #

    @staticmethod
    def _regra(perfil):
        tipo = getattr(perfil, 'tipo_usuario', None)

        if tipo not in regras:
            raise PermissionError('Apenas discentes e docentes podem reservar livros.')

        return regras[tipo]

    def _listar(self, perfil, so_ativos):
        self._regra(perfil)

        consulta = '''
            SELECT emprestimos.*, livros.titulo
            FROM emprestimos JOIN livros ON livros.id = emprestimos.livro_id
            WHERE emprestimos.usuario_id = ?
        '''

        if so_ativos:
            consulta += ' AND emprestimos.devolvido_em IS NULL'

        consulta += ' ORDER BY emprestimos.retirado_em DESC, emprestimos.id DESC'

        with closing(_conectar()) as conexao:
            linhas = conexao.execute(consulta, (perfil.id_user,)).fetchall()

        hoje = self.__hoje()
        return [Emprestimo(linha, hoje) for linha in linhas]

    def emprestimos_ativos(self, perfil):
        return self._listar(perfil, so_ativos=True)

    def historico(self, perfil):
        # Todos os livros que o usuário já reservou (devolvidos e em andamento), do mais recente ao mais antigo.
        return self._listar(perfil, so_ativos=False)

    def _obter_emprestimo(self, perfil, id_emprestimo):
        for emprestimo in self.emprestimos_ativos(perfil):
            if emprestimo.id == id_emprestimo:
                return emprestimo

        raise ValueError('Empréstimo em andamento não encontrado.')

    # ========== { Reserva, renovação e devolução } ========== #

    def reservar(self, perfil, id_livro):
        regra = self._regra(perfil)
        livro = self.obter_livro(id_livro)
        ativos = self.emprestimos_ativos(perfil)

        if any(e.atrasado for e in ativos):
            raise ValueError('Você tem livro em atraso. Devolva-o antes de reservar outro.')

        if len(ativos) >= regra['limite']:
            raise ValueError(f"Limite de {regra['limite']} livros emprestados ao mesmo tempo.")

        if any(e.livro_id == id_livro for e in ativos):
            raise ValueError('Você já está com um exemplar deste livro.')

        if not livro.disponiveis:
            raise ValueError('Todos os exemplares deste livro estão emprestados.')

        hoje = self.__hoje()
        devolver_ate = hoje + timedelta(days=regra['prazo_dias'])

        with closing(_conectar()) as conexao, conexao:
            conexao.execute(
                '''
                INSERT INTO emprestimos (livro_id, usuario_id, retirado_em, devolver_ate)
                VALUES (?, ?, ?, ?)
                ''',
                (id_livro, perfil.id_user, hoje.isoformat(), devolver_ate.isoformat())
            )

        return livro, devolver_ate

    def renovar(self, perfil, id_emprestimo):
        regra = self._regra(perfil)
        emprestimo = self._obter_emprestimo(perfil, id_emprestimo)

        if emprestimo.atrasado:
            raise ValueError('Não é possível renovar um livro em atraso. Devolva-o.')

        if emprestimo.renovacoes >= max_renovacoes:
            raise ValueError(f'Limite de {max_renovacoes} renovações atingido. Devolva o livro.')

        # Como na UnB, o novo prazo conta a partir do dia da renovação.
        nova_data = self.__hoje() + timedelta(days=regra['prazo_dias'])

        with closing(_conectar()) as conexao, conexao:
            conexao.execute(
                'UPDATE emprestimos SET devolver_ate = ?, renovacoes = renovacoes + 1 WHERE id = ?',
                (nova_data.isoformat(), id_emprestimo)
            )

        return nova_data

    def devolver(self, perfil, id_emprestimo):
        # Devolve o livro e informa a multa (0 se estiver no prazo).
        emprestimo = self._obter_emprestimo(perfil, id_emprestimo)
        hoje = self.__hoje()

        with closing(_conectar()) as conexao, conexao:
            conexao.execute(
                'UPDATE emprestimos SET devolvido_em = ? WHERE id = ?',
                (hoje.isoformat(), id_emprestimo)
            )

        return max(0, (hoje - emprestimo.devolver_ate).days) * multa_por_dia

    # ========== { Administração } ========== #

    def cadastrar_livro(self, conta, titulo, autores, area, exemplares):
        exigir_admin(conta)

        titulo, autores, area = titulo.strip(), autores.strip(), area.strip()

        if not titulo or not autores or not area:
            raise ValueError('Título, autores e área são obrigatórios.')

        if exemplares < 1:
            raise ValueError('O livro precisa ter ao menos 1 exemplar.')

        try:
            with closing(_conectar()) as conexao, conexao:
                conexao.execute(
                    'INSERT INTO livros (titulo, autores, area, exemplares) VALUES (?, ?, ?, ?)',
                    (titulo, autores, area, exemplares)
                )
        except sqlite3.IntegrityError:
            raise ValueError('Este livro já está cadastrado.')

    def importar_csv(self, conta, caminho):
        # Importa livros de um CSV: tudo ou nada. Devolve (livros novos, livros atualizados).
        exigir_admin(conta)
 
        livros = _ler_csv(caminho)
        novos = 0
 
        with closing(_conectar()) as conexao, conexao:
            for livro in livros:
                existe = conexao.execute(
                    'SELECT 1 FROM livros WHERE titulo = ? AND autores = ?', livro[:2]
                ).fetchone()
 
                novos += existe is None
                conexao.execute(sql_inserir_ou_atualizar, livro)
 
        return novos, len(livros) - novos


    def recarregar_acervo(self, conta):
        # Relê acervo_biblioteca.json (novos livros entram; quantidades são atualizadas).
        exigir_admin(conta)

        with closing(_conectar()) as conexao, conexao:
            return _carregar_json(conexao)


# ============================= { PÁGINA DA BIBLIOTECA } ============================= #

class PaginaBiblioteca(PaginaPerfil):

    exige_login = False         # A busca no acervo também aparece no portal público (sem login)

    def __init__(self, sessao):
        super().__init__(sessao)
        self._biblioteca = Biblioteca()

    @property
    def titulo(self):
        return 'BIBLIOTECA FCTE'

    @property
    def _tem_perfil(self):
        return getattr(self._perfil, 'tipo_usuario', None) in regras

    @property
    def _eh_admin(self):
        return getattr(self._conta, 'eh_admin', False)

    def _opcoes(self):
        opcoes = [
            ('Buscar livro (título, autor ou área)', self._buscar),
            ('Ver acervo por área', self._por_area),
            ('Ver só livros disponíveis', lambda: self._mostrar(self._biblioteca.buscar(so_disponiveis=True))),
        ]

        if self._tem_perfil:
            opcoes += [
                ('Reservar livro', self._reservar),
                ('Meus empréstimos (prazo de devolução)', self._meus),
                ('Renovar empréstimo', self._renovar),
                ('Devolver livro', self._devolver),
                ('Histórico de livros reservados', self._historico),
            ]

        if self._eh_admin:
            opcoes += [
                ('Cadastrar livro', self._cadastrar),
                ('Recarregar acervo do arquivo JSON', self._recarregar),
            ]

        return opcoes

    # ========== { Helpers } ========== #

    @staticmethod
    def _ler_codigo(rotulo):
        valor = input(f'{rotulo} (#): ').strip().lstrip('#')

        if not valor.isdigit():
            raise ValueError('Código inválido.')

        return int(valor)

    @staticmethod
    def _mostrar(livros):
        if not livros:
            print('Nenhum livro encontrado.')
            return

        print(f'\n{len(livros)} livro(s) encontrado(s):\n')

        for livro in livros[:limite_exibicao]:
            print(livro)
            print()

        if len(livros) > limite_exibicao:
            print(f'(Mostrando {limite_exibicao} de {len(livros)}. Refine a busca para ver os demais.)')

    # ========== { Busca } ========== #

    def _buscar(self):
        termo = input('Buscar por: ').strip()

        if not termo:
            raise ValueError('Digite ao menos uma palavra para buscar.')

        so_disponiveis = input('Mostrar só os disponíveis? (s/n): ').strip().lower() == 's'
        self._mostrar(self._biblioteca.buscar(termo, so_disponiveis=so_disponiveis))

    def _por_area(self):
        areas = {area: area for area in self._biblioteca.areas()}
        area = self._escolher('Áreas do acervo:', areas)
        self._mostrar(self._biblioteca.buscar(area=area))

    # ========== { Reserva, prazo, renovação, devolução } ========== #

    def _reservar(self):
        livro = self._biblioteca.obter_livro(self._ler_codigo('Código do livro'))
        print(f'\n{livro}')

        if not self._confirmar('Reservar este livro?'):
            return

        _, devolver_ate = self._biblioteca.reservar(self._perfil, livro.id)
        print(f'Reserva feita! Retire na Biblioteca FCTE e devolva até {formatar_data(devolver_ate)}.')

    def _meus(self):
        emprestimos = self._biblioteca.emprestimos_ativos(self._perfil)

        if not emprestimos:
            print('Você não tem livros emprestados.')
            return

        print(f'\n{len(emprestimos)} livro(s) em seu poder:\n')

        for emprestimo in emprestimos:
            print(emprestimo)
            print()

    def _renovar(self):
        self._meus()
        nova_data = self._biblioteca.renovar(self._perfil, self._ler_codigo('Código do empréstimo'))
        print(f'Renovado! Novo prazo: {formatar_data(nova_data)}.')

    def _devolver(self):
        self._meus()
        multa = self._biblioteca.devolver(self._perfil, self._ler_codigo('Código do empréstimo'))
        print('Livro devolvido.')

        if multa:
            print(f'Multa por atraso: R$ {multa:.2f}')

    def _historico(self):
        historico = self._biblioteca.historico(self._perfil)

        if not historico:
            print('Você ainda não reservou nenhum livro.')
            return

        print(f'\nHISTÓRICO ({len(historico)} reserva(s)):\n')

        for emprestimo in historico:
            print(emprestimo)
            print()

    # ========== { Admin } ========== #

    def _cadastrar(self):
        titulo = input('Título: ')
        autores = input('Autor(es): ')
        area = input('Área: ')

        try:
            exemplares = int(input('Número de exemplares: '))
        except ValueError:
            raise ValueError('Número de exemplares inválido.')

        self._biblioteca.cadastrar_livro(self._conta, titulo, autores, area, exemplares)
        print('Livro cadastrado.')


    def _importar_csv(self):    # [NEW]
        caminho = input('Caminho do arquivo CSV (colunas: titulo;autores;area;exemplares): ')
        novos, atualizados = self._biblioteca.importar_csv(self._conta, caminho)
        print(f'Acervo importado: {novos} livro(s) novo(s), {atualizados} atualizado(s).')


    def _recarregar(self):
        if self._confirmar('Reler o arquivo acervo_biblioteca.json?'):
            total = self._biblioteca.recarregar_acervo(self._conta)
            print(f'Acervo atualizado ({total} livros no arquivo).')