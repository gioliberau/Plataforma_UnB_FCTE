from datetime import datetime
from contextlib import closing
import json

from .banco import conectar
from .sigaa import buscar_turmas_publicas
from .ru import buscar_cardapios_publicos, interpretar_periodo_cardapio
from .cardapio import atualizar_cardapio

# ============================= { SISTEMA FCTE } ============================= #


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

    def __init__(self):

        # Prepara o armazenamento dos dados públicos.
        self.__criar_tabela_dados_publicos()
        self.__carregar_cursos_iniciais()


    def atualizar_turmas_sigaa(self, ano=2026, semestre=2):
        turmas = buscar_turmas_publicas(ano, semestre)

        with closing(conectar()) as conexao:
            conexao.execute('''
                CREATE TABLE IF NOT EXISTS dados_publicos (
                    categoria TEXT NOT NULL,
                    chave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    fonte TEXT NOT NULL,
                    PRIMARY KEY (categoria, chave)
                )
            ''')

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

    def listar_turmas_sigaa(self, ano=2026, semestre=2):
        periodo = f'{ano}.{semestre}'

        with closing(conectar()) as conexao:
            registros = conexao.execute('''
                SELECT valor
                FROM dados_publicos
                WHERE categoria = ?
                ORDER BY chave
            ''', ('turma_sigaa',)).fetchall()

        turmas = []

        for registro in registros:
            turma = json.loads(registro['valor'])

            if turma.get('periodo') == periodo:
                turmas.append(turma)

        return turmas

    def __criar_tabela_dados_publicos(self):

        # Cria uma tabela para armazenar informações públicas.
        with closing(conectar()) as conexao:
            conexao.execute('''
                CREATE TABLE IF NOT EXISTS dados_publicos (
                    categoria TEXT NOT NULL,
                    chave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    fonte TEXT NOT NULL,
                    PRIMARY KEY (categoria, chave)
                )
            ''')
            conexao.commit()


    def __carregar_cursos_iniciais(self):
        cursos = [
            'Engenharia Automotiva',
            'Engenharia Aeroespacial',
            'Engenharia Eletrônica',
            'Engenharia de Energia',
            'Engenharia de Software'
        ]

        with closing(conectar()) as conexao:
            for curso in cursos:
                conexao.execute('''
                    INSERT OR IGNORE INTO dados_publicos
                    (categoria, chave, valor, fonte)
                    VALUES (?, ?, ?, ?)
                ''', (
                    'curso',
                    curso,
                    curso,
                    self.url_cursos
                ))

            conexao.commit()


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
            'docentes': ('https://sigaa.unb.br/sigaa/public/docente/busca_docentes.jsf'),
            'ru_cardapio': 'https://ru.unb.br/cardapio-refeitorio/',
            'ru_valores': 'https://ru.unb.br/precos-e-grupos/',
            'biblioteca_fcte': 'https://fcte.unb.br/contato/',
            'catalogo_biblioteca': 'https://bce.unb.br/'
        }



    def salvar_dado_publico(self, categoria, chave, valor, fonte):

        # Valida os dados antes de armazená-los.
        campos = (categoria, chave, valor, fonte)

        if any(
            not isinstance(campo, str) or not campo.strip()
            for campo in campos
        ):
            raise ValueError(
                'Categoria, chave, valor e fonte devem ser preenchidos.'
            )

        with closing(conectar()) as conexao:
            conexao.execute('''
                INSERT INTO dados_publicos
                (categoria, chave, valor, fonte)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(categoria, chave)
                DO UPDATE SET
                    valor = excluded.valor,
                    fonte = excluded.fonte
            ''', tuple(campo.strip() for campo in campos))

            conexao.commit()


    def listar_dados_publicos(self, categoria):

        # Consulta os dados de uma categoria específica.
        with closing(conectar()) as conexao:
            dados = conexao.execute('''
                SELECT chave, valor, fonte
                FROM dados_publicos
                WHERE categoria = ?
                ORDER BY chave
            ''', (categoria,)).fetchall()

        return dados


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


    
    def atualizar_cardapio_ru(self, campus='Gama'):
        dados_ru = buscar_cardapios_publicos(campus)

        with closing(conectar()) as conexao:
            with conexao:
                for cardapio in dados_ru['cardapios']:
                    chave = (
                        f"{campus.casefold()}|"
                        f"{cardapio['url']}"
                    )

                    valor = {
                        **cardapio,
                        'consultado_em': dados_ru['consultado_em']
                    }

                    conexao.execute('''
                        INSERT INTO dados_publicos
                            (categoria, chave, valor, fonte)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(categoria, chave)
                        DO UPDATE SET
                            valor = excluded.valor,
                            fonte = excluded.fonte
                    ''', (
                        'cardapio_ru',
                        chave,
                        json.dumps(valor, ensure_ascii=False),
                        cardapio['fonte']
                    ))

        return len(dados_ru['cardapios'])

    
    def listar_cardapio_ru(self, campus='Gama', apenas_vigentes=True):
        prefixo = f"{campus.casefold()}|"

        with closing(conectar()) as conexao:
            registros = conexao.execute('''
                SELECT chave, valor, fonte
                FROM dados_publicos
                WHERE categoria = ?
                  AND chave LIKE ?
                ORDER BY chave
            ''', (
                'cardapio_ru',
                prefixo + '%'
            )).fetchall()

        hoje = datetime.now().astimezone().date()
        cardapios = []

        for registro in registros:
            cardapio = json.loads(registro['valor'])

            periodo = interpretar_periodo_cardapio(
                cardapio.get('titulo', ''),
                hoje=hoje
            )

            cardapio.update(periodo)
            cardapio['fonte'] = registro['fonte']
            cardapios.append(cardapio)

        if apenas_vigentes:
            cardapios = [
                cardapio for cardapio in cardapios
                if cardapio['vigente']
            ]

        return sorted(
            cardapios,
            key=lambda cardapio: cardapio['data_inicio'] or '',
            reverse=True
        )
