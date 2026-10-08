import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pandas as pd


def carregar_dias_evento():
    caminho_config = "public/config/config_evento.json"
    if os.path.exists(caminho_config):
        try:
            with open(caminho_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("DIAS_EVENTO", 2)
        except Exception:
            pass
    return 2


def carregar_ensalamento_completo(nome_base):
    dfs = []
    dias_evento = carregar_dias_evento()

    for dia in range(1, dias_evento + 1):
        caminho = f"public/csv/{nome_base}_dia{dia}.csv"
        try:
            df_dia = pd.read_csv(caminho, encoding="utf-8-sig")
            df_dia['Dia'] = dia
            dfs.append(df_dia)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            pass

    if not dfs:
        return None

    return pd.concat(dfs, ignore_index=True)


class JanelaConsultar(tk.Toplevel):
    def __init__(self, parent, nome_base):
        super().__init__(parent)
        self.title(f"Consultar Ensalamento - {nome_base}")
        self.geometry("750x520")

        self.df = carregar_ensalamento_completo(nome_base)
        if self.df is None or self.df.empty:
            self.destroy()
            messagebox.showerror(
                "Erro",
                f"Arquivos de ensalamento para '{nome_base}' não foram encontrados ou estão vazios.",
                parent=parent
            )
            return

        # --- Widgets da Interface ---
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame de busca
        search_frame = tk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=35)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", self.executar_busca)

        self.search_type = tk.StringVar(value="Apresentador(a)")

        ttk.Radiobutton(
            search_frame,
            text="Por Apresentador",
            variable=self.search_type,
            value="Apresentador(a)"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            search_frame,
            text="Por Orientador",
            variable=self.search_type,
            value="Orientador(a)"
        ).pack(side=tk.LEFT)

        ttk.Button(search_frame, text="Buscar", command=self.executar_busca).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Listar Todos", command=lambda: self.executar_busca(listar_tudo=True)).pack(
            side=tk.LEFT, padx=2)

        # Caixa de texto para resultados
        self.result_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, bg="#fdfdfd", font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        self.executar_busca(listar_tudo=True)

    def executar_busca(self, event=None, listar_tudo=False):
        self.result_text.delete(1.0, tk.END)
        termo_busca = self.search_var.get().strip().lower()

        if listar_tudo:
            col_ordem = "Apresentador(a)" if "Apresentador(a)" in self.df.columns else self.df.columns[0]
            resultados = self.df.sort_values(by=col_ordem)
            self.result_text.insert(tk.END, "--- LISTANDO TODOS OS TRABALHOS ---\n\n")
        elif not termo_busca:
            self.result_text.insert(tk.END, "Digite um termo no campo de busca.")
            return
        else:
            coluna_busca = self.search_type.get()

            # Se a coluna com nome exato não existir, busca por aproximada
            if coluna_busca not in self.df.columns:
                colunas_possiveis = [c for c in self.df.columns if coluna_busca.split('(')[0] in c]
                coluna_busca = colunas_possiveis[0] if colunas_possiveis else self.df.columns[0]

            resultados = self.df[self.df[coluna_busca].astype(str).str.lower().str.contains(termo_busca, na=False)]
            self.result_text.insert(tk.END, f"--- RESULTADOS DA BUSCA POR '{termo_busca}' ---\n\n")

        if resultados.empty:
            self.result_text.insert(tk.END, "Nenhum resultado encontrado.")
        else:
            for _, trabalho in resultados.iterrows():
                apresentador = trabalho.get('Apresentador(a)', trabalho.get('Apresentador', 'N/A'))
                orientador = trabalho.get('Orientador(a)', trabalho.get('Orientador', 'N/A'))
                titulo = trabalho.get('Título', trabalho.get('Titulo', 'N/A'))
                sala = trabalho.get('Sala', 'N/A')
                horario = trabalho.get('Horário', trabalho.get('Horario', 'N/A'))
                dia = trabalho.get('Dia', 'N/A')

                self.result_text.insert(tk.END, f"Apresentador(a): {apresentador}\n")
                self.result_text.insert(tk.END, f"  Orientador(a) : {orientador}\n")
                self.result_text.insert(tk.END, f"  Título        : {titulo}\n")
                self.result_text.insert(tk.END, f"  --> LOCAL     : Dia {dia}, Sala {sala}, Horário: {horario}\n")
                self.result_text.insert(tk.END, "-" * 55 + "\n")