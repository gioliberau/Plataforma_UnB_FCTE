from datetime import date, datetime
import re
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


# ============================= { PALETA E IDENTIDADE VISUAL } ============================= #

CORES = {
    'primaria': '#003366',         # Azul institucional UnB
    'primaria_hover': '#00509e',
    'destaque': '#006633',         # Verde institucional UnB
    'destaque_hover': '#008040',
    'perigo': '#b91c1c',
    'perigo_hover': '#991b1b',
    'fundo': '#eef2f7',
    'cartao': '#ffffff',
    'superficie': '#f8fafc',
    'borda': '#d9e2ec',
    'texto': '#1f2933',
    'texto_suave': '#52606d',
    'erro_fundo': '#fde8e8',
    'erro_texto': '#9b1c1c',
    'aviso_fundo': '#fef3c7',
    'aviso_texto': '#92400e',
    'sucesso_fundo': '#def7ec',
    'sucesso_texto': '#03543f',
    'sidebar_fundo': '#0b2545',
    'sidebar_hover': '#163a66',
    'sidebar_ativo': '#006633',
}


# ============================= { HELPERS PUROS } ============================= #

def converter_data_br(texto):
    # Converte 'DD/MM/AAAA' para date, ou None se o texto for vazio.
    valor = (texto or '').strip()
    if not valor:
        return None
    try:
        return datetime.strptime(valor, '%d/%m/%Y').date()
    except ValueError:
        raise ValueError('Data inválida. Use o formato DD/MM/AAAA.')


def formatar_data_br(valor):
    # Aceita date ou string ISO 'AAAA-MM-DD' e devolve 'DD/MM/AAAA'.
    if not valor:
        return '—'
    if isinstance(valor, date):
        return valor.strftime('%d/%m/%Y')
    texto = str(valor).strip()[:10]
    try:
        return date.fromisoformat(texto).strftime('%d/%m/%Y')
    except ValueError:
        return texto


def parsear_periodo(texto):
    # Converte 'AAAA.S' para (ano, semestre); vazio retorna (None, None).
    valor = (texto or '').strip()
    if not valor:
        return None, None
    correspondencia = re.fullmatch(r'(\d{4})\.([12])', valor)
    if not correspondencia:
        raise ValueError('Período inválido. Use o formato AAAA.S (ex.: 2026.2).')
    return int(correspondencia.group(1)), int(correspondencia.group(2))


def formatar_indice(valor):
    # Formata MP ou IRA na escala UnB (0 a 5).
    return 'sem notas' if valor is None else f'{valor:.2f}'


# ============================= { CONFIGURAÇÃO DO TTK } ============================= #

def configurar_estilo(raiz):
    estilo = ttk.Style(raiz)
    temas = estilo.theme_names()
    if 'clam' in temas:
        estilo.theme_use('clam')

    familia = tkfont.nametofont('TkDefaultFont').actual().get('family', 'Sans')

    estilo.configure('.', font=(familia, 10), background=CORES['fundo'], foreground=CORES['texto'])
    estilo.configure('TFrame', background=CORES['fundo'])
    estilo.configure('Card.TFrame', background=CORES['cartao'])
    estilo.configure('Superficie.TFrame', background=CORES['superficie'])

    estilo.configure('TLabel', background=CORES['fundo'], foreground=CORES['texto'])
    estilo.configure('Card.TLabel', background=CORES['cartao'], foreground=CORES['texto'])
    estilo.configure('Suave.TLabel', background=CORES['fundo'], foreground=CORES['texto_suave'], font=(familia, 9))
    estilo.configure('CardSuave.TLabel', background=CORES['cartao'], foreground=CORES['texto_suave'], font=(familia, 9))
    estilo.configure('Titulo.TLabel', background=CORES['fundo'], foreground=CORES['primaria'], font=(familia, 15, 'bold'))
    estilo.configure('Subtitulo.TLabel', background=CORES['cartao'], foreground=CORES['primaria'], font=(familia, 11, 'bold'))
    estilo.configure('IndicadorValor.TLabel', background=CORES['cartao'], foreground=CORES['primaria'], font=(familia, 18, 'bold'))
    estilo.configure('IndicadorRotulo.TLabel', background=CORES['cartao'], foreground=CORES['texto_suave'], font=(familia, 8, 'bold'))

    estilo.configure('TCheckbutton', background=CORES['fundo'], foreground=CORES['texto'])
    estilo.configure('Card.TCheckbutton', background=CORES['cartao'], foreground=CORES['texto'])
    estilo.configure('TLabelframe', background=CORES['cartao'], bordercolor=CORES['borda'])
    estilo.configure('TLabelframe.Label', background=CORES['cartao'], foreground=CORES['primaria'], font=(familia, 10, 'bold'))

    estilo.configure(
        'Primario.TButton',
        background=CORES['primaria'],
        foreground='#ffffff',
        font=(familia, 10, 'bold'),
        padding=(12, 7),
        borderwidth=0,
    )
    estilo.map(
        'Primario.TButton',
        background=[('active', CORES['primaria_hover']), ('disabled', '#9fb3c8')],
        foreground=[('disabled', '#f0f4f8')],
    )

    estilo.configure(
        'Destaque.TButton',
        background=CORES['destaque'],
        foreground='#ffffff',
        font=(familia, 10, 'bold'),
        padding=(12, 7),
        borderwidth=0,
    )
    estilo.map(
        'Destaque.TButton',
        background=[('active', CORES['destaque_hover']), ('disabled', '#9fb3c8')],
    )

    estilo.configure(
        'Perigo.TButton',
        background=CORES['perigo'],
        foreground='#ffffff',
        font=(familia, 10, 'bold'),
        padding=(12, 7),
        borderwidth=0,
    )
    estilo.map(
        'Perigo.TButton',
        background=[('active', CORES['perigo_hover']), ('disabled', '#d6a3a3')],
    )

    estilo.configure(
        'Secundario.TButton',
        background='#ffffff',
        foreground=CORES['primaria'],
        font=(familia, 9, 'bold'),
        padding=(10, 6),
        borderwidth=1,
    )
    estilo.map(
        'Secundario.TButton',
        background=[('active', '#e6eff8')],
    )

    estilo.configure(
        'Treeview',
        background='#ffffff',
        fieldbackground='#ffffff',
        foreground=CORES['texto'],
        rowheight=27,
        borderwidth=0,
        font=(familia, 9),
    )
    estilo.configure(
        'Treeview.Heading',
        background='#e4ecf4',
        foreground=CORES['primaria'],
        font=(familia, 9, 'bold'),
        relief='flat',
        padding=(6, 6),
    )
    estilo.map(
        'Treeview',
        background=[('selected', '#cfe2f3')],
        foreground=[('selected', CORES['primaria'])],
    )

    estilo.configure('TNotebook', background=CORES['fundo'], borderwidth=0)
    estilo.configure(
        'TNotebook.Tab',
        background='#dce6f1',
        foreground=CORES['texto'],
        padding=(14, 7),
        font=(familia, 9, 'bold'),
    )
    estilo.map(
        'TNotebook.Tab',
        background=[('selected', CORES['cartao'])],
        foreground=[('selected', CORES['primaria'])],
    )

    return familia


# ============================= { WIDGETS REUTILIZÁVEIS } ============================= #

class TabelaRolavel(ttk.Frame):
    # Treeview com barras de rolagem vertical e horizontal + mapa de dados por item.

    def __init__(self, master, colunas, altura=12, ao_selecionar=None):
        super().__init__(master, style='Card.TFrame')
        self.__dados_por_iid = {}
        self.__ao_selecionar = ao_selecionar

        ids = [col[0] for col in colunas]
        self.tree = ttk.Treeview(self, columns=ids, show='headings', height=altura, selectmode='browse')

        for col_id, titulo, largura, ancora in colunas:
            self.tree.heading(col_id, text=titulo, anchor=ancora)
            self.tree.column(col_id, width=largura, minwidth=max(50, largura // 2), anchor=ancora, stretch=True)

        barra_v = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        barra_h = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        barra_v.grid(row=0, column=1, sticky='ns')
        barra_h.grid(row=1, column=0, sticky='ew')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        if ao_selecionar is not None:
            self.tree.bind('<<TreeviewSelect>>', self.__disparar_selecao)

    def preencher(self, linhas):
        # linhas: iterável de tuplas (valores_tupla, objeto_associado)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.__dados_por_iid.clear()

        for indice, (valores, objeto) in enumerate(linhas):
            tag = 'par' if indice % 2 == 0 else 'impar'
            iid = self.tree.insert('', 'end', values=valores, tags=(tag,))
            self.__dados_por_iid[iid] = objeto

        self.tree.tag_configure('par', background='#ffffff')
        self.tree.tag_configure('impar', background='#f8fafc')

    def selecionado(self):
        selecao = self.tree.selection()
        if not selecao:
            return None
        return self.__dados_por_iid.get(selecao[0])

    def __disparar_selecao(self, _evento=None):
        if self.__ao_selecionar:
            self.__ao_selecionar(self.selecionado())


class DialogoBase(tk.Toplevel):
    # Janela modal centralizada sobre a janela-mãe.

    def __init__(self, master, titulo, largura=460, altura=None):
        super().__init__(master)
        self.title(titulo)
        self.configure(bg=CORES['cartao'])
        self.resizable(False, False)
        self.resultado = None

        self.transient(master)
        self.protocol('WM_DELETE_WINDOW', self.cancelar)
        self.bind('<Escape>', lambda _e: self.cancelar())

        self.corpo = ttk.Frame(self, style='Card.TFrame', padding=20)
        self.corpo.pack(fill='both', expand=True)

        self._largura_alvo = largura
        self._altura_alvo = altura

    def finalizar_layout(self):
        self.update_idletasks()
        largura = max(self._largura_alvo, self.winfo_reqwidth())
        altura = self._altura_alvo or self.winfo_reqheight()

        pai = self.master.winfo_toplevel()
        px = pai.winfo_rootx() + (pai.winfo_width() - largura) // 2
        py = pai.winfo_rooty() + (pai.winfo_height() - altura) // 2
        self.geometry(f'{largura}x{altura}+{max(px, 20)}+{max(py, 20)}')
        self.grab_set()
        self.focus_set()

    def cancelar(self):
        self.resultado = None
        self.destroy()


def criar_card_indicador(master, rotulo, valor, detalhe, cor_borda=None):
    externo = tk.Frame(master, bg=cor_borda or CORES['primaria'], padx=0, pady=0)
    interno = ttk.Frame(externo, style='Card.TFrame', padding=(14, 12))
    interno.pack(fill='both', expand=True, padx=(4, 0))

    ttk.Label(interno, text=rotulo.upper(), style='IndicadorRotulo.TLabel').pack(anchor='w')
    lbl_valor = ttk.Label(interno, text=str(valor), style='IndicadorValor.TLabel')
    lbl_valor.pack(anchor='w', pady=(4, 2))
    lbl_detalhe = ttk.Label(interno, text=detalhe, style='CardSuave.TLabel')
    lbl_detalhe.pack(anchor='w')

    return externo, lbl_valor, lbl_detalhe
