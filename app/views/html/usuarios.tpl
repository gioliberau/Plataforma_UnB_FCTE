<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestão de Usuários - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Gestão de Usuários e Acessos (Restrito a Admin)</h2>
            <p>Crie novos acessos com senha temporária, edite perfis cadastrados ou remova contas.</p>
        </section>

        <section class="bloco">
            <h3>Gerar Novo Acesso</h3>
            <form action="/usuarios/novo" method="post" class="barra-filtro">
                <div class="campo-filtro">
                    <label for="email">E-mail institucional</label>
                    <input id="email" name="email" type="email" placeholder="novo.usuario@unb.br" required>
                </div>
                <div class="campo-filtro" style="max-width: 190px;">
                    <label for="tipo">Tipo de vínculo</label>
                    <select id="tipo" name="tipo" required>
                        % for t in tipos_usuario:
                        <option value="{{t}}">{{t.capitalize()}}</option>
                        % end
                    </select>
                </div>
                <button type="submit" class="btn-destaque">Gerar Acesso</button>
            </form>
        </section>

        <section class="bloco">
            <h3>Contas Cadastradas ({{len(registros)}})</h3>
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>Vínculo</th>
                            <th>E-mail</th>
                            <th>Nome</th>
                            <th>Matrícula</th>
                            <th>Curso / Área</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for r in registros:
                        <tr>
                            <td><strong>{{r['tipo_usuario'].capitalize()}}</strong></td>
                            <td>{{r['email']}}</td>
                            <td>{{r['nome']}}</td>
                            <td><code>{{r['matricula']}}</code></td>
                            <td>{{r['curso_ou_area']}}</td>
                            <td>
                                % if r['precisa_trocar_senha']:
                                <span class="badge-status badge-encerrada">1º acesso pendente</span>
                                % else:
                                <span class="badge-status badge-aberta">Ativo</span>
                                % end
                            </td>
                            <td>
                                <div class="acoes-linha">
                                    % if r['tem_perfil']:
                                    <a href="/usuarios/editar?email={{r['email']}}" class="btn btn-pequeno">Editar</a>
                                    % end
                                    % if not r['eh_proprio']:
                                    <form action="/usuarios/excluir" method="post" onsubmit="return confirm('Remover definitivamente esta conta e seu perfil?');">
                                        <input type="hidden" name="email" value="{{r['email']}}">
                                        <button type="submit" class="btn-perigo btn-pequeno">Excluir</button>
                                    </form>
                                    % else:
                                    <span class="texto-suave">(sua conta)</span>
                                    % end
                                </div>
                            </td>
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
        </section>
    </main>
</body>
</html>
