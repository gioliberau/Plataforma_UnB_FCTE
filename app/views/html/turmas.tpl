<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Turmas do SIGAA - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Turmas do SIGAA — FCTE</h2>
            <p>Consulta de ofertas, horários traduzidos, notas e gestão de matrículas.</p>
        </section>

        % if usuario['tipo_usuario'] == 'docente' and docente_turmas:
        <section class="bloco">
            <h3>Minhas Turmas — Lançamento de Notas</h3>
            % for bloco_t in docente_turmas:
            <div style="margin-bottom: 18px;">
                <p style="margin: 0 0 8px;">
                    <strong>{{bloco_t['turma']['codigo_disciplina']}} — {{bloco_t['turma']['nome_disciplina']}}</strong>
                    <span class="texto-suave">| Turma {{bloco_t['turma']['numero_turma']}} ({{bloco_t['turma']['periodo']}}) | {{bloco_t['horario_legivel']}}</span>
                </p>
                % if bloco_t['alunos']:
                <div class="tabela-wrapper">
                    <table class="tabela">
                        <thead>
                            <tr>
                                <th>Matrícula</th>
                                <th>Discente</th>
                                <th>Nota Atual</th>
                                <th>Lançar / Atualizar Nota (0 a 10)</th>
                            </tr>
                        </thead>
                        <tbody>
                            % for a in bloco_t['alunos']:
                            <tr>
                                <td><code>{{a['matricula']}}</code></td>
                                <td>{{a['nome']}}</td>
                                <td>{{'Sem nota' if a['nota'] is None else f"{a['nota']:.1f} ({a['mencao']})"}}</td>
                                <td>
                                    <form action="/turmas/nota" method="post" class="form-inline-nota">
                                        <input type="hidden" name="chave" value="{{bloco_t['chave']}}">
                                        <input type="hidden" name="matricula" value="{{a['matricula']}}">
                                        <input type="number" name="nota" min="0" max="10" step="0.1" value="{{'' if a['nota'] is None else '%.1f' % a['nota']}}" required>
                                        <button type="submit" class="btn-destaque btn-pequeno">Salvar</button>
                                    </form>
                                </td>
                            </tr>
                            % end
                        </tbody>
                    </table>
                </div>
                % else:
                <p class="texto-suave">Nenhum discente matriculado nesta turma.</p>
                % end
            </div>
            % end
        </section>
        % end

        % if usuario['eh_admin']:
        <div class="grade-principal">
            <section class="bloco">
                <h3>Matricular Discente em Turma</h3>
                <form action="/turmas/matricular" method="post">
                    <label for="sel_disc">Discente</label>
                    <select id="sel_disc" name="matricula" required>
                        % for d in discentes_admin:
                        <option value="{{d.id_user}}">{{d.nome}} ({{d.id_user}})</option>
                        % end
                    </select>

                    <label for="sel_turma_m">Turma</label>
                    <select id="sel_turma_m" name="chave" required>
                        % for item in turmas_semestre:
                        <option value="{{item['chave']}}">{{item['turma']['periodo']}} | {{item['turma']['codigo_disciplina']}} - {{item['turma']['nome_disciplina']}} (T{{item['turma']['numero_turma']}})</option>
                        % end
                    </select>

                    <button type="submit" class="btn-destaque">Matricular</button>
                </form>
            </section>

            <section class="bloco">
                <h3>Atribuir Docente a Turma</h3>
                <form action="/turmas/atribuir-docente" method="post">
                    <label for="sel_doc">Docente</label>
                    <select id="sel_doc" name="id_docente" required>
                        % for d in docentes_admin:
                        <option value="{{d.id_user}}">{{d.nome}} ({{d.id_user}})</option>
                        % end
                    </select>

                    <label for="sel_turma_d">Turma</label>
                    <select id="sel_turma_d" name="chave" required>
                        % for item in turmas_semestre:
                        <option value="{{item['chave']}}">{{item['turma']['periodo']}} | {{item['turma']['codigo_disciplina']}} - {{item['turma']['nome_disciplina']}} (T{{item['turma']['numero_turma']}})</option>
                        % end
                    </select>

                    <button type="submit">Atribuir Docente</button>
                </form>
            </section>
        </div>

        <section class="bloco">
            <h3>Matrículas Atuais ({{len(matriculas_admin)}})</h3>
            % if matriculas_admin:
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>Discente</th>
                            <th>Disciplina</th>
                            <th>Período</th>
                            <th>Nota</th>
                            <th>Ação</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for m in matriculas_admin:
                        <tr>
                            <td>{{m['discente_nome']}} (<code>{{m['matricula']}}</code>)</td>
                            <td><code>{{m['turma']['codigo_disciplina']}}</code> — {{m['turma']['nome_disciplina']}}</td>
                            <td>{{m['turma']['periodo']}}</td>
                            <td>{{'Sem nota' if m['nota'] is None else f"{m['nota']:.1f} ({m['mencao']})"}}</td>
                            <td>
                                <form action="/turmas/desmatricular" method="post" onsubmit="return confirm('Desmatricular este discente?');">
                                    <input type="hidden" name="matricula" value="{{m['matricula']}}">
                                    <input type="hidden" name="chave" value="{{m['chave']}}">
                                    <button type="submit" class="btn-perigo btn-pequeno">Desmatricular</button>
                                </form>
                            </td>
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
            % else:
            <p class="texto-suave">Nenhuma matrícula registrada.</p>
            % end
        </section>

        <section class="bloco">
            <h3>Ofertas de Docentes ({{len(ofertas_admin)}})</h3>
            % if ofertas_admin:
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>Docente</th>
                            <th>Disciplina</th>
                            <th>Turma / Período</th>
                            <th>Ação</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for o in ofertas_admin:
                        <tr>
                            <td>{{o['docente_nome']}} (<code>{{o['id_docente']}}</code>)</td>
                            <td><code>{{o['turma']['codigo_disciplina']}}</code> — {{o['turma']['nome_disciplina']}}</td>
                            <td>T{{o['turma']['numero_turma']}} ({{o['turma']['periodo']}})</td>
                            <td>
                                <form action="/turmas/remover-oferta" method="post" onsubmit="return confirm('Remover vínculo docente-turma?');">
                                    <input type="hidden" name="chave" value="{{o['chave']}}">
                                    <button type="submit" class="btn-perigo btn-pequeno">Remover vínculo</button>
                                </form>
                            </td>
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
            % else:
            <p class="texto-suave">Nenhuma oferta vinculada.</p>
            % end
        </section>
        % end

        <section class="bloco">
            <h3>Consultar Turmas do SIGAA ({{len(turmas_sigaa)}})</h3>
            <form action="/turmas" method="get" class="barra-filtro">
                <div class="campo-filtro">
                    <label for="filtro">Disciplina, código ou docente</label>
                    <input id="filtro" name="filtro" type="text" value="{{filtro}}" placeholder="Ex.: FGA0170, Banco de Dados...">
                </div>
                <div class="campo-filtro" style="max-width: 150px;">
                    <label for="periodo">Período (AAAA.S)</label>
                    <input id="periodo" name="periodo" type="text" value="{{periodo_atual}}">
                </div>
                <button type="submit">Buscar</button>
                <a href="/turmas" class="btn btn-secundario">Limpar</a>
            </form>

            % if turmas_sigaa:
            <div class="tabela-wrapper">
                <table class="tabela">
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Disciplina</th>
                            <th>Turma</th>
                            <th>Docente</th>
                            <th>Horário</th>
                            <th>Local</th>
                            <th>Vagas</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for t in turmas_sigaa:
                        <tr>
                            <td><code>{{t['codigo_disciplina']}}</code></td>
                            <td>{{t['nome_disciplina']}}</td>
                            <td>{{t['numero_turma']}} ({{t['periodo']}})</td>
                            <td>{{t.get('docente', '—')}}</td>
                            <td>{{t['horario_legivel']}}</td>
                            <td>{{t.get('local', '—')}}</td>
                            <td>{{t.get('vagas_ocupadas', '?')}}/{{t.get('vagas_ofertadas', '?')}}</td>
                        </tr>
                        % end
                    </tbody>
                </table>
            </div>
            % else:
            <p class="texto-suave">Nenhuma turma encontrada para este período/filtro.</p>
            % end
        </section>
    </main>
</body>
</html>
