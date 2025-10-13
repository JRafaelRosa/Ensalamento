import os
import sys
from src.organizar import consultar
from src.gerar_ensalamento import ensalamento
from src.verifica import verificar
from src.pdf_ensalamento import pdf_ensalamento
from src.trocar import trocar
from src.sala import carregar_config_geral


def limpar_console(): os.system("cls" if sys.platform.startswith("win") else "clear")


def pausar_e_voltar(): input("\nPressione Enter para continuar..."); limpar_console()


def menu(nome_base, configs):
    config_evento, config_areas_df, mapa_salas_df, horarios_sessoes_df = configs
    while True:
        print("\n=== MENU ===");
        print(f"Área selecionada: {nome_base}")
        print("1 - Analisar Arquivo de Entrada");
        print("2 - Gerar Arquivos de Ensalamento (.csv)")
        print("3 - Consultar Ensalamento Gerado");
        print("4 - Verificar Ensalamento Gerado")
        print("5 - Gerar Relatórios Finais em PDF");
        print("6 - Fazer Ajuste Manual (Trocar/Mover)")
        print("0 - Sair\n")
        resp = input("Escolha uma opção: ").strip();
        limpar_console()

        if resp == "1":
            print(f"--- ANÁLISE DE ORIENTADORES: {nome_base} ---");
            orientador(nome_base);
            pausar_e_voltar()
        elif resp == "2":
            print(f"--- GERANDO ARQUIVOS DE ENSALAMENTO: {nome_base} ---")
            ensalamento(nome_base, config_evento, config_areas_df, mapa_salas_df, horarios_sessoes_df)
            pausar_e_voltar()
        elif resp == "3":
            print("Função de consulta ainda não implementada nesta estrutura.");
            pausar_e_voltar()
        elif resp == "4":
            print(f"--- VERIFICANDO ARQUIVOS DE {nome_base} ---")
            for dia in ["1", "2"]:
                caminho_csv = f"public/csv/{nome_base}_dia{dia}.csv"
                verificar(caminho_csv)
            pausar_e_voltar()
        elif resp == "5":
            print(f"--- GERANDO ARQUIVOS PDF: {nome_base} ---")
            for dia in ["1", "2"]:
                caminho_csv = f"public/csv/{nome_base}_dia{dia}.csv"
                pdf_ensalamento(caminho_csv, config_areas_df, mapa_salas_df)
            pausar_e_voltar()
        elif resp == "6":
            print(f"--- FERRAMENTA DE AJUSTE MANUAL: {nome_base} ---");
            trocar(nome_base);
            pausar_e_voltar()
        elif resp == "0":
            print("Saindo do programa...");
            break
        else:
            print("Opção inválida.");
            pausar_e_voltar()


def main():
    limpar_console()
    print("Carregando arquivos de configuração...")
    configs = carregar_config_geral()
    if configs[0] is None:
        input("Pressione Enter para sair.")
        return

    arquivo = input("Digite o nome base da área (ex: EXATAS): ").strip()
    if not arquivo: print("Nenhum nome fornecido."); return
    limpar_console();
    menu(arquivo, configs)


if __name__ == "__main__":
    main()