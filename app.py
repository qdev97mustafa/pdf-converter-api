import os
import uuid
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks

SECRET = "dEg7qeUnUyULsmtLkleecNWpnnBmnVnu"

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Direct HTTP ConvertAPI is running"}

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

@app.post("/convert-pdf-to-docx")
async def convert_pdf_to_docx(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    output_docx_path = f"/tmp/{session_id}.docx"

    try:
        file_bytes = await file.read()

        # إرسال الملف مباشرة لـ ConvertAPI عبر REST API الرسمي
        response = requests.post(
            "https://v2.convertapi.com/convert/pdf/to/docx",
            headers={"Authorization": f"Bearer {SECRET}"},
            files={"File": (file.filename or "input.pdf", file_bytes, "application/pdf")},
            params={"StoreFile": "false"}  # لإرجاع بايتات الملف فوراً في الرد
        )

        data = response.json()
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=str(data))

        # استخراج بيانات الملف وتنزيلها
        file_info = data["Files"][0]
        
        if "FileData" in file_info:
            import base64
            with open(output_docx_path, "wb") as f:
                f.write(base64.b64decode(file_info["FileData"]))
        elif "Url" in file_info:
            download_res = requests.get(file_info["Url"])
            with open(output_docx_path, "wb") as f:
                f.write(download_res.content)
        else:
            raise HTTPException(status_code=500, detail="No file data found in response")

        background_tasks.add_task(remove_file, output_docx_path)

        original_name = os.path.splitext(file.filename or "document")[0]
        return FileResponse(
            path=output_docx_path,
            filename=f"{original_name}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        remove_file(output_docx_path)
        raise HTTPException(status_code=500, detail=str(e))
