
import os, base64, uuid
from pathlib import Path
from flask import current_app
from PIL import Image
from io import BytesIO
from deepface import DeepFace

def save_dataurl_to_file(data_url: str, out_path: Path):
    # data_url like "data:image/png;base64,..."
    header, b64 = data_url.split(",", 1)
    binary = base64.b64decode(b64)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(binary)
    return str(out_path)

def verify_face(data_url: str, ref_image_path: str) -> bool:
    """Verify the captured face against the user's registered reference image using VGG-Face.
    Returns True if match with reasonable threshold, else False.
    """
    if not ref_image_path or not os.path.exists(ref_image_path):
        return False
    # Save temporary capture
    tmp_path = Path(current_app.root_path) / "static" / "uploads" / f"capture_{uuid.uuid4().hex}.png"
    save_dataurl_to_file(data_url, tmp_path)
    try:
        result = DeepFace.verify(img1_path=str(tmp_path), img2_path=str(ref_image_path), model_name="VGG-Face", enforce_detection=False)
        return bool(result.get("verified", False))
    except Exception as e:
        # Fallback to False on error
        current_app.logger.exception("DeepFace verification error: %s", e)
        return False
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
