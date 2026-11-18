import base64
import logging
import warnings
from pathlib import Path

import cv2
import numpy as np
from django.conf import settings

warnings.filterwarnings("ignore", category=FutureWarning, module="insightface")

logger = logging.getLogger(__name__)

RASM_TURLARI = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
THRESHOLD = 0.45       # shundan past ball -> "Noma'lum"
MIN_DET_SCORE = 0.6    # shundan past ishonch bilan topilgan yuz tanilmaydi


class FaceRecognitionEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.app = None
        self.baza = {}
        self.ismlar = []
        self.matritsa = None
        self.papka = getattr(settings, "RASMLAR_PAPKASI", Path(settings.BASE_DIR) / "rasmlar")
        self._initialized = True

    def ensure_model_loaded(self):
        if self.app is None:
            from insightface.app import FaceAnalysis

            logger.info("InsightFace modeli (buffalo_l) yuklanmoqda...")
            self.app = FaceAnalysis(
                name="buffalo_l",
                allowed_modules=["detection", "recognition"],
                providers=["CPUExecutionProvider"],
            )
            self.app.prepare(ctx_id=-1, det_size=(640, 640))
            logger.info("InsightFace modeli tayyor.")

    def rasm_ekanmi(self, p: Path) -> bool:
        return p.is_file() and not p.name.startswith(".") and p.suffix.lower() in RASM_TURLARI

    def get_embedding(self, path):
        self.ensure_model_loaded()
        img = cv2.imread(str(path))
        if img is None:
            logger.warning(f"[!] O'qib bo'lmadi: {path}")
            return None

        faces = self.app.get(img)
        if not faces:
            logger.warning(f"[!] Yuz topilmadi: {path}")
            return None

        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        return face.normed_embedding

    def rasmlarni_yigish(self, papka=None):
        papka = Path(papka or self.papka)
        if not papka.is_dir():
            papka.mkdir(parents=True, exist_ok=True)
            return {}

        natija = {}
        for item in sorted(papka.iterdir()):
            if item.name.startswith("."):
                continue
            if item.is_dir():
                rasmlar = [p for p in sorted(item.iterdir()) if self.rasm_ekanmi(p)]
                if rasmlar:
                    natija[item.name] = rasmlar
            elif self.rasm_ekanmi(item):
                natija.setdefault(item.stem, []).append(item)
        return natija

    def reload_database(self, papka=None):
        """rasmlar papkasidan barcha yuz embedding'larini yig'adi va xotiraga yuklaydi."""
        self.ensure_model_loaded()
        target_dir = Path(papka or self.papka)
        to_process = self.rasmlarni_yigish(target_dir)

        baza = {}
        for ism, rasmlar in to_process.items():
            embs = [e for e in (self.get_embedding(p) for p in rasmlar) if e is not None]
            if not embs:
                logger.warning(f"[!] {ism}: birorta ham yaroqli rasm yo'q")
                continue
            ortacha = np.mean(embs, axis=0)
            baza[ism] = ortacha / np.linalg.norm(ortacha)
            logger.info(f"[+] {ism}: {len(embs)}/{len(rasmlar)} ta rasm qabul qilindi")

        self.baza = baza
        self.ismlar = list(baza.keys())
        if self.ismlar:
            self.matritsa = np.stack([baza[i] for i in self.ismlar])
        else:
            self.matritsa = None

        return self.ismlar

    def ensure_database_loaded(self):
        if self.matritsa is None:
            self.reload_database()

    def tanish(self, emb):
        """emb ni bazadagi hamma odam bilan bir yo'la solishtiradi."""
        self.ensure_database_loaded()
        if not self.ismlar or self.matritsa is None:
            return "Noma'lum", 0.0, False

        ballar = self.matritsa @ emb
        i = int(np.argmax(ballar))
        ball = float(ballar[i])

        if ball < THRESHOLD:
            return "Noma'lum", ball, False
        return self.ismlar[i], ball, True

    def process_frame(self, frame):
        """
        Kamera kadrini tahlil qiladi.
        Qaytaradi:
          {
            "faces_count": N,
            "results": [
                {
                   "bbox": [x1, y1, x2, y2],
                   "det_score": float,
                   "status": "recognized" | "unknown" | "low_quality",
                   "name": "...",
                   "score": float,
                   "recognized": bool,
                   "message": "..."
                }
            ]
          }
        """
        self.ensure_model_loaded()
        self.ensure_database_loaded()

        faces = self.app.get(frame)
        if not faces:
            return {
                "faces_count": 0,
                "results": [],
                "message": "Kadrda yuz topilmadi",
            }

        results = []
        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int).tolist()
            det_score = float(face.det_score)

            if det_score < MIN_DET_SCORE:
                results.append({
                    "bbox": [x1, y1, x2, y2],
                    "det_score": round(det_score, 2),
                    "status": "low_quality",
                    "name": "...",
                    "score": 0.0,
                    "recognized": False,
                    "message": "Yuz sifati past",
                })
            else:
                ism, ball, recognized = self.tanish(face.normed_embedding)
                status = "recognized" if recognized else "unknown"
                msg = f"{ism} ({round(ball * 100)}%)" if recognized else "Bazada topilmadi"
                results.append({
                    "bbox": [x1, y1, x2, y2],
                    "det_score": round(det_score, 2),
                    "status": status,
                    "name": ism,
                    "score": round(ball, 2),
                    "recognized": recognized,
                    "message": msg,
                })

        return {
            "faces_count": len(faces),
            "results": results,
            "message": f"{len(faces)} ta yuz aniqlandi",
        }

    def process_base64_image(self, base64_data: str):
        """Brauzerdan kelgan base64 tasvirni qabul qilib tekshiradi."""
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]

        image_bytes = base64.b64decode(base64_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {
                "faces_count": 0,
                "results": [],
                "message": "Rasmni o'qib bo'lmadi",
            }

        return self.process_frame(frame)


# Yagona engine obyekti
face_engine = FaceRecognitionEngine()

