<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cardápio do RU - Plataforma UnB FCTE</title>
    <link rel="stylesheet" type="text/css" href="/static/css/login.css?v=2">
</head>
<body class="pagina-menu">
% include('app/views/html/_topo.tpl', usuario=usuario, pagina_ativa=pagina_ativa, flash=flash)

        <section class="secao-boas-vindas">
            <h2>Cardápio do RU — Campus Gama</h2>
            <p>Refeições da semana filtradas pela sua preferência alimentar.</p>
        </section>

        % if desatualizado and ultima_data:
        <div class="alerta-aviso">Aviso: o cardápio carregado é de {{ultima_data}} e pode estar desatualizado.</div>
        % end

        <section class="bloco">
            <form action="/cardapio" method="get" class="barra-filtro">
                <div class="campo-filtro">
                    <label for="dia">Dia</label>
                    <select id="dia" name="dia">
                        % for d in datas:
                        <option value="{{d['iso']}}" {{'selected' if d['iso'] == dia_atual else ''}}>{{d['rotulo']}}</option>
                        % end
                    </select>
                </div>
                <div class="campo-filtro">
                    <label for="dieta">Preferência alimentar</label>
                    <select id="dieta" name="dieta">
                        % for chave, rotulo in dietas.items():
                        <option value="{{chave}}" {{'selected' if chave == dieta_atual else ''}}>{{rotulo}}</option>
                        % end
                    </select>
                </div>
                <button type="submit">Ver cardápio</button>
            </form>
        </section>

        % if refeicoes:
        <div class="grade-cardapio">
            % for r in refeicoes:
            <section class="bloco">
                <h3>{{r['nome']}}</h3>
                <dl class="lista-dados">
                    % for rotulo, texto in r['itens']:
                    <div>
                        <dt>{{rotulo}}</dt>
                        <dd>{{texto}}</dd>
                    </div>
                    % end
                </dl>
            </section>
            % end
        </div>
        % else:
        <section class="bloco">
            <p class="texto-suave">Nenhum cardápio disponível para exibição.</p>
        </section>
        % end
    </main>
</body>
</html>
