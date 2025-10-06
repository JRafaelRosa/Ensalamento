import pandas as pd


def carregar_ensalamento_completo(nome_base):
    """Carrega e junta os arquivos CSV do dia 1 e 2."""
    dfs = []
    for dia in [1, 2]:
        caminho = f"public/csv/{nome_base}_dia{dia}.csv"
        try:
            df_dia = pd.read_csv(caminho)
            df_dia['Dia'] = dia
            dfs.append(df_dia)
        except FileNotFoundError:
            pass
    if not dfs:
        return None
    return pd.concat(dfs, ignore_index=True)


def consultar(nome_base):
    """Função principal de consulta interativa."""
    df = carregar_ensalamento_completo(nome_base)
    if df is None:
        print("Arquivos de ensalamento (.csv) não encontrados. Execute a 'Opção 2 - Gerar Ensalamento' primeiro.")
        return

    while True:
        print("\n--- Ferramenta de Consulta ---")
        print("1. Buscar por Apresentador(a)")
        print("2. Buscar por Orientador(a)")
        print("3. Listar TUDO (organizado por Orientador)")  # <-- Nome da opção atualizado
        print("0. Voltar ao menu principal")
        resp = input("Escolha uma opção: ").strip()

        if resp == '0':
            break
        elif resp == '1':
            termo_busca = input("Digite o nome (ou parte do nome) do(a) Apresentador(a): ").strip().lower()
            if not termo_busca: continue
            coluna_busca = 'Apresentador(a)'

            resultados = df[df[coluna_busca].str.lower().str.contains(termo_busca, na=False)]
            if resultados.empty:
                print("Nenhum resultado encontrado.")
            else:
                print("\n--- Resultados Encontrados ---")
                for _, trabalho in resultados.iterrows():
                    print(f"Apresentador(a): {trabalho['Apresentador(a)']}")
                    print(f"  Orientador(a): {trabalho['Orientador(a)']}")
                    print(f"  Título: {trabalho['Título']}")
                    print(
                        f"  --> LOCAL: Dia {trabalho['Dia']}, Sala {trabalho['Sala']}, Horário: {trabalho['Horário']} ({trabalho['Sessão']})")
                    print("-" * 30)

            input("\nPressione Enter para continuar...")

        elif resp == '2':
            termo_busca = input("Digite o nome (ou parte do nome) do(a) Orientador(a): ").strip().lower()
            if not termo_busca: continue
            coluna_busca = 'Orientador(a)'

            resultados = df[df[coluna_busca].str.lower().str.contains(termo_busca, na=False)]
            if resultados.empty:
                print("Nenhum resultado encontrado.")
            else:
                print("\n--- Resultados Encontrados ---")
                for _, trabalho in resultados.iterrows():
                    print(f"Apresentador(a): {trabalho['Apresentador(a)']}")
                    print(f"  Orientador(a): {trabalho['Orientador(a)']}")
                    print(f"  Título: {trabalho['Título']}")
                    print(
                        f"  --> LOCAL: Dia {trabalho['Dia']}, Sala {trabalho['Sala']}, Horário: {trabalho['Horário']} ({trabalho['Sessão']})")
                    print("-" * 30)

            input("\nPressione Enter para continuar...")

        # --- BLOCO DE CÓDIGO ATUALIZADO ---
        elif resp == '3':
            # Agrupa todos os trabalhos pelo orientador
            trabalhos_agrupados = df.groupby('Orientador(a)')
            # Ordena os nomes dos orientadores para exibir em ordem alfabética
            orientadores_ordenados = sorted(trabalhos_agrupados.groups.keys())

            print("\n" + "=" * 70)
            print(" RELATÓRIO COMPLETO POR ORIENTADOR ".center(70, "="))
            print("=" * 70)

            for orientador in orientadores_ordenados:
                print("\n########################################################\n")
                print(f"-------------------- {orientador} -----------------------")
                print("########################################################\n")

                # Pega o grupo de trabalhos daquele orientador
                df_orientador = trabalhos_agrupados.get_group(orientador)

                for _, trabalho in df_orientador.iterrows():
                    print("\n")
                    print(f"  - Apresentador(a): {trabalho['Apresentador(a)']}")
                    print(f"    Título: {trabalho['Título']}")
                    print(f"    Local: Dia {trabalho['Dia']}, Sala {trabalho['Sala']}, Horário: {trabalho['Horário']}")

            input("\nFim do relatório. Pressione Enter para continuar...")

        else:
            print("Opção inválida.")
            input("\nPressione Enter para continuar...")