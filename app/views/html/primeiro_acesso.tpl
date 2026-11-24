<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Primeiro Acesso - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-login">
    <main class="cartao">
        <img class="logo-login" src="/static/img/logo_unb.svg" alt="Logo da UnB">
        <h1>Primeiro Acesso</h1>
        <p class="sub">Conta: {{email}} — Escolha uma nova senha para continuar.</p>

        % if defined('flash') and flash:
            <div class="{{'alerta-sucesso' if flash['tipo'] == 'sucesso' else 'alerta-erro'}}" role="alert">{{flash['texto']}}</div>
        % end

        <form action="/primeiro-acesso" method="post">
            <label for="nova_senha">Nova senha (mínimo 8 caracteres)</label>
            <input id="nova_senha" name="nova_senha" type="password" minlength="8" required>

            <label for="confirmacao">Confirme a nova senha</label>
            <input id="confirmacao" name="confirmacao" type="password" minlength="8" required>

            <button type="submit" class="bloco-btn btn-destaque">Salvar nova senha</button>
        </form>

        <form action="/logout" method="post" style="margin-top: 10px;">
            <button type="submit" class="bloco-btn btn-secundario">Cancelar e voltar ao login</button>
        </form>
    </main>
</body>
</html>
