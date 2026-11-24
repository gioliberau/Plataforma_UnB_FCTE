<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Livro - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Editar Livro #{{livro.id}}</h2>
            <p>Disponíveis atualmente: {{livro.disponiveis}} de {{livro.exemplares}} exemplar(es).</p>
        </section>

        <section class="bloco">
            <form action="/biblioteca/{{livro.id}}/editar" method="post" class="grade-form">
                <div>
                    <label for="titulo">Título</label>
                    <input id="titulo" name="titulo" type="text" value="{{livro.titulo}}" required>
                </div>
                <div>
                    <label for="autores">Autor(es)</label>
                    <input id="autores" name="autores" type="text" value="{{livro.autores}}" required>
                </div>
                <div>
                    <label for="area">Área</label>
                    <input id="area" name="area" type="text" value="{{livro.area}}" required>
                </div>
                <div>
                    <label for="exemplares">Exemplares</label>
                    <input id="exemplares" name="exemplares" type="number" min="1" value="{{livro.exemplares}}" required>
                </div>
                <div class="largura-total acoes-linha">
                    <button type="submit" class="btn-destaque">Salvar alterações</button>
                    <a href="/biblioteca" class="btn btn-secundario">Cancelar</a>
                </div>
            </form>
        </section>
    </main>
</body>
</html>
