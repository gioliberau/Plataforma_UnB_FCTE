from datetime import date
import tkinter as tk
from tkinter import ttk

from code_py import consultas_publicas as cp

from ..estilo import CORES, formatar_data_br
from .base import TelaBase, criar_bloco


# ============================= { TELA DO CARDÁPIO DO RU } ============================= #

class TelaCardapio(TelaBase):

    def __init__(self, master, sessao, ao_status=None, ao_navegar=None):
        super().__init__(master, sessao, ao_status=ao_status, ao_navegar=ao_navegar)
        self.__ja_tentou_auto = False
        self.__mapa_dias = {}
        self.__mapa_dietas = {rotulo: chave for chave, rotulo in cp.dietas.items()}

        self.criar_cabecalho(
            'Cardápio do Restaurante Universitário — Gama',
            'Consulte as refeições do dia conforme sua preferência alimentar.',
        )

        # Barra de filtros
        barra = criar_bloco(self, padding=12)
        barra.pack(fill='x', pady=(0, 10))

        linha = ttk.Frame(barra, style='Card.TFrame')
        linha.pack(fill='x')

        ttk.Label(linha, text='Dia:', style='Card.TLabel').pack(side='left')
        self.__var_dia = tk.StringVar()
        self.__cmb_dia = ttk.Combobox(linha, textvariable=self.__var_dia, state='readonly', width=28)
        self.__cmb_dia.pack(side='left', padx=(6, 16))
        self.__cmb_dia.bind('<<ComboboxSelected>>', lambda _e: self.__renderizar_dia())

        ttk.Label(linha, text='Preferência alimentar:', style='Card.TLabel').pack(side='left')
        self.__var_dieta = tk.StringVar(value=cp.dietas['padrao'])
        self.__cmb_dieta = ttk.Combobox(
            linha,
            textvariable=self.__var_dieta,
            values=list(self.__mapa_dietas),
            state='readonly',
            width=24,
        )
        self.__cmb_dieta.pack(side='left', padx=(6, 12))
        self.__cmb_dieta.bind('<<ComboboxSelected>>', lambda _e: self.__renderizar_dia())

        if self._eh_admin:
            self.__btn_atualizar = ttk.Button(
                linha,
                text='Atualizar do site do RU',
                style='Primario.TButton',
                command=self.__atualizar_manual,
            )
            self.__btn_atualizar.pack(side='right')

        self.__lbl_aviso = tk.Label(
            self,
            text='',
            bg=CORES['aviso_fundo'],
            fg=CORES['aviso_texto'],
            font=('Sans', 9, 'bold'),
            padx=12,
            pady=6,
            anchor='w',
        )

        self.__container = ttk.Frame(self, style='TFrame')
        self.__container.pack(fill='both', expand=True, pady=(6, 0))

    def atualizar(self):
        self.__carregar_dias()
        if not self.__ja_tentou_auto:
            self.__ja_tentou_auto = True
            self.executar_em_segundo_plano(
                cp.garantir_cardapio_atualizado,
                self.__apos_auto_atualizacao,
                mensagem_status='Verificando cardápio mais recente do RU...',
                silencioso=True,
            )

    def __apos_auto_atualizacao(self, atualizou):
        if atualizou:
            self.__carregar_dias()

    def __carregar_dias(self):
        try:
            datas = cp.datas_disponiveis()
        except RuntimeError as erro:
            self.tratar_erro(erro)
            datas = []

        self.__mapa_dias = {}
        rotulos = []
        hoje_iso = date.today().isoformat()
        selecao_padrao = None

        for data_iso in datas:
            rotulo = f'{formatar_data_br(data_iso)} ({cp.nome_dia_semana(data_iso)})'
            self.__mapa_dias[rotulo] = data_iso
            rotulos.append(rotulo)
            if data_iso == hoje_iso:
                selecao_padrao = rotulo

        self.__cmb_dia['values'] = rotulos

        if rotulos:
            if self.__var_dia.get() not in self.__mapa_dias:
                self.__var_dia.set(selecao_padrao or rotulos[-1])
        else:
            self.__var_dia.set('')

        if datas and datas[-1] < hoje_iso:
            self.__lbl_aviso.configure(
                text=f'Aviso: este cardápio está desatualizado (data mais recente: {formatar_data_br(datas[-1])}).'
            )
            if not self.__lbl_aviso.winfo_ismapped():
                self.__lbl_aviso.pack(fill='x', pady=(0, 8), before=self.__container)
        elif self.__lbl_aviso.winfo_ismapped():
            self.__lbl_aviso.pack_forget()

        self.__renderizar_dia()

    def __renderizar_dia(self):
        for filho in self.__container.winfo_children():
            filho.destroy()

        data_iso = self.__mapa_dias.get(self.__var_dia.get())
        dieta = self.__mapa_dietas.get(self.__var_dieta.get(), 'padrao')

        if not data_iso:
            bloco = criar_bloco(self.__container, padding=18)
            bloco.pack(fill='x')
            ttk.Label(
                bloco,
                text='Nenhum cardápio carregado ainda. Um administrador pode baixá-lo pelo botão acima.',
                style='CardSuave.TLabel',
            ).pack(anchor='w')
            return

        refeicoes = cp.cardapio_do_dia(data_iso)
        if not refeicoes:
            bloco = criar_bloco(self.__container, padding=18)
            bloco.pack(fill='x')
            ttk.Label(
                bloco,
                text=f'Não há refeições cadastradas para {formatar_data_br(data_iso)}.',
                style='CardSuave.TLabel',
            ).pack(anchor='w')
            return

        grade = ttk.Frame(self.__container, style='TFrame')
        grade.pack(fill='both', expand=True)
        for col in range(len(refeicoes)):
            grade.columnconfigure(col, weight=1)
        grade.rowconfigure(0, weight=1)

        for idx, (chave, itens) in enumerate(refeicoes.items()):
            bloco = criar_bloco(grade, titulo=cp.refeicoes[chave], padding=14)
            bloco.grid(row=0, column=idx, sticky='nsew', padx=(0 if idx == 0 else 10, 0))

            linhas = cp.formatar_refeicao(itens, dieta)
            if not linhas:
                ttk.Label(bloco, text='Sem itens para esta dieta.', style='CardSuave.TLabel').pack(anchor='w')
                continue

            for rotulo, texto in linhas:
                item_frame = ttk.Frame(bloco, style='Card.TFrame')
                item_frame.pack(fill='x', pady=3)
                ttk.Label(item_frame, text=f'{rotulo}:', style='IndicadorRotulo.TLabel').pack(anchor='w')
                ttk.Label(item_frame, text=texto, style='Card.TLabel', wraplength=250, justify='left').pack(anchor='w')

    def __atualizar_manual(self):
        if not self.confirmar('Baixar o PDF do cardápio mais recente no site do RU agora?'):
            return

        self.__btn_atualizar.configure(state='disabled')

        def tarefa():
            return cp.atualizar_cardapio_ru(self._conta)

        def ao_sucesso(total):
            self.__btn_atualizar.configure(state='normal')
            self.__carregar_dias()
            self.mostrar_info(f'Cardápio atualizado com sucesso ({total} refeições carregadas).')

        def ao_erro(erro):
            self.__btn_atualizar.configure(state='normal')
            self.tratar_erro(erro)

        self.executar_em_segundo_plano(tarefa, ao_sucesso, 'Baixando cardápio do RU...', ao_erro=ao_erro)
