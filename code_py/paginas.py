import re
from abc import ABC, abstractmethod
from datetime import date, datetime

# ----------------------------------------------- #

from . import organizacoes as ops
from . import consultas_publicas as cp
from .system import SistemaFCTE

# ============================= { MENU GENÉRICO } ============================= #

def abrir_menu(titulo, opcoes, saida='Voltar', ativo=lambda: True, cabecalho=None):
 
    while ativo():
        lista = opcoes()
 
        if cabecalho:
            cabecalho()
 
        print(f'\n===== {titulo} =====')
 
        for numero, (rotulo, _) in enumerate(lista, start=1):
            print(f'{numero} - {rotulo}')
 
        print(f'0 - {saida}')
 
        escolha = input('Escolha uma opção: ').strip()
 
        if escolha == '0':
            break
 
        if not escolha.isdigit() or not 1 <= int(escolha) <= len(lista):
            print('Opção inválida. Tente novamente.')
            continue
 
        try:
            lista[int(escolha) - 1][1]()
        except (ValueError, PermissionError, RuntimeError) as erro:
            print(f'Não foi possível concluir: {erro}')

# ============================= { PÁGINA BASE } ============================= #

class PaginaPerfil(ABC):
    # Esqueleto comum: o loop do menu é igual; cada perfil define seu título e suas opções.

    exige_login = True

    def __init__(self, sessao):
        self._sessao = sessao

    @property
    @abstractmethod
    def titulo(self):
        pass

    @abstractmethod
    def _opcoes(self):
        # Retorna uma lista de tuplas (rótulo, função sem argumentos).
        pass

    @property
    def _perfil(self):
        return self._sessao.perfil
    
    @property
    def _conta(self):
        return self._sessao.usuario

    @property
    def _autor(self):
        # Quem publica/gerencia: o perfil (docente). A PaginaAdmin troca pela Conta
        return self._sessao.perfil

    def executar(self):
        abrir_menu(
            self.titulo,
            self._opcoes,
            ativo=lambda: not self.exige_login or self._sessao.autenticada
        )

    # ========== { Helpers de entrada } ========== #
 
    @staticmethod
    def _confirmar(pergunta):
        # [NEW] Substitui os "if input(...).strip().lower() != 's'" repetidos.
        if input(f'{pergunta} (s/n): ').strip().lower() != 's':
            print('Operação cancelada.')
            return False
 
        return True
 
    @staticmethod
    def _escolher(titulo, rotulos):
        # [NEW] Lista numerada a partir de um dict {chave: rótulo} e devolve a chave escolhida.
        # Substitui os blocos "for numero, chave in enumerate(...)" de categoria, tipo, dieta e dia.
        chaves = tuple(rotulos)
 
        print(f'\n{titulo}')
 
        for numero, chave in enumerate(chaves, start=1):
            print(f'{numero} - {rotulos[chave]}')
 
        escolha = input('Número da opção: ').strip()
 
        if not escolha.isdigit() or not 1 <= int(escolha) <= len(chaves):
            raise ValueError('Opção inválida.')
 
        return chaves[int(escolha) - 1]
 
    @staticmethod
    def _converter_data(texto):
        try:
            return datetime.strptime(texto, '%d/%m/%Y').date()
        except ValueError:
            raise ValueError('Data inválida. Use o formato DD/MM/AAAA.')
 
    @classmethod
    def _ler_prazo(cls):
        valor = input('Prazo (DD/MM/AAAA, Enter para nenhum): ').strip()
        return cls._converter_data(valor) if valor else None
 
    @staticmethod
    def _ler_id():
        valor = input('Código da publicação (#): ').strip().lstrip('#')
 
        if not valor.isdigit():
            raise ValueError('Código inválido.')
 
        return int(valor)

    # ========== { Comportamento compartilhado } ========== #

    def _ver_perfil(self):
        perfil = self._perfil

        print('\n----- MEU PERFIL -----')
        print(f'Nome: {perfil.nome}')
        print(f'Matrícula: {perfil.id_user}')
        print(f'E-mail: {perfil.email}')
        print(f'Tipo: {perfil.tipo_usuario}')
        print(f'Curso/Área: {perfil.curso_ou_area}')

    def _publicar(self):
        # O docente só vê as categorias do seu perfil; o admin vê todas (ver organizacoes.categorias_por_perfil).
        permitidas = ops.categorias_do_perfil(self._autor)
        categoria = self._escolher(
            'Categoria:', {c: ops.categorias_oportunidades[c] for c in permitidas}
        )
 
        titulo = input('Título: ')
        descricao = input('Descrição: ')
        contato = input('Contato (e-mail ou sala): ')
        prazo = self._ler_prazo()
 
        nova = ops.publicar(self._autor, titulo, categoria, descricao, contato, prazo)
        print(f'Oportunidade publicada! Código: #{nova.id}')
 
    def _interessados(self):
        lista = ops.listar_interessados(self._autor, self._ler_id())
 
        if not lista:
            print('Ninguém demonstrou interesse até agora.')
            return
 
        print(f'\n{len(lista)} interessado(s):')
 
        for aluno in lista:
            print(
                f'- {aluno["nome"]} | Matrícula: {aluno["matricula"]} | '
                f'{aluno["curso"]} | {aluno["email"]} | em {aluno["criado_em"][:10]}'
            )
 
    def _encerrar(self):
        id_oportunidade = self._ler_id()
 
        if self._confirmar('Encerrar esta publicação?'):
            ops.encerrar(self._autor, id_oportunidade)
            print('Publicação encerrada.')

    @staticmethod
    def _mostrar(lista, vazio):
        if not lista:
            print(vazio)
            return

        print()

        for oportunidade in lista:
            print(oportunidade)
            print()


    @staticmethod
    def _mostrar_entidades(lista):
        if not lista:
            print('Nenhuma entidade cadastrada.')
            return

        print()

        for entidade in lista:
            tipo = ops.tipos_entidades_fixas.get(entidade['tipo'], entidade['tipo'])
            print(f'- {entidade["nome"]} ({tipo})')
            print(f'    {entidade["instagram_link"]}')

        print()


# ============================= { PÁGINA DO DISCENTE } ============================= #

class PaginaDiscente(PaginaPerfil):

    @property
    def titulo(self):
        return 'ÁREA DO DISCENTE'

    def _opcoes(self):
        opcoes = [('Consultar todas as oportunidades', lambda: self._consultar(None))]

        # O menu é montado a partir das categorias que o discente pode ver.
        for chave in ops.categorias_do_perfil(self._perfil):
            opcoes.append((
                f'Consultar: {ops.categorias_oportunidades[chave]}',
                lambda c=chave: self._consultar(c)
            ))

        # Entidades fixas (empresas juniores, atlética, equipes de competição).
        for tipo, rotulo in ops.tipos_entidades_fixas.items():
            opcoes.append((
                f'Conhecer: {rotulo}',
                lambda t=tipo: self._consultar_entidades(t)
            ))

        opcoes += [
            ('Demonstrar interesse em uma oportunidade', self._demonstrar_interesse),
            ('Meus interesses', self._meus_interesses),
            ('Retirar interesse', self._retirar_interesse),
            ('Ver meu perfil', self._ver_perfil),
        ]
        return opcoes

    def _consultar(self, categoria):
        lista = ops.listar_para_discente(self._perfil, categoria)
        self._mostrar(lista, 'Nenhuma oportunidade aberta nesta categoria no momento.')

    def _consultar_entidades(self, tipo):
        self._mostrar_entidades(ops.listar_entidades_fixas(self._perfil, tipo))

    def _demonstrar_interesse(self):
        id_oportunidade = self._ler_id()

        print('Seu nome, matrícula, curso e e-mail ficarão visíveis para quem publicou.')

        if input('Confirmar interesse? (s/n): ').strip().lower() != 's':
            print('Operação cancelada.')
            return

        oportunidade = ops.demonstrar_interesse(self._perfil, id_oportunidade)
        print(f'Interesse registrado em "{oportunidade.titulo}"!')

    def _meus_interesses(self):
        self._mostrar(
            ops.listar_meus_interesses(self._perfil),
            'Você ainda não demonstrou interesse em nenhuma oportunidade.'
        )

    def _retirar_interesse(self):
        ops.retirar_interesse(self._perfil, self._ler_id())
        print('Interesse removido.')


# ============================= { PÁGINA DO DOCENTE } ============================= #

class PaginaDocente(PaginaPerfil):

    @property
    def titulo(self):
        return 'ÁREA DO DOCENTE'

    def _opcoes(self):
        return [
            ('Publicar oportunidade', self._publicar),
            ('Consultar minhas publicações', self._minhas),
            ('Ver interessados em uma publicação', self._interessados),
            ('Editar publicação', self._editar),
            ('Encerrar publicação', self._encerrar),
            ('Consultar meu perfil', self._ver_perfil),
        ]

    def _minhas(self):
        lista = ops.listar_minhas(self._perfil)

        if not lista:
            print('Você ainda não publicou nenhuma oportunidade.')
            return

        print()

        for oportunidade in lista:
            print(oportunidade)
            print(f'    Interessados: {ops.contar_interessados(oportunidade.id)}')
            print()

    def _editar(self):
        id_oportunidade = self._ler_id()

        print('Deixe em branco para manter o valor atual.')
        titulo = input('Novo título: ').strip()
        descricao = input('Nova descrição: ').strip()
        contato = input('Novo contato: ').strip()
        prazo_txt = input('Novo prazo (DD/MM/AAAA, "-" para remover): ').strip()

        campos = {}

        if titulo:
            campos['titulo'] = titulo
        if descricao:
            campos['descricao'] = descricao
        if contato:
            campos['contato'] = contato

        if prazo_txt == '-':
            campos['prazo'] = None
        elif prazo_txt:
            campos['prazo'] = self._converter_data(prazo_txt)

        ops.editar(self._perfil, id_oportunidade, **campos)
        print('Publicação atualizada!')


# ============================= { PÁGINA DO ADMIN } ============================= #

class PaginaAdmin(PaginaPerfil):
    # Admin não tem perfil: usa a Conta da sessão.

    @property
    def titulo(self):
        return 'ÁREA DO ADMIN - OPORTUNIDADES'

    @property
    def _autor(self):
        return self._conta

    def _opcoes(self):
        return [
            ('Listar todas as publicações', self._listar),
            ('Publicar oportunidade (qualquer categoria)', self._publicar),
            ('Ver interessados em uma publicação', self._interessados),
            ('Encerrar publicação', self._encerrar),
            ('Remover publicação', self._remover),
            ('Listar entidades fixas', self._listar_entidades),
            ('Cadastrar entidade fixa', self._cadastrar_entidade),
        ]

    def _listar(self):
        self._mostrar(
            ops.listar_todas(self._conta),
            'Nenhuma oportunidade cadastrada.'
        )

    def _listar_entidades(self):
        self._mostrar_entidades(ops.listar_entidades_fixas(self._conta))

    def _cadastrar_entidade(self):
        tipos = tuple(ops.tipos_entidades_fixas)

        print('\nTipo de entidade:')
        for numero, chave in enumerate(tipos, start=1):
            print(f'{numero} - {ops.tipos_entidades_fixas[chave]}')

        escolha = input('Número do tipo: ').strip()

        if not escolha.isdigit() or not 1 <= int(escolha) <= len(tipos):
            raise ValueError('Tipo inválido.')

        nome = input('Nome: ')
        link = input('Link do Instagram: ')

        ops.cadastrar_entidade_fixa(self._conta, nome, tipos[int(escolha) - 1], link)
        print('Entidade cadastrada!')

    def _remover(self):
        id_oportunidade = self._ler_id()

        if input('Remover DEFINITIVAMENTE (e os interesses ligados a ela)? (s/n): ').strip().lower() != 's':
            print('Operação cancelada.')
            return

        ops.remover(self._conta, id_oportunidade)
        print('Publicação removida.')

# ============================= { PÁGINA DO CARDÁPIO } ============================= #
 
class PaginaCardapio(PaginaPerfil):
 
    exige_login = False         
 
    def __init__(self, sessao):
        super().__init__(sessao)
        self._dieta = 'padrao'      # preferência valida só enquanto este menu estiver aberto
 
    @property
    def titulo(self):
        return 'CARDÁPIO DO RU - GAMA'
 
    @property
    def _eh_admin(self):
        return getattr(self._conta, 'eh_admin', False)
 
    def _opcoes(self):
        opcoes = [
            ('Cardápio de hoje', self._hoje),
            ('Escolher outro dia', self._escolher_dia),
            (f'Alterar preferência alimentar (atual: {cp.dietas[self._dieta]})', self._escolher_dieta),
        ]
 
        if self._eh_admin:
            opcoes.append(('Atualizar cardápio a partir do site do RU', self._atualizar))
 
        return opcoes
 
    def _hoje(self):
        self._mostrar_dia(date.today().isoformat())
 
    def _escolher_dia(self):
        datas = cp.datas_disponiveis()
 
        if not datas:
            print('Nenhum cardápio carregado ainda. Peça a um admin para atualizá-lo.')
            return
 
        dia = self._escolher('Dias disponíveis:', {
            data: f'{self._data_br(data)} ({cp.nome_dia_semana(data)})' for data in datas
        })
 
        self._mostrar_dia(dia)
 
    def _escolher_dieta(self):
        self._dieta = self._escolher('Preferência alimentar:', cp.dietas)
        print(f'Preferência alterada para: {cp.dietas[self._dieta]}.')
 
    def _mostrar_dia(self, data_iso):
        refeicoes = cp.cardapio_do_dia(data_iso)
        datas = cp.datas_disponiveis()
 
        if not refeicoes:
            if not datas:
                print('Nenhum cardápio carregado ainda. Peça a um admin para atualizá-lo.')
            else:
                print(
                    f'Não há cardápio para {self._data_br(data_iso)}. '
                    f'Disponível de {self._data_br(datas[0])} a {self._data_br(datas[-1])}.'
                )
 
            return
 
        print(
            f'\n=== {cp.nome_dia_semana(data_iso).capitalize()}, '
            f'{self._data_br(data_iso)} | Preferência: {cp.dietas[self._dieta]} ==='
        )
 
        for chave, itens in refeicoes.items():
            print(f'\n-- {cp.refeicoes[chave]} --')
 
            for rotulo, texto in cp.formatar_refeicao(itens, self._dieta):
                print(f'{rotulo}: {texto}')
 
        if datas[-1] < date.today().isoformat():
            print(
                '\nAviso: este cardápio está desatualizado '
                f'(o mais recente é de {self._data_br(datas[-1])}).'
            )
 
    def _atualizar(self):
        if self._confirmar('Baixar o cardápio do site do RU agora?'):
            total = cp.atualizar_cardapio_ru(self._conta)
            print(f'Cardápio atualizado ({total} refeições carregadas).')
 
    @staticmethod
    def _data_br(data_iso):
        ano, mes, dia = data_iso.split('-')
        return f'{dia}/{mes}/{ano}'
 
 
# ============================= { PÁGINA DAS TURMAS } ============================= #
 
class PaginaTurmas(PaginaPerfil):
 
    exige_login = False         # [NEW] também aparece no portal público (sem login)
 
    def __init__(self, sessao):
        super().__init__(sessao)
        self._sistema = SistemaFCTE()      
 
    @property
    def titulo(self):
        return 'TURMAS DO SIGAA - FGA'
 
    @property
    def _eh_admin(self):
        return getattr(self._conta, 'eh_admin', False)
 
    @property
    def _eh_docente(self):
        return getattr(self._perfil, 'tipo_usuario', None) == 'docente'
 
    def _opcoes(self):
        opcoes = [
            ('Buscar turmas (disciplina, código ou docente)', self._buscar),
            ('Listar todas as turmas do semestre atual', self._listar_todas),
        ]
 
        if self._eh_docente:
            opcoes.append(('Minhas turmas', self._minhas))
 
        if self._eh_admin:
            opcoes.append(('Atualizar turmas a partir do SIGAA', self._atualizar))
 
        return opcoes
 
    @staticmethod
    def _ler_periodo():
        valor = input('Período (AAAA.S, Enter para o semestre atual): ').strip()
 
        if not valor:
            return None, None
 
        correspondencia = re.fullmatch(r'(\d{4})\.([12])', valor)
 
        if not correspondencia:
            raise ValueError('Período inválido. Use o formato AAAA.S (ex.: 2026.2).')
 
        return int(correspondencia.group(1)), int(correspondencia.group(2))
 
    def _buscar(self):
        filtro = input('Buscar por: ').strip()
 
        if not filtro:
            raise ValueError('Digite ao menos uma palavra para buscar.')
 
        ano, semestre = self._ler_periodo()
        self._mostrar_turmas(filtro, ano, semestre)
 
    def _listar_todas(self):
        self._mostrar_turmas(None, None, None)
 
    def _minhas(self):
        self._mostrar_turmas(self._perfil.nome, None, None, vazio=(
            'Não encontrei turmas com o seu nome neste semestre. '
            'Se o seu nome no SIGAA for diferente, use "Buscar turmas".'
        ))
 
    def _mostrar_turmas(self, filtro, ano, semestre, vazio=None):
        turmas = self._sistema.listar_turmas(ano, semestre, filtro)
 
        if not turmas:
            print(vazio or (
                'Nenhuma turma encontrada. Se os dados ainda não foram carregados, '
                'peça a um admin para atualizá-los.'
            ))
            return
 
        limite = SistemaFCTE.limite_turmas
 
        print(f'\n{len(turmas)} turma(s) encontrada(s):\n')
 
        for turma in turmas[:limite]:
            print(self._sistema.formatar_turma(turma))
            print()
 
        if len(turmas) > limite:
            print(f'(Mostrando {limite} de {len(turmas)}. Refine a busca para ver as demais.)')
 
    def _atualizar(self):
        ano, semestre = self._ler_periodo()
 
        if self._confirmar('Consultar o SIGAA agora?'):
            total = self._sistema.atualizar_turmas_sigaa(self._conta, ano, semestre)
            print(f'Turmas atualizadas ({total} turmas gravadas).')


# ============================= { FÁBRICA } ============================= #

paginas_por_tipo = {
    'discente': PaginaDiscente,
    'docente': PaginaDocente,
    'admin': PaginaAdmin,
}


def criar_pagina(sessao):
    # Devolve a página do tipo de usuário logado.
    if not sessao.autenticada:
        raise ValueError('Nenhum usuário conectado.')

    tipo = sessao.usuario.tipo_usuario

    if tipo not in paginas_por_tipo:
        raise ValueError('Este tipo de usuário não possui página de oportunidades.')

    return paginas_por_tipo[tipo](sessao)