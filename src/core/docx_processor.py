from docx import Document
from docx.oxml.ns import qn
import os
import re
from pathlib import Path
import requests
from typing import Dict

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
        self.sciledger_url = 'http://localhost:5173'
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
            
            # Processar parágrafos
            for para in doc.paragraphs:
                self._process_paragraph(para)

            # Processar tabelas
            for table in doc.tables:
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
        text = self._substituir_citacoes(raw_text)
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
            self._process_list_item(text, is_bullet, is_numbered)
        else:
            if self.in_list:
                self.html_output += f"</{self.list_type}>\n"
                self.in_list = False
                self.list_type = None
            self.html_output += f"<p>{text}</p>\n"

    def _process_table(self, table):
        self.html_output += "<table border='1' style='border-collapse:collapse;'>\n"
        for row in table.rows:
            self.html_output += "<tr>\n"
            for cell in row.cells:
                cell_text = self._substituir_citacoes(cell.text.strip()).replace("\n", "<br>")
                self.html_output += f"<td>{cell_text}</td>\n"
            self.html_output += "</tr>\n"
        self.html_output += "</table>\n<br/>\n"

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
        item_text = re.sub(self.bullet_regex if is_bullet else self.numbered_regex, '', text)

        if not self.in_list or new_list_type != self.list_type:
            if self.in_list:
                self.html_output += f"</{self.list_type}>\n"
            self.html_output += f"<{new_list_type}>\n"
            self.in_list = True
            self.list_type = new_list_type

        self.html_output += f"<li>{item_text}</li>\n"