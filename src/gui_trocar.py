import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

try:
    from src.trocar import carregar_ensalamento, salvar_ensalamento, movimento_e_valido
except ImportError:
    from trocar import carregar_ensalamento, salvar_ensalamento, movimento_e_valido


def carregar_regras_evento():
    caminho_config = "public/config/config_evento.json"
    min_trabalhos = 4
    max_trabalhos = 6
    if os.path.exists(caminho_config):
        try:
            with open(caminho_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                min_trabalhos = config.get("MIN_TRABALHOS_SESSAO", 4)
                max_trabalhos = config.get("MAX_TRABALHOS_ORIENTADOR_SESSAO", 6)
        except Exception:
            pass
    return min_trabalhos, max_trabalhos


class JanelaTrocar(tk.Toplevel):
    COLUNAS_TREE = ('Apresentador(a)', 'Orientador(a)', 'Data', 'Sala', 'Horário')

    def __init__(self, parent, nome_base):
        super().__init__(parent)
        self.title(f"Ajuste Manual Avançado - {nome_base}")
        self.geometry("1200x700")
        self.nome_base = nome_base

        self.min_trabalhos, self.max_trabalhos = carregar_regras_evento()

        try:
            self.df, self.orientadores_por_bloco = carregar_ensalamento(nome_base)
            if self.df is None or self.df.empty:
                raise FileNotFoundError
        except Exception:
            self.destroy()
            messagebox.showerror(
                "Erro",
                f"Arquivos de ensalamento para '{nome_base}' não foram encontrados ou estão vazios.",
                parent=parent
            )
            return

        self.opcoes_validas = []
        self.trabalho_original = None
        self.idx_original = None
        self.resultados = []

        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        busca_frame = ttk.LabelFrame(main_frame, text="1. Buscar Apresentador ou Orientador")
        busca_frame.pack(fill=tk.X, pady=(0, 10))

        entry_frame = tk.Frame(busca_frame)
        entry_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(entry_frame, text="Termo de Busca:").pack(side=tk.LEFT)
        self.termo_busca_var = tk.StringVar()
        self.busca_entry = ttk.Entry(entry_frame, textvariable=self.termo_busca_var, width=50)
        self.busca_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.busca_entry.bind("<Return>", self.executar_busca)

        radio_frame = tk.Frame(busca_frame)
        radio_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.search_type = tk.StringVar(value="Apresentador(a)")

        ttk.Radiobutton(
            radio_frame,
            text="Buscar por Apresentador",
            variable=self.search_type,
            value="Apresentador(a)"
        ).pack(side=tk.LEFT)

        ttk.Radiobutton(
            radio_frame,
            text="Buscar por Orientador",
            variable=self.search_type,
            value="Orientador(a)"
        ).pack(side=tk.LEFT, padx=20)

        self.btn_encontrar = ttk.Button(radio_frame, text="Buscar", command=self.executar_busca)
        self.btn_encontrar.pack(side=tk.RIGHT, padx=5)

        panels_frame = tk.Frame(main_frame)
        panels_frame.pack(fill=tk.BOTH, expand=True)

        # Painel da Esquerda (Resultados da Busca)
        resultados_frame = ttk.LabelFrame(panels_frame, text="2. Resultados da Busca (clique para selecionar)")
        resultados_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.resultados_tree = ttk.Treeview(resultados_frame, columns=self.COLUNAS_TREE, show='headings')
        self._configurar_treeview(self.resultados_tree)
        self.resultados_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.resultados_tree.bind('<<TreeviewSelect>>', self.on_resultado_select)

        # Painel da Direita (Opções para Troca)
        opcoes_frame = ttk.LabelFrame(panels_frame, text="3. Opções Disponíveis para o Trabalho Selecionado")
        opcoes_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.opcoes_tree = ttk.Treeview(opcoes_frame, columns=self.COLUNAS_TREE, show='headings')
        self._configurar_treeview(self.opcoes_tree)
        self.opcoes_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        confirm_frame = tk.Frame(main_frame)
        confirm_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_confirmar = ttk.Button(
            confirm_frame,
            text="Realizar Troca/Movimento Selecionado",
            command=self.executar_alteracao,
            state=tk.DISABLED
        )
        self.btn_confirmar.pack(fill=tk.X)

    def _configurar_treeview(self, tree):
        tree.heading('Apresentador(a)', text='Apresentador(a)')
        tree.heading('Orientador(a)', text='Orientador(a)')
        tree.heading('Data', text='Data')
        tree.heading('Sala', text='Sala')
        tree.heading('Horário', text='Horário')

        tree.column('Apresentador(a)', width=180)
        tree.column('Orientador(a)', width=180)
        tree.column('Data', width=80, anchor='center')
        tree.column('Sala', width=80, anchor='center')
        tree.column('Horário', width=110, anchor='center')

    def formatar_horario(self, horario_str):
        h_str = str(horario_str)
        try:
            horario_fim = (pd.to_datetime(h_str, format='%H:%M') + pd.Timedelta(minutes=15)).strftime('%H:%M')
            return f"{h_str}-{horario_fim}"
        except Exception:
            return h_str

    def executar_busca(self, event=None):
        termo_busca = self.termo_busca_var.get().strip().lower()
        if not termo_busca:
            messagebox.showerror("Erro", "Digite um termo para buscar.", parent=self)
            return

        self.resultados_tree.delete(*self.resultados_tree.get_children())
        self.opcoes_tree.delete(*self.opcoes_tree.get_children())
        self.btn_confirmar.config(state=tk.DISABLED)

        coluna_busca = self.search_type.get()
        if coluna_busca not in self.df.columns:
            coluna_busca = self.df.columns[0]

        self.resultados = self.df[
            self.df[coluna_busca].astype(str).str.lower().str.contains(termo_busca, na=False)].to_dict('records')

        if not self.resultados:
            self.resultados_tree.insert('', tk.END, values=("Nenhum resultado encontrado.", "", "", "", ""))
        else:
            for i, trab in enumerate(self.resultados):
                horario_formatado = self.formatar_horario(trab.get('Horário', '08:30'))
                valores_linha = (
                    trab.get('Apresentador(a)', 'N/A'),
                    trab.get('Orientador(a)', 'N/A'),
                    f"Dia {trab.get('Dia', '1')}",
                    trab.get('Sala', 'N/A'),
                    horario_formatado
                )
                self.resultados_tree.insert('', tk.END, iid=i, values=valores_linha)

    def on_resultado_select(self, event=None):
        selecao = self.resultados_tree.selection()
        if not selecao:
            return

        try:
            idx_lista_resultados = int(selecao[0])
            self.trabalho_original = self.resultados[idx_lista_resultados]
        except (ValueError, IndexError):
            return

        matching_indices = self.df[
            (self.df['Apresentador(a)'] == self.trabalho_original['Apresentador(a)']) &
            (self.df['Título'] == self.trabalho_original['Título'])
        ].index

        if matching_indices.empty:
            return

        self.idx_original = matching_indices[0]

        self.opcoes_tree.delete(*self.opcoes_tree.get_children())
        self.btn_confirmar.config(state=tk.DISABLED)
        self.opcoes_validas = []

        bloco_origem = self.trabalho_original.get('Bloco_ID', '')
        sala_origem = self.trabalho_original.get('Sala', '')

        df_sessao_origem = self.df[(self.df['Bloco_ID'] == bloco_origem) & (self.df['Sala'] == sala_origem)]

        # 1. Busca por opções de TROCA entre dois trabalhos
        for idx_alvo, trabalho_alvo in self.df.iterrows():
            if idx_alvo == self.idx_original:
                continue

            mov_A = movimento_e_valido(
                self.trabalho_original['Orientador(a)'],
                trabalho_alvo['Bloco_ID'],
                trabalho_alvo['Sala'],
                self.orientadores_por_bloco
            )
            mov_B = movimento_e_valido(
                trabalho_alvo['Orientador(a)'],
                self.trabalho_original['Bloco_ID'],
                self.trabalho_original['Sala'],
                self.orientadores_por_bloco
            )

            if mov_A and mov_B:
                self.opcoes_validas.append({"tipo": "TROCAR", "idx_alvo": idx_alvo, "alvo": trabalho_alvo.to_dict()})

        # 2. Busca por opções de MOVER para vaga
        if len(df_sessao_origem) - 1 >= self.min_trabalhos:
            sessoes_com_vagas = self.df.groupby(['Dia', 'Sessão', 'Sala', 'Bloco_ID']).filter(
                lambda x: len(x) < self.max_trabalhos
            )
            sessoes_unicas_com_vagas = sessoes_com_vagas[['Dia', 'Sessão', 'Sala', 'Bloco_ID']].drop_duplicates()

            for _, sessao_alvo in sessoes_unicas_com_vagas.iterrows():
                if movimento_e_valido(
                        self.trabalho_original['Orientador(a)'],
                        sessao_alvo['Bloco_ID'],
                        sessao_alvo['Sala'],
                        self.orientadores_por_bloco
                ):
                    self.opcoes_validas.append({"tipo": "MOVER", "destino": sessao_alvo.to_dict()})

        if not self.opcoes_validas:
            self.opcoes_tree.insert('', tk.END, values=("Nenhuma opção válida encontrada.", "", "", "", ""))
        else:
            for i, opcao in enumerate(self.opcoes_validas):
                if opcao['tipo'] == 'MOVER':
                    destino = opcao['destino']
                    valores_linha = (
                        "--- MOVER PARA VAGA ---",
                        "",
                        f"Dia {destino['Dia']}",
                        destino['Sala'],
                        destino['Sessão']
                    )
                else:
                    alvo = opcao['alvo']
                    horario_alvo_fmt = self.formatar_horario(alvo.get('Horário', '08:30'))

                    valores_linha = (
                        alvo.get('Apresentador(a)', 'N/A'),
                        alvo.get('Orientador(a)', 'N/A'),
                        f"Dia {alvo.get('Dia', '1')}",
                        alvo.get('Sala', 'N/A'),
                        horario_alvo_fmt
                    )
                self.opcoes_tree.insert('', tk.END, iid=i, values=valores_linha)
            self.btn_confirmar.config(state=tk.NORMAL)

    def executar_alteracao(self):
        selecao_opcao = self.opcoes_tree.selection()
        if not selecao_opcao:
            messagebox.showerror("Erro", "Selecione uma opção da tabela da direita.", parent=self)
            return

        try:
            escolha_idx = int(selecao_opcao[0])
            opcao_escolhida = self.opcoes_validas[escolha_idx]

            if opcao_escolhida['tipo'] == 'MOVER':
                destino = opcao_escolhida['destino']
                self.df.loc[self.idx_original, ['Dia', 'Sessão', 'Sala', 'Bloco_ID']] = [
                    destino['Dia'],
                    destino['Sessão'],
                    destino['Sala'],
                    destino['Bloco_ID']
                ]
                msg_sucesso = "Movimentação realizada!"

            elif opcao_escolhida['tipo'] == 'TROCAR':
                idx_alvo = opcao_escolhida['idx_alvo']

                loc_original = (
                    self.trabalho_original['Dia'],
                    self.trabalho_original['Sessão'],
                    self.trabalho_original['Horário'],
                    self.trabalho_original['Sala'],
                    self.trabalho_original['Bloco_ID']
                )

                trabalho_alvo = self.df.loc[idx_alvo]
                loc_alvo = (
                    trabalho_alvo['Dia'],
                    trabalho_alvo['Sessão'],
                    trabalho_alvo['Horário'],
                    trabalho_alvo['Sala'],
                    trabalho_alvo['Bloco_ID']
                )

                self.df.loc[self.idx_original, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_alvo
                self.df.loc[idx_alvo, ['Dia', 'Sessão', 'Horário', 'Sala', 'Bloco_ID']] = loc_original
                msg_sucesso = "Troca realizada!"

            if messagebox.askyesno("Confirmar e Salvar", f"{msg_sucesso}\nDeseja salvar as alterações?", parent=self):
                salvar_ensalamento(self.df, self.nome_base)
                messagebox.showinfo("Sucesso", "Alterações salvas! A janela será fechada.", parent=self)
                self.destroy()
            else:
                messagebox.showinfo("Cancelado", "As alterações foram descartadas.", parent=self)

        except (ValueError, IndexError, KeyError) as e:
            messagebox.showerror("Erro", f"Seleção ou alteração inválida: {e}", parent=self)