<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Usuário - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Editar Perfil — {{alvo.nome}}</h2>
            <p>{{alvo.tipo_usuario.capitalize()}} &middot; Matrícula {{alvo.id_user}} &middot; {{alvo.email}}</p>
        </section>

        <section class="bloco">
            <form action="/usuarios/editar" method="post" class="grade-form">
                <input type="hidden" name="email" value="{{alvo.email}}">
                <div>
                    <label for="nome">Nome completo</label>
                    <input id="nome" name="nome" type="text" value="{{alvo.nome}}" required>
                </div>
                <div>
                    <label for="curso_ou_area">{{'Curso' if alvo.tipo_usuario == 'discente' else 'Área de atuação'}}</label>
                    <select id="curso_ou_area" name="curso_ou_area" required>
                        % for c in cursos:
                        <option value="{{c}}" {{'selected' if c == alvo.curso_ou_area else ''}}>{{c}}</option>
                        % end
                    </select>
                </div>
                <div class="largura-total acoes-linha">
                    <button type="submit" class="btn-destaque">Salvar alterações</button>
                    <a href="/usuarios" class="btn btn-secundario">Cancelar</a>
                </div>
            </form>
        </section>
    </main>
</body>
</html>
