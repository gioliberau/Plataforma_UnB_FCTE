from getpass import getpass     # Lê a senha no terminal sem exibi-la.

from .login import autenticar, trocar_senha, gerar_acesso, tipos_usuario
from .session import Sessao


# ============================= { INTERFACE DO SISTEMA } ============================= #

class InterfaceFCTE:

    def __init__(self):
        self.__sessao = Sessao()

    def executar(self):
        
        while True:
            print('\n===== PORTAL DISCENTE - UNB FCTE =====')
            print('1 - Fazer login')
            print('2 - Acessar portal público')
            print('3 - Sair')

            opcao = input('Escolha uma opção: ').strip()

            if opcao == '1':
                self.__fazer_login()

            elif opcao == '2':
                self.__portal_publico()

            elif opcao == '3':
                print('Encerrando o sistema...')
                break

            else:
                print('Opção inválida. Tente novamente.')


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

        # Inicia a sessão com o usuário autenticado.
        self.__sessao.iniciar(conta)

        print(f'\nBem-vindo(a), {conta.email}!')

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
        conta = self.__sessao.usuario

        while self.__sessao.autenticada:
            print('\n===== MENU DO USUÁRIO =====')
            print(f'E-mail: {conta.email}')
            print(f'Tipo: {conta.tipo_usuario}')

            if conta.eh_admin:
                print('1 - Gerar acesso para um e-mail')

            print('0 - Sair da conta')

            opcao = input('Escolha uma opção: ').strip()

            if opcao == '0':
                self.__sessao.encerrar()
                print('Logout realizado com sucesso!')
            elif opcao == '1' and conta.eh_admin:
                self.__gerar_acesso()
            else:
                print('Opção inválida. Tente novamente.')


if __name__ == '__main__':
    InterfaceFCTE().executar()
