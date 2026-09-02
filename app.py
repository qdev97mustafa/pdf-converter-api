import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks
from pdf2docx import Converter

app = FastAPI()

@app.get("/")
def home():
    return {"status": "PDF to Word Converter API is Running on Render!"}

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

@app.post("/convert-pdf-to-docx")
async def convert_pdf_to_docx(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # استخدام UUID فريد لمنع تداخل الملفات وضمان الامتداد الصحيح
    session_id = str(uuid.uuid4())
    input_pdf_path = f"temp_{session_id}.pdf"
    output_docx_path = f"temp_{session_id}.docx"

    try:
        # قراءة المحتوى وحفظ ملف الـ PDF المؤقت
        contents = await file.read()
        with open(input_pdf_path, "wb") as f:
            f.write(contents)

        # التحويل عبر pdf2docx
        cv = Converter(input_pdf_path)
        cv.convert(output_docx_path, start=0, end=None)
        cv.close()

        # التحقق من أن ملف docx تم إنشاؤه وله حجم حقيقي
        if not os.path.exists(output_docx_path) or os.path.getsize(output_docx_path) == 0:
            raise HTTPException(status_code=400, detail="Conversion resulted in an empty or corrupt file.")

        # حذف ملف الـ PDF الأصلي فوراً
        remove_file(input_pdf_path)

        # جدولة حذف ملف الـ docx بعد إرساله للعميل حتى لا يمتلئ السيرفر
        background_tasks.add_task(remove_file, output_docx_path)

        # إرجاع الملف بترميز ثنائي رسمي
        return FileResponse(
            path=output_docx_path,
            filename=f"{os.path.splitext(file.filename or 'document')[0]}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        remove_file(input_pdf_path)
        remove_file(output_docx_path)
        # إرجاع كود 500 حقيقي حتى يفهم تطبيق الهاتف أن هناك خطأ ولا يقوم بحفظ نصوص الخطأ
        raise HTTPException(status_code=500, detail=str(e))
