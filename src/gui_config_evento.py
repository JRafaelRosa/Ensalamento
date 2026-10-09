import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

PASTA_CONFIG = "public/config"
ARQUIVO_AREAS = os.path.join(PASTA_CONFIG, "config_areas.csv")
ARQUIVO_MAPA = os.path.join(PASTA_CONFIG, "mapa_salas.csv")
ARQUIVO_HORARIOS = os.path.join(PASTA_CONFIG, "horarios_sessoes.csv")
ARQUIVO_EVENTO = os.path.join(PASTA_CONFIG, "config_evento.json")


class JanelaConfig(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gerenciador de Configurações do Evento (EAIC)")
        self.geometry("950x680")

        os.makedirs(PASTA_CONFIG, exist_ok=True)

        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Barra de Ações Rápidas (Preset)
        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        btn_preset = ttk.Button(
            top_bar,
            text="⚡ Carregar Predefinições Padrão (EAIC UEPG)",
            command=self.carregar_preset_padrao
        )
        btn_preset.pack(side=tk.LEFT)

        btn_salvar_tudo = ttk.Button(
            top_bar,
            text="💾 Salvar Todas as Alterações",
            command=self.salvar_tudo
        )
        btn_salvar_tudo.pack(side=tk.RIGHT)

        # Notebook com Abas para cada arquivo de configuração
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Aba 1: Áreas
        self.aba_areas = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_areas, text=" 1. Áreas do Evento ")
        self._construir_aba_areas()

        # Aba 2: Mapa de Salas
        self.aba_mapa = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_mapa, text=" 2. Mapeamento de Salas ")
        self._construir_aba_mapa()

        # Aba 3: Horários e Sessões
        self.aba_horarios = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_horarios, text=" 3. Horários & Sessões ")
        self._construir_aba_horarios()

        # Aba 4: Regras Gerais e Ignorar
        self.aba_regras = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_regras, text=" 4. Regras & Arquivos Ignorados ")
        self._construir_aba_regras()

        self.carregar_dados_existentes()

    # =========================================================================
    # CONSTRUÇÃO DAS ABAS
    # =========================================================================

    def _construir_aba_areas(self):
        cols = ('nome_base', 'codigo_area', 'num_salas', 'nome_completo', 'caminho_arquivo_base')
        self.tree_areas = ttk.Treeview(self.aba_areas, columns=cols, show='headings')
        for c in cols:
            self.tree_areas.heading(c, text=c.upper().replace('_', ' '))
            self.tree_areas.column(c, width=150)
        self.tree_areas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        form_frame = ttk.LabelFrame(self.aba_areas, text="Adicionar / Editar Área")
        form_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(form_frame, text="Nome Base:").grid(row=0, column=0, padx=2)
        self.ent_area_base = ttk.Entry(form_frame, width=12)
        self.ent_area_base.grid(row=0, column=1, padx=2)

        tk.Label(form_frame, text="Sigla:").grid(row=0, column=2, padx=2)
        self.ent_area_sigla = ttk.Entry(form_frame, width=6)
        self.ent_area_sigla.grid(row=0, column=3, padx=2)

        tk.Label(form_frame, text="Salas:").grid(row=0, column=4, padx=2)
        self.ent_area_salas = ttk.Entry(form_frame, width=6)
        self.ent_area_salas.grid(row=0, column=5, padx=2)

        tk.Label(form_frame, text="Nome Completo:").grid(row=1, column=0, padx=2, pady=5)
        self.ent_area_nome_comp = ttk.Entry(form_frame, width=25)
        self.ent_area_nome_comp.grid(row=1, column=1, columnspan=2, padx=2, pady=5)

        tk.Label(form_frame, text="Arquivo Base:").grid(row=1, column=3, padx=2, pady=5)
        self.ent_area_caminho = ttk.Entry(form_frame, width=25)
        self.ent_area_caminho.grid(row=1, column=4, columnspan=2, padx=2, pady=5)

        btn_add = ttk.Button(form_frame, text="Adicionar", command=self.add_area)
        btn_add.grid(row=0, column=6, rowspan=2, padx=10, pady=5)

    def _construir_aba_mapa(self):
        cols = ('codigo_logico', 'nome_fisico')
        self.tree_mapa = ttk.Treeview(self.aba_mapa, columns=cols, show='headings')
        self.tree_mapa.heading('codigo_logico', text='CÓDIGO LÓGICO')
        self.tree_mapa.heading('nome_fisico', text='NOME DA SALA FÍSICA')
        self.tree_mapa.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        form_frame = ttk.LabelFrame(self.aba_mapa, text="Adicionar Mapeamento")
        form_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(form_frame, text="Código Lógico (ex: EN1):").pack(side=tk.LEFT, padx=5)
        self.ent_mapa_logico = ttk.Entry(form_frame, width=12)
        self.ent_mapa_logico.pack(side=tk.LEFT, padx=5)

        tk.Label(form_frame, text="Nome Físico (ex: Sala 24):").pack(side=tk.LEFT, padx=5)
        self.ent_mapa_fisico = ttk.Entry(form_frame, width=20)
        self.ent_mapa_fisico.pack(side=tk.LEFT, padx=5)

        ttk.Button(form_frame, text="Adicionar", command=self.add_mapa).pack(side=tk.LEFT, padx=10)

    def _construir_aba_horarios(self):
        cols = ('dia', 'sala_fisica', 'nome_sessao', 'horario_inicio', 'capacidade')
        self.tree_horarios = ttk.Treeview(self.aba_horarios, columns=cols, show='headings')
        for c in cols:
            self.tree_horarios.heading(c, text=c.upper().replace('_', ' '))
            self.tree_horarios.column(c, width=120)
        self.tree_horarios.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        form_frame = ttk.LabelFrame(self.aba_horarios, text="Adicionar Bloco de Horário")
        form_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(form_frame, text="Dia:").grid(row=0, column=0)
        self.ent_hor_dia = ttk.Entry(form_frame, width=5)
        self.ent_hor_dia.grid(row=0, column=1)

        tk.Label(form_frame, text="Sala Físia:").grid(row=0, column=2)
        self.ent_hor_sala = ttk.Entry(form_frame, width=10)
        self.ent_hor_sala.grid(row=0, column=3)

        tk.Label(form_frame, text="Sessão:").grid(row=0, column=4)
        self.ent_hor_sessao = ttk.Entry(form_frame, width=12)
        self.ent_hor_sessao.grid(row=0, column=5)

        tk.Label(form_frame, text="Horário:").grid(row=0, column=6)
        self.ent_hor_inicio = ttk.Entry(form_frame, width=8)
        self.ent_hor_inicio.grid(row=0, column=7)

        tk.Label(form_frame, text="Capacidade:").grid(row=0, column=8)
        self.ent_hor_cap = ttk.Entry(form_frame, width=6)
        self.ent_hor_cap.grid(row=0, column=9)

        ttk.Button(form_frame, text="Adicionar", command=self.add_horario).grid(row=0, column=10, padx=5)

    def _construir_aba_regras(self):
        main_regras = tk.Frame(self.aba_regras, padx=10, pady=10)
        main_regras.pack(fill=tk.BOTH, expand=True)

        # Parâmetros Globais do Evento
        f_globais = ttk.LabelFrame(main_regras, text="Parâmetros Globais do Evento")
        f_globais.pack(fill=tk.X, pady=5)

        tk.Label(f_globais, text="Dias do Evento:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.spin_dias = ttk.Spinbox(f_globais, from_=1, to=10, width=6)
        self.spin_dias.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(f_globais, text="Datas do Evento (separadas por vírgula):").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.ent_datas_evento = ttk.Entry(f_globais, width=30)
        self.ent_datas_evento.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(f_globais, text="Mínimo Trabalhos/Sessão:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.spin_min = ttk.Spinbox(f_globais, from_=1, to=20, width=6)
        self.spin_min.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(f_globais, text="Máximo Trabalhos por Orientador/Sessão:").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        self.spin_max = ttk.Spinbox(f_globais, from_=1, to=30, width=6)
        self.spin_max.grid(row=1, column=3, padx=5, pady=5)

        # Tabela de Arquivos a Ignorar
        f_ignorar = ttk.LabelFrame(main_regras, text="Regras de Arquivos a Ignorar")
        f_ignorar.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ('escopo', 'caminho_arquivo')
        self.tree_ignorar = ttk.Treeview(f_ignorar, columns=cols, show='headings')
        self.tree_ignorar.heading('escopo', text='ESCOPO (GLOBAL OU ÁREA)')
        self.tree_ignorar.heading('caminho_arquivo', text='CAMINHO DO ARQUIVO')
        self.tree_ignorar.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        form_ignorar = tk.Frame(f_ignorar)
        form_ignorar.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(form_ignorar, text="Escopo (GLOBAL ou NOME_BASE):").pack(side=tk.LEFT)
        self.ent_ignorar_escopo = ttk.Entry(form_ignorar, width=15)
        self.ent_ignorar_escopo.pack(side=tk.LEFT, padx=5)

        tk.Label(form_ignorar, text="Caminho Arquivo:").pack(side=tk.LEFT)
        self.ent_ignorar_caminho = ttk.Entry(form_ignorar, width=35)
        self.ent_ignorar_caminho.pack(side=tk.LEFT, padx=5)

        ttk.Button(form_ignorar, text="Adicionar Regra", command=self.add_ignorar).pack(side=tk.LEFT, padx=5)

    # =========================================================================
    # LÓGICA DE PREDEFINIÇÕES (PRESETS)
    # =========================================================================

    def carregar_preset_padrao(self):
        confirm = messagebox.askyesno(
            "Carregar Predefinições",
            "Isso substituirá as tabelas atuais com a configuração padrão do EAIC. Deseja continuar?"
        )
        if not confirm:
            return

        areas_data = [
            {"nome_base": "ENGENHARIAS", "codigo_area": "EN", "num_salas": 4, "nome_completo": "ENGENHARIAS - EAIC", "caminho_arquivo_base": "public/engenharias.xlsx"},
            {"nome_base": "EXATAS", "codigo_area": "EX", "num_salas": 4, "nome_completo": "EXATAS E DA TERRA - EAIC", "caminho_arquivo_base": "public/exatas.xlsx"},
            {"nome_base": "BIOLOGICAS", "codigo_area": "BI", "num_salas": 3, "nome_completo": "CIÊNCIAS BIOLÓGICAS - EAIC", "caminho_arquivo_base": "public/biologicas.xlsx"},
            {"nome_base": "AGRARIAS", "codigo_area": "AG", "num_salas": 3, "nome_completo": "CIÊNCIAS AGRÁRIAS - EAIC", "caminho_arquivo_base": "public/agrarias.xlsx"},
            {"nome_base": "SAUDE", "codigo_area": "SA", "num_salas": 4, "nome_completo": "CIÊNCIAS DA SAÚDE - EAIC", "caminho_arquivo_base": "public/saude.xlsx"},
            {"nome_base": "HUMANAS", "codigo_area": "HU", "num_salas": 4, "nome_completo": "CIÊNCIAS HUMANAS - EAIC", "caminho_arquivo_base": "public/humanas.xlsx"},
            {"nome_base": "SOCIAIS", "codigo_area": "SO", "num_salas": 4, "nome_completo": "SOCIAIS APLICADAS - EAIC", "caminho_arquivo_base": "public/sociais.xlsx"}
        ]

        self.tree_areas.delete(*self.tree_areas.get_children())
        for a in areas_data:
            self.tree_areas.insert('', tk.END, values=(a['nome_base'], a['codigo_area'], a['num_salas'], a['nome_completo'], a['caminho_arquivo_base']))

        mapa_data = []
        for a in areas_data:
            for i in range(1, a['num_salas'] + 1):
                mapa_data.append({"codigo_logico": f"{a['codigo_area']}{i}", "nome_fisico": f"Sala {a['codigo_area']}-{i:02d}"})

        self.tree_mapa.delete(*self.tree_mapa.get_children())
        for m in mapa_data:
            self.tree_mapa.insert('', tk.END, values=(m['codigo_logico'], m['nome_fisico']))

        sessoes_padrao = [
            {"nome_sessao": "Manhã 1", "horario_inicio": "08:30", "capacidade": 6},
            {"nome_sessao": "Manhã 2", "horario_inicio": "10:30", "capacidade": 6},
            {"nome_sessao": "Tarde", "horario_inicio": "14:00", "capacidade": 6}
        ]

        self.tree_horarios.delete(*self.tree_horarios.get_children())
        for dia in [1, 2]:
            for m in mapa_data:
                for s in sessoes_padrao:
                    self.tree_horarios.insert('', tk.END, values=(dia, m['nome_fisico'], s['nome_sessao'], s['horario_inicio'], s['capacidade']))

        self.spin_dias.set(2)
        self.ent_datas_evento.delete(0, tk.END)
        self.ent_datas_evento.insert(0, "27/10/2026, 28/10/2026")
        self.spin_min.set(4)
        self.spin_max.set(6)

        self.tree_ignorar.delete(*self.tree_ignorar.get_children())
        self.tree_ignorar.insert('', tk.END, values=("GLOBAL", "public/PIBIC_Jr.xlsx"))

        messagebox.showinfo("Predefinições Carregadas", "As predefinições padrão foram carregadas! Clique em 'Salvar Todas as Alterações' para gravar.")

    # =========================================================================
    # INSERÇÃO NAS TABELAS
    # =========================================================================

    def add_area(self):
        b = self.ent_area_base.get().strip().upper()
        s = self.ent_area_sigla.get().strip().upper()
        n = self.ent_area_salas.get().strip()
        c = self.ent_area_nome_comp.get().strip()
        p = self.ent_area_caminho.get().strip()

        if b and s and n:
            self.tree_areas.insert('', tk.END, values=(b, s, n, c, p))
            self.ent_area_base.delete(0, tk.END)
            self.ent_area_sigla.delete(0, tk.END)

    def add_mapa(self):
        l = self.ent_mapa_logico.get().strip().upper()
        f = self.ent_mapa_fisico.get().strip()
        if l and f:
            self.tree_mapa.insert('', tk.END, values=(l, f))
            self.ent_mapa_logico.delete(0, tk.END)
            self.ent_mapa_fisico.delete(0, tk.END)

    def add_horario(self):
        d = self.ent_hor_dia.get().strip()
        s = self.ent_hor_sala.get().strip()
        se = self.ent_hor_sessao.get().strip()
        h = self.ent_hor_inicio.get().strip()
        c = self.ent_hor_cap.get().strip()
        if d and s and se and h:
            self.tree_horarios.insert('', tk.END, values=(d, s, se, h, c))

    def add_ignorar(self):
        e = self.ent_ignorar_escopo.get().strip().upper() or "GLOBAL"
        c = self.ent_ignorar_caminho.get().strip()
        if c:
            self.tree_ignorar.insert('', tk.END, values=(e, c))
            self.ent_ignorar_caminho.delete(0, tk.END)

    # =========================================================================
    # PERSISTÊNCIA DE DADOS
    # =========================================================================

    def carregar_dados_existentes(self):
        if os.path.exists(ARQUIVO_AREAS):
            try:
                df = pd.read_csv(ARQUIVO_AREAS)
                for _, r in df.iterrows():
                    self.tree_areas.insert('', tk.END, values=(
                        r.get('nome_base', ''), r.get('codigo_area', ''), r.get('num_salas', ''),
                        r.get('nome_completo', ''), r.get('caminho_arquivo_base', '')
                    ))
            except Exception:
                pass

        if os.path.exists(ARQUIVO_MAPA):
            try:
                df = pd.read_csv(ARQUIVO_MAPA)
                for _, r in df.iterrows():
                    self.tree_mapa.insert('', tk.END, values=(r.get('codigo_logico', ''), r.get('nome_fisico', '')))
            except Exception:
                pass

        if os.path.exists(ARQUIVO_HORARIOS):
            try:
                df = pd.read_csv(ARQUIVO_HORARIOS)
                for _, r in df.iterrows():
                    self.tree_horarios.insert('', tk.END, values=(
                        r.get('dia', ''), r.get('sala_fisica', ''), r.get('nome_sessao', ''),
                        r.get('horario_inicio', ''), r.get('capacidade', '')
                    ))
            except Exception:
                pass

        if os.path.exists(ARQUIVO_EVENTO):
            try:
                with open(ARQUIVO_EVENTO, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.spin_dias.set(cfg.get('DIAS_EVENTO', 2))

                    datas_lst = cfg.get('DATAS_EVENTO', ["27/10/2026", "28/10/2026"])
                    self.ent_datas_evento.delete(0, tk.END)
                    self.ent_datas_evento.insert(0, ", ".join(datas_lst))

                    self.spin_min.set(cfg.get('MIN_TRABALHOS_SESSAO', 4))
                    self.spin_max.set(cfg.get('MAX_TRABALHOS_ORIENTADOR_SESSAO', 6))

                    ignorar = cfg.get('ARQUIVOS_A_IGNORAR', {})
                    for escopo, lista in ignorar.items():
                        for item in lista:
                            self.tree_ignorar.insert('', tk.END, values=(escopo, item))
            except Exception:
                pass

    def salvar_tudo(self):
        try:
            list_areas = []
            for item in self.tree_areas.get_children():
                v = self.tree_areas.item(item)['values']
                list_areas.append({
                    'nome_base': v[0], 'codigo_area': v[1], 'num_salas': v[2],
                    'nome_completo': v[3], 'caminho_arquivo_base': v[4]
                })
            pd.DataFrame(list_areas).to_csv(ARQUIVO_AREAS, index=False)

            list_mapa = []
            for item in self.tree_mapa.get_children():
                v = self.tree_mapa.item(item)['values']
                list_mapa.append({'codigo_logico': v[0], 'nome_fisico': v[1]})
            pd.DataFrame(list_mapa).to_csv(ARQUIVO_MAPA, index=False)

            list_horarios = []
            for item in self.tree_horarios.get_children():
                v = self.tree_horarios.item(item)['values']
                list_horarios.append({
                    'dia': v[0], 'sala_fisica': v[1], 'nome_sessao': v[2],
                    'horario_inicio': v[3], 'capacidade': v[4]
                })
            pd.DataFrame(list_horarios).to_csv(ARQUIVO_HORARIOS, index=False)

            dic_ignorar = {}
            for item in self.tree_ignorar.get_children():
                v = self.tree_ignorar.item(item)['values']
                escopo, caminho = str(v[0]), str(v[1])
                if escopo not in dic_ignorar:
                    dic_ignorar[escopo] = []
                dic_ignorar[escopo].append(caminho)

            raw_datas = self.ent_datas_evento.get().split(',')
            datas_limpas = [d.strip() for d in raw_datas if d.strip()]

            cfg_evento = {
                "ARQUIVOS_A_IGNORAR": dic_ignorar,
                "DIAS_EVENTO": int(self.spin_dias.get()),
                "DATAS_EVENTO": datas_limpas,
                "MIN_TRABALHOS_SESSAO": int(self.spin_min.get()),
                "MAX_TRABALHOS_ORIENTADOR_SESSAO": int(self.spin_max.get())
            }

            with open(ARQUIVO_EVENTO, 'w', encoding='utf-8') as f:
                json.dump(cfg_evento, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Sucesso", "Todas as configurações foram salvas com sucesso!")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar os arquivos:\n{e}")