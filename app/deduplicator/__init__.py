# This file makes 'deduplicator' a Python sub-package
from .core import find_exact_duplicates, remove_exact_duplicates, find_near_duplicates
from .utils import parse_file, parse_txt_file, parse_docx_file, parse_pdf_file
