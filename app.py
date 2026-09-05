import os
import uuid
import convertapi
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTasks

# مفتاح الاعتماد
convertapi.api_credentials = 'c7t6OHCnY6CpkJYuqkz9qVkfn8hms8m9'

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

# 1. تحويل PDF إلى Word
@app.post("/convert-pdf-to-docx")
async def convert_pdf_to_docx(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    input_pdf_path = f"/tmp/{session_id}.pdf"
    output_docx_path = f"/tmp/{session_id}.docx"

    try:
        contents = await file.read()
        with open(input_pdf_path, "wb") as f:
            f.write(contents)

        result = convertapi.convert(
            'docx',
            {'File': input_pdf_path},
            from_format='pdf'
        )

        saved_files = result.save_files(output_docx_path)
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

# 2. تحويل Word إلى PDF
@app.post("/convert-docx-to-pdf")
async def convert_docx_to_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    input_docx_path = f"/tmp/{session_id}.docx"
    output_pdf_path = f"/tmp/{session_id}.pdf"

    try:
        contents = await file.read()
        with open(input_docx_path, "wb") as f:
            f.write(contents)

        result = convertapi.convert(
            'pdf',
            {'File': input_docx_path},
            from_format='docx'
        )

        saved_files = result.save_files(output_pdf_path)
        actual_path = saved_files[0] if isinstance(saved_files, list) else output_pdf_path

        remove_file(input_docx_path)
        background_tasks.add_task(remove_file, actual_path)

        original_name = os.path.splitext(file.filename or "document")[0]
        return FileResponse(
            path=actual_path,
            filename=f"{original_name}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        remove_file(input_docx_path)
        remove_file(output_pdf_path)
        raise HTTPException(status_code=500, detail=str(e))

# 3. دمج وتحويل الصور إلى ملف PDF
@app.post("/convert-images-to-pdf")
async def convert_images_to_pdf(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    session_id = str(uuid.uuid4())
    output_pdf_path = f"/tmp/{session_id}.pdf"
    temp_files = []

    try:
        for idx, file in enumerate(files):
            temp_path = f"/tmp/{session_id}_{idx}_{file.filename}"
            contents = await file.read()
            with open(temp_path, "wb") as f:
                f.write(contents)
            temp_files.append(temp_path)

        result = convertapi.convert(
            'pdf',
            {'Files': temp_files},
            from_format='images'
        )

        saved_files = result.save_files(output_pdf_path)
        actual_path = saved_files[0] if isinstance(saved_files, list) else output_pdf_path

        for p in temp_files:
            remove_file(p)

        background_tasks.add_task(remove_file, actual_path)

        return FileResponse(
            path=actual_path,
            filename=f"scanned_{session_id[:8]}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        for p in temp_files:
            remove_file(p)
        remove_file(output_pdf_path)
        raise HTTPException(status_code=500, detail=str(e))

# 4. التعرف الضوئي التلقائي واستخراج النصوص بأي لغة كانت من الصورة
@app.post("/extract-text-ocr")
async def extract_text_ocr(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "image.jpg")[1]
    input_img_path = f"/tmp/{session_id}{ext}"
    output_txt_path = f"/tmp/{session_id}.txt"

    try:
        contents = await file.read()
        with open(input_img_path, "wb") as f:
            f.write(contents)

        # استخراج النص بجميع اللغات عبر محرك ConvertAPI OCR
        result = convertapi.convert(
            'txt',
            {'File': input_img_path},
            from_format='images'
        )

        saved_files = result.save_files(output_txt_path)
        actual_path = saved_files[0] if isinstance(saved_files, list) else output_txt_path

        with open(actual_path, "r", encoding="utf-8", errors="ignore") as f:
            extracted_text = f.read()

        remove_file(input_img_path)
        background_tasks.add_task(remove_file, actual_path)

        return JSONResponse(content={"text": extracted_text.strip()})
    except Exception as e:
        remove_file(input_img_path)
        remove_file(output_txt_path)
        raise HTTPException(status_code=500, detail=str(e))
