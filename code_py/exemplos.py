from . import banco, login

# ============================= { USUÁRIOS DE EXEMPLO } ============================= #
# Dados sintéticos para testar o sistema no terminal (python -m code_py.exemplos).
# As senhas são públicas de propósito: não use estes usuários fora dos testes.

admin_exemplo = ('admin@exemplo.unb.br', 'admin12345')

usuarios_exemplo = (
    # (e-mail, senha, tipo, nome, CPF sintético válido, ano, semestre, curso/área)
    ('aluno@exemplo.unb.br', 'aluno12345', 'discente', 'Ana Exemplo',
     '52998224725', 2024, 1, 'Engenharia de Software'),
    ('professor@exemplo.unb.br', 'professor12345', 'docente', 'Paulo Exemplo',
     '11144477735', 2015, 2, 'Engenharia de Software'),
)

# ============================= { CRIAÇÃO } ============================= #

def criar_exemplos():
    # Pode rodar mais de uma vez: o que já existe é mantido.
    admin = login.autenticar(*admin_exemplo)

    if admin is None:
        try:
            admin = login.criar_admin_inicial(*admin_exemplo)
        except PermissionError:
            raise PermissionError(
                'Já existe outro admin; crie os usuários pelo menu com ele.'
            )

    for email, senha, tipo, nome, cpf, ano, semestre, curso in usuarios_exemplo:
        conta = login.autenticar(email, senha)

        if conta is None:
            senha_inicial = login.gerar_acesso(admin, email, tipo)
            conta = login.trocar_senha(email, senha_inicial, senha)

        if banco.buscar_perfil(email) is None:
            banco.cadastrar_perfil(conta, nome, cpf, ano, semestre, curso)


def main():
    try:
        criar_exemplos()
    except (ValueError, PermissionError) as erro:
        print(f'Não foi possível criar os exemplos: {erro}')
        return

    print('Usuários de exemplo prontos:')
    print(f'  admin     {admin_exemplo[0]} / {admin_exemplo[1]}')

    for email, senha, tipo, *_ in usuarios_exemplo:
        perfil = banco.buscar_perfil(email)
        print(f'  {tipo:<9} {email} / {senha} (matrícula {perfil.id_user})')


if __name__ == '__main__':
    main()
