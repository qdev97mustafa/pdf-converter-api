import os
import uuid
import convertapi
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks

# المفتاح الخاص بك تم دمجه هنا مباشرة
convertapi.api_credentials = 'dEg7qeUnUyULsmtLkleecNWpnnBmnVnu'

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Cloud PDF to Word Converter is Running!"}

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
        # قراءة محتوى الملف المرفوع وحفظه مؤقتاً
        contents = await file.read()
        with open(input_pdf_path, "wb") as f:
            f.write(contents)

        # تنفيذ التحويل السحابي مع دعم قراءة النصوص والصور (OCR)
        result = convertapi.convert(
            'docx',
            {
                'File': input_pdf_path,
                'EnableOcr': 'true'
            },
            from_format='pdf'
        )

        # حفظ الملف الناتج محلياً
        result.file.save(output_docx_path)

        # حذف الـ PDF الأصلي فوراً
        remove_file(input_pdf_path)

        # جدولة حذف ملف docx تلقائياً بعد إرساله للتطبيق لتوفير المساحة
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
