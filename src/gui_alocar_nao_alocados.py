import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

from src.trocar import (
    carregar_ensalamento,
    carregar_trabalhos_nao_alocados,
    forcar_alocacao_manual
)
from src.sala import carregar_config_geral


class JanelaCadastrarAluno(tk.Toplevel):
    """Janela Modal para criar um novo trabalho do zero."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cadastrar Novo Aluno/Trabalho")
        self.geometry("500x320")
        self.resizable(False, False)
        self.resultado = None

        main_frame = tk.Frame(self, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Apresentador(a):", font=("Helvetica", 9, "bold")).pack(anchor='w')
        self.entry_apresentador = ttk.Entry(main_frame)
        self.entry_apresentador.pack(fill=tk.X, pady=(0, 10))

        tk.Label(main_frame, text="Orientador(a):", font=("Helvetica", 9, "bold")).pack(anchor='w')
        self.entry_orientador = ttk.Entry(main_frame)
        self.entry_orientador.pack(fill=tk.X, pady=(0, 10))

        tk.Label(main_frame, text="Título do Trabalho:", font=("Helvetica", 9, "bold")).pack(anchor='w')
        self.entry_titulo = ttk.Entry(main_frame)
        self.entry_titulo.pack(fill=tk.X, pady=(0, 15))

        btn_box = tk.Frame(main_frame)
        btn_box.pack(fill=tk.X)

        ttk.Button(btn_box, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_box, text="Adicionar à Lista", command=self.confirmar).pack(side=tk.RIGHT)

        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def confirmar(self):
        apres = self.entry_apresentador.get().strip()
        orient = self.entry_orientador.get().strip()
        tit = self.entry_titulo.get().strip()

        if not apres or not orient or not tit:
            messagebox.showerror("Erro", "Preencha todos os campos para cadastrar o trabalho.", parent=self)
            return

        self.resultado = {
            'Apresentador(a)': apres,
            'Orientador(a)': orient,
            'Título': tit
        }
        self.destroy()


class JanelaAlocarNaoAlocados(tk.Toplevel):
    def __init__(self, parent, nome_base_origem):
        super().__init__(parent)
        self.title(f"Gestão de Repescagem & Alocação Manual - Área Origem: {nome_base_origem}")
        self.geometry("980x680")
        self.nome_base_origem = nome_base_origem

        # Carrega as configurações das áreas para permitir migração entre áreas
        try:
            self.configs = carregar_config_geral()
            config_areas_df = self.configs[1].reset_index() if self.configs[1].index.name == 'nome_base' else self.configs[1]
            self.lista_todas_areas = [str(a) for a in config_areas_df['nome_base'].unique()]
        except Exception:
            self.lista_todas_areas = [nome_base_origem]

        self.lista_nao_alocados = carregar_trabalhos_nao_alocados(nome_base_origem)

        main_frame = tk.Frame(self, padx=12, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---------------------------------------------------------------------
        # SEÇÃO 1: Tabela de Alunos Não Alocados e Ações
        # ---------------------------------------------------------------------
        frame_top = ttk.LabelFrame(main_frame, text=f"1. Alunos Não Alocados em '{nome_base_origem}'")
        frame_top.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        cols = ('Apresentador(a)', 'Orientador(a)', 'Título')
        self.tree_nao_alocados = ttk.Treeview(frame_top, columns=cols, show='headings')
        self.tree_nao_alocados.heading('Apresentador(a)', text='Apresentador(a)')
        self.tree_nao_alocados.heading('Orientador(a)', text='Orientador(a)')
        self.tree_nao_alocados.heading('Título', text='Título')

        self.tree_nao_alocados.column('Apresentador(a)', width=220)
        self.tree_nao_alocados.column('Orientador(a)', width=220)
        self.tree_nao_alocados.column('Título', width=450)

        self.tree_nao_alocados.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_add_manual = ttk.Button(
            frame_top,
            text="+ Cadastrar Aluno Fora do CSV...",
            command=self.cadastrar_aluno_avulso
        )
        btn_add_manual.pack(anchor='e', padx=5, pady=(0, 5))

        self.atualizar_tabela_nao_alocados()

        # ---------------------------------------------------------------------
        # SEÇÃO 2: Escolha do Destino (Área, Dia, Sessão e Sala)
        # ---------------------------------------------------------------------
        frame_destino = ttk.LabelFrame(main_frame, text="2. Selecione a Área e Sessão de Destino")
        frame_destino.pack(fill=tk.X, pady=(0, 10))

        box_inputs = tk.Frame(frame_destino)
        box_inputs.pack(fill=tk.X, padx=10, pady=10)

        # Área Destino (Migração)
        ttk.Label(box_inputs, text="Área Destino:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.combo_area_destino = ttk.Combobox(box_inputs, values=self.lista_todas_areas, width=15, state="readonly")
        self.combo_area_destino.set(nome_base_origem)
        self.combo_area_destino.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.combo_area_destino.bind("<<ComboboxSelected>>", self.ao_mudar_area_destino)

        # Dia
        ttk.Label(box_inputs, text="Dia:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.combo_dia = ttk.Combobox(box_inputs, values=["1", "2"], width=6, state="readonly")
        self.combo_dia.set("1")
        self.combo_dia.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        # Sessão
        ttk.Label(box_inputs, text="Sessão:").grid(row=0, column=4, padx=5, pady=5, sticky='e')
        sessoes_disponiveis = ["Manhã 1", "Manhã 2", "Tarde"]
        self.combo_sessao = ttk.Combobox(box_inputs, values=sessoes_disponiveis, width=12, state="readonly")
        self.combo_sessao.set("Manhã 1")
        self.combo_sessao.grid(row=0, column=5, padx=5, pady=5, sticky='w')

        # Sala
        ttk.Label(box_inputs, text="Sala:").grid(row=0, column=6, padx=5, pady=5, sticky='e')
        self.combo_sala = ttk.Combobox(box_inputs, values=[], width=10, state="readonly")
        self.combo_sala.grid(row=0, column=7, padx=5, pady=5, sticky='w')

        self.carregar_salas_area_destino()

        # ---------------------------------------------------------------------
        # SEÇÃO 3: Botão de Ação
        # ---------------------------------------------------------------------
        self.btn_confirmar = ttk.Button(
            main_frame,
            text="Confirmar e Alocar Aluno na Sessão Escolhida",
            command=self.executar_alocacao
        )
        self.btn_confirmar.pack(fill=tk.X, ipady=5)

    def ao_mudar_area_destino(self, event=None):
        self.carregar_salas_area_destino()

    def carregar_salas_area_destino(self):
        area_alvo = self.combo_area_destino.get()
        try:
            df_ensalado, _ = carregar_ensalamento(area_alvo)
            if df_ensalado is not None and not df_ensalado.empty:
                salas_disponiveis = sorted(list(df_ensalado['Sala'].astype(str).unique()))
            else:
                salas_disponiveis = []
        except Exception:
            salas_disponiveis = []

        self.combo_sala['values'] = salas_disponiveis
        if salas_disponiveis:
            self.combo_sala.set(salas_disponiveis[0])
        else:
            self.combo_sala.set("")

    def atualizar_tabela_nao_alocados(self):
        self.tree_nao_alocados.delete(*self.tree_nao_alocados.get_children())

        if not self.lista_nao_alocados:
            self.tree_nao_alocados.insert('', tk.END, values=("Nenhum aluno pendente na lista!", "", ""))
        else:
            for i, trab in enumerate(self.lista_nao_alocados):
                self.tree_nao_alocados.insert('', tk.END, iid=i, values=(
                    trab.get('Apresentador(a)', 'N/A'),
                    trab.get('Orientador(a)', 'N/A'),
                    trab.get('Título', 'N/A')
                ))

    def cadastrar_aluno_avulso(self):
        janela_cad = JanelaCadastrarAluno(self)
        if janela_cad.resultado:
            self.lista_nao_alocados.append(janela_cad.resultado)
            self.atualizar_tabela_nao_alocados()
            # Seleciona automaticamente o novo aluno cadastrado
            novo_idx = len(self.lista_nao_alocados) - 1
            self.tree_nao_alocados.selection_set(str(novo_idx))
            self.tree_nao_alocados.see(str(novo_idx))

    def executar_alocacao(self):
        selecao = self.tree_nao_alocados.selection()
        if not selecao:
            messagebox.showerror("Atenção", "Selecione um aluno da lista antes de continuar.", parent=self)
            return

        try:
            idx = int(selecao[0])
            trabalho_escolhido = self.lista_nao_alocados[idx]
        except (ValueError, IndexError):
            messagebox.showerror("Erro", "Seleção inválida.", parent=self)
            return

        area_destino = self.combo_area_destino.get()
        dia_alvo = self.combo_dia.get()
        sessao_alvo = self.combo_sessao.get()
        sala_alvo = self.combo_sala.get()

        if not sala_alvo:
            messagebox.showerror("Erro", f"Selecione uma sala válida para a área '{area_destino}'.", parent=self)
            return

        msg_migracao = f" (Migração de Área)" if area_destino != self.nome_base_origem else ""

        confirmar = messagebox.askyesno(
            "Confirmar Alocação Manual",
            f"Deseja inserir o aluno abaixo?{msg_migracao}\n\n"
            f"• Apresentador: {trabalho_escolhido.get('Apresentador(a)')}\n"
            f"• Orientador: {trabalho_escolhido.get('Orientador(a)')}\n\n"
            f"Destino: Área {area_destino} | Dia {dia_alvo} | Sessão: {sessao_alvo} | Sala: {sala_alvo}",
            parent=self
        )

        if confirmar:
            # Carrega o dataframe atual da área de destino
            df_ensalado_dest, _ = carregar_ensalamento(area_destino)
            if df_ensalado_dest is None:
                df_ensalado_dest = pd.DataFrame()

            sucesso = forcar_alocacao_manual(
                df_ensalado_dest,
                trabalho_escolhido,
                dia_alvo,
                sessao_alvo,
                sala_alvo,
                area_destino
            )
            if sucesso:
                messagebox.showinfo("Sucesso", f"Aluno alocado com sucesso na área '{area_destino}'!", parent=self)
                # Recarrega as listas
                self.lista_nao_alocados = carregar_trabalhos_nao_alocados(self.nome_base_origem)
                self.atualizar_tabela_nao_alocados()
                self.carregar_salas_area_destino()