<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css">
</head>
<body class="pagina-login">
    <main class="cartao">
        <img class="logo-login" src="/static/img/logo_unb.svg" alt="Logo da UnB">
        <h1>Plataforma UnB FCTE</h1>
        <p class="sub">Campus Gama — Acesso ao Portal</p>

        % if defined('erro') and erro:
            <div class="alerta-erro" role="alert">E-mail ou senha incorretos.</div>
        % end

        <form action="/login" method="post">
            <label for="email">E-mail</label>
            <input id="email" name="email" type="email" placeholder="seu.email@unb.br" required>

            <label for="senha">Senha</label>
            <input id="senha" name="senha" type="password" placeholder="Mínimo de 8 caracteres" minlength="8" required>

            <button type="submit">Entrar</button>
        </form>
    </main>
</body>
</html>
