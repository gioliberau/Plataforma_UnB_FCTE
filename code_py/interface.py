from datetime import datetime
from getpass import getpass     # Lê a senha no terminal sem exibi-la.

from .login import autenticar, trocar_senha, gerar_acesso, tipos_usuario, Sessao
from .banco import buscar_perfil, cadastrar_perfil
from .user import cursos_disponiveis
from .paginas import abrir_menu, criar_pagina, PaginaCardapio, PaginaTurmas
from .biblioteca import PaginaBiblioteca          
from . import consultas_publicas as cp
from .tela import limpar_tela, pausar, linha, formatar_data_hora, formatar_duracao


# ============================= { INTERFACE DO SISTEMA } ============================= #

class InterfaceFCTE:

    def __init__(self):
        self.__sessao = Sessao()

    def executar(self):
        abrir_menu(
            'PORTAL DISCENTE - UNB FCTE',
            lambda: [
                ('Fazer login', self.__fazer_login),
                ('Acessar portal público', self.__portal_publico),
            ],
            saida='Sair',
            cabecalho=self.__boas_vindas
        )
 
        print('Encerrando o sistema...')

    @staticmethod
    def __boas_vindas():
        print('  Bem-vindo(a) ao Portal Discente da UnB FCTE!')
        print(f'  Hoje: {formatar_data_hora(datetime.now())}')



    def __fazer_login(self):

        # Solicita as credenciais do usuário.
        email = input('E-mail: ').strip()
        senha = getpass('Senha: ')

        # Verifica as credenciais no banco de dados.
        conta = autenticar(email, senha)

        if conta is None:
            print('E-mail ou senha incorretos.')
            return

        # No primeiro acesso, a senha inicial (gerada pelo admin) precisa ser trocada.
        if conta.precisa_trocar_senha:
            conta = self.__trocar_senha_inicial(email, senha)

            if conta is None:
                return

        # Discentes e docentes precisam de perfil (nome, matrícula, curso/área) para entrar.
        perfil = None

        if not conta.eh_admin:
            perfil = buscar_perfil(conta.email) or self.__completar_perfil(conta)

            if perfil is None:
                return

        # Inicia a sessão com o usuário autenticado.
        self.__sessao.iniciar(conta, perfil)

        # Direciona o usuário para o menu correspondente ao seu tipo.
        self.__abrir_menu_usuario()


    def __trocar_senha_inicial(self, email, senha_atual):
        print('\nPrimeiro acesso: escolha uma nova senha (mínimo 8 caracteres).')

        nova_senha = getpass('Nova senha: ')

        if nova_senha != getpass('Confirme a nova senha: '):
            print('As senhas não conferem.')
            return None

        try:
            conta = trocar_senha(email, senha_atual, nova_senha)
        except ValueError as erro:
            print(f'Não foi possível trocar a senha: {erro}')
            return None

        print('Senha alterada com sucesso!')
        return conta


    def __completar_perfil(self, conta):
        print('\nComplete seu cadastro para continuar.')

        nome = input('Nome completo: ').strip()
        cpf = input('CPF (somente números): ').strip()

        rotulo = 'Curso' if conta.tipo_usuario == 'discente' else 'Área de atuação'
        print(f'{rotulo}:')

        for numero, curso in enumerate(cursos_disponiveis, start=1):
            print(f'{numero} - {curso}')

        try:
            ano = int(input('Ano de entrada: '))
            semestre = int(input('Semestre de entrada (1 ou 2): '))
            escolha = int(input(f'Número do(a) {rotulo.lower()}: '))

            if not 1 <= escolha <= len(cursos_disponiveis):
                raise ValueError(f'{rotulo} inválido(a).')

            perfil = cadastrar_perfil(
                conta, nome, cpf, ano, semestre,
                cursos_disponiveis[escolha - 1]
            )

        except ValueError as erro:
            print(f'Não foi possível salvar o cadastro: {erro}')
            print('Faça login novamente para tentar outra vez.')
            return None

        print(f'Cadastro concluído! Sua matrícula é {perfil.id_user}.')
        return perfil


    def __gerar_acesso(self):
        # Admin libera um e-mail e recebe a senha inicial para repassar.
        email = input('E-mail do usuário: ').strip()
        tipo = input(f'Tipo ({"/".join(tipos_usuario)}): ').strip().lower()

        try:
            senha_inicial = gerar_acesso(self.__sessao.usuario, email, tipo)
        except (ValueError, PermissionError) as erro:
            print(f'Não foi possível gerar o acesso: {erro}')
            return

        print(f'Acesso criado. Senha inicial de {email}: {senha_inicial}')
        print('Repasse esta senha ao usuário; ela não será exibida novamente.')


    def __portal_publico(self):
        abrir_menu(
            'PORTAL PÚBLICO',
            lambda: [
                ('Consultar cursos', self.__consultar_cursos),                              
                ('Consultar organizações estudantis', self.__consultar_organizacoes),      
                ('Consultar calendário acadêmico', self.__consultar_calendario), 
                ('Cardápio do RU', lambda: PaginaCardapio(self.__sessao).executar()),
                ('Turmas do SIGAA', lambda: PaginaTurmas(self.__sessao).executar()),
                ('Biblioteca FCTE (consultar acervo)', lambda: PaginaBiblioteca(self.__sessao).executar()),
            ],
            saida='Voltar ao menu principal'
        )
    
    # ========== { Consultas públicas } ========== #
 
    def __consultar_cursos(self):
        print('\nCursos de graduação da FCTE:')
 
        for numero, curso in enumerate(cp.listar_cursos(), start=1):
            print(f'{numero} - {curso}')
 
        print(f'\nMais informações sobre cada curso: {cp.site_fcte}')
 
    def __consultar_organizacoes(self):
        abrir_menu(
            'ORGANIZAÇÕES ESTUDANTIS',
            lambda: [
                (rotulo, lambda tipo=tipo: self.__mostrar_organizacoes(tipo))
                for tipo, rotulo in cp.tipos_organizacoes.items()
            ] + [
                ('Todas', lambda: self.__mostrar_organizacoes(None)),
                ('Buscar por nome ou área', self.__buscar_organizacoes),
            ],
            cabecalho=lambda: print(cp.resumo_organizacoes())
        )
 
    @staticmethod
    def __mostrar_organizacoes(tipo):
        print(cp.formatar_lista_organizacoes(cp.listar_organizacoes(tipo)))
 

    def __atualizar_calendario(self):
        if input('Consultar o site da SAA agora? (s/n): ').strip().lower() != 's':
            print('Operação cancelada.')
            return
 
        total = cp.atualizar_calendario(self.__sessao.usuario)
        print(f'Calendário atualizado ({total} datas lidas).')


    @staticmethod
    def __buscar_organizacoes():                                                
        termo = input('Buscar por nome, área ou tipo: ')
        print()

        print(cp.formatar_lista_organizacoes(cp.buscar_organizacoes(termo)))

    def __consultar_calendario(self):
        periodos = cp.periodos_calendario()
 
        if not periodos:
            print('O calendário ainda não foi carregado.')
            return
 
        abrir_menu(
            'CALENDÁRIO ACADÊMICO',
            lambda: [(f'Período {periodo}', lambda periodo=periodo: self.__mostrar_calendario(periodo))
                     for periodo in periodos]
        )
 
    @staticmethod
    def __mostrar_calendario(periodo):
        print(f'\nPeríodo {periodo}:')
 
        for evento in cp.eventos_do_periodo(periodo):
            print(f'  {cp.formatar_evento(evento)}')
 
        print('\nAs datas podem mudar. Confira em: https://saa.unb.br/calendario-academico-graduacao/')
 
    def __abrir_menu_usuario(self):
        conta = self.__sessao.usuario
        perfil = self.__sessao.perfil
 
        def cabecalho():
            # Boas-vindas + dados da sessão, no topo de toda vez que o menu é desenhado.
            inicio = self.__sessao.iniciada_em

            print(f'  Bem-vindo(a), {perfil.nome if perfil else conta.email}!')
            print(f'  Sessão iniciada em {formatar_data_hora(inicio)}')
            print(f'  Tempo de sessão: {formatar_duracao(inicio)}')
            print(linha('─'))

            if perfil is not None:
                print(f'  Nome: {perfil.nome}')
                print(f'  Matrícula: {perfil.id_user}')
                print(f'  Curso/Área: {perfil.curso_ou_area}')
 
            print(f'  E-mail: {conta.email}')
            print(f'  Tipo: {conta.tipo_usuario}')
 
        def opcoes():
            lista = [
                ('Oportunidades e organizações', lambda: criar_pagina(self.__sessao).executar()),
                ('Cardápio do RU', lambda: PaginaCardapio(self.__sessao).executar()),
                ('Turmas do SIGAA', lambda: PaginaTurmas(self.__sessao).executar()),
            ]
 
            if conta.eh_admin:
                lista.append(('Gerar acesso para um e-mail', self.__gerar_acesso))
 
            return lista
 
        abrir_menu('MENU DO USUÁRIO', opcoes, saida='Sair da conta', cabecalho=cabecalho)
 
        duracao = formatar_duracao(self.__sessao.iniciada_em)
        self.__sessao.encerrar()
        
        limpar_tela()                                              
        print(f'Logout realizado com sucesso! Sessão de {duracao}.')
        pausar()                                                   
 
 
if __name__ == '__main__':
    InterfaceFCTE().executar()