# dth-service README.md

# DTH Service

This project is a Python-based service designed to process `.docx` files and convert them into HTML format. It serves as a backend service for the Sciledger application, handling document processing requests.

## Project Structure

```
dth-service
├── src
│   ├── api
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── handlers.py
│   ├── core
│   │   ├── __init__.py
│   │   └── docx_processor.py
│   ├── config
│   │   ├── __init__.py
│   │   └── settings.py
│   └── main.py
├── tests
│   ├── __init__.py
│   └── test_docx_processor.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd dth-service
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   uvicorn src.main:app --reload
   ```

## Usage

The DTH Service exposes an API that can be accessed by the Sciledger application. It accepts `.docx` files and returns the processed HTML output.

## Testing

To run the tests, use the following command:

```bash
pytest tests
```

## Docker

To build and run the application in a Docker container, use the following commands:

```bash
docker build -t dth-service .
docker run -p 8000:8000 dth-service
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.