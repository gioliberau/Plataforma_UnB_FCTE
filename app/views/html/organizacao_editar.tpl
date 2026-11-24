<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Organização - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Editar Organização — {{entidade['nome']}}</h2>
            <p>Atualize as informações exibidas no catálogo do campus.</p>
        </section>

        <section class="bloco">
            <form action="/organizacoes/{{entidade['id']}}/editar" method="post" class="grade-form">
                <div>
                    <label for="nome">Nome</label>
                    <input id="nome" name="nome" type="text" value="{{entidade['nome']}}" required>
                </div>
                <div>
                    <label for="tipo">Tipo</label>
                    <select id="tipo" name="tipo" required>
                        % for chave, rotulo in tipos.items():
                        <option value="{{chave}}" {{'selected' if chave == entidade['tipo'] else ''}}>{{rotulo}}</option>
                        % end
                    </select>
                </div>
                <div>
                    <label for="instagram_link">Link do Instagram</label>
                    <input id="instagram_link" name="instagram_link" type="url" value="{{entidade['instagram_link']}}" required>
                </div>
                <div>
                    <label for="area">Área / Curso (opcional)</label>
                    <input id="area" name="area" type="text" value="{{entidade.get('area') or ''}}">
                </div>
                <div>
                    <label for="contato">Contato (opcional)</label>
                    <input id="contato" name="contato" type="text" value="{{entidade.get('contato') or ''}}">
                </div>
                <div>
                    <label for="como_participar">Como participar (opcional)</label>
                    <input id="como_participar" name="como_participar" type="text" value="{{entidade.get('como_participar') or ''}}">
                </div>
                <div class="largura-total">
                    <label for="descricao">Descrição (opcional)</label>
                    <textarea id="descricao" name="descricao">{{entidade.get('descricao') or ''}}</textarea>
                </div>
                <div class="largura-total acoes-linha">
                    <button type="submit" class="btn-destaque">Salvar alterações</button>
                    <a href="/organizacoes" class="btn btn-secundario">Cancelar</a>
                </div>
            </form>
        </section>
    </main>
</body>
</html>
