import json
import os
import pandas as pd


def carregar_dias_evento():
    caminho_config = "public/config/config_evento.json"
    if os.path.exists(caminho_config):
        try:
            with open(caminho_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("DIAS_EVENTO", 2)
        except Exception:
            pass
    return 2


def carregar_ensalamento_completo(nome_base):
    """Carrega e junta os arquivos CSV de todos os dias do evento."""
    dfs = []
    dias_evento = carregar_dias_evento()

    for dia in range(1, dias_evento + 1):
        caminho = f"public/csv/{nome_base}_dia{dia}.csv"
        try:
            df_dia = pd.read_csv(caminho, encoding="utf-8-sig")
            df_dia['Dia'] = dia
            dfs.append(df_dia)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            pass

    if not dfs:
        return None

    return pd.concat(dfs, ignore_index=True)


def consultar(nome_base):
    """Função principal de consulta interativa via terminal."""
    df = carregar_ensalamento_completo(nome_base)
    if df is None or df.empty:
        print(f"Arquivos de ensalamento (.csv) para '{nome_base}' não foram encontrados ou estão vazios.")
        print("Execute a geração de ensalamento primeiro.")
        return

    while True:
        print("\n--- Ferramenta de Consulta ---")
        print("1. Buscar por Apresentador(a)")
        print("2. Buscar por Orientador(a)")
        print("3. Listar TUDO (organizado por Orientador)")
        print("0. Voltar ao menu principal")
        resp = input("Escolha uma opção: ").strip()

        if resp == '0':
            break

        elif resp == '1':
            termo_busca = input("Digite o nome (ou parte do nome) do(a) Apresentador(a): ").strip().lower()
            if not termo_busca:
                continue

            coluna_busca = 'Apresentador(a)' if 'Apresentador(a)' in df.columns else df.columns[0]
            resultados = df[df[coluna_busca].astype(str).str.lower().str.contains(termo_busca, na=False)]

            if resultados.empty:
                print("\nNenhum resultado encontrado.")
            else:
                print("\n--- Resultados Encontrados ---")
                for _, trabalho in resultados.iterrows():
                    apresentador = trabalho.get('Apresentador(a)', trabalho.get('Apresentador', 'N/A'))
                    orientador = trabalho.get('Orientador(a)', trabalho.get('Orientador', 'N/A'))
                    titulo = trabalho.get('Título', trabalho.get('Titulo', 'N/A'))
                    dia = trabalho.get('Dia', '1')
                    sala = trabalho.get('Sala', 'N/A')
                    horario = trabalho.get('Horário', trabalho.get('Horario', 'N/A'))
                    sessao = trabalho.get('Sessão', 'N/A')

                    print(f"Apresentador(a): {apresentador}")
                    print(f"  Orientador(a): {orientador}")
                    print(f"  Título       : {titulo}")
                    print(f"  --> LOCAL    : Dia {dia}, Sala {sala}, Horário: {horario} ({sessao})")
                    print("-" * 40)

            input("\nPressione Enter para continuar...")

        elif resp == '2':
            termo_busca = input("Digite o nome (ou parte do nome) do(a) Orientador(a): ").strip().lower()
            if not termo_busca:
                continue

            coluna_busca = 'Orientador(a)' if 'Orientador(a)' in df.columns else df.columns[0]
            resultados = df[df[coluna_busca].astype(str).str.lower().str.contains(termo_busca, na=False)]

            if resultados.empty:
                print("\nNenhum resultado encontrado.")
            else:
                print("\n--- Resultados Encontrados ---")
                for _, trabalho in resultados.iterrows():
                    apresentador = trabalho.get('Apresentador(a)', trabalho.get('Apresentador', 'N/A'))
                    orientador = trabalho.get('Orientador(a)', trabalho.get('Orientador', 'N/A'))
                    titulo = trabalho.get('Título', trabalho.get('Titulo', 'N/A'))
                    dia = trabalho.get('Dia', '1')
                    sala = trabalho.get('Sala', 'N/A')
                    horario = trabalho.get('Horário', trabalho.get('Horario', 'N/A'))
                    sessao = trabalho.get('Sessão', 'N/A')

                    print(f"Apresentador(a): {apresentador}")
                    print(f"  Orientador(a): {orientador}")
                    print(f"  Título       : {titulo}")
                    print(f"  --> LOCAL    : Dia {dia}, Sala {sala}, Horário: {horario} ({sessao})")
                    print("-" * 40)

            input("\nPressione Enter para continuar...")

        elif resp == '3':
            col_orientador = 'Orientador(a)' if 'Orientador(a)' in df.columns else 'Orientador'
            if col_orientador not in df.columns:
                print("Coluna de Orientador não encontrada no arquivo.")
                continue

            trabalhos_agrupados = df.groupby(col_orientador)
            orientadores_ordenados = sorted(trabalhos_agrupados.groups.keys())

            print("\n" + "=" * 70)
            print(" RELATÓRIO COMPLETO POR ORIENTADOR ".center(70, "="))
            print("=" * 70)

            for orientador in orientadores_ordenados:
                print("\n########################################################\n")
                print(f"-------------------- {orientador} -----------------------")
                print("########################################################\n")

                df_orientador = trabalhos_agrupados.get_group(orientador)

                for _, trabalho in df_orientador.iterrows():
                    apresentador = trabalho.get('Apresentador(a)', trabalho.get('Apresentador', 'N/A'))
                    titulo = trabalho.get('Título', trabalho.get('Titulo', 'N/A'))
                    dia = trabalho.get('Dia', '1')
                    sala = trabalho.get('Sala', 'N/A')
                    horario = trabalho.get('Horário', trabalho.get('Horario', 'N/A'))

                    print(f"  - Apresentador(a): {apresentador}")
                    print(f"    Título         : {titulo}")
                    print(f"    Local          : Dia {dia}, Sala {sala}, Horário: {horario}\n")

            input("\nFim do relatório. Pressione Enter para continuar...")

        else:
            print("Opção inválida.")
            input("\nPressione Enter para continuar...")