import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from src.trocar import carregar_ensalamento, salvar_ensalamento, movimento_e_valido

MIN_TRABALHOS_SESSAO = 4
MAX_TRABALHOS_SESSAO = 6


class JanelaTrocar(tk.Toplevel):
    # --- ALTERAÇÃO 1: Trocada a coluna 'Título' por 'Data' ---
    COLUNAS_TREE = ('Apresentador(a)', 'Orientador(a)', 'Data', 'Sala', 'Horário')

    def __init__(self, parent, nome_base):
        super().__init__(parent)
        self.title(f"Ajuste Manual Avançado - {nome_base}")
        self.geometry("1200x700")
        self.nome_base = nome_base

        try:
            self.df, self.orientadores_por_bloco = carregar_ensalamento(nome_base)
            if self.df is None: raise FileNotFoundError
        except FileNotFoundError:
            self.destroy()
            messagebox.showerror("Erro", f"Arquivos de ensalamento para '{nome_base}' não encontrados.")
            return

        self.opcoes_validas = []
        self.trabalho_original = None
        self.idx_original = None
        self.resultados_busca = []

        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        busca_frame = ttk.LabelFrame(main_frame, text="1. Buscar Apresentador ou Orientador")
        busca_frame.pack(fill=tk.X, pady=(0, 10))
        entry_frame = tk.Frame(busca_frame);
        entry_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(entry_frame, text="Termo de Busca:").pack(side=tk.LEFT)
        self.termo_busca_var = tk.StringVar()
        self.busca_entry = ttk.Entry(entry_frame, textvariable=self.termo_busca_var, width=50)
        self.busca_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.busca_entry.bind("<Return>", self.executar_busca)
        radio_frame = tk.Frame(busca_frame);
        radio_frame.pack(fill=tk.X, padx=5)
        self.search_type = tk.StringVar(value="Apresentador(a)")
        ttk.Radiobutton(radio_frame, text="Buscar por Apresentador", variable=self.search_type,
                        value="Apresentador(a)").pack(side=tk.LEFT)
        ttk.Radiobutton(radio_frame, text="Buscar por Orientador", variable=self.search_type,
                        value="Orientador(a)").pack(side=tk.LEFT, padx=20)
        self.btn_encontrar = ttk.Button(radio_frame, text="Buscar", command=self.executar_busca)
        self.btn_encontrar.pack(side=tk.RIGHT, padx=5, pady=5)

        panels_frame = tk.Frame(main_frame)
        panels_frame.pack(fill=tk.BOTH, expand=True)

        resultados_frame = ttk.LabelFrame(panels_frame, text="2. Resultados da Busca (clique para selecionar)")
        resultados_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.resultados_tree = ttk.Treeview(resultados_frame, columns=self.COLUNAS_TREE, show='headings')
        self._configurar_treeview(self.resultados_tree)
        self.resultados_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.resultados_tree.bind('<<TreeviewSelect>>', self.on_resultado_select)

        opcoes_frame = ttk.LabelFrame(panels_frame, text="3. Opções Disponíveis para o Trabalho Selecionado")
        opcoes_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.opcoes_tree = ttk.Treeview(opcoes_frame, columns=self.COLUNAS_TREE, show='headings')
        self._configurar_treeview(self.opcoes_tree)
        self.opcoes_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        confirm_frame = tk.Frame(main_frame)
        confirm_frame.pack(fill=tk.X, pady=(10, 0))
        self.btn_confirmar = ttk.Button(confirm_frame, text="Realizar Troca/Movimento Selecionado",
                                        command=self.executar_alteracao, state=tk.DISABLED)
        self.btn_confirmar.pack(fill=tk.X)

    def _configurar_treeview(self, tree):
        # --- ALTERAÇÃO 2: Configuração da coluna 'Data' no lugar de 'Título' ---
        tree.heading('Apresentador(a)', text='Apresentador(a)')
        tree.heading('Orientador(a)', text='Orientador(a)')
        tree.heading('Data', text='Data')
        tree.heading('Sala', text='Sala')
        tree.heading('Horário', text='Horário')

        tree.column('Apresentador(a)', width=180)
        tree.column('Orientador(a)', width=180)
        tree.column('Data', width=80, anchor='center')
        tree.column('Sala', width=80, anchor='center')
        tree.column('Horário', width=100, anchor='center')

    def executar_busca(self, event=None):
        termo_busca = self.termo_busca_var.get().strip().lower()
        if not termo_busca: messagebox.showerror("Erro", "Digite um termo para buscar."); return

        self.resultados_tree.delete(*self.resultados_tree.get_children())
        self.opcoes_tree.delete(*self.opcoes_tree.get_children())
        self.btn_confirmar.config(state=tk.DISABLED)

        coluna_busca = self.search_type.get()
        self.resultados = self.df[self.df[coluna_busca].str.lower().str.contains(termo_busca, na=False)].to_dict(
            'records')

        if not self.resultados:
            self.resultados_tree.insert('', tk.END, values=("Nenhum resultado encontrado.", "", "", "", ""))
        else:
            for i, trab in enumerate(self.resultados):
                horario_fim = (pd.to_datetime(trab['Horário']) + pd.Timedelta(minutes=15)).strftime('%H:%M')
                horario_formatado = f"{trab['Horário']}-{horario_fim}"

                # --- ALTERAÇÃO 3: Usar 'Dia' no lugar de 'Título' ao popular a tabela ---
                valores_linha = (
                    trab['Apresentador(a)'],
                    trab['Orientador(a)'],
                    f"Dia {trab['Dia']}",  # Adicionado "Dia " para clareza
                    trab['Sala'],
                    horario_formatado
                )
                self.resultados_tree.insert('', tk.END, iid=i, values=valores_linha)

    def on_resultado_select(self, event=None):
        selecao = self.resultados_tree.selection()
        if not selecao: return

        idx_lista_resultados = int(selecao[0])
        self.trabalho_original = self.resultados[idx_lista_resultados]

        self.idx_original = self.df[
            (self.df['Apresentador(a)'] == self.trabalho_original['Apresentador(a)']) &
            (self.df['Título'] == self.trabalho_original['Título'])
            ].index[0]

        self.opcoes_tree.delete(*self.opcoes_tree.get_children())
        self.btn_confirmar.config(state=tk.DISABLED)
        self.opcoes_validas = []

        df_sessao_origem = self.df[(self.df['Bloco_ID'] == self.trabalho_original['Bloco_ID']) & (
                    self.df['Sala'] == self.trabalho_original['Sala'])]
        for idx_alvo, trabalho_alvo in self.df.iterrows():
            if idx_alvo == self.idx_original: continue
            mov_A = movimento_e_valido(self.trabalho_original['Orientador(a)'], trabalho_alvo['Bloco_ID'],
                                       trabalho_alvo['Sala'], self.orientadores_por_bloco)
            mov_B = movimento_e_valido(trabalho_alvo['Orientador(a)'], self.trabalho_original['Bloco_ID'],
                                       self.trabalho_original['Sala'], self.orientadores_por_bloco)
            if mov_A and mov_B: self.opcoes_validas.append(
                {"tipo": "TROCAR", "idx_alvo": idx_alvo, "alvo": trabalho_alvo})
        if len(df_sessao_origem) - 1 >= MIN_TRABALHOS_SESSAO:
            sessoes_com_vagas = self.df.groupby(['Dia', 'Sessão', 'Sala', 'Bloco_ID']).filter(
                lambda x: len(x) < MAX_TRABALHOS_SESSAO)
            sessoes_unicas_com_vagas = sessoes_com_vagas[['Dia', 'Sessão', 'Sala', 'Bloco_ID']].drop_duplicates()
            for _, sessao_alvo in sessoes_unicas_com_vagas.iterrows():
                if movimento_e_valido(self.trabalho_original['Orientador(a)'], sessao_alvo['Bloco_ID'],
                                      sessao_alvo['Sala'], self.orientadores_por_bloco):
                    self.opcoes_validas.append({"tipo": "MOVER", "destino": sessao_alvo.to_dict()})

        if not self.opcoes_validas:
            self.opcoes_tree.insert('', tk.END, values=("Nenhuma opção válida encontrada.", "", "", "", ""))
        else:
            for i, opcao in enumerate(self.opcoes_validas):
                # --- ALTERAÇÃO 4: Usar 'Dia' no lugar de 'Título' também nas opções ---
                if opcao['tipo'] == 'MOVER':
                    destino = opcao['destino']
                    valores_linha = (f"--- MOVER PARA VAGA ---", "", f"Dia {destino['Dia']}", destino['Sala'],
                                     destino['Sessão'])
                else:  # 'TROCAR'
                    alvo = opcao['alvo']
                    horario_fim_alvo = (pd.to_datetime(alvo['Horário']) + pd.Timedelta(minutes=15)).strftime('%H:%M')
                    horario_formatado_alvo = f"{alvo['Horário']}-{horario_fim_alvo}"
                    valores_linha = (
                        alvo['Apresentador(a)'],
                        alvo['Orientador(a)'],
                        f"Dia {alvo['Dia']}",
                        alvo['Sala'],
                        horario_formatado_alvo
                    )
                self.opcoes_tree.insert('', tk.END, iid=i, values=valores_linha)
            self.btn_confirmar.config(state=tk.NORMAL)

    def executar_alteracao(self):
        selecao_opcao = self.opcoes_tree.selection()
        if not selecao_opcao:
            messagebox.showerror("Erro", "Selecione uma opção da tabela da direita.");
            return

        try:
            escolha_idx = int(selecao_opcao[0])
            opcao_escolhida = self.opcoes_validas[escolha_idx]

            if opcao_escolhida['tipo'] == 'MOVER':
                destino = opcao_escolhida['destino']
                self.df.loc[self.idx_original, ['Dia', 'Sessão', 'Sala', 'Bloco_ID', 'Horário']] = [destino['Dia'],
                                                                                                    destino['Sessão'],
                                                                                                    destino['Sala'],
                                                                                                    destino['Bloco_ID'],
                                                                                                    '23:59']
                msg_sucesso = "Movimentação realizada!"
            elif opcao_escolhida['tipo'] == 'TROCAR':
                idx_alvo = opcao_escolhida['idx_alvo']
                loc_original = (self.trabalho_original['Dia'], self.trabalho_original['Sessão'],
                                self.trabalho_original['Horário'], self.trabalho_original['Sala'],
                                self.trabalho_original['Bloco_ID'])
                trabalho_alvo = self.df.loc[idx_alvo]
                loc_alvo = (trabalho_alvo['Dia'], trabalho_alvo['Sessão'], trabalho_alvo['Horário'],
                            trabalho_alvo['Sala'], trabalho_alvo['Bloco_ID'])
                self.df.loc[self.idx_original, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_alvo
                self.df.loc[idx_alvo, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_original
                msg_sucesso = "Troca realizada!"

            if messagebox.askyesno("Confirmar e Salvar", f"{msg_sucesso}\nDeseja salvar as alterações?"):
                salvar_ensalamento(self.df, self.nome_base)
                messagebox.showinfo("Sucesso", "Alterações salvas! A janela será fechada.")
                self.destroy()
            else:
                messagebox.showinfo("Cancelado", "As alterações foram descartadas.")
        except (ValueError, IndexError):
            messagebox.showerror("Erro", "Seleção inválida.")