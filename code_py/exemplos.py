import json
from contextlib import closing

from . import banco, login
from .user import semestre_atual

# ============================= { USUÁRIOS DE EXEMPLO } ============================= #
# Dados sintéticos para testar o sistema no terminal (python -m code_py.exemplos).
# As senhas são públicas de propósito: não use estes usuários fora dos testes.

admin_exemplo = ('admin@exemplo.unb.br', 'admin12345')

usuarios_exemplo = (
    # (e-mail, senha, tipo, nome, CPF sintético válido, ano, semestre, curso/área)
    ('aluno@exemplo.unb.br', 'aluno12345', 'discente', 'Ana Exemplo',
     '52998224725', 2024, 1, 'Engenharia de Software'),
    ('professor@exemplo.unb.br', 'professor12345', 'docente', 'Paulo Exemplo',
     '11144477735', 2015, 2, 'Engenharia de Software'),
)

# ============================= { TURMAS DE EXEMPLO } ============================= #
# Períodos passados têm notas; o semestre atual (calculado na hora) fica sem nota,
# para que "Listar todas as turmas do semestre atual" nunca venha vazio.

def _periodo_atual():
    ano, semestre = semestre_atual()
    return f'{ano}.{semestre}'


def _turmas_exemplo():
    atual = _periodo_atual()

    # (código, nome, turma, período, docente, carga, horário, local, vagas, ocupadas)
    linhas = (
        ('FGA0158', 'Introdução à Engenharia de Software', '01', '2024.1',
         'Paulo Exemplo', 60, '35T23', 'FGA - S4', 50, 48),
        ('FGA0160', 'Algoritmos e Programação', '01', '2024.2',
         'Paulo Exemplo', 90, '24M12', 'FGA - I3', 40, 40),
        ('FGA0170', 'Programação Orientada a Objetos', '01', '2025.1',
         'Paulo Exemplo', 60, '2T12', 'FGA - I1', 45, 41),
        ('FGA0138', 'Estruturas de Dados', '01', '2025.2',
         'Paulo Exemplo', 60, '46T12', 'FGA - I2', 40, 37),
        # Semestre atual.
        ('FGA0161', 'Banco de Dados', '01', atual,
         'Paulo Exemplo', 60, '35T23', 'FGA - S1', 40, 33),
        ('FGA0172', 'Engenharia de Requisitos', '01', atual,
         'Paulo Exemplo', 60, '24M34', 'FGA - S3', 45, 30),
    )

    return tuple(
        {
            'codigo_disciplina': codigo,
            'nome_disciplina': nome,
            'numero_turma': numero,
            'periodo': periodo,
            'docente': docente,
            'carga_horaria': carga,
            'horario': horario,
            'local': local,
            'vagas_ofertadas': str(vagas),
            'vagas_ocupadas': str(ocupadas),
            'fonte': 'exemplo',
        }
        for (codigo, nome, numero, periodo, docente,
             carga, horario, local, vagas, ocupadas) in linhas
    )


def _matriculas_exemplo(turmas):
    # (índice da turma em _turmas_exemplo, nota) da Ana.
    # Histórico com SS, MS, MM e MI; as turmas do semestre atual ficam sem nota.
    return (
        (0, 9.5),
        (1, 7.5),
        (2, 5.5),
        (3, 3.5),
        (4, None),
        (5, None),
    )


def _chave(turma):
    return f"{turma['periodo']}|{turma['codigo_disciplina']}|{turma['numero_turma']}"


def _criar_historico_academico(aluno, professor):
    """Cria turmas, ofertas e matrículas sem duplicar os registros."""
    turmas = _turmas_exemplo()

    with closing(banco.conectar()) as conexao, conexao:
        for turma in turmas:
            chave = _chave(turma)

            conexao.execute(
                '''
                INSERT OR IGNORE INTO dados_publicos (categoria, chave, valor, fonte)
                VALUES ('turma_sigaa', ?, ?, 'exemplo')
                ''',
                (chave, json.dumps(turma, ensure_ascii=False)),
            )

            conexao.execute(
                'INSERT OR IGNORE INTO ofertas (turma, docente_id) VALUES (?, ?)',
                (chave, professor.id_user),
            )

        for indice, nota in _matriculas_exemplo(turmas):
            conexao.execute(
                '''
                INSERT OR IGNORE INTO matriculas (discente_id, turma, nota)
                VALUES (?, ?, ?)
                ''',
                (aluno.id_user, _chave(turmas[indice]), nota),
            )

# ============================= { CRIAÇÃO } ============================= #

def criar_exemplos():
    # Pode rodar mais de uma vez: o que já existe é mantido.
    admin = login.autenticar(*admin_exemplo)

    if admin is None:
        try:
            admin = login.criar_admin_inicial(*admin_exemplo)
        except PermissionError:
            raise PermissionError(
                'Já existe outro admin; crie os usuários pelo menu com ele.'
            )

    perfis = {}

    for email, senha, tipo, nome, cpf, ano, semestre, curso in usuarios_exemplo:
        conta = login.autenticar(email, senha)

        if conta is None:
            senha_inicial = login.gerar_acesso(admin, email, tipo)
            conta = login.trocar_senha(email, senha_inicial, senha)

        perfil = banco.buscar_perfil(email)

        if perfil is None:
            perfil = banco.cadastrar_perfil(
                conta, nome, cpf, ano, semestre, curso
            )

        perfis[tipo] = perfil

    _criar_historico_academico(perfis['discente'], perfis['docente'])


def main():
    try:
        criar_exemplos()
    except (ValueError, PermissionError) as erro:
        print(f'Não foi possível criar os exemplos: {erro}')
        return

    print('Usuários de exemplo prontos:')
    print(f'  admin     {admin_exemplo[0]} / {admin_exemplo[1]}')

    for email, senha, tipo, *_ in usuarios_exemplo:
        perfil = banco.buscar_perfil(email)
        print(f'  {tipo:<9} {email} / {senha} (matrícula {perfil.id_user})')


if __name__ == '__main__':
    main()
