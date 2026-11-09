import json
import re
from collections import defaultdict
from datetime import date, datetime
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen


from .login import exigir_admin


# ============================= { CONFIGURAÇÕES } ============================= #

pag_cardapio = "https://ru.unb.br/cardapio-gama/"
arquivo_saida = Path(__file__).resolve().parent.parent / 'data' / "cardapio_extraido.json"

refeicao_da_pagina = {
    0: "cafe_da_manha",
    1: "almoco",
    2: "jantar",
}

mostrar_diagnostico = False

# Categorias que, no PDF, ocupam a linha inteira (células mescladas) e valem para todos os dias. Chave: número da página.
categorias_todos_os_dias = {
    0: {"bebidas", "gordura"},
}

colunas = [
    (145, 285),
    (285, 420),
    (420, 560),
    (560, 690),
    (690, 835),
]

faixas = {
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

# ============================= { LEITURA DE LINKS DA PÁGINA } ============================= #
 
class AnalisadorLinks(HTMLParser):
 
    def __init__(self):
        super().__init__()
        self.links = []
        self.link_atual = None
 
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
 
            if href:
                self.link_atual = {'texto': [], 'url': href}
 
    def handle_data(self, data):
        if self.link_atual is not None:
            self.link_atual['texto'].append(data.strip())
 
    def handle_endtag(self, tag):
        if tag == 'a' and self.link_atual is not None:
            texto = ' '.join(parte for parte in self.link_atual['texto'] if parte).strip()
            self.links.append({'texto': texto, 'url': self.link_atual['url']})
            self.link_atual = None


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


def encontrar_pdf_cardapio():
    # Encontra o PDF do cardápio de Gama na página oficial.
    html = baixar_conteudo(pag_cardapio).decode(
        "utf-8",
        errors="replace",
    )

    analisador = AnalisadorLinks()
    analisador.feed(html)

    candidatos = []

    for link in analisador.links:
        url = link["url"].strip()
        texto = normalizar(link["texto"])
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

        url_completa = urljoin(pag_cardapio, url)

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
    for inicio, fim, categoria in faixas.get(numero_pagina, []):
        if inicio <= altura < fim:
            return categoria

    return None


def coluna_por_posicao(x):
    # Retorna a coluna do dia conforme a posição horizontal.
    for indice, (inicio, fim) in enumerate(colunas):
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
        "sujeito a alterações",
        "açúcar e adoçante",
        "acucar e adocante",
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

    if len(encontradas) < len(colunas):
        raise ValueError(
            f"Encontrei {len(encontradas)} datas no cabeçalho; "
            f"eram esperadas {len(colunas)}."
        )

    return encontradas[: len(colunas)]


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

    comuns = categorias_todos_os_dias.get(numero_pagina, set())

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


# ============================= { LIMPEZA DOS ITENS } ============================= #

padrao_data = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")

# Títulos de linha do PDF que escapam para dentro dos itens.
rotulos_soltos = {"padrao", "padrão", "estrito", "ovolactovegetariano", "vegetariano"}


def _sem_sobras(lista):
    # Tira datas, rodapé e títulos de linha que vazaram para a lista de itens.
    limpa = []

    for item in lista:
        item = normalizar(padrao_data.sub("", item))
        item = re.sub(r"^(PADRÃO|ESTRITO)\s+", "", item)

        if not item or item.casefold() in rotulos_soltos or eh_texto_de_rodape(item):
            continue

        limpa.append(item)

    return limpa


def sanitizar_registro(registro):
    # Devolve uma cópia do registro (data/refeicao/itens) sem as sobras do PDF
    # e com os itens deslocados recolocados na categoria certa.
    itens = {}

    for categoria, lista in registro.get("itens", {}).items():
        lista = _sem_sobras(lista)

        if lista:
            itens[categoria] = lista

    # Café da manhã: o PDF tem a linha "padrão" mesclada (todos os dias) e as faixas
    # ficam uma linha acima. Sem fruta, tudo desce uma posição.
    if (
        registro.get("refeicao") == "cafe_da_manha"
        and "fruta" not in itens
        and "gordura" in itens
        and "complemento_vegetariano_estrito" in itens
    ):
        deslocadas = {
            "complemento_padrao": [
                parte
                for texto in itens.pop("gordura")
                for parte in re.split(r"(?<=[a-zà-ú]) (?=[A-ZÀ-Ú])", texto)
            ],
            "complemento_ovolactovegetariano": itens.get("complemento_padrao"),
            "complemento_vegetariano_estrito": itens.get("complemento_ovolactovegetariano"),
            "fruta": itens.get("complemento_vegetariano_estrito"),
        }
        for categoria in ("complemento_padrao", "complemento_ovolactovegetariano",
                          "complemento_vegetariano_estrito", "fruta"):
            itens.pop(categoria, None)
        itens.update({c: v for c, v in deslocadas.items() if v})

    # Duas saladas coladas na mesma faixa: a primeira ficou sem lugar.
    if "salada_1" not in itens and len(itens.get("salada_2", [])) >= 2:
        primeira, *resto = itens["salada_2"]
        itens = {"salada_1": [primeira], "salada_2": resto, **{
            k: v for k, v in itens.items() if k != "salada_2"}}

    # Feijão/arroz que caíram na faixa da sobremesa.
    if "sobremesa" in itens:
        fora = [i for i in itens["sobremesa"] if re.match(r"(Feijão|Arroz)\b", i)]

        if fora:
            itens["sobremesa"] = [i for i in itens["sobremesa"] if i not in fora]
            itens["acompanhamentos"] = itens.get("acompanhamentos", []) + fora

            if not itens["sobremesa"]:
                del itens["sobremesa"]

    return {**registro, "itens": itens}


def extrair_cardapio(conteudo_pdf):
    # Gera os registros para os cinco dias e as três refeições.# 
    import pdfplumber

    registros = []

    with pdfplumber.open(BytesIO(conteudo_pdf)) as pdf:
        if len(pdf.pages) < 3:
            raise ValueError(
                f"O PDF tem {len(pdf.pages)} páginas. "
                "Eram esperadas pelo menos 3."
            )

        if mostrar_diagnostico:
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

            refeicao = refeicao_da_pagina[numero_pagina]

            # Ordem das categorias conforme aparecem no PDF.
            ordem = [
                categoria
                for _, _, categoria in faixas[numero_pagina]
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

                registros.append(sanitizar_registro({
                    "data": data,
                    "refeicao": refeicao,
                    "itens": itens,
                }))

    return registros

# ============================= { CONSULTA AO CARDÁPIO (era consultas_publicas.py) } ============================= #
 
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
 
 
def nome_dia_semana(data_iso):
    return dias_semana[date.fromisoformat(data_iso).weekday()]
 
 
def carregar_cardapio():
    # Lê o JSON gerado por atualizar_cardapio(). Lista vazia se ele ainda não existe.
    if not arquivo_saida.exists():
        return []
 
    try:
        with open(arquivo_saida, encoding='utf-8') as arquivo:
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
 
 
def atualizar_cardapio_ru(conta):
    # Baixa o PDF do RU e regrava o JSON. Só admin.
    exigir_admin(conta)
 
    try:
        registros = atualizar_cardapio()
    except (OSError, ValueError, RuntimeError) as erro:
        raise RuntimeError(f'Não foi possível atualizar o cardápio: {erro}')
 
    return len(registros)


# ============================= { EXECUÇÃO } ============================= #

def atualizar_cardapio(conteudo_pdf=None):
    
    # Baixa (ou recebe), extrai, valida e salva o cardápio atualizado.

    # 1. Localiza e baixa o PDF do RU (a menos que ele já tenha sido entregue).
    if conteudo_pdf is None:
        url_pdf = encontrar_pdf_cardapio()
        conteudo_pdf = baixar_conteudo(url_pdf)

    # 2. Extrai os dados do PDF.
    registros = extrair_cardapio(conteudo_pdf)

    # 3. Verifica se foram gerados os 15 registros esperados.
    if len(registros) != 15:
        raise ValueError(
            f"Esperados 15 registros, mas foram gerados {len(registros)}."
        )

    # 4. Verifica se todas as refeições possuem itens.
    for registro in registros:
        if not registro.get("itens"):
            raise ValueError(
                f"Refeição sem itens encontrada: "
                f"{registro.get('refeicao')} - {registro.get('data')}."
            )

    # 5. Garante que a pasta de destino exista.
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    # 6. Salva primeiro em um arquivo temporário.
    arquivo_temporario = arquivo_saida.with_suffix(".tmp")

    try:
        with open(arquivo_temporario, "w", encoding="utf-8") as arquivo:
            json.dump(
                registros,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

        # 7. Substitui o JSON anterior somente após a gravação.
        arquivo_temporario.replace(arquivo_saida)

    finally:
        # Remove o temporário caso ocorra algum erro.
        if arquivo_temporario.exists():
            arquivo_temporario.unlink()

    print(f"Cardápio atualizado em: {arquivo_saida}")

    return registros


def main():
    # python -m code_py.cardapio                      -> baixa o PDF do site do RU
    # python -m code_py.cardapio arquivo.pdf          -> usa um PDF local
    # python -m code_py.cardapio arquivo.pdf --diag   -> também imprime a posição de cada palavra
    import sys

    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    global mostrar_diagnostico
    mostrar_diagnostico = "--diag" in sys.argv

    try:
        if argumentos:
            atualizar_cardapio(Path(argumentos[0]).read_bytes())
        else:
            atualizar_cardapio()
    except Exception as erro:
        print(f"Erro ao atualizar o cardápio: {erro}")


if __name__ == "__main__":
    main()