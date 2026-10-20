import json
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from io import BytesIO
from datetime import datetime
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pdfplumber


# ============================= { CONFIGURAÇÕES } ============================= #

PAGINA_CARDAPIO = "https://ru.unb.br/cardapio-gama/"
ARQUIVO_SAIDA = "cardapio_extraido.json"

REFEICOES = {
    0: "cafe_da_manha",
    1: "almoco",
    2: "jantar",
}

MOSTRAR_DIAGNOSTICO = False

# Categorias que, no PDF, ocupam a linha inteira (células mescladas) e valem para todos os dias. Chave: número da página.
CATEGORIAS_TODOS_OS_DIAS = {
    0: {"bebidas", "gordura"},
}

COLUNAS = [
    (145, 285),
    (285, 420),
    (420, 560),
    (560, 690),
    (690, 835),
]

FAIXAS = {
    0: [
        (115, 170, "bebidas"),
        (170, 250, "panificacao"),
        (250, 290, "opcao_extra"),
        (290, 315, "gordura"),
        (315, 370, "complemento_padrao"),
        (370, 415, "complemento_ovolactovegetariano"),
        (415, 460, "complemento_vegetariano_estrito"),
        (460, 495, "fruta"),
    ],
    1: [
        (85, 125, "salada_1"),
        (125, 155, "salada_2"),
        (155, 190, "molho_para_salada"),
        (190, 240, "prato_principal_padrao"),
        (240, 300, "prato_principal_ovolactovegetariano"),
        (300, 345, "prato_principal_vegetariano_estrito"),
        (345, 380, "guarnicao"),
        (380, 415, "acompanhamentos"),
        (415, 460, "sobremesa"),
        (460, 490, "bebida"),
    ],
    2: [
        (80, 105, "salada_1"),
        (105, 150, "salada_2"),
        (150, 190, "molho_para_salada"),
        (190, 230, "prato_principal_padrao"),
        (230, 285, "prato_principal_ovolactovegetariano"),
        (285, 335, "prato_principal_vegetariano_estrito"),
        (335, 375, "sopa"),
        (375, 400, "torrada"),
        (400, 430, "acompanhamentos"),
        (430, 460, "sobremesa"),
        (460, 490, "bebida"),
    ],
}


# ============================= { FUNÇÕES AUXILIARES } ============================= #

def normalizar(texto):
    # Normaliza espaços e quebras de linha.#
    return re.sub(r"\s+", " ", str(texto)).strip()


def limpar_final(texto):
    # Remove conectores soltos no fim de um item (ex.: '... ou').# 
    return re.sub(
        r"\s+(ou|e|com|de)\s*$",
        "",
        texto,
        flags=re.IGNORECASE,
    ).strip()


def corrigir_texto(texto):
    # Corrige pequenos erros de digitação herdados do PDF.# 
    texto = normalizar(texto)

    # Espaço depois de vírgula: "sálvia,alecrim" -> "sálvia, alecrim"
    texto = re.sub(r",(?=[^\s\d])", ", ", texto)

    # "Arroz branco e Integral" -> "Arroz branco e integral"
    texto = re.sub(r"\be Integral\b", "e integral", texto)

    return texto


def baixar_conteudo(url):
    # Baixa o conteúdo de uma URL.# 
    requisicao = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    with urlopen(requisicao, timeout=30) as resposta:
        return resposta.read()


class AnalisadorLinks(HTMLParser):
    # Extrai links de uma página HTML.

    def __init__(self):
        super().__init__()
        self.links = []
        self.link_atual = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        atributos = dict(attrs)
        href = atributos.get("href")

        if href:
            self.link_atual = {
                "url": href.strip(),
                "texto": "",
            }

    def handle_data(self, data):
        if self.link_atual is not None:
            self.link_atual["texto"] += data

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.link_atual is not None:
            self.link_atual["texto"] = normalizar(
                self.link_atual["texto"]
            )
            self.links.append(self.link_atual)
            self.link_atual = None


def encontrar_pdf_cardapio():
    # Encontra o PDF do cardápio de Gama na página oficial.
    html = baixar_conteudo(PAGINA_CARDAPIO).decode(
        "utf-8",
        errors="replace",
    )

    analisador = AnalisadorLinks()
    analisador.feed(html)

    candidatos = []

    for link in analisador.links:
        url = link["url"]
        texto = link["texto"]
        referencia = f"{url} {texto}".lower()

        if ".pdf" not in url.lower():
            continue

        if "gama" not in referencia and "ism" not in referencia:
            continue

        # Reconhece datas como 19/10/2026 ou 19-10-2026.
        datas = re.findall(
            r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
            f"{texto} {url}",
        )

        data_inicio = datetime.min

        if datas:
            dia, mes, ano = map(int, datas[0])

            try:
                data_inicio = datetime(ano, mes, dia)
            except ValueError:
                pass

        url_completa = urljoin(PAGINA_CARDAPIO, url)

        candidatos.append(
            (data_inicio, url_completa, texto)
        )

    if not candidatos:
        raise RuntimeError(
            "Não encontrei um PDF de Gama/ISM na página oficial."
        )

    candidatos.sort(key=lambda item: item[0], reverse=True)

    _, url, titulo = candidatos[0]

    print(f"PDF encontrado: {titulo or url}")
    print(f"URL: {url}")

    return url


def categoria_por_altura(numero_pagina, altura):
    # Retorna a categoria conforme a posição vertical.
    for inicio, fim, categoria in FAIXAS.get(numero_pagina, []):
        if inicio <= altura < fim:
            return categoria

    return None


def coluna_por_posicao(x):
    # Retorna a coluna do dia conforme a posição horizontal.
    for indice, (inicio, fim) in enumerate(COLUNAS):
        if inicio <= x < fim:
            return indice

    return None


def eh_texto_de_rodape(texto):
    # Identifica avisos e textos de apoio que não são alimentos.
    texto = normalizar(texto).lower()

    trechos_rodape = (
        "mesa de apoio",
        "cardápio sujeito a alteração",
        "cardapio sujeito a alteracao",
    )

    return any(trecho in texto for trecho in trechos_rodape)


def extrair_datas(pagina):
    # Lê as cinco datas (dd/mm/aaaa) do cabeçalho da página.
    texto = pagina.extract_text() or ""

    encontradas = []

    for dia, mes, ano in re.findall(
        r"(\d{2})/(\d{2})/(\d{4})",
        texto,
    ):
        data_iso = f"{ano}-{mes}-{dia}"

        try:
            datetime.strptime(data_iso, "%Y-%m-%d")
        except ValueError:
            continue

        if data_iso not in encontradas:
            encontradas.append(data_iso)

    if len(encontradas) < len(COLUNAS):
        raise ValueError(
            f"Encontrei {len(encontradas)} datas no cabeçalho; "
            f"eram esperadas {len(COLUNAS)}."
        )

    return encontradas[: len(COLUNAS)]


# ============================= { AGRUPAMENTO DE TEXTO } ============================= #

def agrupar_palavras_por_linha(palavras, tolerancia=3):
    # Agrupa palavras próximas verticalmente na mesma linha.
    palavras = sorted(
        palavras,
        key=lambda palavra: (palavra["top"], palavra["x0"]),
    )

    linhas = []

    for palavra in palavras:
        if not linhas:
            linhas.append({
                "top": palavra["top"],
                "palavras": [palavra],
            })
            continue

        ultima = linhas[-1]

        if abs(palavra["top"] - ultima["top"]) <= tolerancia:
            ultima["palavras"].append(palavra)
        else:
            linhas.append({
                "top": palavra["top"],
                "palavras": [palavra],
            })

    resultado = []

    for linha in linhas:
        palavras_linha = sorted(
            linha["palavras"],
            key=lambda palavra: palavra["x0"],
        )

        texto = " ".join(
            palavra["text"] for palavra in palavras_linha
        )

        resultado.append({
            "top": linha["top"],
            "texto": normalizar(texto),
        })

    return resultado


def parece_continuacao(texto):
    # Identifica finais que sugerem que a descrição não terminou.
    texto = texto.rstrip().lower()

    finais = (
        " e",
        " ou",
        " com",
        " de",
        " da",
        " do",
        " dos",
        " das",
        " ao",
        " à",
        " para",
        " em",
        " no",
        " na",
        " nos",
        " nas",
        " por",
        ",",
        "(",
        "-",
    )

    return texto.endswith(finais)


def comeca_com_continuacao(texto):
    # Detecta linhas que parecem continuar uma descrição anterior.# 
    texto = normalizar(texto)

    if not texto:
        return False

    return (
        texto[0].islower()
        or texto.startswith("(")
    )


def juntar_linhas(linhas, intervalo_maximo=35):
    
    # Junta linhas quando a descrição parece continuar.

    # Mantém as linhas separadas quando a descrição anterior parece completa e a próxima começa como um novo alimento.
    
    itens = []

    for linha in linhas:
        texto = normalizar(linha["texto"])

        if not texto or eh_texto_de_rodape(texto):
            continue

        if not itens:
            itens.append({
                "texto": texto,
                "top_final": linha["top"],
            })
            continue

        anterior = itens[-1]
        distancia = linha["top"] - anterior["top_final"]

        termina_incompleto = parece_continuacao(
            anterior["texto"]
        )
        comeca_em_continuacao = comeca_com_continuacao(texto)

        deve_juntar = (
            0 <= distancia <= intervalo_maximo
            and (
                termina_incompleto
                or comeca_em_continuacao
            )
        )

        if deve_juntar:
            anterior["texto"] = normalizar(
                anterior["texto"] + " " + texto
            )
            anterior["top_final"] = linha["top"]
        else:
            itens.append({
                "texto": texto,
                "top_final": linha["top"],
            })

    return [
        item["texto"]
        for item in itens
        if not eh_texto_de_rodape(item["texto"])
    ]


# ============================= { DIAGNÓSTICO } ============================= #

def diagnosticar_pagina(pagina, numero_pagina):
    # Exibe as coordenadas das palavras extraídas do PDF.# 
    print(f"\n--- PÁGINA {numero_pagina + 1} ---")

    palavras = pagina.extract_words(
        x_tolerance=2,
        y_tolerance=3,
        keep_blank_chars=False,
    )

    for palavra in sorted(
        palavras,
        key=lambda item: (item["top"], item["x0"]),
    ):
        print(
            f"y={palavra['top']:7.2f} "
            f"x={palavra['x0']:7.2f} "
            f"texto={palavra['text']}"
        )


# ============================= { EXTRAÇÃO DE UMA PÁGINA } ============================= #

def extrair_pagina(pagina, numero_pagina):
    
    # Extrai e organiza os itens de uma página do cardápio.

    # Retorna (por_coluna, todos_os_dias):
    #  - por_coluna[coluna][categoria] -> lista de itens
    #  - todos_os_dias[categoria]      -> lista de itens comuns
    #                                     a todos os dias
    
    palavras = pagina.extract_words(
        x_tolerance=2,
        y_tolerance=3,
        keep_blank_chars=False,
    )

    comuns = CATEGORIAS_TODOS_OS_DIAS.get(numero_pagina, set())

    grupos = defaultdict(list)
    grupos_comuns = defaultdict(list)

    for palavra in palavras:
        centro_x = (palavra["x0"] + palavra["x1"]) / 2
        altura = palavra["top"]
        texto = normalizar(palavra["text"])

        # Exclui o rodapé antes da classificação por categoria.
        # Isso evita que "molho de pimenta, vinagre e azeite"
        # seja incorporado à categoria de bebidas.
        if altura >= 485:
            continue

        if eh_texto_de_rodape(texto):
            continue

        coluna = coluna_por_posicao(centro_x)
        categoria = categoria_por_altura(
            numero_pagina,
            altura,
        )

        if coluna is None or categoria is None:
            continue

        # Células mescladas: ignora a coluna e junta tudo em um
        # único grupo, para o texto não ser cortado entre colunas.
        if categoria in comuns:
            grupos_comuns[categoria].append(palavra)
        else:
            grupos[(coluna, categoria)].append(palavra)

    por_coluna = defaultdict(lambda: defaultdict(list))

    for (coluna, categoria), palavras_grupo in grupos.items():
        linhas = agrupar_palavras_por_linha(palavras_grupo)
        itens = juntar_linhas(linhas)

        por_coluna[coluna][categoria].extend(
            item for item in itens if item
        )

    todos_os_dias = {}

    for categoria, palavras_grupo in grupos_comuns.items():
        linhas = agrupar_palavras_por_linha(palavras_grupo)
        itens = [item for item in juntar_linhas(linhas) if item]

        if itens:
            todos_os_dias[categoria] = itens

    return por_coluna, todos_os_dias


# ============================= { EXTRAÇÃO DE 3 REFEIÇÕES } ============================= #

def limpar_itens(lista_itens):
    # Aplica todas as limpezas de texto a uma lista de itens.# 
    resultado = []

    for item in lista_itens:
        item = normalizar(item)

        if not item or eh_texto_de_rodape(item):
            continue

        item = corrigir_texto(limpar_final(item))

        if item:
            resultado.append(item)

    return resultado


def extrair_cardapio(conteudo_pdf):
    # Gera os registros para os cinco dias e as três refeições.# 
    registros = []

    with pdfplumber.open(BytesIO(conteudo_pdf)) as pdf:
        if len(pdf.pages) < 3:
            raise ValueError(
                f"O PDF tem {len(pdf.pages)} páginas. "
                "Eram esperadas pelo menos 3."
            )

        if MOSTRAR_DIAGNOSTICO:
            for numero_pagina in range(3):
                diagnosticar_pagina(
                    pdf.pages[numero_pagina],
                    numero_pagina,
                )

        datas = extrair_datas(pdf.pages[0])

        for numero_pagina in range(3):
            pagina = pdf.pages[numero_pagina]

            if numero_pagina > 0:
                datas_pagina = extrair_datas(pagina)

                if datas_pagina != datas:
                    print(
                        f"ATENÇÃO: as datas da página "
                        f"{numero_pagina + 1} diferem da página 1."
                    )

            por_coluna, todos_os_dias = extrair_pagina(
                pagina,
                numero_pagina,
            )

            refeicao = REFEICOES[numero_pagina]

            # Ordem das categorias conforme aparecem no PDF.
            ordem = [
                categoria
                for _, _, categoria in FAIXAS[numero_pagina]
            ]

            for coluna, data in enumerate(datas):
                brutos = {
                    categoria: lista
                    for categoria, lista in por_coluna[coluna].items()
                }

                # Itens comuns a todos os dias (bebidas, gordura).
                for categoria, lista in todos_os_dias.items():
                    brutos[categoria] = lista

                itens = {}

                for categoria in ordem:
                    if categoria not in brutos:
                        continue

                    lista_limpa = limpar_itens(brutos[categoria])

                    if lista_limpa:
                        itens[categoria] = lista_limpa

                registros.append({
                    "data": data,
                    "refeicao": refeicao,
                    "itens": itens,
                })

    return registros


# ============================= { EXECUÇÃO } ============================= #

def atualizar_cardapio():
    #Baixa, extrai e salva o cardápio atualizado.
    url_pdf = encontrar_pdf_cardapio()
    registros = extrair_cardapio(url_pdf)

    if len(registros) != 15:
        raise ValueError(
            f"Esperados 15 registros, mas foram gerados {len(registros)}."
        )

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as arquivo:
        json.dump(registros, arquivo, ensure_ascii=False, indent=4)

    print(f"Cardápio atualizado em: {ARQUIVO_SAIDA}")
    return registros


def main():
    try:
        atualizar_cardapio()
    except Exception as erro:
        print(f"Erro ao atualizar o cardápio: {erro}")


if __name__ == "__main__":
    main()