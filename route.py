import os

from app.controllers.application import Application
from bottle import Bottle, redirect, request, response, run, static_file


app = Bottle()
ctl = Application()


# ============================= { ROTAS } ============================= #

@app.route('/static/<filepath:path>')
def serve_static(filepath):
    return static_file(filepath, root='./app/static')


@app.route('/', method='GET')
@app.route('/login', method='GET')
def login():
    return ctl.render('login')


@app.route('/login', method='POST')
def acao_login():
    email = request.forms.getunicode('email') or ''
    senha = request.forms.getunicode('senha') or ''

    session_id, erro = ctl.autenticar_usuario(email, senha)

    if not session_id:
        return redirect(f'/login?erro={erro}')

    response.set_cookie('session_id', session_id, httponly=True, max_age=3600, path='/')
    return redirect('/menu')


@app.route('/menu', method='GET')
def menu():
    return ctl.render('menu')


@app.route('/logout', method='POST')
def logout():
    ctl.encerrar_sessao()
    response.delete_cookie('session_id', path='/')
    return redirect('/login')


if __name__ == '__main__':
    run(app, host='0.0.0.0', port=8080, debug=os.environ.get('BMVC_DEBUG') == '1')
