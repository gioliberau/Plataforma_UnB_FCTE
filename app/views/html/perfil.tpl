<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meu Perfil - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Meu Perfil</h2>
            <p>Atualize seus dados cadastrais e gerencie a senha da sua conta.</p>
        </section>

        <div class="grade-principal">
            % if perfil is not None:
            <section class="bloco">
                <h3>Editar Dados Cadastrais</h3>
                <form action="/perfil/editar" method="post">
                    <label for="nome">Nome completo</label>
                    <input id="nome" name="nome" type="text" value="{{perfil.nome}}" required>

                    <label for="curso_ou_area">{{'Curso' if perfil.tipo_usuario == 'discente' else 'Área de atuação'}}</label>
                    <select id="curso_ou_area" name="curso_ou_area" required>
                        % for c in cursos:
                        <option value="{{c}}" {{'selected' if c == perfil.curso_ou_area else ''}}>{{c}}</option>
                        % end
                    </select>

                    <p class="texto-suave">
                        Matrícula: <strong>{{perfil.id_user}}</strong> &middot;
                        E-mail: <strong>{{perfil.email}}</strong> &middot;
                        CPF: <strong>{{perfil.cpf or '—'}}</strong>
                    </p>

                    <button type="submit" class="btn-destaque">Salvar alterações</button>
                </form>
            </section>
            % else:
            <section class="bloco">
                <h3>Conta de Administrador</h3>
                <p class="texto-suave">
                    E-mail: <strong>{{usuario['email']}}</strong><br>
                    Administradores não possuem matrícula acadêmica, mas podem alterar sua senha ao lado e gerenciar todos os perfis em <a href="/usuarios">Usuários</a>.
                </p>
            </section>
            % end

            <section class="bloco">
                <h3>Alterar Senha</h3>
                <form action="/perfil/senha" method="post">
                    <label for="senha_atual">Senha atual</label>
                    <input id="senha_atual" name="senha_atual" type="password" required>

                    <label for="nova_senha">Nova senha (mínimo 8 caracteres)</label>
                    <input id="nova_senha" name="nova_senha" type="password" minlength="8" required>

                    <label for="confirmacao">Confirme a nova senha</label>
                    <input id="confirmacao" name="confirmacao" type="password" minlength="8" required>

                    <button type="submit">Atualizar senha</button>
                </form>
            </section>
        </div>
    </main>
</body>
</html>
