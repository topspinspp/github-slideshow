import unittest
from unittest.mock import patch, mock_open
from app.deduplicator import utils

class TestUtilsFileParsing(unittest.TestCase):

    # Tests for parse_txt_file
    def test_parse_txt_file_success(self):
        mock_content = "This is a test text file.\nHello world."
        # Mock open function to return our mock_content
        with patch('builtins.open', mock_open(read_data=mock_content)) as mock_file:
            content = utils.parse_txt_file("dummy/path/to/file.txt")
            self.assertEqual(content, mock_content)
            mock_file.assert_called_once_with("dummy/path/to/file.txt", 'r', encoding='utf-8')

    def test_parse_txt_file_file_not_found(self):
        # Mock open to raise FileNotFoundError
        with patch('builtins.open', side_effect=FileNotFoundError) as mock_file:
            content = utils.parse_txt_file("dummy/path/nonexistent.txt")
            self.assertEqual(content, "Error: File not found.")
            mock_file.assert_called_once_with("dummy/path/nonexistent.txt", 'r', encoding='utf-8')

    def test_parse_txt_file_other_exception(self):
        # Mock open to raise a generic Exception
        with patch('builtins.open', side_effect=Exception("Test general error")) as mock_file:
            content = utils.parse_txt_file("dummy/path/error.txt")
            self.assertEqual(content, "Error parsing TXT file: Test general error")
            mock_file.assert_called_once_with("dummy/path/error.txt", 'r', encoding='utf-8')

    # Tests for parse_docx_file
    @patch('app.deduplicator.utils.docx.Document')
    def test_parse_docx_file_success(self, mock_docx_document):
        # Create mock paragraph objects
        mock_para1 = unittest.mock.Mock()
        mock_para1.text = "This is paragraph one."
        mock_para2 = unittest.mock.Mock()
        mock_para2.text = "This is paragraph two."

        mock_doc_instance = unittest.mock.Mock()
        mock_doc_instance.paragraphs = [mock_para1, mock_para2]
        mock_docx_document.return_value = mock_doc_instance

        content = utils.parse_docx_file("dummy/path/to/file.docx")
        expected_content = "This is paragraph one.\\nThis is paragraph two."
        self.assertEqual(content, expected_content)
        mock_docx_document.assert_called_once_with("dummy/path/to/file.docx")

    @patch('app.deduplicator.utils.docx.Document', side_effect=FileNotFoundError)
    def test_parse_docx_file_not_found(self, mock_docx_document):
        content = utils.parse_docx_file("dummy/path/nonexistent.docx")
        self.assertEqual(content, "Error: File not found.")
        mock_docx_document.assert_called_once_with("dummy/path/nonexistent.docx")

    @patch('app.deduplicator.utils.docx.Document', side_effect=Exception("DOCX specific error"))
    def test_parse_docx_file_other_exception(self, mock_docx_document):
        content = utils.parse_docx_file("dummy/path/error.docx")
        # The actual exception message from python-docx might be different or wrapped.
        # For this test, we check if our function catches the generic Exception.
        self.assertEqual(content, "Error parsing DOCX file: DOCX specific error")
        mock_docx_document.assert_called_once_with("dummy/path/error.docx")

    # Tests for parse_pdf_file
    @patch('app.deduplicator.utils.PyPDF2.PdfReader')
    @patch('builtins.open', new_callable=mock_open) # Mock open for file reading
    def test_parse_pdf_file_success(self, mock_file_open, mock_pdf_reader):
        # Mock page objects and their extract_text method
        mock_page1 = unittest.mock.Mock()
        mock_page1.extract_text.return_value = "PDF page 1 content. "
        mock_page2 = unittest.mock.Mock()
        mock_page2.extract_text.return_value = "PDF page 2 content."

        mock_reader_instance = unittest.mock.Mock()
        mock_reader_instance.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader_instance

        content = utils.parse_pdf_file("dummy/path/to/file.pdf")
        expected_content = "PDF page 1 content. PDF page 2 content."
        self.assertEqual(content, expected_content)
        mock_file_open.assert_called_once_with("dummy/path/to/file.pdf", 'rb')
        mock_pdf_reader.assert_called_once_with(mock_file_open.return_value)

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_parse_pdf_file_not_found(self, mock_file_open):
        # We don't even need to mock PdfReader if open fails first
        content = utils.parse_pdf_file("dummy/path/nonexistent.pdf")
        self.assertEqual(content, "Error: File not found.")
        mock_file_open.assert_called_once_with("dummy/path/nonexistent.pdf", 'rb')

    @patch('app.deduplicator.utils.PyPDF2.PdfReader', side_effect=Exception("PDF specific error"))
    @patch('builtins.open', new_callable=mock_open)
    def test_parse_pdf_file_other_exception(self, mock_file_open, mock_pdf_reader):
        content = utils.parse_pdf_file("dummy/path/error.pdf")
        self.assertEqual(content, "Error parsing PDF file: PDF specific error")
        mock_file_open.assert_called_once_with("dummy/path/error.pdf", 'rb')
        mock_pdf_reader.assert_called_once_with(mock_file_open.return_value)

    # Tests for the main parse_file function (dispatcher)
    @patch('app.deduplicator.utils.parse_txt_file')
    def test_parse_file_calls_txt_parser(self, mock_parse_txt):
        mock_parse_txt.return_value = "txt content"
        result = utils.parse_file("document.txt")
        self.assertEqual(result, "txt content")
        mock_parse_txt.assert_called_once_with("document.txt")

    @patch('app.deduplicator.utils.parse_docx_file')
    def test_parse_file_calls_docx_parser(self, mock_parse_docx):
        mock_parse_docx.return_value = "docx content"
        result = utils.parse_file("document.docx")
        self.assertEqual(result, "docx content")
        mock_parse_docx.assert_called_once_with("document.docx")

    @patch('app.deduplicator.utils.parse_pdf_file')
    def test_parse_file_calls_pdf_parser(self, mock_parse_pdf):
        mock_parse_pdf.return_value = "pdf content"
        result = utils.parse_file("document.pdf")
        self.assertEqual(result, "pdf content")
        mock_parse_pdf.assert_called_once_with("document.pdf")

    def test_parse_file_unsupported_extension(self):
        result = utils.parse_file("document.unsupported")
        self.assertEqual(result, "Error: Unsupported file type.")

    def test_parse_file_case_insensitivity_extension(self):
        with patch('app.deduplicator.utils.parse_txt_file') as mock_parse_txt:
            mock_parse_txt.return_value = "txt content upper"
            result = utils.parse_file("document.TXT")
            self.assertEqual(result, "txt content upper")
            mock_parse_txt.assert_called_once_with("document.TXT")

    def test_parse_file_no_extension(self):
        result = utils.parse_file("document_no_extension")
        self.assertEqual(result, "Error: Unsupported file type.")

    def test_parse_file_hidden_file_with_extension(self):
         with patch('app.deduplicator.utils.parse_txt_file') as mock_parse_txt:
            mock_parse_txt.return_value = "hidden txt content"
            result = utils.parse_file(".hidden_document.txt")
            self.assertEqual(result, "hidden txt content")
            mock_parse_txt.assert_called_once_with(".hidden_document.txt")

if __name__ == '__main__':
    unittest.main()
