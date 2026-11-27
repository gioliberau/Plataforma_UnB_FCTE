try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

import os

from app.controllers.application import Application
from bottle import Bottle, abort, redirect, request, response, run, static_file


app = Bottle()
ctl = Application()


@app.hook('after_request')
def desativar_cache_paginas():
    if not request.path.startswith('/static/'):
        response.set_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        response.set_header('Pragma', 'no-cache')


# ============================= { ESTÁTICOS E LOGIN } ============================= #

@app.route('/static/<filepath:path>')
def serve_static(filepath):
    return static_file(filepath, root='./app/static')


@app.route('/', method='GET')
@app.route('/login', method='GET')
def login_pagina():
    return ctl.login()


@app.route('/login', method='POST')
def acao_login():
    email = request.forms.getunicode('email') or ''
    senha = request.forms.getunicode('senha') or ''

    session_id, erro, destino = ctl.autenticar_usuario(email, senha)

    if not session_id:
        return redirect(f'/login?erro={erro}')

    response.set_cookie('session_id', session_id, httponly=True, max_age=3600, path='/')
    return redirect(destino)


@app.route('/primeiro-acesso', method='GET')
def primeiro_acesso():
    return ctl.form_primeiro_acesso()


@app.route('/primeiro-acesso', method='POST')
def acao_primeiro_acesso():
    return ctl.acao_primeiro_acesso()


@app.route('/completar-perfil', method='GET')
def completar_perfil():
    return ctl.form_completar_perfil()


@app.route('/completar-perfil', method='POST')
def acao_completar_perfil():
    return ctl.acao_completar_perfil()


@app.route('/logout', method='POST')
def logout():
    ctl.encerrar_sessao()
    response.delete_cookie('session_id', path='/')
    return redirect('/login')


# ============================= { MENU E PERFIL } ============================= #

@app.route('/menu', method='GET')
def menu():
    return ctl.menu()


@app.route('/perfil', method='GET')
def perfil():
    return ctl.perfil()


@app.route('/perfil/editar', method='POST')
def editar_perfil():
    return ctl.editar_perfil()


@app.route('/perfil/senha', method='POST')
def trocar_senha_perfil():
    return ctl.trocar_senha_perfil()


# ============================= { CRUD: OPORTUNIDADES } ============================= #

@app.route('/oportunidades', method='GET')
def oportunidades():
    return ctl.oportunidades()


@app.route('/oportunidades/novo', method='POST')
def criar_oportunidade():
    return ctl.criar_oportunidade()


@app.route('/oportunidades/<id_oportunidade:int>/editar', method='GET')
def form_editar_oportunidade(id_oportunidade):
    return ctl.form_editar_oportunidade(id_oportunidade)


@app.route('/oportunidades/<id_oportunidade:int>/editar', method='POST')
def editar_oportunidade(id_oportunidade):
    return ctl.editar_oportunidade(id_oportunidade)


@app.route('/oportunidades/<id_oportunidade:int>/encerrar', method='POST')
def encerrar_oportunidade(id_oportunidade):
    return ctl.encerrar_oportunidade(id_oportunidade)


@app.route('/oportunidades/<id_oportunidade:int>/excluir', method='POST')
def excluir_oportunidade(id_oportunidade):
    return ctl.excluir_oportunidade(id_oportunidade)


@app.route('/oportunidades/<id_oportunidade:int>/interesse', method='POST')
def demonstrar_interesse(id_oportunidade):
    return ctl.demonstrar_interesse(id_oportunidade)


@app.route('/oportunidades/<id_oportunidade:int>/retirar-interesse', method='POST')
def retirar_interesse(id_oportunidade):
    return ctl.retirar_interesse(id_oportunidade)


# ============================= { CRUD: ORGANIZAÇÕES } ============================= #

@app.route('/organizacoes', method='GET')
def organizacoes():
    return ctl.organizacoes()


@app.route('/organizacoes/novo', method='POST')
def criar_organizacao():
    return ctl.criar_organizacao()


@app.route('/organizacoes/<id_entidade:int>/editar', method='GET')
def form_editar_organizacao(id_entidade):
    return ctl.form_editar_organizacao(id_entidade)


@app.route('/organizacoes/<id_entidade:int>/editar', method='POST')
def editar_organizacao(id_entidade):
    return ctl.editar_organizacao(id_entidade)


@app.route('/organizacoes/<id_entidade:int>/excluir', method='POST')
def excluir_organizacao(id_entidade):
    return ctl.excluir_organizacao(id_entidade)


# ============================= { CRUD: BIBLIOTECA } ============================= #

@app.route('/biblioteca', method='GET')
def biblioteca():
    return ctl.biblioteca()


@app.route('/biblioteca/novo', method='POST')
def criar_livro():
    return ctl.criar_livro()


@app.route('/biblioteca/<id_livro:int>/editar', method='GET')
def form_editar_livro(id_livro):
    return ctl.form_editar_livro(id_livro)


@app.route('/biblioteca/<id_livro:int>/editar', method='POST')
def editar_livro(id_livro):
    return ctl.editar_livro(id_livro)


@app.route('/biblioteca/<id_livro:int>/excluir', method='POST')
def excluir_livro(id_livro):
    return ctl.excluir_livro(id_livro)


@app.route('/biblioteca/<id_livro:int>/reservar', method='POST')
def reservar_livro(id_livro):
    return ctl.reservar_livro(id_livro)


@app.route('/biblioteca/emprestimo/<id_emprestimo:int>/renovar', method='POST')
def renovar_emprestimo(id_emprestimo):
    return ctl.renovar_emprestimo(id_emprestimo)


@app.route('/biblioteca/emprestimo/<id_emprestimo:int>/devolver', method='POST')
def devolver_emprestimo(id_emprestimo):
    return ctl.devolver_emprestimo(id_emprestimo)


# ============================= { CRUD: TURMAS E NOTAS } ============================= #

@app.route('/turmas', method='GET')
def turmas():
    return ctl.turmas()


@app.route('/turmas/matricular', method='POST')
def matricular_discente():
    return ctl.matricular_discente()


@app.route('/turmas/desmatricular', method='POST')
def desmatricular_discente():
    return ctl.desmatricular_discente()


@app.route('/turmas/atribuir-docente', method='POST')
def atribuir_docente():
    return ctl.atribuir_docente()


@app.route('/turmas/remover-oferta', method='POST')
def remover_oferta():
    return ctl.remover_oferta()


@app.route('/turmas/nota', method='POST')
def lancar_nota():
    return ctl.lancar_nota()


# ============================= { CRUD: USUÁRIOS (ADMIN) } ============================= #

@app.route('/usuarios', method='GET')
def usuarios():
    return ctl.usuarios()


@app.route('/usuarios/novo', method='POST')
def criar_usuario():
    return ctl.criar_usuario()


@app.route('/usuarios/editar', method='GET')
def form_editar_usuario():
    return ctl.form_editar_usuario()


@app.route('/usuarios/editar', method='POST')
def editar_usuario():
    return ctl.editar_usuario()


@app.route('/usuarios/excluir', method='POST')
def excluir_usuario():
    return ctl.excluir_usuario()


# ============================= { CARDÁPIO DO RU } ============================= #

@app.route('/cardapio', method='GET')
def cardapio():
    return ctl.cardapio()


# ============================= { WEBSOCKET TEMPO REAL } ============================= #

@app.route('/ws')
def websocket_canal():
    ws = request.environ.get('wsgi.websocket')
    if not ws:
        abort(400, 'Conexão WebSocket esperada.')

    if not ctl.sessao_valida_ws():
        ws.close()
        return

    ctl.registrar_ws(ws)
    try:
        while True:
            mensagem = ws.receive()
            if mensagem is None:
                break
    finally:
        ctl.remover_ws(ws)


if __name__ == '__main__':
    try:
        from gevent.pywsgi import WSGIServer
        from geventwebsocket.handler import WebSocketHandler

        servidor = WSGIServer(('0.0.0.0', 8080), app, handler_class=WebSocketHandler)
        print('Servidor BMVC com WebSocket rodando em http://0.0.0.0:8080')
        servidor.serve_forever()
    except ImportError:
        run(app, host='0.0.0.0', port=8080, debug=os.environ.get('BMVC_DEBUG') == '1')
