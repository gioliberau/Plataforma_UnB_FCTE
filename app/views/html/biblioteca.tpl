<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Biblioteca FCTE - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Biblioteca FCTE</h2>
            <p>Pesquise o acervo, reserve exemplares, renove empréstimos ou gerencie livros.</p>
        </section>

        % if usuario['eh_admin']:
        <section class="bloco">
            <h3>Cadastrar Novo Livro no Acervo</h3>
            <form action="/biblioteca/novo" method="post" class="grade-form" data-async-form="criar">
                <div>
                    <label for="titulo">Título</label>
                    <input id="titulo" name="titulo" type="text" required>
                </div>
                <div>
                    <label for="autores">Autor(es)</label>
                    <input id="autores" name="autores" type="text" required>
                </div>
                <div>
                    <label for="area">Área</label>
                    <input id="area" name="area" type="text" required>
                </div>
                <div>
                    <label for="exemplares">Exemplares</label>
                    <input id="exemplares" name="exemplares" type="number" min="1" value="1" required>
                </div>
                <div class="largura-total">
                    <button type="submit" class="btn-destaque">Cadastrar Livro</button>
                </div>
            </form>
        </section>
        % end

        <div id="conteudo-tempo-real" data-canal="biblioteca">
        % if tem_perfil:
        <section class="bloco">
            <h3>Meus Empréstimos Ativos ({{len(emprestimos)}})</h3>
            % if emprestimos:
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Livro</th>
                            <th>Retirado em</th>
                            <th>Devolver até</th>
                            <th>Renovações</th>
                            <th>Situação</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for e in emprestimos:
                        <tr>
                            <td><code>#{{e.id}}</code></td>
                            <td><strong>{{e.titulo}}</strong></td>
                            <td>{{data_br(e.retirado_em)}}</td>
                            <td>{{data_br(e.devolver_ate)}}</td>
                            <td>{{e.renovacoes}}/{{max_renovacoes}}</td>
                            <td>{{e.status}}</td>
                            <td>
                                <div class="acoes-linha">
                                    <form action="/biblioteca/emprestimo/{{e.id}}/renovar" method="post">
                                        <button type="submit" class="btn-pequeno">Renovar</button>
                                    </form>
                                    <form action="/biblioteca/emprestimo/{{e.id}}/devolver" method="post">
                                        <button type="submit" class="btn-perigo btn-pequeno">Devolver</button>
                                    </form>
                                </div>
                            </td>
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
            % else:
            <p class="texto-suave">Você não possui empréstimos em andamento. Multa em caso de atraso: R$ {{'%.2f' % multa_por_dia}}/dia.</p>
            % end
        </section>
        % end

        <section class="bloco">
            <h3>Acervo de Livros ({{len(livros)}})</h3>
            <form action="/biblioteca" method="get" class="barra-filtro">
                <div class="campo-filtro">
                    <label for="busca">Buscar por título, autor ou área</label>
                    <input id="busca" name="busca" type="text" value="{{busca}}" placeholder="Ex.: Cálculo, Sommerville...">
                </div>
                <div class="campo-filtro">
                    <label for="filtro_area">Área</label>
                    <select id="filtro_area" name="area">
                        <option value="">Todas as áreas</option>
                        % for a in areas:
                        <option value="{{a}}" {{'selected' if a == area_atual else ''}}>{{a}}</option>
                        % end
                    </select>
                </div>
                <label class="check-inline">
                    <input type="checkbox" name="disponiveis" value="1" {{'checked' if so_disp else ''}}>
                    Só disponíveis
                </label>
                <button type="submit">Pesquisar</button>
                % if busca or area_atual or so_disp:
                <a href="/biblioteca" class="btn btn-secundario">Limpar</a>
                % end
            </form>

            % if livros:
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Título</th>
                            <th>Autor(es)</th>
                            <th>Área</th>
                            <th>Disponíveis</th>
                            % if tem_perfil or usuario['eh_admin']:
                            <th>Ações</th>
                            % end
                        </tr>
                    </thead>
                    <tbody>
                        % for l in livros:
                        <tr>
                            <td><code>#{{l.id}}</code></td>
                            <td><strong>{{l.titulo}}</strong></td>
                            <td>{{l.autores}}</td>
                            <td>{{l.area}}</td>
                            <td>
                                % if l.disponiveis:
                                <span class="badge-status badge-aberta">{{l.disponiveis}}/{{l.exemplares}}</span>
                                % else:
                                <span class="badge-status badge-alerta">Indisponível</span>
                                % end
                            </td>
                            % if tem_perfil or usuario['eh_admin']:
                            <td>
                                <div class="acoes-linha">
                                    % if tem_perfil and l.disponiveis:
                                    <form action="/biblioteca/{{l.id}}/reservar" method="post">
                                        <button type="submit" class="btn-destaque btn-pequeno">Reservar</button>
                                    </form>
                                    % end
                                    % if usuario['eh_admin']:
                                    <a href="/biblioteca/{{l.id}}/editar" class="btn btn-pequeno">Editar</a>
                                    <form action="/biblioteca/{{l.id}}/excluir" method="post" onsubmit="return confirm('Remover este livro do acervo?');">
                                        <button type="submit" class="btn-perigo btn-pequeno">Excluir</button>
                                    </form>
                                    % end
                                </div>
                            </td>
                            % end
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
            % else:
            <p class="texto-suave">Nenhum livro encontrado para os filtros informados.</p>
            % end
        </section>

        % if tem_perfil and historico:
        <section class="bloco">
            <h3>Histórico de Reservas ({{len(historico)}})</h3>
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Livro</th>
                            <th>Retirado em</th>
                            <th>Devolvido em</th>
                            <th>Situação</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for e in historico:
                        <tr>
                            <td><code>#{{e.id}}</code></td>
                            <td>{{e.titulo}}</td>
                            <td>{{data_br(e.retirado_em)}}</td>
                            <td>{{data_br(e.devolvido_em) if e.devolvido_em else 'Em aberto'}}</td>
                            <td>{{e.status}}</td>
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
        </section>
        % end
        </div>
    </main>
</body>
</html>
