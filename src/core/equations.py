"""Convert native Word equations without changing DTH's document layout."""

from copy import deepcopy
from io import BytesIO
import os
import shutil
import subprocess

from docx import Document
from docx.oxml.ns import qn
from lxml import etree


class EquationConversionError(ValueError):
    pass


class PandocUnavailableError(EquationConversionError):
    pass


def resolve_pandoc():
    """Use an explicit/system installation, then the binary shipped with pip."""
    pandoc = os.environ.get("PANDOC_PATH") or shutil.which("pandoc")
    if pandoc:
        return pandoc
    try:
        import pypandoc
        return pypandoc.get_pandoc_path()
    except (ImportError, OSError) as error:
        raise PandocUnavailableError(
            "This document contains native equations, but Pandoc is not installed "
            "on the DTH server. Install the DTH requirements (pypandoc_binary), "
            "install Pandoc, or set PANDOC_PATH."
        ) from error


def convert_equations(document):
    """Batch OMML equations through Pandoc and map MathML to the original nodes.

    Only equations enter Pandoc; paragraphs, tables, images and references keep
    using DTH's existing converter. No subprocess is needed for ordinary files.
    """
    equations = [
        equation for equation in document.element.body.iter(qn("m:oMath"))
        if not any(parent.tag == qn("w:del") for parent in equation.iterancestors())
    ]
    if not equations:
        return {}

    pandoc = resolve_pandoc()

    math_document = Document()
    for equation in equations:
        math_document.add_paragraph()._p.append(deepcopy(equation))
    buffer = BytesIO()
    math_document.save(buffer)

    try:
        converted = subprocess.run(
            [pandoc, "--from=docx", "--to=html5", "--mathml", "--fail-if-warnings"],
            input=buffer.getvalue(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise EquationConversionError(
            "DTH could not convert the document's native equations. "
            "No equations were silently removed. Check the server's Pandoc installation "
            "and the equation format."
        ) from error

    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(b"<root>" + converted.stdout + b"</root>", parser)
        rendered = root.findall(".//{http://www.w3.org/1998/Math/MathML}math")
    except etree.XMLSyntaxError as error:
        raise EquationConversionError("Pandoc returned invalid equation markup.") from error

    if len(rendered) != len(equations):
        raise EquationConversionError(
            "DTH could not preserve every native equation: "
            f"found {len(equations)}, converted {len(rendered)}."
        )

    result = {}
    for original, math in zip(equations, rendered):
        is_display = any(parent.tag == qn("m:oMathPara") for parent in original.iterancestors())
        math.set("display", "block" if is_display else "inline")
        math.set("data-equation-source", "omml")
        result[original] = etree.tostring(math, encoding="unicode", with_tail=False)
    return result
