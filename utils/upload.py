import os
import docx2txt
import fitz  # PyMuPDF for PDFs

UPLOAD_FOLDER = "temp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text(file):
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    ext = os.path.splitext(file.filename)[1].lower()

    if ext == ".pdf":
        text = ""
        with fitz.open(filepath) as pdf:
            for page in pdf:
                text += page.get_text()
    elif ext == ".docx":
        text = docx2txt.process(filepath)
    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = ""

    return text
