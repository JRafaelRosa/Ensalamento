import os
import glob
import shutil


def executar_limpeza():
    """
    Apaga todos os arquivos e subpastas gerados nas pastas de configuração e saída.
    Pede uma confirmação explícita para segurança.
    """
    pastas_para_limpar = [
        os.path.normpath("public/csv"),
        os.path.normpath("pdfs"),
        os.path.normpath("public/config")
    ]

    print("=" * 60)
    print(" CUIDADO: AÇÃO DE LIMPEZA IRREVERSÍVEL ".center(60, "!"))
    print("=" * 60)
    print("\nEsta função irá apagar TODOS os arquivos das seguintes pastas:")
    for pasta in pastas_para_limpar:
        print(f"- {pasta}/")
    print("\nIsso inclui todos os CSVs de ensalamento, todos os PDFs")
    print("e todos os arquivos de configuração do evento (áreas, salas, horários).")

    confirmacao = input("\nPara confirmar que deseja apagar tudo, digite a frase 'APAGAR TUDO': ").strip()

    if confirmacao == "APAGAR TUDO":
        print("\nIniciando limpeza...")
        arquivos_apagados = 0

        for pasta in pastas_para_limpar:
            if os.path.exists(pasta):
                itens = glob.glob(os.path.join(pasta, '*'))
                for item in itens:
                    nome_base = os.path.basename(item)
                    # Proteção para manter arquivos de controle de versão
                    if nome_base in ['.gitkeep', '.gitignore']:
                        continue

                    try:
                        if os.path.isfile(item) or os.path.islink(item):
                            os.remove(item)
                            print(f"Apagado arquivo: {item}")
                            arquivos_apagados += 1
                        elif os.path.isdir(item):
                            shutil.rmtree(item)
                            print(f"Apagado diretório: {item}")
                            arquivos_apagados += 1
                    except PermissionError:
                        print(
                            f"Erro de Permissão ao apagar {item}: Verifique se o arquivo está aberto em outro programa.")
                    except Exception as e:
                        print(f"Erro ao apagar {item}: {e}")
            else:
                print(f"Pasta '{pasta}' não encontrada, pulando.")

        print(f"\nLimpeza concluída! {arquivos_apagados} item(ns) apagado(s).")
    else:
        print("\nOperação cancelada. Nenhum arquivo foi apagado.")


if __name__ == "__main__":
    executar_limpeza()