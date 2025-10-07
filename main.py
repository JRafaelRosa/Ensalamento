import os
import sys
from src.verifica import verificar
from src.organizar import consultar
from src.gerar_ensalamento import ensalamento
from src.pdf_ensalamento import pdf_ensalamento
from src.trocar import trocar


def limpar_console():
    os.system("cls" if sys.platform.startswith("win") else "clear")

def pausar_e_voltar():
    input("\nPressione Enter para continuar...")
    limpar_console()

def menu(nome_base):
    while True:
        print("\n=== MENU ===")
        print(f"Área selecionada: {nome_base}")
        print("1 - Buscar orientador ou apresentador")
        print("2 - Verificar Ensalamento Gerado (.csv)")
        print("3 - Gerar Arquivos de Ensalamento (.csv)")
        print("4 - Gerar Relatórios Finais em PDF")
        print("5 - Fazer Ajuste Manual no Ensalamento")
        print("6 - Sair\n")

        resp = input("Escolha uma opção: ").strip()
        limpar_console()

        if resp == "1":
            print(f"--- ANÁLISE DE ORIENTADORES: {nome_base} ---")
            consultar(nome_base)
            pausar_e_voltar()
        elif resp == "2":
            print(f"--- VERIFICANDO ARQUIVOS DE {nome_base} ---")
            for dia in ["1", "2"]:

                caminho_csv_completo = f"public/csv/{nome_base}_dia{dia}.csv"
                verificar(caminho_csv_completo)
            pausar_e_voltar()
        elif resp == "3":
            print(f"--- GERANDO ARQUIVOS DE ENSALAMENTO: {nome_base} ---")
            ensalamento(nome_base)
            pausar_e_voltar()
        elif resp == "4":
            print(f"--- GERANDO ARQUIVOS PDF: {nome_base} ---")
            for dia in ["1", "2"]:

                caminho_csv_completo = f"public/csv/{nome_base}_dia{dia}.csv"
                pdf_ensalamento(caminho_csv_completo)
            pausar_e_voltar()
        elif resp == "5":
            print(f"--- FERRAMENTA DE AJUSTE MANUAL: {nome_base} ---")
            trocar(nome_base)
            pausar_e_voltar()
        elif resp == "6":
            print("Saindo do programa...")
            break
        else:
            print("Opção inválida. Tente novamente.")
            pausar_e_voltar()

def processar():
    nomes = ["AGRARIAS"]

    for nome_base in nomes:
        print(f"\n\n{'=' * 20} PROCESSANDO ÁREA: {nome_base.upper()} {'=' * 20}")

        print("\n--- Gerando arquivos CSV... ---")
        ensalamento(nome_base)

        for dia in [1, 2]:
            print(f"\n--- Processando Dia {dia}... ---")

            caminho_csv_completo = f"public/csv/{nome_base}_dia{dia}.csv"

            if os.path.exists(caminho_csv_completo):

                print(f"\nVerificando {caminho_csv_completo}...")
                verificar(caminho_csv_completo)

                print(f"\nGerando PDF para {caminho_csv_completo}...")
                pdf_ensalamento(caminho_csv_completo)
            else:
                print(
                    f"AVISO: Arquivo '{caminho_csv_completo}' não encontrado. Pulando verificação e PDF para o Dia {dia}.")

    print(f"\n\n{'=' * 20} PROCESSO FINALIZADO PARA TODAS AS ÁREAS {'=' * 20}")


def gerar_pdf():
    nomes = ["AGRARIAS","BIOLOGICAS","EXATAS", "ENGENHARIAS", "HUMANAS", "LINGUISTICA", "SAUDE", "SOCIAIS"]

    for nome_base in nomes:
        for dia in [1, 2]:
            caminho_csv_completo = f"public/csv/{nome_base}_dia{dia}.csv"
            pdf_ensalamento(caminho_csv_completo)

def main():

    processar()

    # gerar_pdf()

    arquivo = input("Nome arquivo: ").strip()
    if not arquivo:
        print("Nenhum nome fornecido. Encerrando.")
        return
    limpar_console()
    menu(arquivo)

if __name__ == "__main__":
    main()