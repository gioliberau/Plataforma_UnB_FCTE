    <header class="topo">
        <div class="topo-conteudo">
            <a class="topo-marca" href="/menu">
                <img class="logo-topo" src="/static/img/logo_unb.svg" alt="Logo da UnB">
                <div>
                    <h1>Plataforma UnB FCTE</h1>
                    <span class="sub-topo">Portal Acadêmico — Campus Gama | Semestre {{usuario['semestre_atual']}}</span>
                </div>
            </a>
            <div class="topo-acoes">
                <span class="badge-tipo">{{usuario['tipo_usuario'].upper()}}</span>
                <form action="/logout" method="post" style="margin:0;">
                    <button type="submit" class="btn-sair">Sair</button>
                </form>
            </div>
        </div>
    </header>
    <div class="barra-nav-wrap">
        <nav class="barra-nav" aria-label="Navegação principal">
            <a href="/menu" class="{{'ativo' if pagina_ativa == 'menu' else ''}}">Início</a>
            <a href="/turmas" class="{{'ativo' if pagina_ativa == 'turmas' else ''}}">Turmas</a>
            <a href="/cardapio" class="{{'ativo' if pagina_ativa == 'cardapio' else ''}}">Cardápio RU</a>
            <a href="/oportunidades" class="{{'ativo' if pagina_ativa == 'oportunidades' else ''}}">Oportunidades</a>
            <a href="/organizacoes" class="{{'ativo' if pagina_ativa == 'organizacoes' else ''}}">Organizações</a>
            <a href="/biblioteca" class="{{'ativo' if pagina_ativa == 'biblioteca' else ''}}">Biblioteca</a>
            <a href="/perfil" class="{{'ativo' if pagina_ativa == 'perfil' else ''}}">Meu Perfil</a>
            % if usuario['eh_admin']:
            <a href="/usuarios" class="{{'ativo' if pagina_ativa == 'usuarios' else ''}}">Usuários (Admin)</a>
            % end
        </nav>
    </div>

    <main class="painel">
        % if defined('flash') and flash:
            <div class="{{'alerta-sucesso' if flash['tipo'] == 'sucesso' else 'alerta-erro'}}" role="alert">{{flash['texto']}}</div>
        % end
