from datetime import date, datetime
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urljoin
import re

url_cardapio_gama = 'https://ru.unb.br/cardapio-gama/'


class AnalisadorLinks(HTMLParser):

    def __init__(self):
        super().__init__()
        self.links = []
        self.link_atual = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            atributos = dict(attrs)
            href = atributos.get('href')

            if href:
                self.link_atual = {
                    'texto': [],
                    'url': href
                }

    def handle_data(self, data):
        if self.link_atual is not None:
            self.link_atual['texto'].append(data.strip())

    def handle_endtag(self, tag):
        if tag == 'a' and self.link_atual is not None:
            texto = ' '.join(
                parte for parte in self.link_atual['texto']
                if parte
            ).strip()

            self.links.append({
                'texto': texto,
                'url': self.link_atual['url']
            })

            self.link_atual = None


def _buscar_pagina(url):
    requisicao = Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (compatible; SistemaFCTE/1.0)'
        }
    )

    with urlopen(requisicao, timeout=30) as resposta:
        return resposta.read().decode(
            'utf-8',
            errors='replace'
        )


def buscar_cardapios_publicos(campus='Gama'):
    campus_normalizado = campus.strip().casefold()

    paginas = {
        'gama': url_cardapio_gama,
        'darcy ribeiro': 'https://ru.unb.br/cardapio/',
        'ceilandia': 'https://ru.unb.br/cardapio-ceilandia/',
        'planaltina': 'https://ru.unb.br/cardapio-planaltina/',
        'fazenda agua limpa': 'https://ru.unb.br/cardapio-fazenda/'
    }

    if campus_normalizado not in paginas:
        raise ValueError(
            'Campus inválido. Consulte as unidades disponíveis '
            'na página oficial do RU.'
        )

    url_pagina = paginas[campus_normalizado]
    html = _buscar_pagina(url_pagina)

    analisador = AnalisadorLinks()
    analisador.feed(html)

    cardapios = []

    for link in analisador.links:
        url = urljoin(url_pagina, link['url'])
        texto = link['texto']
        caminho = url.split('?', 1)[0].lower()

        if (
            caminho.endswith('.pdf')
            and (
                'cardapio' in url.lower()
                or 'cardápio' in texto.casefold()
                or 'semana' in url.lower()
                or 'ism' in texto.casefold()
            )
        ):
            
            titulo = texto or 'Cardápio do RU'

            cardapios.append({
                'campus': campus,
                'titulo': titulo,
                'url': url,
                'fonte': url_pagina,
                **interpretar_periodo_cardapio(titulo)
            })


    # Evita repetir links encontrados na mesma página.
    links_unicos = {}
    for cardapio in cardapios:
        links_unicos[cardapio['url']] = cardapio

    cardapios = list(links_unicos.values())

    if not cardapios:
        raise RuntimeError(
            'Nenhum PDF de cardápio foi identificado. '
            'A página pode ter mudado de estrutura ou '
            'utilizar outro formato de publicação.'
        )

    return {
        'campus': campus,
        'consultado_em': datetime.now().astimezone().isoformat(
            timespec='seconds'
        ),
        'fonte': url_pagina,
        'cardapios': cardapios
    }


def interpretar_periodo_cardapio(titulo, hoje=None):
    
    #Extrai as datas do título e identifica se o cardápio está vigente.
    
    hoje = hoje or date.today()

    correspondencia = re.search(
        r'(\d{2}/\d{2}/\d{4})\s*A\s*(\d{2}/\d{2}/\d{4})',
        titulo,
        re.IGNORECASE
    )

    if not correspondencia:
        return {
            'data_inicio': None,
            'data_fim': None,
            'vigente': False
        }

    try:
        inicio = datetime.strptime(
            correspondencia.group(1), '%d/%m/%Y'
        ).date()
        fim = datetime.strptime(
            correspondencia.group(2), '%d/%m/%Y'
        ).date()
    except ValueError:
        return {
            'data_inicio': None,
            'data_fim': None,
            'vigente': False
        }

    if fim < inicio:
        return {
            'data_inicio': inicio.isoformat(),
            'data_fim': fim.isoformat(),
            'vigente': False
        }

    return {
        'data_inicio': inicio.isoformat(),
        'data_fim': fim.isoformat(),
        'vigente': inicio <= hoje <= fim
    }
