import json
import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pandas as pd

PASTA_CONFIG = "public/config"
PASTA_PUBLICA = "public"
ARQUIVO_AREAS = os.path.join(PASTA_CONFIG, "config_areas.csv")
ARQUIVO_MAPA = os.path.join(PASTA_CONFIG, "mapa_salas.csv")
ARQUIVO_HORARIOS = os.path.join(PASTA_CONFIG, "horarios_sessoes.csv")
ARQUIVO_EVENTO = os.path.join(PASTA_CONFIG, "config_evento.json")


class JanelaConfig(tk.Toplevel):
    COLUNAS_AREAS = ["nome_base", "nome_completo", "codigo_area", "num_salas", "caminho_arquivo_base"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Assistente de Configuração do Evento")
        self.geometry("980x640")

        if not os.path.exists(PASTA_CONFIG):
            os.makedirs(PASTA_CONFIG, exist_ok=True)
        if not os.path.exists(PASTA_PUBLICA):
            os.makedirs(PASTA_PUBLICA, exist_ok=True)

        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.aba_areas = ttk.Frame(notebook)
        self.aba_salas = ttk.Frame(notebook)
        self.aba_regras = ttk.Frame(notebook)

        notebook.add(self.aba_areas, text='Gerenciar Áreas')
        notebook.add(self.aba_salas, text='Mapear Salas Físicas')
        notebook.add(self.aba_regras, text='Gerenciar Regras Gerais')

        self.criar_aba_areas()
        self.criar_aba_salas()
        self.criar_aba_regras()

    def criar_aba_areas(self):
        frame = self.aba_areas
        ttk.Label(
            frame,
            text="Gerenciar as áreas do evento (config_areas.csv)",
            font=("Helvetica", 12, "bold")
        ).pack(pady=10)

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree_areas = ttk.Treeview(tree_frame, columns=self.COLUNAS_AREAS, show='headings')
        self.tree_areas.heading("nome_base", text="Nome Base")
        self.tree_areas.heading("nome_completo", text="Nome Completo")
        self.tree_areas.heading("codigo_area", text="Sigla")
        self.tree_areas.heading("num_salas", text="Nº de Salas")
        self.tree_areas.heading("caminho_arquivo_base", text="Arquivo Base")

        self.tree_areas.column("num_salas", width=80, anchor='center')
        self.tree_areas.column("codigo_area", width=80, anchor='center')
        self.tree_areas.column("nome_base", width=120)
        self.tree_areas.column("nome_completo", width=220)
        self.tree_areas.column("caminho_arquivo_base", width=260)

        self.tree_areas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_areas.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_areas.configure(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="Adicionar Nova Área", command=self.adicionar_area).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Editar Área Selecionada", command=self.editar_area).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Excluir Área Selecionada", command=self.excluir_area).pack(side="left", padx=5)

        self.carregar_dados_areas()

    def carregar_dados_areas(self):
        for i in self.tree_areas.get_children():
            self.tree_areas.delete(i)
        try:
            if not os.path.exists(ARQUIVO_AREAS):
                pd.DataFrame(columns=self.COLUNAS_AREAS).to_csv(ARQUIVO_AREAS, index=False, encoding="utf-8-sig")
                return

            df = pd.read_csv(ARQUIVO_AREAS, encoding="utf-8-sig").fillna('')

            if df.empty:
                return

            for _, row in df.iterrows():
                self.tree_areas.insert("", "end", values=[
                    str(row.get('nome_base', '')),
                    str(row.get('nome_completo', '')),
                    str(row.get('codigo_area', '')),
                    str(row.get('num_salas', '')),
                    str(row.get('caminho_arquivo_base', ''))
                ])

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar as áreas:\n{e}", parent=self)

    def adicionar_area(self):
        dialog = tk.Toplevel(self)
        dialog.title("Adicionar Nova Área")
        dialog.transient(self)
        dialog.grab_set()

        labels = ["Nome Base (ex: EXATAS):", "Nome Completo:", "Sigla (ex: EX):", "Nº de Salas:"]
        entries = {}

        for i, label in enumerate(labels):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(dialog, width=50)
            entry.grid(row=i, column=1, padx=10, pady=5, columnspan=2)
            entries[self.COLUNAS_AREAS[i]] = entry

        caminho_var = tk.StringVar(value="Nenhum arquivo selecionado.")
        ttk.Label(dialog, text="Arquivo Base:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(dialog, textvariable=caminho_var, relief="sunken", width=40).grid(row=4, column=1, padx=5, pady=5,
                                                                                    sticky="ew")

        ttk.Button(
            dialog,
            text="Selecionar...",
            command=lambda: self._selecionar_e_copiar_arquivo(caminho_var, dialog)
        ).grid(row=4, column=2, padx=5, pady=5)

        def salvar():
            num_salas_texto = entries['num_salas'].get().strip()
            try:
                int(num_salas_texto)
            except ValueError:
                messagebox.showerror("Erro", "O 'Nº de Salas' deve ser um número inteiro.", parent=dialog)
                return

            nova_area = {key: entries[key].get().strip() for key in self.COLUNAS_AREAS[:4]}
            nova_area["caminho_arquivo_base"] = caminho_var.get() if "Nenhum" not in caminho_var.get() else ""
            nova_area["nome_base"] = nova_area["nome_base"].upper()
            nova_area["codigo_area"] = nova_area["codigo_area"].upper()

            if not all(list(nova_area.values())[:4]):
                messagebox.showerror("Erro", "Campos textuais básicos são obrigatórios.", parent=dialog)
                return

            try:
                df = pd.read_csv(ARQUIVO_AREAS, encoding="utf-8-sig") if os.path.exists(
                    ARQUIVO_AREAS) else pd.DataFrame(columns=self.COLUNAS_AREAS)

                if not df.empty and nova_area["nome_base"] in df["nome_base"].values:
                    messagebox.showerror("Erro", "O 'Nome Base' já existe.", parent=dialog)
                    return

                df_nova = pd.DataFrame([nova_area], columns=self.COLUNAS_AREAS)
                df = pd.concat([df, df_nova], ignore_index=True)
                df.to_csv(ARQUIVO_AREAS, index=False, encoding="utf-8-sig")

                self.carregar_dados_areas()
                messagebox.showinfo("Sucesso", "Área adicionada!", parent=self)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}", parent=self)

        ttk.Button(dialog, text="Salvar", command=salvar).grid(row=len(labels) + 1, column=0, columnspan=3, pady=10)

    def editar_area(self):
        selecionado = self.tree_areas.focus()
        if not selecionado:
            messagebox.showerror("Erro", "Nenhuma área selecionada.", parent=self)
            return

        valores_lista = self.tree_areas.item(selecionado, 'values')
        valores_dict = dict(zip(self.COLUNAS_AREAS, valores_lista))

        dialog = tk.Toplevel(self)
        dialog.title("Editar Área")
        dialog.transient(self)
        dialog.grab_set()

        labels_map = {
            "nome_base": "Nome Base:",
            "nome_completo": "Nome Completo:",
            "codigo_area": "Sigla:",
            "num_salas": "Nº de Salas:"
        }
        entries = {}

        for i, (key, label) in enumerate(labels_map.items()):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(dialog, width=50)
            entry.grid(row=i, column=1, padx=10, pady=5, columnspan=2)
            entry.insert(0, valores_dict.get(key, ''))
            entries[key] = entry

        entries["nome_base"].config(state="disabled")

        caminho_inicial = valores_dict.get('caminho_arquivo_base', "Nenhum arquivo selecionado.")
        caminho_var = tk.StringVar(value=caminho_inicial if caminho_inicial else "Nenhum arquivo selecionado.")

        ttk.Label(dialog, text="Arquivo Base:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(dialog, textvariable=caminho_var, relief="sunken", width=40).grid(row=4, column=1, padx=5, pady=5,
                                                                                    sticky="ew")

        ttk.Button(
            dialog,
            text="Selecionar...",
            command=lambda: self._selecionar_e_copiar_arquivo(caminho_var, dialog)
        ).grid(row=4, column=2, padx=5, pady=5)

        def salvar_edicao():
            num_salas_texto = entries['num_salas'].get().strip()
            try:
                num_salas_valor = int(num_salas_texto)
            except ValueError:
                messagebox.showerror("Erro", "O 'Nº de Salas' deve ser um número inteiro.", parent=dialog)
                return

            try:
                df = pd.read_csv(ARQUIVO_AREAS, encoding="utf-8-sig")
                indices = df.index[df['nome_base'] == entries["nome_base"].get()].tolist()

                if not indices:
                    messagebox.showerror("Erro", "Área não encontrada no arquivo.", parent=dialog)
                    return

                idx = indices[0]
                df.loc[idx, 'nome_completo'] = entries['nome_completo'].get().strip()
                df.loc[idx, 'codigo_area'] = entries['codigo_area'].get().strip().upper()
                df.loc[idx, 'num_salas'] = num_salas_valor

                caminho_final = caminho_var.get() if "Nenhum" not in caminho_var.get() else ""
                df.loc[idx, 'caminho_arquivo_base'] = caminho_final

                df.to_csv(ARQUIVO_AREAS, index=False, encoding="utf-8-sig")
                self.carregar_dados_areas()
                messagebox.showinfo("Sucesso", "Área atualizada!", parent=self)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}", parent=self)

        ttk.Button(dialog, text="Salvar Alterações", command=salvar_edicao).grid(row=len(labels_map) + 1, column=0,
                                                                                 columnspan=3, pady=10)

    def _selecionar_e_copiar_arquivo(self, caminho_var, parent_dialog):
        caminho_origem = filedialog.askopenfilename(
            title="Selecione o arquivo base da área",
            filetypes=[("Planilhas Excel", "*.xlsx"), ("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")],
            parent=parent_dialog
        )
        if not caminho_origem:
            return

        nome_arquivo = os.path.basename(caminho_origem)
        caminho_destino = os.path.join(PASTA_PUBLICA, nome_arquivo).replace("\\", "/")

        try:
            shutil.copy(caminho_origem, caminho_destino)
            caminho_var.set(caminho_destino)
            messagebox.showinfo("Sucesso", f"Arquivo '{nome_arquivo}' copiado para a pasta '{PASTA_PUBLICA}'.",
                                parent=parent_dialog)
        except Exception as e:
            messagebox.showerror("Erro ao Copiar", f"Não foi possível copiar o arquivo:\n{e}", parent=parent_dialog)

    def excluir_area(self):
        selecionado = self.tree_areas.focus()
        if not selecionado:
            messagebox.showerror("Erro", "Nenhuma área selecionada.", parent=self)
            return

        valores = self.tree_areas.item(selecionado, 'values')
        nome_base_para_excluir = valores[0]

        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja excluir a área '{nome_base_para_excluir}'?",
                               parent=self):
            try:
                df = pd.read_csv(ARQUIVO_AREAS, encoding="utf-8-sig")
                df = df[df.nome_base != nome_base_para_excluir]
                df.to_csv(ARQUIVO_AREAS, index=False, encoding="utf-8-sig")
                self.carregar_dados_areas()
                messagebox.showinfo("Sucesso", "Área excluída.", parent=self)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}", parent=self)

    def criar_aba_salas(self):
        frame = self.aba_salas
        ttk.Label(
            frame,
            text="Mapear Salas Lógicas para Salas Físicas (mapa_salas.csv)",
            font=("Helvetica", 12, "bold")
        ).pack(pady=10)

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree_salas = ttk.Treeview(tree_frame, columns=("codigo_logico", "nome_fisico"), show='headings')
        self.tree_salas.heading("codigo_logico", text="Código Lógico")
        self.tree_salas.heading("nome_fisico", text="Nome Físico")
        self.tree_salas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_salas.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_salas.configure(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="Recarregar Lista", command=self.carregar_dados_salas).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Editar Sala Selecionada", command=self.editar_sala).pack(side="left", padx=5)

        self.carregar_dados_salas()

    def carregar_dados_salas(self):
        for i in self.tree_salas.get_children():
            self.tree_salas.delete(i)
        try:
            if not os.path.exists(ARQUIVO_MAPA):
                pd.DataFrame(columns=["codigo_logico", "nome_fisico"]).to_csv(ARQUIVO_MAPA, index=False,
                                                                              encoding="utf-8-sig")
                return

            df = pd.read_csv(ARQUIVO_MAPA, encoding="utf-8-sig").fillna('')
            for _, row in df.iterrows():
                self.tree_salas.insert("", "end", values=[str(row['codigo_logico']), str(row['nome_fisico'])])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar o mapa de salas:\n{e}", parent=self)

    def editar_sala(self):
        selecionado = self.tree_salas.focus()
        if not selecionado:
            messagebox.showerror("Erro", "Nenhuma sala selecionada.", parent=self)
            return

        valores = self.tree_salas.item(selecionado, 'values')
        codigo_logico, nome_atual = valores[0], valores[1]

        try:
            df = pd.read_csv(ARQUIVO_MAPA, encoding="utf-8-sig")
            outros_nomes = df[df['codigo_logico'] != codigo_logico]['nome_fisico'].astype(str).values

            novo_nome = simpledialog.askstring(
                "Editar Sala",
                f"Digite o novo nome físico para '{codigo_logico}':",
                initialvalue=nome_atual,
                parent=self
            )

            if novo_nome and novo_nome.strip() and novo_nome.strip() != nome_atual:
                novo_nome = novo_nome.strip()
                if novo_nome in outros_nomes:
                    messagebox.showerror("Erro de Duplicidade", f"O nome '{novo_nome}' já está em uso.", parent=self)
                    return

                df.loc[df['codigo_logico'] == codigo_logico, 'nome_fisico'] = novo_nome
                df.to_csv(ARQUIVO_MAPA, index=False, encoding="utf-8-sig")
                self.carregar_dados_salas()
                messagebox.showinfo("Sucesso", "Nome da sala atualizado!", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}", parent=self)

    def criar_aba_regras(self):
        frame = self.aba_regras
        self.config_evento_data = {}

        ttk.Label(
            frame,
            text="Gerenciar Regras Gerais do Evento (config_evento.json)",
            font=("Helvetica", 12, "bold")
        ).pack(pady=10)

        regras_num_frame = ttk.LabelFrame(frame, text="Regras de Alocação")
        regras_num_frame.pack(fill="x", padx=10, pady=5)

        self.regras_vars = {}
        regras_para_exibir = ["MAX_TRABALHOS_ORIENTADOR_SESSAO", "MIN_TRABALHOS_SESSAO", "DIAS_EVENTO"]

        for i, regra in enumerate(regras_para_exibir):
            ttk.Label(regras_num_frame, text=f"{regra}:").grid(row=i, column=0, padx=5, pady=4, sticky="w")
            var = tk.StringVar()
            self.regras_vars[regra] = var
            ttk.Entry(regras_num_frame, textvariable=var, width=12).grid(row=i, column=1, padx=5, pady=4, sticky="w")

        ignorar_frame = ttk.LabelFrame(frame, text="Arquivos com Nomes a Ignorar")
        ignorar_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree_ignorar = ttk.Treeview(ignorar_frame, columns=("escopo", "caminho"), show="headings")
        self.tree_ignorar.heading("escopo", text="Escopo")
        self.tree_ignorar.heading("caminho", text="Caminho do Arquivo")
        self.tree_ignorar.column("escopo", width=120)
        self.tree_ignorar.column("caminho", width=400)
        self.tree_ignorar.pack(side="left", fill="both", expand=True)

        scrollbar_ignorar = ttk.Scrollbar(ignorar_frame, orient="vertical", command=self.tree_ignorar.yview)
        scrollbar_ignorar.pack(side="right", fill="y")
        self.tree_ignorar.configure(yscrollcommand=scrollbar_ignorar.set)

        btn_regras_frame = ttk.Frame(frame)
        btn_regras_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_regras_frame, text="Adicionar Arquivo", command=self.adicionar_regra_ignorar).pack(side="left",
                                                                                                          padx=5)
        ttk.Button(btn_regras_frame, text="Remover Selecionado", command=self.remover_regra_ignorar).pack(side="left",
                                                                                                          padx=5)
        ttk.Button(btn_regras_frame, text="Salvar Todas as Regras", command=self.salvar_regras).pack(side="right",
                                                                                                     padx=5)

        self.carregar_dados_regras()

    def carregar_dados_regras(self):
        try:
            if not os.path.exists(ARQUIVO_EVENTO):
                self.config_evento_data = {
                    "ARQUIVOS_A_IGNORAR": {"GLOBAL": []},
                    "DIAS_EVENTO": 2,
                    "MAX_TRABALHOS_ORIENTADOR_SESSAO": 3,
                    "MIN_TRABALHOS_SESSAO": 4
                }
            else:
                with open(ARQUIVO_EVENTO, 'r', encoding='utf-8') as f:
                    self.config_evento_data = json.load(f)

            for chave, var in self.regras_vars.items():
                var.set(str(self.config_evento_data.get(chave, "")))

            for i in self.tree_ignorar.get_children():
                self.tree_ignorar.delete(i)

            regras_ignorar = self.config_evento_data.get("ARQUIVOS_A_IGNORAR", {})
            for escopo, arquivos in regras_ignorar.items():
                for arquivo in arquivos:
                    self.tree_ignorar.insert("", "end", values=(escopo, arquivo))

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar as regras:\n{e}", parent=self)

    def adicionar_regra_ignorar(self):
        escopo = simpledialog.askstring("Adicionar Regra", "Digite o escopo (ex: GLOBAL, EXATAS):", parent=self)
        if not escopo or not escopo.strip():
            return
        escopo = escopo.strip().upper()

        caminho = simpledialog.askstring(
            "Adicionar Regra",
            f"Digite o caminho do arquivo para '{escopo}':\n(ex: public/pibic_jr.xlsx)",
            parent=self
        )
        if not caminho or not caminho.strip():
            return

        caminho_normalizado = caminho.strip().replace("\\", "/")
        self.tree_ignorar.insert("", "end", values=(escopo, caminho_normalizado))
        messagebox.showinfo("Sucesso", "Regra adicionada. Clique em 'Salvar Todas as Regras' para confirmar.",
                            parent=self)

    def remover_regra_ignorar(self):
        selecionado = self.tree_ignorar.focus()
        if not selecionado:
            messagebox.showerror("Erro", "Nenhuma regra selecionada.", parent=self)
            return

        self.tree_ignorar.delete(selecionado)
        messagebox.showinfo("Sucesso", "Regra removida. Clique em 'Salvar Todas as Regras' para confirmar.",
                            parent=self)

    def salvar_regras(self):
        try:
            for chave, var in self.regras_vars.items():
                valor_str = var.get().strip()
                if not valor_str.isdigit():
                    messagebox.showerror("Erro de Validação", f"O valor para '{chave}' deve ser um número inteiro.",
                                         parent=self)
                    return
                self.config_evento_data[chave] = int(valor_str)

            novas_regras_ignorar = {}
            for item_id in self.tree_ignorar.get_children():
                escopo, caminho = self.tree_ignorar.item(item_id, 'values')
                if escopo not in novas_regras_ignorar:
                    novas_regras_ignorar[escopo] = []
                novas_regras_ignorar[escopo].append(caminho)

            self.config_evento_data["ARQUIVOS_A_IGNORAR"] = novas_regras_ignorar

            with open(ARQUIVO_EVENTO, 'w', encoding='utf-8') as f:
                json.dump(self.config_evento_data, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Sucesso", "Todas as regras foram salvas!", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar as regras:\n{e}", parent=self)