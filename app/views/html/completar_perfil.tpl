<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Completar Cadastro - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-login">
    <main class="cartao">
        <img class="logo-login" src="/static/img/logo_unb.svg" alt="Logo da UnB">
        <h1>Completar Cadastro</h1>
        <p class="sub">{{conta.tipo_usuario.capitalize()}} — {{conta.email}}</p>

        % if defined('flash') and flash:
            <div class="{{'alerta-sucesso' if flash['tipo'] == 'sucesso' else 'alerta-erro'}}" role="alert">{{flash['texto']}}</div>
        % end

        <form action="/completar-perfil" method="post">
            <label for="nome">Nome completo</label>
            <input id="nome" name="nome" type="text" required>

            <label for="cpf">CPF (11 dígitos, somente números)</label>
            <input id="cpf" name="cpf" type="text" required>

            <div class="grade-form">
                <div>
                    <label for="ano_entrada">Ano de entrada</label>
                    <input id="ano_entrada" name="ano_entrada" type="number" value="{{ano_padrao}}" required>
                </div>
                <div>
                    <label for="semestre_entrada">Semestre</label>
                    <select id="semestre_entrada" name="semestre_entrada" required>
                        <option value="1" {{'selected' if sem_padrao == 1 else ''}}>1</option>
                        <option value="2" {{'selected' if sem_padrao == 2 else ''}}>2</option>
                    </select>
                </div>
            </div>

            <label for="curso_ou_area">{{'Curso' if conta.tipo_usuario == 'discente' else 'Área de atuação'}}</label>
            <select id="curso_ou_area" name="curso_ou_area" required>
                % for c in cursos:
                <option value="{{c}}">{{c}}</option>
                % end
            </select>

            <button type="submit" class="bloco-btn btn-destaque">Concluir cadastro</button>
        </form>

        <form action="/logout" method="post" style="margin-top: 10px;">
            <button type="submit" class="bloco-btn btn-secundario">Sair</button>
        </form>
    </main>
</body>
</html>
