from docx import Document
from docx.oxml.ns import qn
import html
import os
import re
from pathlib import Path
import requests
from typing import Dict
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

class DocxProcessor:
    def __init__(self):
        # def __init__(self, sciledger_url: str, paper_id: str):
        self.heading_map = {
            "Heading 1": "h1",
            "Heading 2": "h2",
            "Heading 3": "h3",
            "Heading 4": "h4",
        }
        self.bullet_regex = r"^[•\-–‣·◦●◉○\*]\s+"
        self.numbered_regex = r"^\d+[\.\)]\s+"
        self.image_index = 1
        self.in_list = False
        self.list_type = None
        self.in_references = False
        self.ref_index = 1
        self.references_html = ""
        self.html_output = ""
        self.sciledger_url = 'https://scideep.imd.ufrn.br' #'http://localhost:5173'
        # sciledger_url
        self.paper_id = "tc"
        self.image_map: Dict[int, str] = {}  # maps image_index to MongoDB _id

    def convert(self, docx_path):
        # Reset state
        self.html_parts = []
        self.image_index = 1
        self.in_list = False
        self.list_type = None
        self.in_references = False
        self.ref_index = 1
        self.references_html = ""
        
        try:
            doc = Document(docx_path)
            
            # Criar diretório de imagens
            images_dir = Path(docx_path).parent / "images"
            images_dir.mkdir(exist_ok=True)
            
            # Processar elementos na ordem original do documento
            for element in doc.element.body:
                if isinstance(element, CT_P):  # Parágrafo
                    para = Paragraph(element, doc)
                    self._process_paragraph(para)
                elif isinstance(element, CT_Tbl):  # Tabela
                    table = Table(element, doc)
                    self._process_table(table)

            # Fechar tags abertas
            if self.in_references:
                self.html_output += "<ol>\n" + self.references_html + "</ol>\n"
            
            if self.in_list:
                self.html_output += f"</{self.list_type}>\n"

            return self.html_output
            

        except Exception as e:
            print(f"Debug - Processing Error: {str(e)}")
            raise

    def _process_paragraph(self, para):
        raw_text = para.text.strip()
        if not raw_text and not any('graphic' in run._element.xml for run in para.runs):
            return

        style = para.style.name
        text = self._substituir_citacoes(self._format_paragraph_runs(para).strip())
        is_list_style = style == "List Paragraph"
        is_bullet = re.match(self.bullet_regex, raw_text)
        is_numbered = re.match(self.numbered_regex, raw_text)

        # Processar imagens
        for run in para.runs:
            self._salvar_imagens(run)

        # Seção de referências
        if style in self.heading_map:
            if self.in_references:
                self.html_output += "<ol>\n" + self.references_html + "</ol>\n"
                self.in_references = False
                self.references_html = ""
                self.ref_index = 1

            tag = self.heading_map[style]
            self.html_output += f"<{tag}>{text}</{tag}>\n"

            if text.lower() in ["referências", "references"]:
                self.in_references = True
            return

        if self.in_references:
            self.references_html += f'<li id="ref-{self.ref_index}">{text}</li>\n'
            self.ref_index += 1
            return

        # Processar listas
        if is_list_style or is_bullet or is_numbered:
            list_prefix_len = 0
            if is_bullet:
                list_prefix_len = len(is_bullet.group(0))
            elif is_numbered:
                list_prefix_len = len(is_numbered.group(0))

            list_text = self._substituir_citacoes(
                self._format_paragraph_runs(para, skip_chars=list_prefix_len).strip()
            )
            self._process_list_item(list_text, is_bullet, is_numbered)
        else:
            if self.in_list:
                self.html_output += f"</{self.list_type}>\n"
                self.in_list = False
                self.list_type = None
            self.html_output += f"<p>{text}</p>\n"

    def _format_paragraph_runs(self, para, skip_chars=0):
        parts = []
        remaining_skip = skip_chars

        for child in para._p:
            if child.tag == qn("w:r"):
                segment, remaining_skip = self._format_run_segment_from_element(child, remaining_skip)
                if segment:
                    parts.append(segment)
                continue

            if child.tag == qn("w:hyperlink"):
                hyperlink_url = self._resolve_hyperlink_url(para, child)
                hyperlink_parts = []

                for run_element in child.findall(qn("w:r")):
                    segment, remaining_skip = self._format_run_segment_from_element(run_element, remaining_skip)
                    if segment:
                        hyperlink_parts.append(segment)

                if hyperlink_parts:
                    hyperlink_content = "".join(hyperlink_parts)
                    if hyperlink_url:
                        safe_url = html.escape(hyperlink_url, quote=True)
                        parts.append(f'<a href="{safe_url}">{hyperlink_content}</a>')
                    else:
                        parts.append(hyperlink_content)

        if parts:
            return "".join(parts)

        return html.escape(para.text or "")

    def _format_run_segment_from_element(self, run_element, remaining_skip=0):
        run_text = "".join(t.text or "" for t in run_element.findall('.//' + qn("w:t")))
        if not run_text:
            return "", remaining_skip

        if remaining_skip >= len(run_text):
            return "", remaining_skip - len(run_text)

        if remaining_skip > 0:
            run_text = run_text[remaining_skip:]
            remaining_skip = 0

        segment = html.escape(run_text)
        run_properties = run_element.find(qn("w:rPr"))
        if self._is_toggle_enabled(run_properties, "w:b"):
            segment = f"<strong>{segment}</strong>"
        if self._is_toggle_enabled(run_properties, "w:i"):
            segment = f"<em>{segment}</em>"

        return segment, remaining_skip

    def _is_toggle_enabled(self, run_properties, tag_name):
        if run_properties is None:
            return False

        element = run_properties.find(qn(tag_name))
        if element is None:
            return False

        val = element.get(qn("w:val"))
        if val is None:
            return True

        return str(val).lower() not in {"0", "false", "off"}

    def _resolve_hyperlink_url(self, para, hyperlink_element):
        rel_id = hyperlink_element.get(qn("r:id"))
        if rel_id and rel_id in para.part.rels:
            relationship = para.part.rels[rel_id]
            return getattr(relationship, "target_ref", None)

        anchor = hyperlink_element.get(qn("w:anchor"))
        if anchor:
            return f"#{anchor}"

        return None

    def _process_table(self, table):
        self.html_output += "<table border='1' style='border-collapse:collapse;'>\n"
        rows = table._tbl.tr_lst
        for row_idx, tr in enumerate(rows):
            self.html_output += "<tr>\n"
            col_idx = 0
            for tc in tr.tc_lst:
                col_span = self._get_col_span(tc)
                v_merge = self._get_vmerge_type(tc)

                if v_merge == "continue":
                    col_idx += col_span
                    continue

                row_span = 1
                if v_merge == "restart":
                    row_span = self._count_vertical_span(rows, row_idx, col_idx)

                cell = _Cell(tc, table)
                cell_text = "\n".join(paragraph.text for paragraph in cell.paragraphs).strip()
                cell_text = html.escape(cell_text)
                cell_text = self._substituir_citacoes(cell_text).replace("\n", "<br>")

                attrs = ""
                if row_span > 1:
                    attrs += f' rowspan="{row_span}"'
                if col_span > 1:
                    attrs += f' colspan="{col_span}"'

                self.html_output += f"<td{attrs}>{cell_text}</td>\n"
                col_idx += col_span
            self.html_output += "</tr>\n"
        self.html_output += "</table>\n<br/>\n"

    def _get_col_span(self, tc):
        tc_pr = tc.tcPr
        if tc_pr is None or tc_pr.gridSpan is None:
            return 1
        return int(tc_pr.gridSpan.val)

    def _get_vmerge_type(self, tc):
        tc_pr = tc.tcPr
        if tc_pr is None or tc_pr.vMerge is None:
            return None
        # In WordprocessingML, missing vMerge@val means continuation.
        return tc_pr.vMerge.val or "continue"

    def _find_tc_at_col(self, tr, target_col):
        current_col = 0
        for tc in tr.tc_lst:
            span = self._get_col_span(tc)
            if current_col == target_col:
                return tc
            current_col += span
        return None

    def _count_vertical_span(self, rows, row_idx, col_idx):
        span = 1
        for next_row in rows[row_idx + 1:]:
            next_tc = self._find_tc_at_col(next_row, col_idx)
            if next_tc is None:
                break
            if self._get_vmerge_type(next_tc) != "continue":
                break
            span += 1
        return span

    def _salvar_imagens(self, run):
        drawing_elements = run._element.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
        for blip in drawing_elements:
            embed = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            if not embed:
                continue
                
            image_part = run.part.related_parts[embed]
            image_data = image_part.blob
            content_type = image_part.content_type

            # Create multipart form data with correct structure
            files = {
                'image': ('image.jpg', image_data, content_type)
            }

            # Add necessary headers
            # headers = {
            #     'Accept': 'application/json',
            #     #'Origin': self.sciledger_url
            #     'X-Requested-With': 'XMLHttpRequest',
            #     'X-Internal-Request': 'true'
            # }
            
            headers = {
                "Content-Type": "application/octet-stream",
                "X-Filename": "image.jpg",
                "X-Content-Type": "image/jpeg"
}

            url = f"{self.sciledger_url}/api/images/uploadraw"

            print(f"Sending request to: {url}")
            try:
                response = requests.post(
                    url, 
                    # files=files,
                    data=image_data,
                    headers=headers
                )
                
                print('Response:', response)
                print('Response status code:', response.status_code)
                print('Response content:', response.text)
                
                if response.status_code != 200:
                    raise Exception(f"Failed to upload image: {response.text}")
                    
                result = response.json()
                if not result.get('success'):
                    raise Exception("Image upload failed")
                    
                image_id = result['id']
                self.image_map[self.image_index] =  image_id
                
                # Add image tag using the correct path
                self.html_output += (
                    f'<img src="/api/images/{image_id}" '
                    f'alt="Image {self.image_index}" '
                    f'style="max-width:100%;"/>\n'
                )
                self.image_index += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {str(e)}")
                raise Exception(f"Failed to upload image: {str(e)}")

    def _substituir_citacoes(self, texto):
        return re.sub(r"\[(\d+)\]", r'<a href="#ref-\1">[\1]</a>', texto)

    def _process_list_item(self, text, is_bullet, is_numbered):
        new_list_type = "ul" if is_bullet else "ol" if is_numbered else "ul"

        if not self.in_list or new_list_type != self.list_type:
            if self.in_list:
                self.html_output += f"</{self.list_type}>\n"
            self.html_output += f"<{new_list_type}>\n"
            self.in_list = True
            self.list_type = new_list_type

        self.html_output += f"<li>{text}</li>\n"