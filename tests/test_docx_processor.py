import unittest
from src.core.docx_processor import DocxProcessor

class TestDocxProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = DocxProcessor()

    def test_process_docx_valid(self):
        # Assuming we have a valid .docx file for testing
        result = self.processor.process_docx('test_file.docx')
        self.assertIsInstance(result, str)  # Expecting HTML output
        self.assertIn('<html>', result)  # Check if HTML tags are present

    def test_process_docx_invalid(self):
        with self.assertRaises(Exception):
            self.processor.process_docx('invalid_file.docx')

if __name__ == '__main__':
    unittest.main()