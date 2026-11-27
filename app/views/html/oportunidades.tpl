<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oportunidades - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Mural de Oportunidades</h2>
            <p>Projetos de extensão, pesquisa científica, estágios e monitorias da FCTE.</p>
        </section>

        % if pode_gerenciar:
        <section class="bloco">
            <h3>Publicar Nova Oportunidade</h3>
            <form action="/oportunidades/novo" method="post" class="grade-form" data-async-form="criar">
                <div>
                    <label for="titulo">Título</label>
                    <input id="titulo" name="titulo" type="text" maxlength="100" required>
                </div>
                <div>
                    <label for="categoria">Categoria</label>
                    <select id="categoria" name="categoria" required>
                        % for chave, rotulo in categorias.items():
                        <option value="{{chave}}">{{rotulo}}</option>
                        % end
                    </select>
                </div>
                <div>
                    <label for="contato">Contato (e-mail ou sala)</label>
                    <input id="contato" name="contato" type="text" maxlength="150" required>
                </div>
                <div>
                    <label for="prazo">Prazo (opcional)</label>
                    <input id="prazo" name="prazo" type="date">
                </div>
                <div class="largura-total">
                    <label for="descricao">Descrição</label>
                    <textarea id="descricao" name="descricao" maxlength="1000" required></textarea>
                </div>
                <div class="largura-total">
                    <button type="submit" class="btn-destaque">Publicar Oportunidade</button>
                </div>
            </form>
        </section>
        % end

        <div id="conteudo-tempo-real" data-canal="oportunidades">
        % if interessados_lista is not None and oportunidade_foco is not None:
        <section class="bloco">
            <h3>Interessados em #{{oportunidade_foco.id}} — {{oportunidade_foco.titulo}} ({{len(interessados_lista)}})</h3>
            % if interessados_lista:
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Matrícula</th>
                            <th>Curso</th>
                            <th>E-mail</th>
                            <th>Registrado em</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for aluno in interessados_lista:
                        <tr>
                            <td>{{aluno['nome']}}</td>
                            <td><code>{{aluno['matricula']}}</code></td>
                            <td>{{aluno['curso']}}</td>
                            <td>{{aluno['email']}}</td>
                            <td>{{data_br(aluno['criado_em'])}}</td>
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
            % else:
            <p class="texto-suave">Nenhum discente demonstrou interesse ainda.</p>
            % end
            <div style="margin-top: 10px;">
                <a href="/oportunidades" class="btn btn-secundario btn-pequeno">Fechar lista de interessados</a>
            </div>
        </section>
        % end

        <section class="bloco">
            <h3>{{'Publicações Cadastradas' if pode_gerenciar else 'Oportunidades Abertas'}}</h3>
            <form action="/oportunidades" method="get" class="barra-filtro">
                <div class="campo-filtro">
                    <label for="filtro_cat">Filtrar por categoria</label>
                    <select id="filtro_cat" name="categoria">
                        <option value="">Todas as categorias</option>
                        % for chave, rotulo in categorias.items():
                        <option value="{{chave}}" {{'selected' if chave == categoria_atual else ''}}>{{rotulo}}</option>
                        % end
                    </select>
                </div>
                <button type="submit">Filtrar</button>
                % if categoria_atual:
                <a href="/oportunidades" class="btn btn-secundario">Limpar</a>
                % end
            </form>

            % if oportunidades:
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Título / Descrição</th>
                            <th>Categoria</th>
                            <th>Autor / Contato</th>
                            <th>Prazo</th>
                            <th>Situação</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for o in oportunidades:
                        <tr>
                            <td><code>#{{o.id}}</code></td>
                            <td>
                                <strong>{{o.titulo}}</strong><br>
                                <span class="texto-suave">{{o.descricao}}</span>
                            </td>
                            <td>{{o.nome_categoria}}</td>
                            <td>
                                {{o.autor_nome}}<br>
                                <span class="texto-suave">{{o.contato}}</span>
                            </td>
                            <td>{{data_br(o.prazo) if o.prazo else 'Sem prazo'}}</td>
                            <td>
                                % if o.encerrada:
                                <span class="badge-status badge-encerrada">Encerrada</span>
                                % else:
                                <span class="badge-status badge-aberta">Aberta</span>
                                % end
                                % if pode_gerenciar:
                                <br><span class="texto-suave">{{contagens.get(o.id, 0)}} interessado(s)</span>
                                % end
                            </td>
                            <td>
                                <div class="acoes-linha">
                                    % if pode_gerenciar:
                                        <a href="/oportunidades?interessados={{o.id}}" class="btn btn-secundario btn-pequeno">Interessados</a>
                                        % if not o.encerrada:
                                        <a href="/oportunidades/{{o.id}}/editar" class="btn btn-pequeno">Editar</a>
                                        <form action="/oportunidades/{{o.id}}/encerrar" method="post">
                                            <button type="submit" class="btn-secundario btn-pequeno">Encerrar</button>
                                        </form>
                                        % end
                                        <form action="/oportunidades/{{o.id}}/excluir" method="post" onsubmit="return confirm('Remover esta oportunidade definitivamente?');">
                                            <button type="submit" class="btn-perigo btn-pequeno">Excluir</button>
                                        </form>
                                    % else:
                                        % if o.id in ids_meus_interesses:
                                        <form action="/oportunidades/{{o.id}}/retirar-interesse" method="post">
                                            <button type="submit" class="btn-perigo btn-pequeno">Retirar interesse</button>
                                        </form>
                                        % else:
                                        <form action="/oportunidades/{{o.id}}/interesse" method="post">
                                            <button type="submit" class="btn-destaque btn-pequeno">Tenho interesse</button>
                                        </form>
                                        % end
                                    % end
                                </div>
                            </td>
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
            % else:
            <p class="texto-suave">Nenhuma oportunidade encontrada.</p>
            % end
        </section>

        % if usuario['tipo_usuario'] == 'discente':
        <section class="bloco">
            <h3>Meus Interesses ({{len(meus_interesses)}})</h3>
            % if meus_interesses:
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Título</th>
                            <th>Categoria</th>
                            <th>Contato</th>
                            <th>Situação</th>
                            <th>Ação</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for o in meus_interesses:
                        <tr>
                            <td><code>#{{o.id}}</code></td>
                            <td><strong>{{o.titulo}}</strong></td>
                            <td>{{o.nome_categoria}}</td>
                            <td>{{o.contato}}</td>
                            <td>{{'Encerrada' if o.encerrada else 'Aberta'}}</td>
                            <td>
                                <form action="/oportunidades/{{o.id}}/retirar-interesse" method="post">
                                    <button type="submit" class="btn-perigo btn-pequeno">Retirar</button>
                                </form>
                            </td>
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
            % else:
            <p class="texto-suave">Você ainda não demonstrou interesse em nenhuma oportunidade.</p>
            % end
        </section>
        % end
        </div>
    </main>
</body>
</html>
