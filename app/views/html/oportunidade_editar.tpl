<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Oportunidade - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Editar Oportunidade #{{oportunidade.id}}</h2>
            <p>Categoria: {{oportunidade.nome_categoria}}</p>
        </section>

        <section class="bloco">
            <form action="/oportunidades/{{oportunidade.id}}/editar" method="post" class="grade-form">
                <div>
                    <label for="titulo">Título</label>
                    <input id="titulo" name="titulo" type="text" value="{{oportunidade.titulo}}" maxlength="100" required>
                </div>
                <div>
                    <label for="contato">Contato</label>
                    <input id="contato" name="contato" type="text" value="{{oportunidade.contato}}" maxlength="150" required>
                </div>
                <div>
                    <label for="prazo">Prazo (deixe vazio para remover)</label>
                    <input id="prazo" name="prazo" type="date" value="{{oportunidade.prazo.isoformat() if oportunidade.prazo else ''}}">
                </div>
                <div class="largura-total">
                    <label for="descricao">Descrição</label>
                    <textarea id="descricao" name="descricao" maxlength="1000" required>{{oportunidade.descricao}}</textarea>
                </div>
                <div class="largura-total acoes-linha">
                    <button type="submit" class="btn-destaque">Salvar alterações</button>
                    <a href="/oportunidades" class="btn btn-secundario">Cancelar</a>
                </div>
            </form>
        </section>
    </main>
</body>
</html>
