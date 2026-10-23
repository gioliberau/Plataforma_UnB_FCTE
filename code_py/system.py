from contextlib import closing
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from urllib.parse import urlencode, urljoin
from urllib.request import Request, build_opener, HTTPCookieProcessor
import json
import re
import unicodedata
 
# ----------------------------------------------- #
 
 
from .banco import conectar
from .login import exigir_admin
from .usuarios import semestre_atual, cursos_disponiveis

# ============================= { SIGAA: LEITURA DA PÁGINA PÚBLICA } ============================= #

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
 
 
def buscar_turmas_publicas(ano, semestre, departamento='673'):
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

# ============================= { SISTEMA FCTE } ============================= #

def _sem_acento(texto):
    texto = unicodedata.normalize('NFD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto.casefold()


class SistemaFCTE:

    # Fontes oficiais para consulta de informações públicas.
    url_cursos = 'https://fcte.unb.br/'
    url_calendario = 'https://saa.unb.br/calendario-academico-graduacao/'
    url_sigaa = 'https://sigaa.unb.br/sigaa/public/home.jsf'
    url_turmas = 'https://sigaa.unb.br/sigaa/public/turmas/listar.jsf'
    url_docentes = 'https://sigaa.unb.br/sigaa/public/docente/busca_docentes.jsf'
    url_ru_cardapio = 'https://ru.unb.br/cardapio-refeitorio/'
    url_ru_valores = 'https://ru.unb.br/precos-e-grupos/'
    url_biblioteca = 'https://fcte.unb.br/contato/'
    url_catalogo_biblioteca = 'https://bce.unb.br/'

    limite_turmas = 30 

    # ========== { Turmas do SIGAA } ========== #

    def atualizar_turmas_sigaa(self, ano=None, semestre=None):
        
        exigir_admin(conta)
 
        if ano is None or semestre is None:
            ano, semestre = semestre_atual()
 
        try:
            turmas = buscar_turmas_publicas(ano, semestre)
        except (OSError, ValueError, RuntimeError) as erro:
            raise RuntimeError(f'Não foi possível atualizar as turmas: {erro}')

        with closing(conectar()) as conexao:
            with conexao:
                for turma in turmas:
                    chave = (
                        f"{turma['periodo']}|"
                        f"{turma['codigo_disciplina']}|"
                        f"{turma['numero_turma']}"
                    )

                    conexao.execute('''
                        INSERT INTO dados_publicos
                            (categoria, chave, valor, fonte)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(categoria, chave)
                        DO UPDATE SET
                            valor = excluded.valor,
                            fonte = excluded.fonte
                    ''', (
                        'turma_sigaa',
                        chave,
                        json.dumps(turma, ensure_ascii=False),
                        turma['fonte']
                    ))

        return len(turmas)

    def listar_turmas(self, ano=None, semestre=None):
        
        if ano is None or semestre is None:
            ano, semestre = semestre_atual()

        with closing(conectar()) as conexao:
            registros = conexao.execute('''
                SELECT valor
                FROM dados_publicos
                WHERE categoria = ?
                ORDER BY chave
            ''', ('turma_sigaa',)).fetchall()

        turmas = [json.loads(registro['valor']) for registro in registros]

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

    @staticmethod
    def formatar_turma(turma):

        carga = f" ({turma['carga_horaria']}h)" if turma.get('carga_horaria') else ''
 
        return (
            f"{turma.get('codigo_disciplina')} - {turma.get('nome_disciplina')} "
            f"| Turma {turma.get('numero_turma')} | {turma.get('periodo')}\n"
            f"    Docente: {turma.get('docente')}{carga}\n"
            f"    Horário: {turma.get('horario')} | Local: {turma.get('local')}\n"
            f"    Vagas ocupadas: {turma.get('vagas_ocupadas')} de {turma.get('vagas_ofertadas')}"
        )


    # ========== { Informações públicas } ========== #

    def listar_cursos(self):

        # Consulta os cursos armazenados no banco.
        with closing(conectar()) as conexao:
            cursos = conexao.execute('''
                SELECT valor, fonte
                FROM dados_publicos
                WHERE categoria = ?
                ORDER BY valor
            ''', ('curso',)).fetchall()

        return cursos


    def consultar_fontes_publicas(self):

        # Reúne os endereços oficiais para consulta pública.
        return {
            'cursos': self.url_cursos,
            'calendario': self.url_calendario,
            'sigaa': self.url_sigaa,
            'turmas': self.url_turmas,
            'docentes': self.url_docentes,
            'ru_cardapio': self.url_ru_cardapio,
            'ru_valores': self.url_ru_valores,
            'biblioteca_fcte': self.url_biblioteca,
            'catalogo_biblioteca': self.url_catalogo_biblioteca
        }


    def consultar_biblioteca(self):

        # Retorna informações públicas divulgadas pela FCTE.
        return {
            'nome': 'Biblioteca da FCTE',
            'local': 'Prédio UAC, Campus UnB Gama',
            'horario': 'Segunda a sexta-feira, das 7h às 19h',
            'email': 'biblioteca.fcte@unb.br',
            'telefone': '(61) 3107-8942',
            'fonte': 'https://fcte.unb.br/contato/'
        }
