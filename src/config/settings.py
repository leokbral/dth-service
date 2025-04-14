import os

class Settings:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'True') == 'True'
        self.api_prefix = os.getenv('API_PREFIX', '/api')
        self.docx_upload_path = os.getenv('DOCX_UPLOAD_PATH', './uploads')
        self.html_output_path = os.getenv('HTML_OUTPUT_PATH', './outputs')

settings = Settings()