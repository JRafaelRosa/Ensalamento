import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pandas as pd

try:
    from src.gerar_ensalamento import ensalamento
    from src.verifica import verificar, verificar_nao_alocados
    from src.doc_ensalamento import gerar_documentos_finais
    from src.gui_trocar import JanelaTrocar
    from src.gui_consultor import JanelaConsultar
    from src.sala import carregar_config_geral
    from src.limpeza import executar_limpeza
    from src.gui_config import JanelaConfig
except ImportError as e:
    messagebox.showerror(
        "Erro de Importação",
        f"Não foi possível carregar um módulo: {e}\n\n"
        "Certifique-se de executar o aplicativo a partir da raiz do projeto "
        "e que a pasta 'src' contém todos os scripts necessários."
    )
    sys.exit(1)


class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, str_):
        self.widget.insert(tk.END, str_)
        self.widget.see(tk.END)

    def flush(self):
        pass


class JanelaGerenciador(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Sistema de Ensalamento EAIC - Gerenciar Evento")
        self.geometry("820x720")

        try:
            self.configs = carregar_config_geral()
            if not self.configs or self.configs[0] is None:
                raise FileNotFoundError("Ficheiros em public/config estão incompletos ou corrompidos.")

            config_areas_df = self.configs[1].reset_index() if self.configs[1].index.name == 'nome_base' else self.configs[1]
            self.dias_evento = self.configs[0].get("DIAS_EVENTO", 2)

            self.todas_areas_base = [str(row['nome_base']) for _, row in config_areas_df.iterrows()]

            self.lista_areas_formatada = [
                "-- Selecione uma Área --",
                "-- TODAS AS ÁREAS --"
            ] + [
                f"{row['nome_base']} ({row['num_salas']} salas)"
                for _, row in config_areas_df.iterrows()
            ]
        except Exception as e:
            self.destroy()
            messagebox.showerror(
                "Erro de Configuração",
                f"Falha ao carregar ficheiros de configuração:\n{e}\n\n"
                "Execute 'Criar / Recriar Configurações do Evento' no menu principal primeiro."
            )
            return

        main_frame = tk.Frame(self, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(top_frame, text="Área de Trabalho:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)

        self.area_selecionada = tk.StringVar()
        self.area_selecionada.set(self.lista_areas_formatada[0])
        self.area_selecionada.trace_add('write', self.atualizar_contagem)

        area_dropdown = ttk.OptionMenu(top_frame, self.area_selecionada, *self.lista_areas_formatada)
        area_dropdown.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        self.label_contagem = ttk.Label(top_frame, text="Total: --", font=("Helvetica", 9, "italic"))
        self.label_contagem.pack(side=tk.LEFT)

        botoes_frame = tk.Frame(main_frame)
        botoes_frame.pack(fill=tk.X, pady=(0, 10))
        btn_gerar = ttk.Button(botoes_frame, text="Gerar/Regerar Ensalamento", command=self.handle_gerar_ensalamento)
        btn_gerar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        botoes_ferramentas_frame = tk.Frame(main_frame)
        botoes_ferramentas_frame.pack(fill=tk.X, pady=(5, 10))
        btn_consultar = ttk.Button(botoes_ferramentas_frame, text="Consultar Ensalamento...", command=self.handle_consultar)
        btn_consultar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        btn_trocar = ttk.Button(botoes_ferramentas_frame, text="Ajuste Manual...", command=self.handle_trocar)
        btn_trocar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        reports_frame = ttk.LabelFrame(main_frame, text="Verificação e Relatórios")
        reports_frame.pack(fill=tk.X, pady=(10, 10))
        btn_verificar = ttk.Button(reports_frame, text="Verificar Consistência", command=self.handle_verificar)
        btn_verificar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=5)
        btn_nao_alocados = ttk.Button(reports_frame, text="Verificar Não Alocados", command=self.handle_verificar_nao_alocados)
        btn_nao_alocados.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=5)
        btn_listar_todos = ttk.Button(reports_frame, text="Listar Todos (Relatório)", command=self.handle_listar_todos)
        btn_listar_todos.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=5)
        btn_pdf = ttk.Button(reports_frame, text="Gerar PDFs / Docxs", command=self.handle_gerar_pdf)
        btn_pdf.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=5)

        config_frame = ttk.LabelFrame(main_frame, text="Configurações")
        config_frame.pack(fill=tk.X, pady=(10, 10))
        btn_configs = ttk.Button(config_frame, text="Abrir Painel de Configurações do Evento...", command=self.handle_abrir_config)
        btn_configs.pack(fill=tk.X, expand=True, padx=2, pady=5)

        log_label = tk.Label(main_frame, text="Log de Operações:", font=("Helvetica", 10, "bold"))
        log_label.pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=18, bg="#f8f9fa")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.all_buttons = [
            btn_gerar, btn_verificar, btn_pdf, btn_consultar, btn_trocar,
            btn_nao_alocados, btn_listar_todos, btn_configs
        ]

        self.original_stdout = sys.stdout
        sys.stdout = TextRedirector(self.log_text)
        print("Janela de gerenciamento pronta.")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.atualizar_contagem()

    def on_close(self):
        sys.stdout = self.original_stdout
        self.destroy()

    def run_in_thread(self, target_func, *args):
        def process():
            self.log_text.delete(1.0, tk.END)
            try:
                target_func(*args)
            except Exception as ex:
                print(f"\n[ERRO NA EXECUÇÃO]: {ex}")
            finally:
                for btn in self.all_buttons:
                    btn.config(state=tk.NORMAL)
                self.atualizar_contagem()

        for btn in self.all_buttons:
            btn.config(state=tk.DISABLED)

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def is_todas_selecionado(self):
        selecionado = self.area_selecionada.get()
        return "TODAS" in selecionado.upper()

    def get_selected_areas_list(self):
        selecionado = self.area_selecionada.get()
        if not selecionado or "-- Selecione" in selecionado:
            messagebox.showwarning(
                "Atenção",
                "Por favor, selecione uma área de trabalho antes de continuar.",
                parent=self
            )
            return []

        if self.is_todas_selecionado():
            return self.todas_areas_base
        else:
            return [selecionado.split(' ')[0]]

    def get_raw_selected_area_name(self):
        selecionado = self.area_selecionada.get()
        if not selecionado or "-- Selecione" in selecionado:
            return None
        if self.is_todas_selecionado():
            return "TODAS"
        return selecionado.split(' ')[0]

    def handle_gerar_ensalamento(self):
        areas = self.get_selected_areas_list()
        if not areas:
            return

        def processar_geracao():
            for area in areas:
                print(f"\n" + "=" * 60)
                print(f"--- GERANDO ENSALAMENTO PARA: {area} ---".center(60))
                print("=" * 60 + "\n")
                ensalamento(area, *self.configs)

        self.run_in_thread(processar_geracao)

    def handle_verificar(self):
        areas = self.get_selected_areas_list()
        if not areas:
            return

        def processar_verificacao():
            for area in areas:
                print(f"\n--- VERIFICANDO ARQUIVOS DE: {area} ---\n")
                for dia in range(1, self.dias_evento + 1):
                    caminho = f"public/csv/{area}_dia{dia}.csv"
                    if os.path.exists(caminho):
                        verificar(caminho)
                    else:
                        print(f"Arquivo não encontrado para verificação: {caminho}")

        self.run_in_thread(processar_verificacao)

    def handle_gerar_pdf(self):
        areas = self.get_selected_areas_list()
        if not areas:
            return

        def processar_documentos():
            for area in areas:
                print(f"\n--- GERANDO ARQUIVOS PDF E WORD PARA: {area} ---\n")
                for dia in range(1, self.dias_evento + 1):
                    caminho = f"public/csv/{area}_dia{dia}.csv"
                    if os.path.exists(caminho):
                        gerar_documentos_finais(caminho, self.configs[1], self.configs[2])
                    else:
                        print(f"Arquivo CSV não encontrado: {caminho}")

        self.run_in_thread(processar_documentos)

    def handle_consultar(self):
        if self.is_todas_selecionado():
            messagebox.showinfo("Aviso", "A ferramenta de consulta interativa requer que uma área específica seja selecionada.", parent=self)
            return
        nome_base = self.get_raw_selected_area_name()
        if not nome_base:
            return
        JanelaConsultar(self, nome_base)

    def handle_trocar(self):
        if self.is_todas_selecionado():
            messagebox.showinfo("Aviso", "A ferramenta de ajuste manual requer que uma área específica seja selecionada.", parent=self)
            return
        nome_base = self.get_raw_selected_area_name()
        if not nome_base:
            return
        JanelaTrocar(self, nome_base)

    def atualizar_contagem(self, *args):
        nome_base = self.get_raw_selected_area_name()
        if not nome_base:
            self.label_contagem.config(text="Total: --")
            return

        total = 0
        dias = getattr(self, 'dias_evento', 2)

        areas_contar = self.todas_areas_base if nome_base == "TODAS" else [nome_base]

        for area in areas_contar:
            for dia in range(1, dias + 1):
                try:
                    df_dia = pd.read_csv(f"public/csv/{area}_dia{dia}.csv")
                    total += len(df_dia)
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    pass

        self.label_contagem.config(text=f"Total: {total}")

    def handle_verificar_nao_alocados(self):
        areas = self.get_selected_areas_list()
        if not areas:
            return

        def processar_nao_alocados():
            for area in areas:
                print(f"\n--- VERIFICANDO NÃO ALOCADOS: {area} ---\n")
                verificar_nao_alocados(area)

        self.run_in_thread(processar_nao_alocados)

    def handle_listar_todos(self):
        areas = self.get_selected_areas_list()
        if not areas:
            return

        relatorio_window = tk.Toplevel(self)
        relatorio_window.title("Relatório Completo - " + ("TODAS AS ÁREAS" if self.is_todas_selecionado() else areas[0]))
        relatorio_window.geometry("800x600")

        txt = scrolledtext.ScrolledText(relatorio_window, wrap=tk.WORD, font=("Courier", 9))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        dfs = []
        for area in areas:
            for dia in range(1, self.dias_evento + 1):
                caminho = f"public/csv/{area}_dia{dia}.csv"
                try:
                    df_dia = pd.read_csv(caminho)
                    df_dia['Área_Origem'] = area
                    dfs.append(df_dia)
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    pass

        if dfs:
            df_completo = pd.concat(dfs, ignore_index=True)
        else:
            df_completo = pd.DataFrame()

        if df_completo.empty:
            txt.insert(tk.END, "Nenhum trabalho encontrado nos arquivos CSV gerados.")
        else:
            trabalhos_agrupados = df_completo.groupby('Orientador(a)')
            orientadores_ordenados = sorted(trabalhos_agrupados.groups.keys())
            for orientador in orientadores_ordenados:
                txt.insert(tk.END, f"\n--- Orientador(a): {orientador} ---\n")
                df_orientador = trabalhos_agrupados.get_group(orientador)
                for _, trabalho in df_orientador.iterrows():
                    txt.insert(tk.END, f"  - Apresentador(a): {trabalho.get('Apresentador(a)', 'N/A')}\n")
                    txt.insert(tk.END, f"    Título: {trabalho.get('Título', 'N/A')}\n")
                    txt.insert(tk.END, f"    Local: Area {trabalho.get('Área_Origem', 'N/A')} - Sala {trabalho.get('Sala', 'N/A')} - {trabalho.get('Horário', 'N/A')} ({trabalho.get('Sessão', 'N/A')})\n")
        txt.config(state=tk.DISABLED)

    def handle_abrir_config(self):
        JanelaConfig(self)


def abrir_gerenciador_evento(root):
    root.withdraw()
    janela = JanelaGerenciador(root)
    janela.protocol("WM_DELETE_WINDOW", lambda: reabrir_menu_principal(root, janela))


def reabrir_menu_principal(root, janela):
    janela.on_close()
    root.deiconify()


def abrir_script_externo(script_relativo):
    """Abre scripts externos garantindo o caminho correto dentro da pasta src/."""
    caminho_script = os.path.normpath(script_relativo)

    messagebox.showinfo(
        "Aviso",
        f"A ferramenta '{caminho_script}' será aberta em um novo terminal.\n"
        "Feche o terminal ao concluir."
    )

    if sys.platform.startswith("win"):
        comando = f'start cmd /k "python {caminho_script}"'
    else:
        comando = f'gnome-terminal -- python3 {caminho_script}'

    subprocess.Popen(comando, shell=True)


def main():
    root = tk.Tk()
    root.withdraw()

    splash = tk.Toplevel(root)
    splash.overrideredirect(True)

    width, height = 400, 250
    pos_x = root.winfo_screenwidth() // 2 - width // 2
    pos_y = root.winfo_screenheight() // 2 - height // 2
    splash.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
    splash.config(bg="#e0e8f0")

    tk.Label(splash, text="Sistema de Ensalamento", font=("Helvetica", 20, "bold"), bg="#e0e8f0", fg="#143278").pack(pady=(40, 10))
    tk.Label(splash, text="EAIC - UEPG", font=("Helvetica", 16), bg="#e0e8f0", fg="#143278").pack()
    tk.Label(splash, text="Carregando...", font=("Helvetica", 10, "italic"), bg="#e0e8f0").pack(pady=10)
    tk.Label(splash, text="Desenvolvido por João Rafael S. Rosa", font=("Helvetica", 9, "italic"), bg="#e0e8f0").pack(side=tk.BOTTOM, pady=10)

    def abrir_menu_principal():
        splash.destroy()
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)
        root.after_idle(root.attributes, '-topmost', False)
        root.focus_force()
        root.title("Sistema de Ensalamento EAIC - Menu Principal")

        m_width, m_height = 500, 320
        m_x = root.winfo_screenwidth() // 2 - m_width // 2
        m_y = root.winfo_screenheight() // 2 - m_height // 2
        root.geometry(f"{m_width}x{m_height}+{m_x}+{m_y}")

        menu_frame = tk.Frame(root, padx=20, pady=20)
        menu_frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(menu_frame, text="Bem-vindo!", font=("Helvetica", 16, "bold")).pack(pady=(0, 20))

        ttk.Button(
            menu_frame,
            text="Criar / Recriar Configurações do Evento",
            command=lambda: abrir_script_externo("src/gerador_config.py")
        ).pack(fill=tk.X, ipady=5, pady=4)

        ttk.Button(
            menu_frame,
            text="Gerenciar Evento Existente",
            command=lambda: abrir_gerenciador_evento(root)
        ).pack(fill=tk.X, ipady=5, pady=4)

        ttk.Button(
            menu_frame,
            text="Limpar Dados Gerados (CSVs, PDFs)",
            command=lambda: abrir_script_externo("src/limpeza.py")
        ).pack(fill=tk.X, ipady=5, pady=4)

    root.after(2000, abrir_menu_principal)
    root.mainloop()


if __name__ == "__main__":
    main()