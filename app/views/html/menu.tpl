<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Menu Principal - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Olá, {{usuario['nome']}}!</h2>
            <p>Confira abaixo seus indicadores acadêmicos e acesse todos os módulos do campus FCTE.</p>
        </section>

        % if usuario['tipo_usuario'] == 'discente':
        <section class="grade-indicadores" aria-label="Indicadores acadêmicos">
            <div class="card-indicador destaque">
                <span class="rotulo-ind">IRA (Índice de Rendimento)</span>
                <strong class="valor-ind">{{usuario['ira']}}</strong>
                <small>Escala UnB (0 a 5)</small>
            </div>
            <div class="card-indicador">
                <span class="rotulo-ind">MP (Média Ponderada)</span>
                <strong class="valor-ind">{{usuario['mp']}}</strong>
                <small>Escala UnB (0 a 5)</small>
            </div>
            <div class="card-indicador">
                <span class="rotulo-ind">Matrícula</span>
                <strong class="valor-ind">{{usuario['matricula']}}</strong>
                <small>Ingresso em {{usuario['ingresso']}}</small>
            </div>
            <div class="card-indicador">
                <span class="rotulo-ind">Créditos Concluídos</span>
                <strong class="valor-ind">{{usuario['creditos']}}</strong>
                <small>{{len(usuario['turmas'])}} disciplinas no histórico</small>
            </div>
        </section>
        % elif usuario['tipo_usuario'] == 'docente':
        <section class="grade-indicadores" aria-label="Indicadores do docente">
            <div class="card-indicador destaque">
                <span class="rotulo-ind">Matrícula Funcional</span>
                <strong class="valor-ind">{{usuario['matricula']}}</strong>
                <small>Ingresso em {{usuario['ingresso']}}</small>
            </div>
            <div class="card-indicador">
                <span class="rotulo-ind">Créditos Ofertados</span>
                <strong class="valor-ind">{{usuario['creditos']}}</strong>
                <small>Semestre {{usuario['semestre_atual']}}</small>
            </div>
            <div class="card-indicador">
                <span class="rotulo-ind">Turmas Ativas</span>
                <strong class="valor-ind">{{len(usuario['turmas'])}}</strong>
                <small>{{usuario['curso_ou_area']}}</small>
            </div>
        </section>
        % elif defined('resumo_admin'):
        <section class="grade-indicadores" aria-label="Resumo administrativo">
            <div class="card-indicador destaque">
                <span class="rotulo-ind">Discentes</span>
                <strong class="valor-ind">{{resumo_admin['discentes']}}</strong>
                <small>Perfis cadastrados</small>
            </div>
            <div class="card-indicador">
                <span class="rotulo-ind">Docentes</span>
                <strong class="valor-ind">{{resumo_admin['docentes']}}</strong>
                <small>Perfis cadastrados</small>
            </div>
            <div class="card-indicador">
                <span class="rotulo-ind">Oportunidades</span>
                <strong class="valor-ind">{{resumo_admin['oportunidades']}}</strong>
                <small>No mural da FCTE</small>
            </div>
            <div class="card-indicador">
                <span class="rotulo-ind">Livros no Acervo</span>
                <strong class="valor-ind">{{resumo_admin['livros']}}</strong>
                <small>Biblioteca FCTE</small>
            </div>
        </section>
        % end

        <div class="grade-principal">
            <section class="bloco">
                <h3>Meus Dados Cadastrais</h3>
                <dl class="lista-dados">
                    <div>
                        <dt>Nome completo</dt>
                        <dd>{{usuario['nome']}}</dd>
                    </div>
                    <div>
                        <dt>Matrícula</dt>
                        <dd>{{usuario['matricula']}}</dd>
                    </div>
                    <div>
                        <dt>Vínculo</dt>
                        <dd>{{usuario['tipo_usuario'].capitalize()}}</dd>
                    </div>
                    <div>
                        <dt>Curso / Área</dt>
                        <dd>{{usuario['curso_ou_area']}}</dd>
                    </div>
                    <div>
                        <dt>Período de entrada</dt>
                        <dd>{{usuario['ingresso']}}</dd>
                    </div>
                    <div>
                        <dt>CPF</dt>
                        <dd>{{usuario['cpf']}}</dd>
                    </div>
                    <div>
                        <dt>E-mail institucional</dt>
                        <dd>{{usuario['email']}}</dd>
                    </div>
                </dl>
                <div style="margin-top: 14px;">
                    <a href="/perfil" class="btn btn-secundario btn-pequeno">Editar perfil / trocar senha</a>
                </div>
            </section>

            <section class="bloco">
                <h3>Menu Rápido — Campus FCTE</h3>
                <div class="atalhos-menu">
                    <a class="item-atalho" href="/turmas">
                        <strong>Turmas do SIGAA</strong>
                        <p>Disciplinas, horários traduzidos, matrículas e lançamento de notas.</p>
                    </a>
                    <a class="item-atalho" href="/cardapio">
                        <strong>Cardápio do RU — Gama</strong>
                        <p>Refeições da semana por dieta (padrão, ovolacto e estrita).</p>
                    </a>
                    <a class="item-atalho" href="/oportunidades">
                        <strong>Mural de Oportunidades</strong>
                        <p>Monitorias, projetos de extensão, iniciação científica e estágios.</p>
                    </a>
                    <a class="item-atalho" href="/organizacoes">
                        <strong>Organizações Estudantis</strong>
                        <p>Empresas juniores, equipes de competição e atlética do campus.</p>
                    </a>
                    <a class="item-atalho" href="/biblioteca">
                        <strong>Biblioteca FCTE</strong>
                        <p>Consulta ao acervo, reservas, renovações, devoluções e gestão de livros.</p>
                    </a>
                    % if usuario['eh_admin']:
                    <a class="item-atalho" href="/usuarios">
                        <strong>Usuários e Acessos</strong>
                        <p>Criar acessos, editar perfis cadastrados e remover contas.</p>
                    </a>
                    % end
                </div>
            </section>
        </div>

        % if usuario['turmas']:
        <section class="bloco">
            % if usuario['tipo_usuario'] == 'discente':
                <h3>Minhas Turmas e Menções</h3>
                <div class="tabela-wrapper">
                    <table class="tabela">
                        <thead>
                            <tr>
                                <th>Código</th>
                                <th>Disciplina</th>
                                <th>Período</th>
                                <th>Créditos</th>
                                <th>Horário</th>
                                <th>Nota / Menção</th>
                            </tr>
                        </thead>
                        <tbody>
                            % for t in usuario['turmas']:
                            <tr>
                                <td><code>{{t['codigo']}}</code></td>
                                <td>{{t['disciplina']}}</td>
                                <td>{{t['periodo']}}</td>
                                <td>{{t['creditos']}}</td>
                                <td>{{t['horario']}}</td>
                                <td><strong>{{t['resultado']}}</strong></td>
                            </tr>
                            % end
                        </tbody>
                    </table>
                </div>
            % elif usuario['tipo_usuario'] == 'docente':
                <h3>Turmas Ofertadas</h3>
                <div class="tabela-wrapper">
                    <table class="tabela">
                        <thead>
                            <tr>
                                <th>Código</th>
                                <th>Disciplina</th>
                                <th>Turma</th>
                                <th>Créditos</th>
                                <th>Horário</th>
                            </tr>
                        </thead>
                        <tbody>
                            % for t in usuario['turmas']:
                            <tr>
                                <td><code>{{t['codigo']}}</code></td>
                                <td>{{t['disciplina']}}</td>
                                <td>{{t['turma']}}</td>
                                <td>{{t['creditos']}}</td>
                                <td>{{t['horario']}}</td>
                            </tr>
                            % end
                        </tbody>
                    </table>
                </div>
            % end
        </section>
        % end
    </main>
</body>
</html>
