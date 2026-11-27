(function () {
    let timerToast = null;
    let atualizando = false;

    function mostrarToast(texto, tipo) {
        const el = document.getElementById('toast-ws');
        if (!el || !texto) return;
        el.textContent = texto;
        el.className = 'toast-ws toast-visivel toast-' + (tipo || 'ws');
        clearTimeout(timerToast);
        timerToast = setTimeout(() => {
            el.className = 'toast-ws';
        }, 4200);
    }

    function atualizarStatusWs(estado, rotulo) {
        const badge = document.getElementById('ws-status');
        if (!badge) return;
        badge.className = 'ws-status ws-' + estado;
        badge.textContent = rotulo;
    }

    function aplicarHtmlAtualizado(html, destacar) {
        const alvo = document.getElementById('conteudo-tempo-real');
        if (!alvo) return null;

        const doc = new DOMParser().parseFromString(html, 'text/html');
        const novo = doc.getElementById('conteudo-tempo-real');
        if (novo) {
            alvo.innerHTML = novo.innerHTML;
            if (destacar) {
                alvo.classList.remove('pulso-atualizado');
                void alvo.offsetWidth;
                alvo.classList.add('pulso-atualizado');
            }
        }

        const alertaErro = doc.querySelector('.alerta-erro');
        if (alertaErro) {
            return { tipo: 'erro', texto: alertaErro.textContent.trim() };
        }
        const alertaOk = doc.querySelector('.alerta-sucesso');
        if (alertaOk) {
            return { tipo: 'sucesso', texto: alertaOk.textContent.trim() };
        }
        return null;
    }

    async function recarregarRegiaoTempoReal(mensagemToast) {
        const alvo = document.getElementById('conteudo-tempo-real');
        if (!alvo || atualizando) return;
        atualizando = true;
        try {
            const resp = await fetch(window.location.href, {
                credentials: 'same-origin',
                cache: 'no-store',
                headers: { 'X-Requested-With': 'WebSocketRefresh' },
            });
            if (resp.redirected && resp.url.includes('/login')) {
                window.location.href = '/login';
                return;
            }
            if (resp.ok) {
                const html = await resp.text();
                aplicarHtmlAtualizado(html, true);
                if (mensagemToast) {
                    mostrarToast('Tempo real: ' + mensagemToast, 'ws');
                }
            }
        } catch (_) {
            // Mantém a tela atual caso haja instabilidade momentânea.
        } finally {
            atualizando = false;
        }
    }

    function conectarWebSocket() {
        const protocolo = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocolo}//${window.location.host}/ws`);

        ws.addEventListener('open', () => {
            atualizarStatusWs('online', '● Tempo real');
        });

        ws.addEventListener('message', (evento) => {
            try {
                const dados = JSON.parse(evento.data);
                const alvo = document.getElementById('conteudo-tempo-real');
                const canalAtual = alvo ? alvo.dataset.canal : '';

                if (dados.canal && dados.canal === canalAtual) {
                    recarregarRegiaoTempoReal(dados.mensagem);
                } else if (dados.mensagem) {
                    mostrarToast('Tempo real: ' + dados.mensagem, 'ws');
                }
            } catch (_) {
                // Ignora mensagens inválidas.
            }
        });

        ws.addEventListener('close', () => {
            atualizarStatusWs('offline', '● Reconectando...');
            setTimeout(conectarWebSocket, 2500);
        });

        ws.addEventListener('error', () => {
            ws.close();
        });
    }

    // Intercepta formulários POST de Oportunidades e Biblioteca para atualizar sem recarregar a página.
    document.addEventListener('submit', async (evento) => {
        if (evento.defaultPrevented) return;
        const form = evento.target;
        if (!(form instanceof HTMLFormElement)) return;
        if ((form.method || '').toUpperCase() !== 'POST') return;

        const dentroTempoReal = Boolean(form.closest('#conteudo-tempo-real'));
        const ehFormCriar = form.dataset.asyncForm === 'criar';
        if (!dentroTempoReal && !ehFormCriar) return;

        // Se o form já tiver confirmação inline (ex.: excluir), respeita o onsubmit antes.
        evento.preventDefault();

        const corpo = new URLSearchParams(new FormData(form));
        try {
            const resp = await fetch(form.action, {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8' },
                body: corpo.toString(),
            });

            if (resp.redirected && resp.url.includes('/login')) {
                window.location.href = '/login';
                return;
            }

            const html = await resp.text();
            const flash = aplicarHtmlAtualizado(html, true);
            if (flash) {
                mostrarToast(flash.texto, flash.tipo);
                if (ehFormCriar && flash.tipo === 'sucesso') {
                    form.reset();
                }
            } else if (ehFormCriar) {
                form.reset();
            }
        } catch (_) {
            mostrarToast('Não foi possível enviar os dados ao servidor.', 'erro');
        }
    });

    conectarWebSocket();
})();
