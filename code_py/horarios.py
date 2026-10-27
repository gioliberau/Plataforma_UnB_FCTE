import re

# ============================= { CONFIGURAÇÃO } ============================= #

# Grade de horários da UnB: (início, fim) de cada horário de cada turno.
grade = {
    'M': (('08:00', '08:55'), ('08:55', '09:50'), ('10:00', '10:55'),
          ('10:55', '11:50'), ('12:00', '12:55')),
    'T': (('12:55', '13:50'), ('14:00', '14:55'), ('14:55', '15:50'),
          ('16:00', '16:55'), ('16:55', '17:50'), ('18:00', '18:55')),
    'N': (('19:00', '19:50'), ('19:50', '20:40'), ('20:50', '21:40'),
          ('21:40', '22:30')),
}

# Numeração do SIGAA: 1 = domingo, 2 = segunda ... 7 = sábado.
dias = {
    1: 'domingo', 2: 'segunda-feira', 3: 'terça-feira', 4: 'quarta-feira',
    5: 'quinta-feira', 6: 'sexta-feira', 7: 'sábado',
}

# Um bloco é: dias + turno + horários. Ex.: '35T23' = ter e qui, tarde, 2º e 3º horários.
padrao_bloco = re.compile(r'([1-7]+)([MTN])([1-7]+)')

# ============================= { TRADUÇÃO } ============================= #

def traduzir(codigo):
    # '35T23 6M12' -> [(3, '14:00', '15:50'), (5, '14:00', '15:50'), (6, '08:00', '09:50')]
    # Horários seguidos viram um só intervalo; a lista sai ordenada por dia e início.

    if not isinstance(codigo, str) or not codigo.strip():
        raise ValueError('Código de horário vazio.')

    blocos = padrao_bloco.findall(codigo)

    # Tudo que sobra fora dos blocos tem que ser espaço (senão o código está errado).
    if not blocos or padrao_bloco.sub('', codigo).strip():
        raise ValueError(f'Código de horário inválido: {codigo!r}.')

    intervalos = []

    for dias_bloco, turno, horarios in blocos:
        numeros = sorted({int(h) for h in horarios})

        if numeros[-1] > len(grade[turno]):
            raise ValueError(f'O turno {turno} não tem o horário {numeros[-1]}.')

        # Junta horários seguidos (2, 3) num só intervalo; (1, 3) viram dois.
        trechos = [[numeros[0], numeros[0]]]

        for numero in numeros[1:]:
            if numero == trechos[-1][1] + 1:
                trechos[-1][1] = numero
            else:
                trechos.append([numero, numero])

        for dia in sorted({int(d) for d in dias_bloco}):
            for primeiro, ultimo in trechos:
                intervalos.append((
                    dia,
                    grade[turno][primeiro - 1][0],
                    grade[turno][ultimo - 1][1],
                ))

    return sorted(intervalos)


def descrever(codigo):
    # Texto legível: 'segunda-feira 14:00-15:50; quarta-feira 14:00-15:50'
    return '; '.join(f'{dias[dia]} {inicio}-{fim}' for dia, inicio, fim in traduzir(codigo))
