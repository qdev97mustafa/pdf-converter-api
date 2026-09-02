import os
import uuid
import subprocess
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks

app = FastAPI()

@app.get("/")
def home():
    return {"status": "LibreOffice PDF to Word Converter is Running!"}

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

@app.post("/convert-pdf-to-docx")
async def convert_pdf_to_docx(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    input_pdf_path = f"/tmp/{session_id}.pdf"
    output_docx_path = f"/tmp/{session_id}.docx"

    try:
        # حفظ ملف الـ PDF مؤقتاً
        contents = await file.read()
        with open(input_pdf_path, "wb") as f:
            f.write(contents)

        # استدعاء محرك LibreOffice للتحويل المباشر
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            "/tmp",
            input_pdf_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)

        # التحقق من نجاح العملية ووجود الملف الناتج
        if not os.path.exists(output_docx_path) or os.path.getsize(output_docx_path) == 0:
            raise HTTPException(status_code=500, detail=f"Conversion failed: {result.stderr.decode()}")

        # تنظيف الـ PDF الأصلي
        remove_file(input_pdf_path)

        # جدولة حذف ملف الـ docx بعد تحميله
        background_tasks.add_task(remove_file, output_docx_path)

        original_name = os.path.splitext(file.filename or "document")[0]
        return FileResponse(
            path=output_docx_path,
            filename=f"{original_name}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        remove_file(input_pdf_path)
        remove_file(output_docx_path)
        raise HTTPException(status_code=500, detail=str(e))
