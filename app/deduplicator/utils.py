import docx
import PyPDF2

def parse_txt_file(file_path: str) -> str:
    """
    Parses a .txt file and returns its content.

    Args:
        file_path: The path to the .txt file.

    Returns:
        The content of the file as a string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error parsing TXT file: {e}"

def parse_docx_file(file_path: str) -> str:
    """
    Parses a .docx file and returns its text content.

    Args:
        file_path: The path to the .docx file.

    Returns:
        The text content of the file as a string.
    """
    try:
        # import docx # Moved to top
        doc = docx.Document(file_path)
        return "\\n".join([paragraph.text for paragraph in doc.paragraphs])
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error parsing DOCX file: {e}"

def parse_pdf_file(file_path: str) -> str:
    """
    Parses a .pdf file and returns its text content.

    Args:
        file_path: The path to the .pdf file.

    Returns:
        The text content of the file as a string.
    """
    try:
        # import PyPDF2 # Moved to top
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text()
        return text
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error parsing PDF file: {e}"

def parse_file(file_path: str) -> str:
    """
    Parses a file based on its extension and returns its text content.

    Args:
        file_path: The path to the file.

    Returns:
        The text content of the file as a string, or an error message
        if the file type is not supported or an error occurs.
    """
    file_extension = file_path.split('.')[-1].lower()
    if file_extension == 'txt':
        return parse_txt_file(file_path)
    elif file_extension == 'docx':
        return parse_docx_file(file_path)
    elif file_extension == 'pdf':
        return parse_pdf_file(file_path)
    else:
        return "Error: Unsupported file type."
