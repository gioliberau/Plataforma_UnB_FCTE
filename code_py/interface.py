from .banco import autenticar_usuario
from .session import Sessao
from .banco import cadastrar_usuario


# ============================= { INTERFACE DO SISTEMA } ============================= #

class InterfaceFCTE:

    def __init__(self):
        self.__sessao = Sessao()

    def executar(self):
        
        while True:
            print('\n===== PORTAL DISCENTE - UNB FCTE =====')
            print('1 - Fazer login')
            print('2 - Criar conta')
            print('3 - Acessar portal público')
            print('3 - Sair')

            opcao = input('Escolha uma opção: ').strip()

            if opcao == '1':
                self.__fazer_login()
            
            elif opcao == '2':
                self.__criar_conta()
            
            elif opcao == '3':
                self.__portal_publico()

            elif opcao == '3':
                print('Encerrando o sistema...')
                break

            else:
                print('Opção inválida. Tente novamente.')


    def __fazer_login(self):

        # Solicita as credenciais do usuário.
        email = input('E-mail: ').strip()
        senha = input('Senha: ')

        # Verifica as credenciais no banco de dados.
        usuario = autenticar_usuario(email, senha)

        if usuario is None:
            print('E-mail ou senha incorretos.')
            return

        # Inicia a sessão com o usuário autenticado.
        self.__sessao.iniciar(usuario)

        print(f'\nBem-vindo(a), {usuario.nome}!')

        # Direciona o usuário para o menu correspondente ao seu tipo.
        self.__abrir_menu_usuario()


    def __criar_conta(self):
        print('\n===== CRIAR CONTA =====')
        print('1 - Discente')
        print('2 - Docente')

        tipo = input('Tipo de usuário: ').strip()

        if tipo not in ('1', '2'):
            print('Tipo de usuário inválido.')
            return

        nome = input('Nome completo: ').strip()
        cpf = input('CPF: ').strip()
        email = input('E-mail: ').strip()
        senha = input('Senha: ')

        if not nome or not cpf or not email or not senha:
            print('Todos os campos são obrigatórios.')
            return

        try:
            ano = int(input('Ano de entrada: '))
            semestre = int(input('Semestre de entrada (1 ou 2): '))

            if tipo == '1':
                curso = input('Curso: ').strip()

                if not curso:
                    print('O curso é obrigatório.')
                    return

                usuario = Discente(
                    ano,
                    semestre,
                    nome,
                    cpf,
                    email,
                    senha,
                    curso
                )

            else:
                area = input('Área de atuação: ').strip()

                if not area:
                    print('A área de atuação é obrigatória.')
                    return

                usuario = Docente(
                    ano,
                    semestre,
                    nome,
                    cpf,
                    email,
                    senha,
                    area
                )

            cadastrar_usuario(usuario)

            print('\nConta criada com sucesso!')
            print(f'Identificador: {usuario.id_user}')
            print('Agora você já pode fazer login.')

        except ValueError as erro:
            print(f'Não foi possível criar a conta: {erro}')

        except sqlite3.IntegrityError:
            print('Não foi possível criar a conta.')
            print('O e-mail, CPF ou identificador já está cadastrado.')


    def __portal_publico(self):
        # Exibe informações que não exigem autenticação.
        while True:
            print('\n========== PORTAL PÚBLICO ==========')
            print('1 - Consultar cursos')
            print('2 - Consultar organizações estudantis')
            print('3 - Consultar calendário acadêmico')
            print('4 - Voltar ao menu principal')

            opcao = input('Escolha uma opção: ').strip()

            if opcao == '1':
                print('Consulta de cursos em desenvolvimento.')
            elif opcao == '2':
                print('Consulta de organizações em desenvolvimento.')
            elif opcao == '3':
                print('Consulta de calendário em desenvolvimento.')
            elif opcao == '4':
                break
            else:
                print('Opção inválida. Tente novamente.')


    def __abrir_menu_usuario(self):
        usuario = self.__sessao.usuario

        print('\n===== MENU DO USUÁRIO =====')
        print(f'Nome: {usuario.nome}')
        print(f'Tipo: {usuario.tipo_usuario}')
        print('0 - Sair da conta')

        while self.__sessao.autenticada:
            opcao = input('Escolha uma opção: ').strip()

            if opcao == '0':
                self.__sessao.encerrar()
                print('Logout realizado com sucesso!')
            else:
                print('Opção inválida. Tente novamente.')
