import os
import json
import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

try:
    from src.sala import obter_info_area, obter_nome_fisico
except ImportError:
    from sala import obter_info_area, obter_nome_fisico

# Definição de Cores Padrão (RGB e HEX exatos)
COLOR_AZUL_FUNDO = (220, 230, 240)
COLOR_AZUL_TEXTO = (20, 50, 120)
COLOR_CINZA_ZEBRA = (240, 240, 240)

HEX_AZUL_FUNDO = "DCE6F0"
HEX_CINZA_ZEBRA = "F0F0F0"
HEX_BORDA_CINZA = "808080"


def sanitize_text(text):
    """Sanitiza o texto para caracteres compatíveis com o FPDF standard fonts."""
    if text is None:
        return ""
    s = str(text)
    substituicoes = {
        '–': '-', '—': '-', '“': '"', '”': '"', '‘': "'", '’': "'", '…': '...'
    }
    for orig, sub in substituicoes.items():
        s = s.replace(orig, sub)
    return s.encode('latin-1', 'replace').decode('latin-1')


def obter_data_evento_por_dia(nome_base_arquivo):
    """Lê o arquivo config_evento.json e retorna a data exata do dia correspondente."""
    caminho_config = "public/config/config_evento.json"
    datas_evento = []

    if os.path.exists(caminho_config):
        try:
            with open(caminho_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                datas_evento = config.get("DATAS_EVENTO", [])
        except Exception:
            pass

    if "_dia" in nome_base_arquivo:
        try:
            dia_num = int(nome_base_arquivo.split('_dia')[1].split('.')[0])
            if datas_evento and 1 <= dia_num <= len(datas_evento):
                return datas_evento[dia_num - 1]
        except Exception:
            pass

    return ""


def obter_ordem_sessao(sessao_str):
    """Mapeia o nome da sessão para uma ordem cronológica estrita."""
    sessao_lower = str(sessao_str).lower()
    if 'manhã 1' in sessao_lower or 'manha 1' in sessao_lower:
        return 1
    elif 'manhã 2' in sessao_lower or 'manha 2' in sessao_lower:
        return 2
    elif 'tarde' in sessao_lower:
        return 3
    elif 'noite' in sessao_lower:
        return 4
    return 99


# ==========================================
# 1. GERAÇÃO DE PDF (FPDF2)
# ==========================================

class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', area_name='Relatório', event_date=''):
        super().__init__(orientation, unit, format)

        nome_limpo = area_name.upper()
        if nome_limpo.endswith(" - EAIC"):
            self.area_name = nome_limpo
        else:
            self.area_name = f"{nome_limpo} - EAIC"

        self.event_date = event_date

    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*COLOR_AZUL_TEXTO)
        self.cell(0, 8, sanitize_text(self.area_name), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 7, 'UNIVERSIDADE ESTADUAL DE PONTA GROSSA', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

        if self.event_date:
            self.cell(0, 7, sanitize_text(f"Data: {self.event_date}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', align='C')


def pdf_ensalamento(caminho_csv, config_areas_df, mapa_salas_df):
    if not caminho_csv or not os.path.exists(caminho_csv):
        return

    try:
        df = pd.read_csv(caminho_csv, encoding="utf-8-sig")
    except Exception as e:
        print(f"  [ERRO PDF] Falha ao ler CSV '{caminho_csv}': {e}")
        return

    if df.empty:
        return

    nome_base_arquivo = os.path.basename(caminho_csv)
    nome_area_base = nome_base_arquivo.split('_dia')[0].upper()
    info_area = obter_info_area(nome_area_base, config_areas_df)

    nome_area_completo = info_area.get('nome_completo', nome_area_base) if info_area else nome_area_base
    data_do_evento = obter_data_evento_por_dia(nome_base_arquivo)

    pdf = PDF('P', 'mm', 'A4', area_name=nome_area_completo, event_date=data_do_evento)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    FONTE_PADRAO = "Helvetica"

    df['Ordem_Sessao'] = df['Sessão'].apply(obter_ordem_sessao)
    df['Horario_DT'] = pd.to_datetime(df['Horário'], format='%H:%M', errors='coerce')
    df_ordenado = df.sort_values(by=['Ordem_Sessao', 'Sala', 'Horario_DT']).reset_index(drop=True)

    sessoes_agrupadas = df_ordenado.groupby(['Sessão', 'Sala'], sort=False)

    for (nome_sessao, nome_sala_logica), df_grupo in sessoes_agrupadas:
        if pdf.get_y() > 230:
            pdf.add_page()

        if "Manhã 1" in str(nome_sessao):
            novo_titulo_sessao = "Horário (08h30 - 10h00)"
        elif "Manhã 2" in str(nome_sessao):
            novo_titulo_sessao = "Horário (10h30 - 12h00)"
        elif "Tarde" in str(nome_sessao):
            novo_titulo_sessao = "Horário (14h00 - 15h30)"
        else:
            novo_titulo_sessao = str(nome_sessao)

        nome_sala_fisica = obter_nome_fisico(nome_sala_logica, mapa_salas_df)
        sala_fisica_str = str(nome_sala_fisica).strip().upper()
        if not sala_fisica_str.startswith("SALA"):
            sala_fisica_str = f"SALA {sala_fisica_str}"

        titulo_sala_final = f"SESSÃO {nome_sala_logica} - {sala_fisica_str}"

        pdf.set_font(FONTE_PADRAO, 'B', 14)
        pdf.set_fill_color(*COLOR_AZUL_FUNDO)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 9, sanitize_text(novo_titulo_sessao), new_x=XPos.LMARGIN, new_y=YPos.NEXT, border=0, align='C', fill=True)

        pdf.set_font(FONTE_PADRAO, 'B', 12)
        pdf.cell(0, 7, sanitize_text(titulo_sala_final), new_x=XPos.LMARGIN, new_y=YPos.NEXT, border=0, align='C', fill=True)
        pdf.ln(4)

        dados_tabela = [[sanitize_text(col) for col in ["Horário", "Apresentador(a)", "Orientador(a)", "Título"]]]

        for _, trabalho in df_grupo.iterrows():
            horario_inicio_slot_str = str(trabalho.get('Horário', '08:30'))
            try:
                horario_inicio_slot_dt = pd.to_datetime(horario_inicio_slot_str, format='%H:%M', errors='coerce')
                if pd.isna(horario_inicio_slot_dt):
                    intervalo_horario = horario_inicio_slot_str
                else:
                    horario_fim_slot_dt = horario_inicio_slot_dt + pd.Timedelta(minutes=15)
                    horario_fim_slot_str = horario_fim_slot_dt.strftime('%H:%M')
                    intervalo_horario = f"{horario_inicio_slot_str}-{horario_fim_slot_str}"
            except Exception:
                intervalo_horario = horario_inicio_slot_str

            dados_tabela.append([
                sanitize_text(intervalo_horario),
                sanitize_text(trabalho.get('Apresentador(a)', '')),
                sanitize_text(trabalho.get('Orientador(a)', '')),
                sanitize_text(trabalho.get('Título', ''))
            ])

        headings_style = FontFace(emphasis="BOLD", color=(0, 0, 0), fill_color=COLOR_AZUL_FUNDO)
        zebra_style = FontFace(fill_color=COLOR_CINZA_ZEBRA)

        pdf.set_font(FONTE_PADRAO, size=9)
        pdf.set_text_color(0, 0, 0)

        with pdf.table(
                col_widths=(22, 40, 40, 88),
                text_align=("CENTER", "LEFT", "LEFT", "LEFT"),
                line_height=5.5,
                headings_style=headings_style
        ) as table:
            for i, data_row in enumerate(dados_tabela):
                row = table.row()
                if i > 0 and i % 2 != 0:
                    row.style = zebra_style
                for datum in data_row:
                    row.cell(datum)

        pdf.ln(12)

    PASTA_SAIDA = "pdfs/"
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    nome_base_saida = os.path.splitext(os.path.basename(caminho_csv))[0]
    nome_arquivo_saida = os.path.join(PASTA_SAIDA, f"{nome_base_saida}.pdf")

    try:
        pdf.output(nome_arquivo_saida)
        print(f"  [PDF OK] '{nome_arquivo_saida}'")
    except Exception as e:
        print(f"  [ERRO PDF] Não foi possível salvar o arquivo: {e}")


# ==========================================
# 2. GERAÇÃO DE WORD (.DOCX) - FORMATO IDÊNTICO AO PDF
# ==========================================

def _set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Define as margens internas da célula no Word para bater com o padding do PDF."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def _set_table_borders(table, color_hex="808080"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>\n'
        f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>\n'
        f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>\n'
        f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>\n'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>\n'
        f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def word_ensalamento(caminho_csv, config_areas_df, mapa_salas_df):
    if not caminho_csv or not os.path.exists(caminho_csv):
        return

    try:
        df = pd.read_csv(caminho_csv, encoding="utf-8-sig")
    except Exception as e:
        print(f"  [ERRO WORD] Falha ao ler CSV '{caminho_csv}': {e}")
        return

    if df.empty:
        return

    nome_base_arquivo = os.path.basename(caminho_csv)
    nome_area_base = nome_base_arquivo.split('_dia')[0].upper()
    info_area = obter_info_area(nome_area_base, config_areas_df)

    nome_area_completo = info_area.get('nome_completo', nome_area_base) if info_area else nome_area_base

    if not nome_area_completo.upper().endswith(" - EAIC"):
        nome_area_completo = f"{nome_area_completo.upper()} - EAIC"
    else:
        nome_area_completo = nome_area_completo.upper()

    data_do_evento = obter_data_evento_por_dia(nome_base_arquivo)

    doc = Document()

    # Margens idênticas ao A4 do PDF
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)

    # 1. Cabeçalho Principal do Documento
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_after = Pt(2)

    run_title = title_p.add_run(f"{nome_area_completo}\n")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(*COLOR_AZUL_TEXTO)

    run_sub = title_p.add_run("UNIVERSIDADE ESTADUAL DE PONTA GROSSA\n")
    run_sub.font.name = 'Arial'
    run_sub.font.size = Pt(12)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(*COLOR_AZUL_TEXTO)

    if data_do_evento:
        run_date = title_p.add_run(f"Data: {data_do_evento}")
        run_date.font.name = 'Arial'
        run_date.font.size = Pt(12)
        run_date.font.bold = True
        run_date.font.color.rgb = RGBColor(*COLOR_AZUL_TEXTO)

    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(0)
    p_space.paragraph_format.space_after = Pt(6)

    # Ordenação Cronológica
    df['Ordem_Sessao'] = df['Sessão'].apply(obter_ordem_sessao)
    df['Horario_DT'] = pd.to_datetime(df['Horário'], format='%H:%M', errors='coerce')
    df_ordenado = df.sort_values(by=['Ordem_Sessao', 'Sala', 'Horario_DT']).reset_index(drop=True)

    sessoes_agrupadas = df_ordenado.groupby(['Sessão', 'Sala'], sort=False)

    for (nome_sessao, nome_sala_logica), df_grupo in sessoes_agrupadas:
        if "Manhã 1" in str(nome_sessao):
            novo_titulo_sessao = "Horário (08h30 - 10h00)"
        elif "Manhã 2" in str(nome_sessao):
            novo_titulo_sessao = "Horário (10h30 - 12h00)"
        elif "Tarde" in str(nome_sessao):
            novo_titulo_sessao = "Horário (14h00 - 15h30)"
        else:
            novo_titulo_sessao = str(nome_sessao)

        nome_sala_fisica = obter_nome_fisico(nome_sala_logica, mapa_salas_df)
        sala_fisica_str = str(nome_sala_fisica).strip().upper()
        if not sala_fisica_str.startswith("SALA"):
            sala_fisica_str = f"SALA {sala_fisica_str}"

        titulo_sala_final = f"SESSÃO {nome_sala_logica} - {sala_fisica_str}"

        # 2. Banner de Título Sem Bordas Externas
        banner_table = doc.add_table(rows=1, cols=1)
        banner_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        banner_cell = banner_table.cell(0, 0)
        _set_cell_background(banner_cell, HEX_AZUL_FUNDO)
        _set_cell_margins(banner_cell, top=120, bottom=120, left=150, right=150)
        banner_cell.width = Inches(7.2)

        # Remove as bordas do banner de sessão para ficar igual ao bloco do PDF
        tblPr = banner_table._tbl.tblPr
        tblBorders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>\n'
            f'  <w:top w:val="none"/>\n'
            f'  <w:bottom w:val="none"/>\n'
            f'  <w:left w:val="none"/>\n'
            f'  <w:right w:val="none"/>\n'
            f'</w:tblBorders>'
        )
        tblPr.append(tblBorders)

        banner_p = banner_cell.paragraphs[0]
        banner_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        banner_p.paragraph_format.space_before = Pt(2)
        banner_p.paragraph_format.space_after = Pt(2)

        r_horario = banner_p.add_run(f"{novo_titulo_sessao}\n")
        r_horario.font.name = 'Arial'
        r_horario.font.size = Pt(13)
        r_horario.font.bold = True
        r_horario.font.color.rgb = RGBColor(0, 0, 0)

        r_sala = banner_p.add_run(titulo_sala_final)
        r_sala.font.name = 'Arial'
        r_sala.font.size = Pt(12)
        r_sala.font.bold = True
        r_sala.font.color.rgb = RGBColor(0, 0, 0)

        p_sp = doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(0)
        p_sp.paragraph_format.space_after = Pt(3)

        # 3. Tabela Principal
        table = doc.add_table(rows=1, cols=4)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(table, HEX_BORDA_CINZA)

        # Proporção idêntica de colunas ao PDF
        widths = [Inches(0.9), Inches(1.65), Inches(1.65), Inches(3.0)]

        # Cabeçalho da Tabela
        hdr_cells = table.rows[0].cells
        cabeçalhos = ["Horário", "Apresentador(a)", "Orientador(a)", "Título"]

        for i, title in enumerate(cabeçalhos):
            hdr_cells[i].width = widths[i]
            _set_cell_background(hdr_cells[i], HEX_AZUL_FUNDO)
            _set_cell_margins(hdr_cells[i], top=80, bottom=80, left=100, right=100)
            hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            p_hdr = hdr_cells[i].paragraphs[0]
            p_hdr.paragraph_format.space_before = Pt(1)
            p_hdr.paragraph_format.space_after = Pt(1)
            p_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT

            r_hdr = p_hdr.add_run(title)
            r_hdr.font.name = 'Arial'
            r_hdr.font.size = Pt(9.5)
            r_hdr.font.bold = True
            r_hdr.font.color.rgb = RGBColor(0, 0, 0)

        # Linhas de Conteúdo
        for row_idx, (_, trabalho) in enumerate(df_grupo.iterrows()):
            row_cells = table.add_row().cells
            horario_str = str(trabalho.get('Horário', '08:30'))

            try:
                dt_inicio = pd.to_datetime(horario_str, format='%H:%M', errors='coerce')
                if pd.isna(dt_inicio):
                    intervalo = horario_str
                else:
                    intervalo = f"{horario_str}-{(dt_inicio + pd.Timedelta(minutes=15)).strftime('%H:%M')}"
            except Exception:
                intervalo = horario_str

            valores = [
                intervalo,
                str(trabalho.get('Apresentador(a)', '')),
                str(trabalho.get('Orientador(a)', '')),
                str(trabalho.get('Título', ''))
            ]

            is_zebra = (row_idx % 2 != 0)

            for i, val in enumerate(valores):
                row_cells[i].width = widths[i]
                _set_cell_margins(row_cells[i], top=70, bottom=70, left=100, right=100)
                row_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

                if is_zebra:
                    _set_cell_background(row_cells[i], HEX_CINZA_ZEBRA)

                p_cell = row_cells[i].paragraphs[0]
                p_cell.paragraph_format.space_before = Pt(1)
                p_cell.paragraph_format.space_after = Pt(1)
                p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT

                r_val = p_cell.add_run(val)
                r_val.font.name = 'Arial'
                r_val.font.size = Pt(9)
                r_val.font.color.rgb = RGBColor(0, 0, 0)

        p_fim = doc.add_paragraph()
        p_fim.paragraph_format.space_before = Pt(0)
        p_fim.paragraph_format.space_after = Pt(14)

    PASTA_SAIDA = "docx/"
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    nome_base_saida = os.path.splitext(os.path.basename(caminho_csv))[0]
    nome_arquivo_saida = os.path.join(PASTA_SAIDA, f"{nome_base_saida}.docx")

    try:
        doc.save(nome_arquivo_saida)
        print(f"  [WORD OK] '{nome_arquivo_saida}'")
    except Exception as e:
        print(f"  [ERRO WORD] Não foi possível salvar o arquivo: {e}")


def gerar_documentos_finais(caminho_csv, config_areas_df, mapa_salas_df):
    pdf_ensalamento(caminho_csv, config_areas_df, mapa_salas_df)
    word_ensalamento(caminho_csv, config_areas_df, mapa_salas_df)