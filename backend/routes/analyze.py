from fastapi import APIRouter, UploadFile, File, HTTPException
from models.detector import detect_disease
from database.database import save_analysis
import uuid, time

router = APIRouter()

@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Recebe uma imagem da planta de guaraná e retorna o diagnóstico.

    Retorno:
    - status: "saudavel" | "praga_detectada"
    - disease: nome da praga (ou None)
    - confidence: porcentagem de confiança (0.0 a 1.0)
    - analysis_id: ID para consulta no histórico
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Formato de imagem inválido. Use JPG, PNG ou WEBP.")

    image_bytes = await file.read()

    try:
        result = detect_disease(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no modelo de IA: {str(e)}")

    analysis_id = str(uuid.uuid4())
    timestamp = int(time.time())

    save_analysis({
        "id": analysis_id,
        "timestamp": timestamp,
        "filename": file.filename,
        "status": result["status"],
        "disease": result["disease"],
        "confidence": result["confidence"],
    })

    return {
        "analysis_id": analysis_id,
        "timestamp": timestamp,
        **result
    }
 
