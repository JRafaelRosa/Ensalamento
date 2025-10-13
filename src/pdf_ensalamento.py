import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace
import os
from src.sala import obter_info_area, obter_nome_fisico

# (As definições de cores, a classe PDF e a função sanitize_text continuam as mesmas)
COLOR_AZUL_FUNDO = (220, 230, 240);
COLOR_AZUL_TEXTO = (20, 50, 120);
COLOR_CINZA_ZEBRA = (240, 240, 240)


def sanitize_text(text): return str(text).encode('latin-1', 'replace').decode('latin-1')


class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', area_name='Relatório', event_date=''):
        super().__init__(orientation, unit, format);
        self.area_name = area_name.upper();
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


def pdf_ensalamento(caminho_completo_do_arquivo_csv, config_areas_df, mapa_salas_df):
    if not caminho_completo_do_arquivo_csv:
        print("Nenhum nome de arquivo fornecido.")
        return

    try:
        df = pd.read_csv(caminho_completo_do_arquivo_csv)
        print(f"\nLendo o arquivo '{caminho_completo_do_arquivo_csv}' para gerar o PDF...")
    except FileNotFoundError:
        print(f"  [ERRO] Arquivo CSV '{caminho_completo_do_arquivo_csv}' não foi encontrado. PDF não gerado.")
        return
    except Exception as e:
        print(f"  [ERRO] Ocorreu um erro ao ler o arquivo: {e}")
        return

    nome_base_arquivo = os.path.basename(caminho_completo_do_arquivo_csv)
    nome_area_base = nome_base_arquivo.split('_dia')[0].upper()
    info_area = obter_info_area(nome_area_base, config_areas_df)
    if info_area is None: return
    nome_area_completo = info_area['nome_completo']

    if "_dia1" in nome_base_arquivo:
        data_do_evento = "06/11/2025"
    elif "_dia2" in nome_base_arquivo:
        data_do_evento = "07/11/2025"
    else:
        data_do_evento = ""

    pdf = PDF('P', 'mm', 'A4', area_name=nome_area_completo, event_date=data_do_evento)
    pdf.add_page();
    pdf.set_auto_page_break(auto=True, margin=15)
    FONTE_PADRAO = "Helvetica"

    sessoes_agrupadas = df.groupby(['Sessão', 'Sala'])
    for (nome_sessao, nome_sala_logica), df_grupo in sessoes_agrupadas:
        if pdf.get_y() > 230: pdf.add_page()

        if "Manhã 1" in nome_sessao:
            novo_titulo_sessao = "Horário (08h20 - 10h00)"
        elif "Manhã 2" in nome_sessao:
            novo_titulo_sessao = "Horário (10h30 - 12h15)"
        elif "Tarde" in nome_sessao:
            novo_titulo_sessao = "Horário (14h00 - 15h45)"
        else:
            novo_titulo_sessao = nome_sessao

        nome_sala_fisica = obter_nome_fisico(nome_sala_logica, mapa_salas_df)

        # --- LINHA CORRIGIDA ---
        # Garante que o nome da sala seja tratado como texto (string) antes de usar .upper()
        titulo_sala_final = f"SESSÃO {nome_sala_logica} - {str(nome_sala_fisica).upper()}"

        pdf.set_font(FONTE_PADRAO, 'B', 14);
        pdf.set_fill_color(*COLOR_AZUL_FUNDO);
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, sanitize_text(novo_titulo_sessao), new_x=XPos.LMARGIN, new_y=YPos.NEXT, border=0, align='C',
                 fill=True)
        pdf.set_font(FONTE_PADRAO, 'B', 12)
        pdf.cell(0, 8, sanitize_text(titulo_sala_final), new_x=XPos.LMARGIN, new_y=YPos.NEXT, border=0, align='C',
                 fill=True)
        pdf.ln(5)

        # O restante do código continua o mesmo...
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

    PASTA_SAIDA = "pdfs/"
    if not os.path.exists(PASTA_SAIDA): os.makedirs(PASTA_SAIDA)
    nome_base_saida = os.path.splitext(os.path.basename(caminho_completo_do_arquivo_csv))[0]
    nome_arquivo_saida = os.path.join(PASTA_SAIDA, f"{nome_base_saida}.pdf")
    try:
        pdf.output(nome_arquivo_saida)
        print(f"PDF gerado com sucesso! Verifique o arquivo: '{nome_arquivo_saida}'")
    except Exception as e:
        print(f"\nOcorreu um erro ao salvar o PDF: {e}")