import os
import uuid
import convertapi
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks

convertapi.api_credentials = 'dEg7qeUnUyULsmtLkleecNWpnnBmnVnu'

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ConvertAPI Service is Running!"}

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
        contents = await file.read()
        with open(input_pdf_path, "wb") as f:
            f.write(contents)

        # التحويل عبر ConvertAPI مع حفظ الملف الناتج مباشرة
        result = convertapi.convert(
            'docx',
            {
                'File': input_pdf_path
            },
            from_format='pdf'
        )

        # حفظ الملف والتأكد من وجوده وحجمه
        saved_files = result.save_files(output_docx_path)
        
        # إذا حفظه كمسار مباشر أو داخل قائمة
        actual_path = saved_files[0] if isinstance(saved_files, list) else output_docx_path

        remove_file(input_pdf_path)
        background_tasks.add_task(remove_file, actual_path)

        original_name = os.path.splitext(file.filename or "document")[0]
        return FileResponse(
            path=actual_path,
            filename=f"{original_name}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        remove_file(input_pdf_path)
        remove_file(output_docx_path)
        raise HTTPException(status_code=500, detail=str(e))
