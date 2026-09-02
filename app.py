import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from pdf2docx import Converter

app = FastAPI()

@app.get("/")
def home():
    return {"status": "PDF to Word Converter API is Running on Render!"}

@app.post("/convert-pdf-to-docx")
async def convert_pdf_to_docx(file: UploadFile = File(...)):
    input_pdf_path = f"temp_{file.filename}"
    output_docx_path = input_pdf_path.replace(".pdf", ".docx")
    
    try:
        # قراءة محتوى الملف وضمان كتابته بالكامل
        contents = await file.read()
        with open(input_pdf_path, "wb") as f:
            f.write(contents)
            
        # التحويل
        cv = Converter(input_pdf_path)
        cv.convert(output_docx_path, start=0, end=None)
        cv.close()
        
        if not os.path.exists(output_docx_path) or os.path.getsize(output_docx_path) == 0:
            return {"error": "Conversion resulted in an empty file."}

    except Exception as e:
        return {"error": str(e)}
        
    finally:
        if os.path.exists(input_pdf_path):
            os.remove(input_pdf_path)
            
    return FileResponse(
        path=output_docx_path,
        filename=os.path.basename(output_docx_path),
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
