from urllib.request import Request, build_opener, HTTPCookieProcessor
from http.cookiejar import CookieJar
from urllib.parse import urlencode, urljoin
from html.parser import HTMLParser
import json
import re


base = 'https://sigaa.unb.br'
url_home = base + '/sigaa/public/home.jsf'
url_turmas = base + '/sigaa/public/turmas/listar.jsf?aba=p-ensino'
url_fontw = base + '/sigaa/public/turmas/listar.jsf'


class AnalisadorViewState(HTMLParser):
    def __init__(self):
        super().__init__()
        self.view_state = None

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)

        if (
            tag == 'input'
            and atributos.get('name') == 'javax.faces.ViewState'
        ):
            self.view_state = atributos.get('value')


class AnalisadorTabelas(HTMLParser):
    def __init__(self):
        super().__init__()
        self.profundidade = 0
        self.em_linha = False
        self.em_celula = False
        self.linha = []
        self.texto_celula = []
        self.linhas = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.profundidade += 1

        elif tag == 'tr' and self.profundidade > 0:
            self.em_linha = True
            self.linha = []

        elif (
            tag in ('td', 'th')
            and self.em_linha
            and self.profundidade > 0
        ):
            self.em_celula = True
            self.texto_celula = []

    def handle_data(self, data):
        if self.em_celula:
            self.texto_celula.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.em_celula:
            texto = ' '.join(self.texto_celula)
            texto = re.sub(r'\s+', ' ', texto).strip()
            self.linha.append(texto)
            self.em_celula = False

        elif tag == 'tr' and self.em_linha:
            if any(c.strip() for c in self.linha):
                self.linhas.append(self.linha)
            self.em_linha = False

        elif tag == 'table' and self.profundidade > 0:
            self.profundidade -= 1


def _requisitar(navegador, url, dados=None, referer=None):
    cabecalhos = {'User-Agent': 'Mozilla/5.0'}

    if referer:
        cabecalhos['Referer'] = referer

    if dados is None:
        requisicao = Request(url, headers=cabecalhos)
    else:
        cabecalhos['Content-Type'] = (
            'application/x-www-form-urlencoded'
        )
        requisicao = Request(
            url,
            data=urlencode(dados).encode('utf-8'),
            headers=cabecalhos,
            method='POST'
        )

    with navegador.open(requisicao, timeout=30) as resposta:
        html = resposta.read().decode('utf-8', errors='replace')
        return html, resposta.geturl()


def buscar_turmas_publicas(ano=2026, semestre=2, departamento='673'):
    if type(ano) is not int or ano < 2000:
        raise ValueError('Informe um ano válido.')

    if semestre not in (1, 2):
        raise ValueError('O semestre deve ser 1 ou 2.')

    navegador = build_opener(HTTPCookieProcessor(CookieJar()))

    # Abre a página inicial e a página de consulta mantendo os cookies.
    _requisitar(navegador, url_home)
    html, url_pagina = _requisitar(
        navegador,
        url_turmas,
        referer=url_home
    )

    analisador = AnalisadorViewState()
    analisador.feed(html)

    if not analisador.view_state:
        raise RuntimeError(
            'O SIGAA não forneceu o ViewState. '
            'A estrutura da página pode ter mudado.'
        )

    dados = {
        'formTurma': 'formTurma',
        'formTurma:inputNivel': 'G',
        'formTurma:inputDepto': str(departamento),
        'formTurma:inputAno': str(ano),
        'formTurma:inputPeriodo': str(semestre),
        'formTurma:j_id_jsp_1370969402_11': 'Buscar',
        'javax.faces.ViewState': analisador.view_state
    }

    url_post = urljoin(url_pagina, '/sigaa/public/turmas/listar.jsf')
    resultado, _ = _requisitar(
        navegador,
        url_post,
        dados=dados,
        referer=url_pagina
    )

    tabelas = AnalisadorTabelas()
    tabelas.feed(resultado)

    turmas = []
    disciplina_atual = None

    for linha in tabelas.linhas:
        texto = ' '.join(linha).strip()

        correspondencia = re.match(
            r'^(FGA\d{4})\s*-\s*(.+)$',
            texto
        )

        if correspondencia:
            disciplina_atual = {
                'codigo_disciplina': correspondencia.group(1),
                'nome_disciplina': correspondencia.group(2).strip()
            }
            continue

        # A linha de turma tem, no mínimo:
        # turma, período, docente, horário, campo auxiliar,
        # vagas ofertadas, vagas ocupadas e local.
        if not disciplina_atual or len(linha) < 8:
            continue

        numero_turma = linha[0].strip()
        periodo = linha[1].strip()

        if not re.fullmatch(r'\d{2}', numero_turma):
            continue

        if not re.fullmatch(r'\d{4}\.[12]', periodo):
            continue

        docente_bruto = linha[2].strip()
        carga = re.search(r'\((\d+)h\)', docente_bruto)
        docente = re.sub(r'\s*\(\d+h\)\s*$', '', docente_bruto)

        turma = {
            **disciplina_atual,
            'numero_turma': numero_turma,
            'periodo': periodo,
            'docente': docente,
            'carga_horaria': int(carga.group(1)) if carga else None,
            'horario': linha[3].strip(),
            'vagas_ofertadas': linha[5].strip(),
            'vagas_ocupadas': linha[6].strip(),
            'local': linha[7].strip(),
            'fonte': url_fontw
        }

        turmas.append(turma)

    if not turmas:
        raise RuntimeError(
            'A consulta não retornou turmas reconhecíveis. '
            'Nenhum dado foi gravado no banco.'
        )

    return turmas
