from datetime import date

from src.parsers.html_parser import HTMLParser
from src.parsers.pdf_parser import PDFParser

def test_html_metadata_extraction():
    """Testa se o parser de HTML consegue extrair os metadados (edição e data)"""
    html_mock = "<html><body><div class='edi-p-id-data'>Edição n° 1234 - 10/05/2026</div></body></html>"
    metadados = HTMLParser.parse_metadata(html_mock)
    
    assert metadados.numero == 1234
    assert metadados.data_publicacao == date(2026, 5, 10)

def test_html_text_extraction():
    """Testa se a extração de texto do HTML remove espaçamentos e HTML tags adequadamente"""
    html_mock = b"<html><body><p>   Texto com    multiplos espacos  \n</p><br/><div>Novo paragrafo</div></body></html>"
    text = HTMLParser.extract_text(html_mock)
    
    assert "Texto com multiplos espacos Novo paragrafo" in text

def test_pdf_extraction_empty():
    """Testa se o parser lida corretamente com PDFs vazios ou inválidos para não quebrar o pipeline"""
    text = PDFParser.extract_text(b"")
    assert text == ""
