import os
import glob


def executar_limpeza():
    """
    Apaga todos os arquivos gerados nas pastas de configuração e saída.
    Pede uma confirmação explícita para segurança.
    """
    pastas_para_limpar = [
        "public/csv",
        "pdfs",
        "public/config"
    ]

    print("=" * 60)
    print(" CUIDADO: AÇÃO DE LIMPEZA IRREVERSÍVEL ".center(60, "!"))
    print("=" * 60)
    print("\nEsta função irá apagar TODOS os arquivos das seguintes pastas:")
    for pasta in pastas_para_limpar:
        print(f"- {pasta}/")
    print("\nIsso inclui todos os CSVs de ensalamento, todos os PDFs")
    print("e todos os arquivos de configuração do evento (áreas, salas, horários).")

    confirmacao = input("\nPara confirmar que deseja apagar tudo, digite a frase 'APAGAR TUDO': ")

    if confirmacao == "APAGAR TUDO":
        print("\nIniciando limpeza...")
        arquivos_apagados = 0
        for pasta in pastas_para_limpar:
            if os.path.exists(pasta):
                # Usa glob para encontrar todos os arquivos dentro da pasta
                arquivos = glob.glob(os.path.join(pasta, '*'))
                for arquivo in arquivos:
                    # Proteção extra para não apagar arquivos .gitkeep
                    if os.path.basename(arquivo) == '.gitkeep':
                        continue
                    try:
                        os.remove(arquivo)
                        print(f"Apagado: {arquivo}")
                        arquivos_apagados += 1
                    except Exception as e:
                        print(f"Erro ao apagar {arquivo}: {e}")
            else:
                print(f"Pasta '{pasta}' não encontrada, pulando.")

        print(f"\nLimpeza concluída! {arquivos_apagados} arquivos foram apagados.")
    else:
        print("\nOperação cancelada. Nenhum arquivo foi apagado.")