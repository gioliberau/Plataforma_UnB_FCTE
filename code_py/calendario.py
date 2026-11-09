import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pdfplumber

pag_calendario = "https://saa.unb.br/calendario-academico-graduacao/"
arquivo_calendario = Path(__file__).resolve().parent.parent / 'data' / 'calendario_academico.json'


def baixar_conteudo(url):
    requisicao = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(requisicao, timeout=30) as resposta:
        return resposta.read()


def extrair_texto_pdf(conteudo_pdf):
    import io
    texto = ""
    with pdfplumber.open(io.BytesIO(conteudo_pdf)) as pdf:
        for pagina in pdf.pages:
            texto += (pagina.extract_text() or "") + "\n"
    return texto


def encontrar_pdfs_matricula(html):
    from html.parser import HTMLParser

    class ParserLinks(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
            self.link_atual = None

        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                href = dict(attrs).get('href')
                if href and '.pdf' in href.lower():
                    self.link_atual = {'url': href, 'texto': []}

        def handle_data(self, data):
            if self.link_atual:
                self.link_atual['texto'].append(data)

        def handle_endtag(self, tag):
            if tag == 'a' and self.link_atual:
                texto = ' '.join(self.link_atual['texto']).strip()
                self.links.append((self.link_atual['url'], texto))
                self.link_atual = None

    parser = ParserLinks()
    parser.feed(html if isinstance(html, str) else html.decode('utf-8', errors='replace'))

    candidatos = {}
    for url, texto in parser.links:
        match_periodo = re.search(r'20\d{2}\.[12]', texto)
        if match_periodo and 'Matrícula' in texto:
            periodo = match_periodo.group(0)
            url_completa = urljoin(pag_calendario, url)
            
            # Tentar extrair data no formato (DD/MM/AAAA) para pegar a versão mais recente
            match_data = re.search(r'(\d{2})/(\d{2})/(\d{4})', texto)
            dt = datetime.min
            if match_data:
                d, m, a = map(int, match_data.groups())
                try:
                    dt = datetime(a, m, d)
                except ValueError:
                    pass

            if periodo not in candidatos or dt > candidatos[periodo][0]:
                candidatos[periodo] = (dt, url_completa)

    return {p: url for p, (_, url) in candidatos.items()}


def ler_eventos(texto_pdf):
    match_periodo = re.search(r'CALENDÁRIO DE MATRÍCULA EM DISCIPLINA\s+(20\d{2}\.[12])', texto_pdf)
    if not match_periodo:
        match_periodo = re.search(r'(20\d{2}\.[12])', texto_pdf)
    if not match_periodo or "Início:" not in texto_pdf:
        return None, []

    periodo = match_periodo.group(1)
    eventos = []

    def formatar_data(d_str):
        if not d_str:
            return None
        partes = d_str.strip().split('/')
        if len(partes) == 3:
            return f"{partes[2]}-{partes[1]}-{partes[0]}"
        return None

    # Mapeamento de regras de Regex para descrições estandardizadas
    regras = [
        (r'solicitação de matrícula.*?(\d{2}/\d{2})\s+até.*?(\d{2}/\d{2}/\d{4})', 'Solicitação de matrícula (SIGAA)'),
        (r'Resultado da matrícula até.*?(\d{2}/\d{2}/\d{4})', 'Resultado da matrícula (até 12h)'),
        (r'solicitação de rematrícula.*?(\d{2}/\d{2}).*?até.*?(\d{2}/\d{2}/\d{4})', 'Rematrícula (SIGAA)'),
        (r'Resultado da rematrícula até.*?(\d{2}/\d{2}/\d{4})', 'Resultado da rematrícula (até 12h)'),
        (r'Matrícula Extraordinária.*?(\d{2}/\d{2})\s+até.*?(\d{2}/\d{2}/\d{4})', 'Matrícula extraordinária'),
        (r'Início:\s*(\d{2}/\d{2}/\d{4}).*?Término:\s*(\d{2}/\d{2}/\d{4})', 'Período de aulas'),
    ]

    for padrao, desc in regras:
        m = re.search(padrao, texto_pdf, re.DOTALL | re.IGNORECASE)
        if m:
            groups = m.groups()
            if len(groups) == 2:
                in_str, fim_str = groups
                if len(in_str.split('/')) == 2 and len(fim_str.split('/')) == 3:
                    ano = fim_str.split('/')[2]
                    in_str = f"{in_str}/{ano}"
                eventos.append({
                    'periodo': periodo,
                    'inicio': formatar_data(in_str),
                    'fim': formatar_data(fim_str),
                    'descricao': desc
                })
            elif len(groups) == 1:
                eventos.append({
                    'periodo': periodo,
                    'inicio': formatar_data(groups[0]),
                    'fim': None,
                    'descricao': desc
                })

    return periodo, eventos


def atualizar_calendario():
    html = baixar_conteudo(pag_calendario)
    pdfs = encontrar_pdfs_matricula(html)
    
    if not pdfs:
        raise RuntimeError("Nenhum PDF encontrado no site.")

    texto_json = arquivo_calendario.read_text(encoding='utf-8')
    dados = json.loads(texto_json)
    
    total_lidos = 0
    novos_eventos_por_periodo = {}

    for periodo, url in pdfs.items():
        conteudo = baixar_conteudo(url)
        texto = extrair_texto_pdf(conteudo)
        p, evs = ler_eventos(texto)
        if p and evs:
            novos_eventos_por_periodo[p] = evs
            total_lidos += len(evs)

    if not novos_eventos_por_periodo:
        raise RuntimeError("PDFs com layout incompatível.")

    eventos_finais = []
    for e in dados.get('eventos', []):
        p = e['periodo']
        if p in novos_eventos_por_periodo:
            substitutos = novos_eventos_por_periodo[p]
            match_sub = [s for s in substitutos if s['descricao'] == e['descricao']]
            if match_sub:
                eventos_finais.append(match_sub[0])
            else:
                eventos_finais.append(e)
        else:
            eventos_finais.append(e)

    for p, evs in novos_eventos_por_periodo.items():
        existentes_desc = {e['descricao'] for e in eventos_finais if e['periodo'] == p}
        for novo in evs:
            if novo['descricao'] not in existentes_desc:
                eventos_finais.append(novo)

    dados['eventos'] = eventos_finais
    dados['atualizado_em'] = datetime.now().isoformat()
    
    arquivo_calendario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
    return total_lidos