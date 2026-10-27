import json
import sqlite3                  # Erro de matrícula repetida (IntegrityError).
from contextlib import closing  # Fechamento da conexão após o uso.

# ----------------------------------------------- #

from .banco import conectar
from .login import exigir_admin
from .user import semestre_atual

# ============================= { CONFIGURAÇÃO } ============================= #

# Menções da UnB: (nota mínima, menção, peso usado no MP e no IRA).
mencoes = (
    (9, 'SS', 5),
    (7, 'MS', 4),
    (5, 'MM', 3),
    (3, 'MI', 2),
    (0.1, 'II', 1),
    (0, 'SR', 0),
)

mencoes_aprovadas = ('SS', 'MS', 'MM')

horas_por_credito = 15

# ============================= { MENÇÃO } ============================= #

def mencao(nota):
    # Converte a nota (0 a 10) na menção da UnB.
    for minimo, sigla, _ in mencoes:
        if nota >= minimo:
            return sigla


def _peso(nota):
    return next(peso for minimo, _, peso in mencoes if nota >= minimo)


# ============================= { CLASSE MATRICULA } ============================= #

class Matricula:
    # Uma turma cursada por um discente, com a nota (None enquanto não for lançada).

    def __init__(self, turma, nota=None):
        self.__turma = turma
        self.__nota = nota

    # ========== { Getters } ========== #

    @property
    def turma(self):
        return self.__turma

    @property
    def nota(self):
        return self.__nota

    @property
    def creditos(self):
        # shortcut: turma sem carga horária no SIGAA conta 0 créditos; revisar se aparecerem muitas.
        return (self.__turma.get('carga_horaria') or 0) // horas_por_credito

    @property
    def mencao(self):
        return None if self.__nota is None else mencao(self.__nota)

    @property
    def aprovado(self):
        return self.mencao in mencoes_aprovadas

    def __str__(self):
        resultado = 'sem nota' if self.__nota is None else f'{self.__nota:.1f} ({self.mencao})'

        return (
            f"{self.__turma['codigo_disciplina']} - {self.__turma['nome_disciplina']} "
            f"| Turma {self.__turma['numero_turma']} | {self.__turma['periodo']} "
            f"| {self.creditos} créditos | {resultado}"
        )


# ============================= { FUNÇÕES AUXILIARES } ============================= #

def chave_turma(turma):
    # Mesma chave usada pelo SistemaFCTE ao gravar as turmas do SIGAA.
    return f"{turma['periodo']}|{turma['codigo_disciplina']}|{turma['numero_turma']}"


def buscar_turma(chave):
    # Devolve o dicionário da turma gravada do SIGAA, ou None.
    with closing(conectar()) as conexao:
        dados = conexao.execute(
            '''
            SELECT valor
            FROM dados_publicos
            WHERE categoria = 'turma_sigaa' AND chave = ?
            ''',
            (chave,)
        ).fetchone()

    return json.loads(dados['valor']) if dados else None


def _exigir_turma(chave):
    turma = buscar_turma(chave)

    if turma is None:
        raise ValueError('Turma não encontrada. Atualize as turmas do SIGAA primeiro.')

    return turma


def _exigir_usuario(id_user, tipo):
    # Garante que a matrícula pertence a um perfil do tipo pedido.
    with closing(conectar()) as conexao:
        dados = conexao.execute(
            'SELECT tipo_usuario FROM usuarios WHERE id_user = ?',
            (id_user,)
        ).fetchone()

    if dados is None or dados['tipo_usuario'] != tipo:
        raise ValueError(f'Nenhum {tipo} com a matrícula {id_user}.')


def _exigir_tipo(perfil, tipo):
    if perfil is None or perfil.tipo_usuario != tipo:
        raise PermissionError(f'Ação permitida apenas para {tipo}s.')


def _exigir_docente_da_turma(docente, chave):
    _exigir_tipo(docente, 'docente')

    with closing(conectar()) as conexao:
        dono = conexao.execute(
            'SELECT 1 FROM ofertas WHERE turma = ? AND docente_id = ?',
            (chave, docente.id_user)
        ).fetchone()

    if dono is None:
        raise PermissionError('Esta turma não está entre as suas.')


# ============================= { ADMIN: MATRÍCULA E OFERTA } ============================= #

def matricular(admin, matricula_aluno, chave):
    exigir_admin(admin)
    _exigir_usuario(matricula_aluno, 'discente')
    _exigir_turma(chave)

    try:
        with closing(conectar()) as conexao, conexao:
            conexao.execute(
                'INSERT INTO matriculas (discente_id, turma) VALUES (?, ?)',
                (matricula_aluno, chave)
            )

    except sqlite3.IntegrityError:
        raise ValueError('O discente já está matriculado nesta turma.')


def atribuir_docente(admin, id_docente, chave):
    # Liga a turma ao docente que a oferta (substitui o anterior, se houver).
    exigir_admin(admin)
    _exigir_usuario(id_docente, 'docente')
    _exigir_turma(chave)

    with closing(conectar()) as conexao, conexao:
        conexao.execute(
            '''
            INSERT INTO ofertas (turma, docente_id) VALUES (?, ?)
            ON CONFLICT(turma) DO UPDATE SET docente_id = excluded.docente_id
            ''',
            (chave, id_docente)
        )


# ============================= { CONSULTAS } ============================= #

def turmas_do_discente(perfil):
    # Lista de Matricula, da mais antiga para a mais recente.
    _exigir_tipo(perfil, 'discente')

    with closing(conectar()) as conexao:
        linhas = conexao.execute(
            'SELECT turma, nota FROM matriculas WHERE discente_id = ? ORDER BY turma',
            (perfil.id_user,)
        ).fetchall()

    matriculas = [Matricula(buscar_turma(linha['turma']), linha['nota']) for linha in linhas]

    # Uma turma pode sumir se o admin regravar o SIGAA de outro jeito; não deixa a lista quebrar.
    return [m for m in matriculas if m.turma is not None]


def turmas_do_docente(perfil):
    # Turmas (dicionários do SIGAA) ligadas ao docente.
    _exigir_tipo(perfil, 'docente')

    with closing(conectar()) as conexao:
        linhas = conexao.execute(
            'SELECT turma FROM ofertas WHERE docente_id = ? ORDER BY turma',
            (perfil.id_user,)
        ).fetchall()

    turmas = [buscar_turma(linha['turma']) for linha in linhas]

    return [t for t in turmas if t is not None]


def alunos_da_turma(docente, chave):
    # Lista de dicionários (matricula, nome, nota) da turma do docente.
    _exigir_docente_da_turma(docente, chave)

    with closing(conectar()) as conexao:
        linhas = conexao.execute(
            '''
            SELECT usuarios.id_user AS matricula, usuarios.nome, matriculas.nota
            FROM matriculas
            JOIN usuarios ON usuarios.id_user = matriculas.discente_id
            WHERE matriculas.turma = ?
            ORDER BY usuarios.nome
            ''',
            (chave,)
        ).fetchall()

    return [dict(linha) for linha in linhas]


# ============================= { DOCENTE: NOTAS } ============================= #

def lancar_nota(docente, chave, matricula_aluno, nota):
    _exigir_docente_da_turma(docente, chave)

    if isinstance(nota, bool) or not isinstance(nota, (int, float)) or not 0 <= nota <= 10:
        raise ValueError('A nota deve ser um número de 0 a 10.')

    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute(
            'UPDATE matriculas SET nota = ? WHERE turma = ? AND discente_id = ?',
            (float(nota), chave, matricula_aluno)
        )

    if cursor.rowcount == 0:
        raise ValueError('Este discente não está matriculado nesta turma.')


# ============================= { DADOS DO USUÁRIO } ============================= #

def mp(perfil):
    # Média ponderada (0 a 5): peso da menção × créditos, só turmas com nota.
    cursadas = [m for m in turmas_do_discente(perfil) if m.nota is not None and m.creditos]
    total = sum(m.creditos for m in cursadas)

    if not total:
        return None

    return sum(_peso(m.nota) * m.creditos for m in cursadas) / total


def _semestre_cursado(perfil, periodo):
    # Em qual semestre do curso o aluno estava (1, 2, ...), limitado a 6 como na UnB.
    ano, semestre = map(int, periodo.split('.'))
    numero = (ano - perfil.ano_entrada) * 2 + (semestre - perfil.semestre_entrada) + 1

    return min(max(numero, 1), 6)


def ira(perfil):
    # Fórmula da UnB: Σ(peso × créditos × semestre) / Σ(créditos × semestre).
    # shortcut: sem o fator de trancamentos (o sistema não tem trancamento); incluir se ele for criado.
    cursadas = [m for m in turmas_do_discente(perfil) if m.nota is not None and m.creditos]

    fatores = [(m, m.creditos * _semestre_cursado(perfil, m.turma['periodo'])) for m in cursadas]
    total = sum(fator for _, fator in fatores)

    if not total:
        return None

    return sum(_peso(m.nota) * fator for m, fator in fatores) / total


def creditos_ofertados(perfil, ano=None, semestre=None):
    # Soma dos créditos das turmas do docente no semestre (atual, se não informado).
    if ano is None or semestre is None:
        ano, semestre = semestre_atual()

    return sum(
        (t.get('carga_horaria') or 0) // horas_por_credito
        for t in turmas_do_docente(perfil)
        if t['periodo'] == f'{ano}.{semestre}'
    )
