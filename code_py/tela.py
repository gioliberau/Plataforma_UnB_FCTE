import os
import sys
import textwrap
from datetime import datetime

# ============================= { CONFIGURAÇÃO } ============================= #

largura = 62

dias_semana = (
    'segunda-feira', 'terça-feira', 'quarta-feira',
    'quinta-feira', 'sexta-feira', 'sábado', 'domingo'
)


# ============================= { CONTROLE DA TELA } ============================= #

def interativo():
    # Só é "modo terminal" quando entrada e saída são um terminal de verdade.
    # Em testes ou com redirecionamento (|, >) a tela não é limpa e não há pausas.
    return sys.stdin.isatty() and sys.stdout.isatty()


def limpar_tela():
    if not interativo():
        return

    if os.name == 'nt':
        os.system('cls')
    else:
        print('\033[H\033[2J\033[3J', end='', flush=True)   # cursor no topo + apaga tela e rolagem


def pausar():
    if interativo():
        input('\nPressione Enter para continuar...')


# ============================= { DESENHO DA PÁGINA } ============================= #

def linha(caractere='═'):
    return caractere * largura


def titulo_pagina(titulo):
    print(linha('═'))
    print(titulo.center(largura).rstrip())
    print(linha('═'))


def titulo_acao(menu, rotulo):
    # Trilha da ação escolhida: "PORTAL PÚBLICO › Consultar cursos".
    print(f'{menu}  ›  {rotulo}')
    print(linha('─'))


def campo(rotulo, valor, recuo=4):
    # "Rótulo: valor" com quebra de linha alinhada sob o valor.
    prefixo = ' ' * recuo + f'{rotulo}: '

    return textwrap.fill(
        str(valor), width=largura,
        initial_indent=prefixo, subsequent_indent=' ' * len(prefixo),
        break_long_words=False, break_on_hyphens=False
    )


# ============================= { DATA E HORA } ============================= #

def formatar_data_hora(momento):
    # Ex.: domingo, 08/11/2026 às 14:32 (sem depender do idioma do sistema).
    return f'{dias_semana[momento.weekday()]}, {momento:%d/%m/%Y} às {momento:%H:%M}'


def formatar_duracao(inicio, fim=None):
    segundos = int(((fim or datetime.now()) - inicio).total_seconds())
    horas, resto = divmod(max(segundos, 0), 3600)
    minutos = resto // 60

    if horas:
        return f'{horas}h{minutos:02d}min'

    return f'{minutos} min' if minutos else 'menos de 1 min'
