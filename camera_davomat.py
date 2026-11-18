"""
Kamerada ko'ringan odamni `rasmlar` papkasidagi baza bilan solishtirib taniydi.

Ishlash tartibi:
  1. Dastur boshida `rasmlar` papkasidagi har bir odamning embedding'i yig'iladi
  2. Kameradan har bir kadrda yuzlar topiladi va embedding'i olinadi
  3. Embedding bazadagi hamma odam bilan bir yo'la solishtiriladi
  4. Eng yuqori ball THRESHOLD dan baland bo'lsa ism yoziladi, aks holda "Noma'lum"

Ranglar:  yashil - tanildi,  qizil - noma'lum,  kulrang - yuz sifati past
Chiqish:  q
"""

import time
import warnings
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis

warnings.filterwarnings("ignore", category=FutureWarning, module="insightface")


# ---------------- Sozlamalar ----------------
RASMLAR_PAPKASI = Path(__file__).resolve().parent / "rasmlar"
THRESHOLD = 0.45       # shundan past ball -> "Noma'lum"
MIN_DET_SCORE = 0.6    # shundan past ishonch bilan topilgan yuz tanilmaydi
KAMERA_INDEX = 0
RASM_TURLARI = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SHRIFT = cv2.FONT_HERSHEY_SIMPLEX

app = FaceAnalysis(
    name="buffalo_l",
    allowed_modules=["detection", "recognition"],
    providers=["CPUExecutionProvider"],
)
app.prepare(ctx_id=-1, det_size=(640, 640))


# ---------------- 1-qism: bazani yig'ish ----------------
def get_embedding(path):
    img = cv2.imread(str(path))
    if img is None:
        print(f"[!] O'qib bo'lmadi: {path}")
        return None
    faces = app.get(img)
    if not faces:
        print(f"[!] Yuz topilmadi: {path}")
        return None
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    return face.normed_embedding


def rasm_ekanmi(p: Path) -> bool:
    return p.is_file() and not p.name.startswith(".") and p.suffix.lower() in RASM_TURLARI


def rasmlarni_yigish(papka):
    papka = Path(papka)
    if not papka.is_dir():
        papka.mkdir(parents=True, exist_ok=True)
        return {}
    natija = {}
    for item in sorted(papka.iterdir()):
        if item.name.startswith("."):
            continue
        if item.is_dir():
            rasmlar = [p for p in sorted(item.iterdir()) if rasm_ekanmi(p)]
            if rasmlar:
                natija[item.name] = rasmlar
        elif rasm_ekanmi(item):
            natija.setdefault(item.stem, []).append(item)
    return natija


def bazani_yuklash(papka):
    baza = {}
    for ism, rasmlar in rasmlarni_yigish(papka).items():
        embs = [e for e in (get_embedding(p) for p in rasmlar) if e is not None]
        if not embs:
            print(f"[!] {ism}: birorta ham yaroqli rasm yo'q")
            continue
        ortacha = np.mean(embs, axis=0)
        baza[ism] = ortacha / np.linalg.norm(ortacha)
        print(f"[+] {ism}: {len(embs)}/{len(rasmlar)} ta rasm qabul qilindi")
    return baza


# ---------------- 2-qism: tanish ----------------
def tanish(emb, ismlar, matritsa):
    """emb ni bazadagi hamma odam bilan bir yo'la solishtiradi."""
    ballar = matritsa @ emb
    i = int(np.argmax(ballar))
    ball = float(ballar[i])
    if ball < THRESHOLD:
        return "Noma'lum", ball
    return ismlar[i], ball


def yozuv_chizish(frame, matn, x, y, rang):
    """Ramka ustiga rangli fon bilan yozuv."""
    (w, h), _ = cv2.getTextSize(matn, SHRIFT, 0.7, 2)
    cv2.rectangle(frame, (x, y - h - 10), (x + w + 6, y), rang, -1)
    cv2.putText(frame, matn, (x + 3, y - 6), SHRIFT, 0.7, (255, 255, 255), 2)


# ---------------- 3-qism: kamera ----------------
def main():
    print(f"Baza yuklanmoqda ({RASMLAR_PAPKASI})...")
    baza = bazani_yuklash(RASMLAR_PAPKASI)
    if not baza:
        print("[!] Baza bo'sh: 'rasmlar' papkasiga odamlar rasmini qo'ying.")
        return

    ismlar = list(baza)
    matritsa = np.stack([baza[i] for i in ismlar])
    print(f"\nBazada {len(ismlar)} kishi: {ismlar}\nKamera ochilmoqda... (chiqish: q)\n")

    cap = cv2.VideoCapture(KAMERA_INDEX)
    if not cap.isOpened():
        print("[X] Kamera ochilmadi: kamera ruxsatini yoki ulanishini tekshiring")
        return

    korilganlar = set()
    oldingi_vaqt = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Kadr o'qilmadi")
            break

        frame = cv2.flip(frame, 1)
        faces = app.get(frame)

        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)

            if face.det_score < MIN_DET_SCORE:
                rang, matn = (128, 128, 128), "..."
            else:
                ism, ball = tanish(face.normed_embedding, ismlar, matritsa)
                matn = f"{ism} {ball:.2f}"
                if ism == "Noma'lum":
                    rang = (0, 0, 255)
                else:
                    rang = (0, 170, 0)
                    if ism not in korilganlar:
                        korilganlar.add(ism)
                        print(f"[OK] {ism} tanildi (ball: {ball:.2f}) - {time.strftime('%H:%M:%S')}")

            cv2.rectangle(frame, (x1, y1), (x2, y2), rang, 2)
            yozuv_chizish(frame, matn, x1, y1, rang)

        hozir = time.time()
        fps = 1 / max(hozir - oldingi_vaqt, 1e-6)
        oldingi_vaqt = hozir
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), SHRIFT, 0.8, (0, 255, 255), 2)

        cv2.imshow("Davomat - Yuzni tanish  (q - chiqish)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
