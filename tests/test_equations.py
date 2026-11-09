"""Native OMML fixtures are converted by the real Pandoc binary, not a mock."""

import os
import shutil
import sys
import subprocess
from types import SimpleNamespace

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from io import BytesIO
import asyncio
from lxml import etree
import pytest

from src.core.docx_processor import DocxProcessor
from src.core.equations import EquationConversionError


def omml(body, display=False):
    math = f"<m:oMath>{body}</m:oMath>"
    if display:
        math = f"<m:oMathPara>{math}</m:oMathPara>"
    return parse_xml(math.replace(
        "<m:oMathPara>" if display else "<m:oMath>",
        f'<m:oMathPara {nsdecls("m")}>' if display else f'<m:oMath {nsdecls("m")}>',
        1,
    ))


def run(text):
    return f"<m:r><m:t>{text}</m:t></m:r>"


FRACTION = f"<m:f><m:num>{run('1')}</m:num><m:den>{run('x')}</m:den></m:f>"
ROOT = f"<m:rad><m:radPr><m:degHide m:val='1'/></m:radPr><m:deg/><m:e>{run('x')}</m:e></m:rad>"
MATRIX = "<m:m>" + "".join(
    f"<m:mr><m:e>{run(a)}</m:e><m:e>{run(b)}</m:e></m:mr>"
    for a, b in [('a', 'b'), ('c', 'd')]
) + "</m:m>"
INTEGRAL = (
    "<m:nary><m:naryPr><m:chr m:val='∫'/><m:limLoc m:val='subSup'/></m:naryPr>"
    f"<m:sub>{run('0')}</m:sub><m:sup>{run('1')}</m:sup><m:e>{run('x dx')}</m:e></m:nary>"
)
SUM = INTEGRAL.replace('∫', '∑')
SCRIPTS = f"<m:sSubSup><m:e>{run('x')}</m:e><m:sub>{run('i')}</m:sub><m:sup>{run('2')}</m:sup></m:sSubSup>"
ALIGNED = f"<m:eqArr><m:e>{run('x=1')}</m:e><m:e>{run('y=2')}</m:e></m:eqArr>"


@pytest.fixture
def pandoc(monkeypatch):
    binary = os.environ.get('PANDOC_PATH') or shutil.which('pandoc')
    if not binary:
        try:
            import pypandoc
            binary = pypandoc.get_pandoc_path()
        except (ImportError, OSError):
            pytest.fail('Install Pandoc (or pypandoc_binary) to run native equation tests.')
    monkeypatch.setenv('PANDOC_PATH', binary)
    return binary


def convert(document, tmp_path, processor=None):
    path = tmp_path / 'equations.docx'
    document.save(path)
    return (processor or DocxProcessor()).convert(str(path))


@pytest.mark.parametrize('source,tag', [
    (FRACTION, 'mfrac'), (ROOT, 'msqrt'), (MATRIX, 'mtable'),
    (INTEGRAL, 'msubsup'), (SUM, 'msubsup'), (SCRIPTS, 'msubsup'), (ALIGNED, 'mtable'),
])
def test_complex_native_equations(source, tag, tmp_path, pandoc):
    document = Document()
    document.add_paragraph()._p.append(omml(source, display=True))
    output = convert(document, tmp_path)
    root = etree.fromstring(f'<root>{output}</root>'.encode())
    assert root.findall(f'.//{{http://www.w3.org/1998/Math/MathML}}{tag}')
    assert 'display="block"' in output
    assert 'data-equation-source="omml"' in output


def test_inline_order_tables_and_reusing_processor(tmp_path, pandoc):
    document = Document()
    paragraph = document.add_paragraph('Before ')
    paragraph._p.append(omml(FRACTION))
    paragraph.add_run(' after. See [1].')
    document.add_table(rows=1, cols=1).cell(0, 0).paragraphs[0]._p.append(omml(MATRIX))
    processor = DocxProcessor()
    output = convert(document, tmp_path, processor)
    assert output.index('Before') < output.index('<math') < output.index('after.')
    assert 'display="inline"' in output
    assert '<a href="#ref-1">[1]</a>' in output
    assert '<td><math' in output
    assert output.count('<math') == 2
    assert output == convert(document, tmp_path, processor)


def test_math_brackets_are_not_rewritten_as_reference_links():
    math = '<math><mtext>[1]</mtext><annotation encoding="application/x-tex">[1]</annotation></math>'
    result = DocxProcessor()._substituir_citacoes(f'{math} see [1]')
    assert result.startswith(math)
    assert result.count('<a ') == 1


def test_equation_in_content_control_and_hyperlink(tmp_path, pandoc):
    document = Document()
    paragraph = document.add_paragraph()
    content = parse_xml(f'<w:sdt {nsdecls("w")}><w:sdtContent/></w:sdt>')
    content[0].append(omml(FRACTION))
    paragraph._p.append(content)
    link = parse_xml(f'<w:hyperlink {nsdecls("w")} w:anchor="target"/>')
    link.append(omml(ROOT))
    paragraph._p.append(link)
    output = convert(document, tmp_path)
    assert output.count('<math') == 2
    assert '<a href="#target"><math' in output


def test_api_returns_native_equations_and_count(pandoc):
    from fastapi import UploadFile
    from src.api.routes import convert_docx
    document = Document()
    document.add_paragraph()._p.append(omml(FRACTION))
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    result = asyncio.run(convert_docx(UploadFile(filename='math.docx', file=buffer)))
    assert result['equationCount'] == 1
    assert '<mfrac>' in result['html']


def test_plain_document_works_without_pandoc(tmp_path, monkeypatch):
    monkeypatch.delenv('PANDOC_PATH', raising=False)
    monkeypatch.setattr(shutil, 'which', lambda _: None)
    document = Document()
    document.add_paragraph('Ordinary text')
    assert convert(document, tmp_path) == '<p>Ordinary text</p>\n'


def test_missing_converter_does_not_silently_drop_equations(tmp_path, monkeypatch):
    monkeypatch.delenv('PANDOC_PATH', raising=False)
    monkeypatch.setattr(shutil, 'which', lambda _: None)
    monkeypatch.setitem(sys.modules, 'pypandoc', None)
    document = Document()
    document.add_paragraph()._p.append(omml(FRACTION))
    with pytest.raises(EquationConversionError, match='Pandoc is not installed'):
        convert(document, tmp_path)


def test_bundled_pandoc_is_used_without_path_configuration(tmp_path, monkeypatch):
    monkeypatch.delenv('PANDOC_PATH', raising=False)
    monkeypatch.setattr(shutil, 'which', lambda _: None)
    document = Document()
    document.add_paragraph()._p.append(omml(FRACTION))
    assert '<mfrac>' in convert(document, tmp_path)


def test_api_reports_missing_dependency_as_503(monkeypatch):
    from fastapi import HTTPException, UploadFile
    from src.api.routes import convert_docx
    monkeypatch.delenv('PANDOC_PATH', raising=False)
    monkeypatch.setattr(shutil, 'which', lambda _: None)
    monkeypatch.setitem(sys.modules, 'pypandoc', None)
    document = Document()
    document.add_paragraph()._p.append(omml(FRACTION))
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    with pytest.raises(HTTPException) as error:
        asyncio.run(convert_docx(UploadFile(filename='math.docx', file=buffer)))
    assert error.value.status_code == 503
    assert 'Pandoc is not installed' in error.value.detail


def test_incomplete_conversion_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv('PANDOC_PATH', 'pandoc')
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(stdout=b'<p></p>'))
    document = Document()
    document.add_paragraph()._p.append(omml(FRACTION))
    with pytest.raises(EquationConversionError, match='found 1, converted 0'):
        convert(document, tmp_path)
