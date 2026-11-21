<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Menu Principal - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css">
</head>
<body class="pagina-menu">
    <header class="topo">
        <div class="topo-conteudo">
            <div class="topo-marca">
                <img class="logo-topo" src="/static/img/logo_unb.svg" alt="Logo da UnB">
                <div>
                    <h1>Plataforma UnB FCTE</h1>
                    <span class="sub-topo">Portal Acadêmico — Campus Gama | Semestre {{usuario['semestre_atual']}}</span>
                </div>
            </div>
            <div class="topo-acoes">
                <span class="badge-tipo">{{usuario['tipo_usuario'].upper()}}</span>
                <form action="/logout" method="post">
                    <button type="submit" class="btn-sair">Sair</button>
                </form>
            </div>
        </div>
    </header>

    <main class="painel">
        <section class="secao-boas-vindas">
            <h2>Olá, {{usuario['nome']}}!</h2>
            <p>Confira abaixo seus dados acadêmicos e os serviços do campus FCTE.</p>
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
            </section>

            <section class="bloco">
                <h3>Menu Rápido — Campus FCTE</h3>
                <div class="atalhos-menu">
                    <div class="item-atalho">
                        <strong>Turmas do SIGAA</strong>
                        <p>Consulta de disciplinas, horários e ocupação de vagas da FGA/FCTE.</p>
                    </div>
                    <div class="item-atalho">
                        <strong>Cardápio do RU — Gama</strong>
                        <p>Refeições da semana por dieta (padrão, ovolactovegetariana e estrita).</p>
                    </div>
                    <div class="item-atalho">
                        <strong>Mural de Oportunidades</strong>
                        <p>Monitorias, projetos de extensão, iniciação científica e estágios.</p>
                    </div>
                    <div class="item-atalho">
                        <strong>Organizações Estudantis</strong>
                        <p>Empresas juniores, equipes de competição e atlética do campus.</p>
                    </div>
                </div>
            </section>
        </div>

        % if usuario['turmas']:
        <section class="bloco">
            % if usuario['tipo_usuario'] == 'discente':
                <h3>Minhas Turmas e Menções</h3>
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Disciplina</th>
                            <th>Período</th>
                            <th>Créditos</th>
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
                            <td><strong>{{t['resultado']}}</strong></td>
                        </tr>
                        % end
                    </tbody>
                </table>
            % elif usuario['tipo_usuario'] == 'docente':
                <h3>Turmas Ofertadas em {{usuario['semestre_atual']}}</h3>
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Disciplina</th>
                            <th>Turma</th>
                            <th>Créditos</th>
                            <th>Horário SIGAA</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for t in usuario['turmas']:
                        <tr>
                            <td><code>{{t['codigo']}}</code></td>
                            <td>{{t['disciplina']}}</td>
                            <td>{{t['turma']}}</td>
                            <td>{{t['creditos']}}</td>
                            <td><code>{{t['horario']}}</code></td>
                        </tr>
                        % end
                    </tbody>
                </table>
            % end
        </section>
        % end
    </main>
</body>
</html>
