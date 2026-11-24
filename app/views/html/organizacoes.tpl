<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Organizações Estudantis - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Organizações Estudantis — FCTE</h2>
            <p>{{resumo}}</p>
        </section>

        % if usuario['eh_admin']:
        <section class="bloco">
            <h3>Cadastrar Nova Organização</h3>
            <form action="/organizacoes/novo" method="post" class="grade-form">
                <div>
                    <label for="nome">Nome</label>
                    <input id="nome" name="nome" type="text" required>
                </div>
                <div>
                    <label for="tipo">Tipo</label>
                    <select id="tipo" name="tipo" required>
                        % for chave, rotulo in tipos.items():
                        <option value="{{chave}}">{{rotulo}}</option>
                        % end
                    </select>
                </div>
                <div>
                    <label for="instagram_link">Link do Instagram</label>
                    <input id="instagram_link" name="instagram_link" type="url" placeholder="https://instagram.com/..." required>
                </div>
                <div>
                    <label for="area">Área / Curso (opcional)</label>
                    <input id="area" name="area" type="text">
                </div>
                <div>
                    <label for="contato">Contato (opcional)</label>
                    <input id="contato" name="contato" type="text">
                </div>
                <div>
                    <label for="como_participar">Como participar (opcional)</label>
                    <input id="como_participar" name="como_participar" type="text">
                </div>
                <div class="largura-total">
                    <label for="descricao">Descrição (opcional)</label>
                    <textarea id="descricao" name="descricao"></textarea>
                </div>
                <div class="largura-total">
                    <button type="submit" class="btn-destaque">Cadastrar Organização</button>
                </div>
            </form>
        </section>
        % end

        <section class="bloco">
            <h3>Catálogo de Organizações ({{len(entidades)}})</h3>
            <form action="/organizacoes" method="get" class="barra-filtro">
                <div class="campo-filtro">
                    <label for="busca">Buscar por nome, área ou descrição</label>
                    <input id="busca" name="busca" type="text" value="{{busca}}" placeholder="Ex.: robótica, foguetes, software...">
                </div>
                <div class="campo-filtro">
                    <label for="filtro_tipo">Tipo</label>
                    <select id="filtro_tipo" name="tipo">
                        <option value="">Todos os tipos</option>
                        % for chave, rotulo in tipos.items():
                        <option value="{{chave}}" {{'selected' if chave == tipo_atual else ''}}>{{rotulo}}</option>
                        % end
                    </select>
                </div>
                <button type="submit">Filtrar</button>
                % if busca or tipo_atual:
                <a href="/organizacoes" class="btn btn-secundario">Limpar</a>
                % end
            </form>

            % if entidades:
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Tipo</th>
                            <th>Área</th>
                            <th>Sobre / Como participar</th>
                            <th>Instagram</th>
                            % if usuario['eh_admin']:
                            <th>Ações</th>
                            % end
                        </tr>
                    </thead>
                    <tbody>
                        % for e in entidades:
                        <tr>
                            <td><strong>{{e['nome']}}</strong></td>
                            <td>{{tipos.get(e['tipo'], e['tipo'])}}</td>
                            <td>{{e.get('area') or '—'}}</td>
                            <td>
                                {{e.get('descricao') or '—'}}
                                % if e.get('como_participar'):
                                <br><span class="texto-suave">Participar: {{e['como_participar']}}</span>
                                % end
                                % if e.get('contato'):
                                <br><span class="texto-suave">Contato: {{e['contato']}}</span>
                                % end
                            </td>
                            <td><a href="{{e['instagram_link']}}" target="_blank" rel="noopener">Instagram</a></td>
                            % if usuario['eh_admin']:
                            <td>
                                <div class="acoes-linha">
                                    <a href="/organizacoes/{{e['id']}}/editar" class="btn btn-pequeno">Editar</a>
                                    <form action="/organizacoes/{{e['id']}}/excluir" method="post" onsubmit="return confirm('Remover esta organização?');">
                                        <button type="submit" class="btn-perigo btn-pequeno">Excluir</button>
                                    </form>
                                </div>
                            </td>
                            % end
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
            % else:
            <p class="texto-suave">Nenhuma organização encontrada.</p>
            % end
        </section>
    </main>
</body>
</html>
