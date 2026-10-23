import json
import unicodedata
from datetime import date
from pathlib import Path

# ----------------------------------------------- #

from .user import semestre_atual

# ============================= { CONFIGURAÇÃO } ============================= #

# Mesmo arquivo que o cardapio.py grava (fica na mesma pasta).
arquivo_cardapio = Path(__file__).resolve().parent / 'cardapio_extraido.json'

refeicoes = {
    'cafe_da_manha': 'Café da manhã',
    'almoco': 'Almoço',
    'jantar': 'Jantar',
}

dietas = {
    'padrao': 'Padrão',
    'ovolactovegetariano': 'Ovolactovegetariano',
    'vegetariano_estrito': 'Vegetariano estrito',
    'todas': 'Todas as opções',
}

dias_semana = (
    'segunda-feira', 'terça-feira', 'quarta-feira',
    'quinta-feira', 'sexta-feira', 'sábado', 'domingo'
)

# Nome amigável de cada categoria do cardápio.
rotulos = {
    'bebidas': 'Bebidas',
    'panificacao': 'Pães',
    'opcao_extra': 'Opção extra',
    'gordura': 'Para o pão',
    'complemento': 'Complemento',
    'fruta': 'Fruta',
    'salada_1': 'Salada 1',
    'salada_2': 'Salada 2',
    'molho_para_salada': 'Molho',
    'prato_principal': 'Prato principal',
    'guarnicao': 'Guarnição',
    'acompanhamentos': 'Acompanhamentos',
    'sopa': 'Sopa',
    'torrada': 'Torrada',
    'sobremesa': 'Sobremesa',
    'bebida': 'Bebida',
}

# Categorias que têm uma versão por tipo de dieta (ex.: prato_principal_padrao).
prefixos_com_dieta = ('complemento_', 'prato_principal_')

limite_turmas = 30

_sistema_cache = None


# ============================= { FUNÇÕES AUXILIARES } ============================= #

def _exigir_admin(conta):
    if conta is None or not getattr(conta, 'eh_admin', False):
        raise PermissionError('Ação permitida apenas para admins.')


def _sem_acento(texto):
    texto = unicodedata.normalize('NFD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto.casefold()


def nome_dia_semana(data_iso):
    return dias_semana[date.fromisoformat(data_iso).weekday()]


def _sistema():
    # Cria o SistemaFCTE só quando precisa (ele abre o banco ao ser criado).
    global _sistema_cache

    if _sistema_cache is None:
        from .system import SistemaFCTE
        _sistema_cache = SistemaFCTE()

    return _sistema_cache


# ============================= { CARDÁPIO DO RU } ============================= #

def carregar_cardapio():
    # Lê o JSON gerado pelo cardapio.py. Lista vazia se ele ainda não existe.
    if not arquivo_cardapio.exists():
        return []

    try:
        with open(arquivo_cardapio, encoding='utf-8') as arquivo:
            registros = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        raise RuntimeError('O arquivo do cardápio está ilegível. Peça ao admin para atualizá-lo.')

    if not isinstance(registros, list):
        raise RuntimeError('O arquivo do cardápio está num formato inesperado.')

    return registros


def datas_disponiveis():
    return sorted({r['data'] for r in carregar_cardapio() if 'data' in r})


def cardapio_do_dia(data_iso):
    # Devolve {refeicao: itens} na ordem café, almoço, jantar. Vazio se não houver o dia.
    por_refeicao = {
        r['refeicao']: r.get('itens', {})
        for r in carregar_cardapio()
        if r.get('data') == data_iso
    }

    return {chave: por_refeicao[chave] for chave in refeicoes if chave in por_refeicao}


def _separar_variante(categoria):
    # 'prato_principal_padrao' -> ('prato_principal', 'padrao'); sem variante -> (categoria, None)
    for prefixo in prefixos_com_dieta:
        if categoria.startswith(prefixo):
            variante = categoria[len(prefixo):]

            if variante in dietas:
                return prefixo.rstrip('_'), variante

    return categoria, None


def formatar_refeicao(itens, dieta='padrao'):
    # Lista de (rótulo, texto) já filtrada pela preferência alimentar escolhida.
    if dieta not in dietas:
        raise ValueError('Preferência alimentar inválida.')

    linhas = []

    for categoria, lista in itens.items():
        base, variante = _separar_variante(categoria)

        if variante and dieta != 'todas' and variante != dieta:
            continue

        rotulo = rotulos.get(base, base.replace('_', ' ').capitalize())

        if variante and dieta == 'todas':
            rotulo += f' ({dietas[variante]})'

        linhas.append((rotulo, '; '.join(lista)))

    return linhas


def ultima_atualizacao_cardapio():
    # Data/hora em que o arquivo foi gravado, ou None.
    if not arquivo_cardapio.exists():
        return None

    from datetime import datetime
    return datetime.fromtimestamp(arquivo_cardapio.stat().st_mtime)


def atualizar_cardapio_ru(conta):
    # Baixa o PDF do RU e regrava o JSON (usa o cardapio.py). Só admin.
    _exigir_admin(conta)

    try:
        from . import cardapio
    except ImportError:
        raise RuntimeError(
            'Falta a biblioteca pdfplumber. Instale com: pip install pdfplumber'
        )

    try:
        registros = cardapio.atualizar_cardapio()
    except (OSError, ValueError, RuntimeError) as erro:
        raise RuntimeError(f'Não foi possível atualizar o cardápio: {erro}')

    return len(registros)


# ============================= { TURMAS DO SIGAA } ============================= #

def listar_turmas(ano=None, semestre=None, filtro=None):
    # Turmas já guardadas no banco, filtradas por texto (disciplina, código ou docente).
    if ano is None or semestre is None:
        ano, semestre = semestre_atual()

    turmas = _sistema().listar_turmas_sigaa(ano, semestre)

    if filtro and filtro.strip():
        termo = _sem_acento(filtro.strip())

        turmas = [
            t for t in turmas
            if termo in _sem_acento(
                f"{t.get('codigo_disciplina', '')} {t.get('nome_disciplina', '')} "
                f"{t.get('docente', '')}"
            )
        ]

    return sorted(
        turmas,
        key=lambda t: (t.get('codigo_disciplina', ''), t.get('numero_turma', ''))
    )


def formatar_turma(turma):
    carga = f" ({turma['carga_horaria']}h)" if turma.get('carga_horaria') else ''

    return (
        f"{turma.get('codigo_disciplina')} - {turma.get('nome_disciplina')} "
        f"| Turma {turma.get('numero_turma')} | {turma.get('periodo')}\n"
        f"    Docente: {turma.get('docente')}{carga}\n"
        f"    Horário: {turma.get('horario')} | Local: {turma.get('local')}\n"
        f"    Vagas ocupadas: {turma.get('vagas_ocupadas')} de {turma.get('vagas_ofertadas')}"
    )


def atualizar_turmas_sigaa(conta, ano=None, semestre=None):
    # Consulta o SIGAA público e grava no banco. Só admin.
    _exigir_admin(conta)

    try:
        return _sistema().atualizar_turmas_sigaa(ano, semestre)
    except (OSError, ValueError, RuntimeError) as erro:
        raise RuntimeError(f'Não foi possível atualizar as turmas: {erro}')