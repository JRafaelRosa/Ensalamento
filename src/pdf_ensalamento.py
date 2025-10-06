import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace
import os

# --- Os dicionários de mapeamento e as cores continuam aqui ---
MAPEAMENTO_AREAS = {
    "EXATAS": "CIÊNCIAS EXATAS E DA TERRA", "BIOLOGICAS": "CIÊNCIAS BIOLÓGICAS",
    "ENGENHARIAS": "ENGENHARIAS", "SOCIAIS": "CIÊNCIAS SOCIAIS APLICADAS",
    "SAUDE": "CIÊNCIAS DA SAÚDE", "LINGUISTICA": "LINGUÍSTICA, LETRAS E ARTES",
    "AGRARIAS": "CIÊNCIAS AGRÁRIAS", "HUMANAS": "CIÊNCIAS HUMANAS"
}
MAPEAMENTO_SALAS = {
    "EXATAS": {"EX1": "Sala 1", "EX2": "Sala 2", "EX3": "Sala 3", "EX4": "Sala 4"},
    "ENGENHARIAS": {"EN1": "Sala 5", "EN2": "Sala 6", "EN3": "Sala 7", "EN4": "Sala 8"},
    "SOCIAIS": {"SO1": "Sala 9", "SO2": "Sala 10", "SO3": "Sala 11", "SO4": "Sala 12"},
    "HUMANAS": {"HU1": "Sala 13", "HU2": "Sala 14", "HU3": "Sala 15", "HU4": "Sala 16"},
    "BIOLOGICAS": {"BI1": "Sala 17", "BI2": "Sala 18", "BI3": "Sala 19", "BI4": "Sala 20"},
    "SAUDE": {"SA1": "Sala 21", "SA2": "Sala 22", "SA3": "Sala 23", "SA4": "Sala 24"},
    "LINGUISTICA": {"LI1": "Sala 25", "LI2": "Sala 26", "LI3": "Sala 27", "LI4": "Sala 28"},
    "AGRARIAS": {"AG1": "Sala 29", "AG2": "Sala 30", "AG3": "Sala 31", "AG4": "Sala 32"}
}
COLOR_AZUL_FUNDO = (220, 230, 240);
COLOR_AZUL_TEXTO = (20, 50, 120);
COLOR_CINZA_ZEBRA = (240, 240, 240)


def sanitize_text(text): return str(text).encode('latin-1', 'replace').decode('latin-1')


class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', area_name='Relatório', event_date=''):
        super().__init__(orientation, unit, format)
        self.area_name = area_name.upper()
        self.event_date = event_date

    def header(self):
        self.set_font('Helvetica', 'B', 16);
        self.set_text_color(*COLOR_AZUL_TEXTO)
        self.cell(0, 8, sanitize_text(f'{self.area_name} - EAIC'), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('Helvetica', '', 12)
        self.cell(0, 8, 'UNIVERSIDADE ESTADUAL DE PONTA GROSSA', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        if self.event_date:
            self.set_font('Helvetica', 'B', 12)
            self.cell(0, 8, sanitize_text(f"Data: {self.event_date}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15);
        self.set_font('Helvetica', 'I', 8);
        self.cell(0, 10, f'Página {self.page_no()}', align='C')


def pdf_ensalamento(caminho_completo_do_arquivo_csv):
    if not caminho_completo_do_arquivo_csv: print("Nenhum nome de arquivo fornecido."); return
    try:
        df = pd.read_csv(caminho_completo_do_arquivo_csv)
        print(f"\nLendo o arquivo '{caminho_completo_do_arquivo_csv}' para gerar o PDF...")
    except FileNotFoundError:
        print(f"  [ERRO] Arquivo CSV '{caminho_completo_do_arquivo_csv}' não foi encontrado."); return
    except Exception as e:
        print(f"  [ERRO] Ocorreu um erro ao ler o arquivo: {e}"); return

    nome_base_arquivo = os.path.basename(caminho_completo_do_arquivo_csv)
    nome_area_base = nome_base_arquivo.split('_dia')[0].upper()
    nome_area_completo = MAPEAMENTO_AREAS.get(nome_area_base, nome_area_base)
    codigo_area_correto = nome_area_base[:2].upper()

    if "_dia1" in nome_base_arquivo:
        data_do_evento = "06/11/2025"
    elif "_dia2" in nome_base_arquivo:
        data_do_evento = "07/11/2025"
    else:
        data_do_evento = ""

    pdf = PDF('P', 'mm', 'A4', area_name=nome_area_completo, event_date=data_do_evento);
    pdf.add_page();
    pdf.set_auto_page_break(auto=True, margin=15)
    FONTE_PADRAO = "Helvetica"

    sessoes_agrupadas = df.groupby(['Sessão', 'Sala'])
    for (nome_sessao, nome_sala_do_csv), df_grupo in sessoes_agrupadas:
        if pdf.get_y() > 230: pdf.add_page()

        if "Manhã 1" in nome_sessao:
            novo_titulo_sessao = "Horário (08h20 - 10h00)"
        elif "Manhã 2" in nome_sessao:
            novo_titulo_sessao = "Horário (10h30 - 12h15)"
        elif "Tarde" in nome_sessao:
            novo_titulo_sessao = "Horário (14h00 - 15h45)"
        else:
            novo_titulo_sessao = nome_sessao

        # --- LÓGICA DE CORREÇÃO DO NOME DA SALA ---
        # 1. Pega apenas o número da sala que veio do CSV (ex: '1' de 'E1')
        numero_sala = ''.join(filter(str.isdigit, nome_sala_do_csv))
        # 2. Monta o código lógico CORRETO (ex: 'HU1', 'SO1')
        nome_sala_logica_corrigido = f"{codigo_area_correto}{numero_sala}"
        # 3. Procura o nome físico no dicionário
        mapa_salas_area = MAPEAMENTO_SALAS.get(nome_area_base, {})
        nome_sala_fisica = mapa_salas_area.get(nome_sala_logica_corrigido,
                                               nome_sala_logica_corrigido)  # Usa o nome corrigido
        # 4. Monta o título final
        titulo_sala_final = f"SESSÃO {nome_sala_logica_corrigido} - {nome_sala_fisica.upper()}"

        pdf.set_font(FONTE_PADRAO, 'B', 14);
        pdf.set_fill_color(*COLOR_AZUL_FUNDO);
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, sanitize_text(novo_titulo_sessao), new_x=XPos.LMARGIN, new_y=YPos.NEXT, border=0, align='C',
                 fill=True)
        pdf.set_font(FONTE_PADRAO, 'B', 12)
        pdf.cell(0, 8, sanitize_text(titulo_sala_final), new_x=XPos.LMARGIN, new_y=YPos.NEXT, border=0, align='C',
                 fill=True)
        pdf.ln(5)

        # O restante do código para criar a tabela continua o mesmo...
        dados_tabela = [[sanitize_text(col) for col in ["Horário", "Apresentador(a)", "Orientador(a)", "Título"]]]
        for _, trabalho in df_grupo.iterrows():
            horario_inicio_slot_str = trabalho['Horário'];
            horario_inicio_slot_dt = pd.to_datetime(horario_inicio_slot_str)
            horario_fim_slot_dt = horario_inicio_slot_dt + pd.Timedelta(minutes=15);
            horario_fim_slot_str = horario_fim_slot_dt.strftime('%H:%M')
            intervalo_horario = f"{horario_inicio_slot_str}-{horario_fim_slot_str}"
            dados_tabela.append([sanitize_text(intervalo_horario), sanitize_text(trabalho['Apresentador(a)']),
                                 sanitize_text(trabalho['Orientador(a)']), sanitize_text(trabalho['Título'])])
        headings_style = FontFace(emphasis="BOLD", color=(0, 0, 0), fill_color=COLOR_AZUL_FUNDO)
        zebra_style = FontFace(fill_color=COLOR_CINZA_ZEBRA)
        pdf.set_font(FONTE_PADRAO, size=9);
        pdf.set_text_color(0, 0, 0)
        with pdf.table(col_widths=(22, 40, 40, 88), text_align=("CENTER", "LEFT", "LEFT", "LEFT"), line_height=5.5,
                       headings_style=headings_style) as table:
            for i, data_row in enumerate(dados_tabela):
                row = table.row()
                if i > 0 and i % 2 != 0: row.style = zebra_style
                for datum in data_row: row.cell(datum)
        pdf.ln(15)

    PASTA_SAIDA = "pdfs";
    if not os.path.exists(PASTA_SAIDA): os.makedirs(PASTA_SAIDA)
    nome_base_saida = os.path.splitext(os.path.basename(caminho_completo_do_arquivo_csv))[0]
    nome_arquivo_saida = os.path.join(PASTA_SAIDA, f"{nome_base_saida}.pdf")
    try:
        pdf.output(nome_arquivo_saida)
        print(f"PDF gerado com sucesso! Verifique o arquivo: '{nome_arquivo_saida}'")
    except Exception as e:
        print(f"\nOcorreu um erro ao salvar o PDF: {e}")