import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd


def carregar_ensalamento_completo(nome_base):
    dfs = []
    for dia in [1, 2]:
        caminho = f"public/csv/{nome_base}_dia{dia}.csv"
        try:
            df_dia = pd.read_csv(caminho);
            df_dia['Dia'] = dia;
            dfs.append(df_dia)
        except FileNotFoundError:
            pass
    if not dfs: return None
    return pd.concat(dfs, ignore_index=True)


class JanelaConsultar(tk.Toplevel):
    def __init__(self, parent, nome_base):
        super().__init__(parent)
        self.title(f"Consultar Ensalamento - {nome_base}")
        self.geometry("700x500")

        self.df = carregar_ensalamento_completo(nome_base)
        if self.df is None:
            self.destroy()
            tk.messagebox.showerror("Erro", f"Arquivos de ensalamento para '{nome_base}' não encontrados.")
            return

        # --- Widgets da Interface ---
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame de busca
        search_frame = tk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", self.executar_busca)  # Permite buscar com Enter

        self.search_type = tk.StringVar(value="Apresentador(a)")
        ttk.Radiobutton(search_frame, text="Por Apresentador", variable=self.search_type, value="Apresentador(a)").pack(
            side=tk.LEFT, padx=5)
        ttk.Radiobutton(search_frame, text="Por Orientador", variable=self.search_type, value="Orientador(a)").pack(
            side=tk.LEFT)

        ttk.Button(search_frame, text="Buscar", command=self.executar_busca).pack(side=tk.LEFT, padx=10)

        # Caixa de texto para resultados
        self.result_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, bg="#fdfdfd")
        self.result_text.pack(fill=tk.BOTH, expand=True)

        self.executar_busca(listar_tudo=True)  # Mostra tudo ao abrir

    def executar_busca(self, event=None, listar_tudo=False):
        self.result_text.delete(1.0, tk.END)
        termo_busca = self.search_var.get().strip().lower()

        if listar_tudo:
            resultados = self.df.sort_values(by="Apresentador(a)")
            self.result_text.insert(tk.END, "--- LISTANDO TODOS OS TRABALHOS ---\n\n")
        elif not termo_busca:
            self.result_text.insert(tk.END, "Digite um termo para buscar.")
            return
        else:
            coluna_busca = self.search_type.get()
            resultados = self.df[self.df[coluna_busca].str.lower().str.contains(termo_busca, na=False)]
            self.result_text.insert(tk.END, f"--- RESULTADOS DA BUSCA POR '{termo_busca}' ---\n\n")

        if resultados.empty and not listar_tudo:
            self.result_text.insert(tk.END, "Nenhum resultado encontrado.")
        else:
            for _, trabalho in resultados.iterrows():
                self.result_text.insert(tk.END, f"Apresentador(a): {trabalho['Apresentador(a)']}\n")
                self.result_text.insert(tk.END, f"  Orientador(a): {trabalho['Orientador(a)']}\n")
                self.result_text.insert(tk.END, f"  Título: {trabalho['Título']}\n")
                self.result_text.insert(tk.END,
                                        f"  --> LOCAL: Dia {trabalho['Dia']}, Sala {trabalho['Sala']}, Horário: {trabalho['Horário']}\n")
                self.result_text.insert(tk.END, "-" * 40 + "\n")