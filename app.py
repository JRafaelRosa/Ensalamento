import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import sys
import threading
import subprocess
import pandas as pd

try:
    from src.gerar_ensalamento import ensalamento
    from src.verifica import verificar, verificar_nao_alocados
    from src.pdf_ensalamento import pdf_ensalamento
    from src.gui_trocar import JanelaTrocar
    from src.gui_consultor import JanelaConsultar
    from src.sala import carregar_config_geral
    from src.limpeza import executar_limpeza
    # <-- ALTERAÇÃO 1: Importar a classe da janela de configuração.
    # Verifique se o nome do arquivo 'gui_config.py' está correto.
    from src.gui_config import JanelaConfig
except ImportError as e:
    messagebox.showerror("Erro de Importação", f"Não foi possível carregar um módulo: {e}\n\nVerifique a pasta 'src'.")
    sys.exit()


class TextRedirector:
    def __init__(self, widget): self.widget = widget
    def write(self, str_): self.widget.insert(tk.END, str_); self.widget.see(tk.END)
    def flush(self): pass


class JanelaGerenciador(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Sistema de Ensalamento EAIC - Gerenciar Evento")
        self.geometry("800x700")

        try:
            self.configs = carregar_config_geral()
            if self.configs[0] is None: raise FileNotFoundError
            config_areas_df = self.configs[1].reset_index()
            self.lista_areas_formatada = ["-- Selecione uma Área --"] + [
                f"{row['nome_base']} ({row['num_salas']} salas)" for index, row in config_areas_df.iterrows()]
        except (FileNotFoundError, IndexError):
            self.destroy()
            messagebox.showerror("Erro Crítico",
                                 "Arquivos de configuração não encontrados!\nExecute 'Criar Novo Evento' no menu principal primeiro.")
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
        btn_consultar = ttk.Button(botoes_ferramentas_frame, text="Consultar Ensalamento...",
                                   command=self.handle_consultar)
        btn_consultar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        btn_trocar = ttk.Button(botoes_ferramentas_frame, text="Ajuste Manual...", command=self.handle_trocar)
        btn_trocar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        reports_frame = ttk.LabelFrame(main_frame, text="Verificação e Relatórios")
        reports_frame.pack(fill=tk.X, pady=(10, 10))
        btn_verificar = ttk.Button(reports_frame, text="Verificar Consistência", command=self.handle_verificar)
        btn_verificar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=5)
        btn_nao_alocados = ttk.Button(reports_frame, text="Verificar Não Alocados",
                                      command=self.handle_verificar_nao_alocados)
        btn_nao_alocados.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=5)
        btn_listar_todos = ttk.Button(reports_frame, text="Listar Todos (Relatório)", command=self.handle_listar_todos)
        btn_listar_todos.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=5)
        btn_pdf = ttk.Button(reports_frame, text="Gerar PDFs Finais", command=self.handle_gerar_pdf)
        btn_pdf.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=5)

        config_frame = ttk.LabelFrame(main_frame, text="Configurações")
        config_frame.pack(fill=tk.X, pady=(10, 10))
        btn_configs = ttk.Button(config_frame, text="Abrir Painel de Configurações do Evento...",
                                 command=self.handle_abrir_config)
        btn_configs.pack(fill=tk.X, expand=True, padx=2, pady=5)

        log_label = tk.Label(main_frame, text="Log de Operações:", font=("Helvetica", 10, "bold"))
        log_label.pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=20, bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.all_buttons = [btn_gerar, btn_verificar, btn_pdf, btn_consultar, btn_trocar, btn_nao_alocados,
                            btn_listar_todos, btn_configs]
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
            target_func(*args)
            for btn in self.all_buttons: btn.config(state=tk.NORMAL)
            self.atualizar_contagem()

        for btn in self.all_buttons: btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=process)
        thread.start()

    def get_selected_area(self):
        selecionado = self.area_selecionada.get()
        if not selecionado or "--" in selecionado:
            messagebox.showwarning("Atenção",
                                   "Por favor, selecione uma área de trabalho antes de continuar.",
                                   parent=self)
            return None
        return selecionado.split(' ')[0]

    def get_raw_selected_area_name(self):
        selecionado = self.area_selecionada.get()
        if not selecionado or "--" in selecionado:
            return None
        return selecionado.split(' ')[0]

    def handle_gerar_ensalamento(self):
        nome_base = self.get_selected_area()
        if not nome_base: return
        print(f"--- GERANDO ARQUIVOS DE ENSALAMENTO PARA: {nome_base} ---\n")
        self.run_in_thread(ensalamento, nome_base, *self.configs)

    def handle_verificar(self):
        nome_base = self.get_selected_area()
        if not nome_base: return
        print(f"--- VERIFICANDO ARQUIVOS DE: {nome_base} ---\n")
        def verificar_ambos(nome):
            for dia in ["1", "2"]: verificar(f"public/csv/{nome}_dia{dia}.csv")
        self.run_in_thread(verificar_ambos, nome_base)

    def handle_gerar_pdf(self):
        nome_base = self.get_selected_area()
        if not nome_base: return
        print(f"--- GERANDO ARQUIVOS PDF PARA: {nome_base} ---\n")
        def gerar_ambos(nome):
            for dia in ["1", "2"]: pdf_ensalamento(f"public/csv/{nome}_dia{dia}.csv", self.configs[1], self.configs[2])
        self.run_in_thread(gerar_ambos, nome_base)

    def handle_consultar(self):
        nome_base = self.get_selected_area()
        if not nome_base: return
        JanelaConsultar(self, nome_base)

    def handle_trocar(self):
        nome_base = self.get_selected_area()
        if not nome_base: return
        JanelaTrocar(self, nome_base)

    def atualizar_contagem(self, *args):
        nome_base = self.get_raw_selected_area_name()
        if not nome_base:
            self.label_contagem.config(text="Total: --")
            return
        total = 0
        for dia in [1, 2]:
            try:
                df_dia = pd.read_csv(f"public/csv/{nome_base}_dia{dia}.csv")
                total += len(df_dia)
            except FileNotFoundError:
                pass
        self.label_contagem.config(text=f"Total: {total}")

    def handle_verificar_nao_alocados(self):
        nome_base = self.get_selected_area()
        if not nome_base: return
        print(f"--- VERIFICANDO NÃO ALOCADOS: {nome_base} ---\n")
        self.run_in_thread(verificar_nao_alocados, nome_base)

    def handle_listar_todos(self):
        nome_base = self.get_selected_area()
        if not nome_base: return
        relatorio_window = tk.Toplevel(self)
        relatorio_window.title(f"Relatório Completo - {nome_base}")
        relatorio_window.geometry("800x600")
        txt = scrolledtext.ScrolledText(relatorio_window, wrap=tk.WORD, font=("Courier", 9))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        try:
            df_dia1 = pd.read_csv(f"public/csv/{nome_base}_dia1.csv")
        except FileNotFoundError:
            df_dia1 = pd.DataFrame()
        try:
            df_dia2 = pd.read_csv(f"public/csv/{nome_base}_dia2.csv")
        except FileNotFoundError:
            df_dia2 = pd.DataFrame()
        df_completo = pd.concat([df_dia1, df_dia2])
        if df_completo.empty:
            txt.insert(tk.END, "Nenhum trabalho encontrado.")
        else:
            trabalhos_agrupados = df_completo.groupby('Orientador(a)')
            orientadores_ordenados = sorted(trabalhos_agrupados.groups.keys())
            for orientador in orientadores_ordenados:
                txt.insert(tk.END, f"\n--- Orientador(a): {orientador} ---\n")
                df_orientador = trabalhos_agrupados.get_group(orientador)
                for _, trabalho in df_orientador.iterrows():
                    txt.insert(tk.END, f"  - Apresentador(a): {trabalho['Apresentador(a)']}\n")
                    txt.insert(tk.END, f"    Título: {trabalho['Título']}\n")
                    txt.insert(tk.END,
                               f"    Local: {trabalho['Sala']} - {trabalho['Horário']} ({trabalho['Sessão']})\n")
        txt.config(state=tk.DISABLED)

    # <-- ALTERAÇÃO 2: Corrigida a função para chamar a JanelaConfig.
    def handle_abrir_config(self):
        JanelaConfig(self)


def abrir_gerenciador_evento(root):
    root.withdraw()
    janela = JanelaGerenciador(root)
    janela.protocol("WM_DELETE_WINDOW", lambda: reabrir_menu_principal(root, janela))


def reabrir_menu_principal(root, janela):
    janela.on_close()
    root.deiconify()


def abrir_script_externo(script_name):
    messagebox.showinfo("Aviso",
                        f"A ferramenta '{script_name}' será aberta em um novo terminal.\nFeche o terminal ao concluir.")
    comando = f'start cmd /k "python {script_name}"' if sys.platform.startswith(
        "win") else f'gnome-terminal -- python3 {script_name}'
    subprocess.Popen(comando, shell=True)


def main():
    root = tk.Tk()
    root.withdraw()
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry("400x250+{}+{}".format(root.winfo_screenwidth() // 2 - 200, root.winfo_screenheight() // 2 - 125))
    splash.config(bg="#e0e8f0")
    tk.Label(splash, text="Sistema de Ensalamento", font=("Helvetica", 20, "bold"), bg="#e0e8f0", fg="#143278").pack(
        pady=(40, 10))
    tk.Label(splash, text="EAIC - UEPG", font=("Helvetica", 16), bg="#e0e8f0", fg="#143278").pack()
    tk.Label(splash, text="Carregando...", font=("Helvetica", 10, "italic"), bg="#e0e8f0").pack(pady=10)
    tk.Label(splash, text="Desenvolvido por João Rafael S. Rosa", font=("Helvetica", 9, "italic"), bg="#e0e8f0").pack(
        side=tk.BOTTOM, pady=10)

    def abrir_menu_principal():
        splash.destroy()
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)
        root.after_idle(root.attributes, '-topmost', False)
        root.focus_force()
        root.title("Sistema de Ensalamento EAIC - Menu Principal")
        root.geometry("500x300+{}+{}".format(root.winfo_screenwidth() // 2 - 250, root.winfo_screenheight() // 2 - 150))
        menu_frame = tk.Frame(root, padx=20, pady=20)
        menu_frame.pack(expand=True, fill=tk.BOTH)
        tk.Label(menu_frame, text="Bem-vindo!", font=("Helvetica", 16, "bold")).pack(pady=(0, 20))
        ttk.Button(menu_frame, text="Criar / Recriar Configurações do Evento",
                   command=lambda: abrir_script_externo("gerador_config.py")).pack(fill=tk.X, ipady=5, pady=4)
        ttk.Button(menu_frame, text="Gerenciar Evento Existente", command=lambda: abrir_gerenciador_evento(root)).pack(
            fill=tk.X, ipady=5, pady=4)
        ttk.Button(menu_frame, text="Limpar Dados Gerados (CSVs, PDFs)",
                   command=lambda: abrir_script_externo("src/limpeza.py")).pack(fill=tk.X, ipady=5, pady=4)

    root.after(2000, abrir_menu_principal)
    root.mainloop()


if __name__ == "__main__":
    main()