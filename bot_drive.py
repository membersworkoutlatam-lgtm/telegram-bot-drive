import os
import gdown
import numpy as np
import cv2

from insightface.app import FaceAnalysis
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ==============================
# 🔐 TOKEN
# ==============================
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ TOKEN no configurado en Railway")

# ==============================
# 📁 CONFIG
# ==============================
DRIVE_FOLDER_LINK = "https://drive.google.com/drive/folders/1eZw2CdmJLLn_zYh_ImNUQAOyjt1bdnv6"
LOCAL_FOLDER = "FOTOS"

# ==============================
# 📥 DESCARGA IMÁGENES (1 VEZ)
# ==============================
if not os.path.exists(LOCAL_FOLDER):
    os.makedirs(LOCAL_FOLDER)
    print("📥 Descargando imágenes...")
    try:
        gdown.download_folder(DRIVE_FOLDER_LINK, output=LOCAL_FOLDER, quiet=True)
    except Exception as e:
        print("⚠️ Error descargando:", e)

# ==============================
# 🧠 IA (LAZY LOADING)
# ==============================
face_app = None

def get_face_app():
    global face_app
    if face_app is None:
        print("🧠 Cargando modelo facial (primera vez)...")
        face_app = FaceAnalysis(name="buffalo_l")
        face_app.prepare(ctx_id=0)
    return face_app

# ==============================
# 📊 BASE DE DATOS
# ==============================
face_db = []
face_embeddings = []
faces_loaded = False

def load_faces():
    global faces_loaded

    if faces_loaded:
        return

    print("📸 Procesando imágenes...")
    app_face = get_face_app()

    for file in os.listdir(LOCAL_FOLDER):
        path = os.path.join(LOCAL_FOLDER, file)

        try:
            img = cv2.imread(path)
            if img is None:
                continue

            faces = app_face.get(img)

            if faces:
                emb = faces[0].embedding
                face_db.append(path)
                face_embeddings.append(emb)

        except Exception as e:
            print("Error procesando:", e)

    print(f"✅ {len(face_db)} rostros cargados")
    faces_loaded = True

# ==============================
# 🔍 SIMILITUD
# ==============================
def find_similar(query_emb, threshold=0.6, top_k=5):
    results = []

    for i, emb in enumerate(face_embeddings):
        sim = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))

        if sim > threshold:
            results.append((face_db[i], sim))

    results = sorted(results, key=lambda x: x[1], reverse=True)

    return [r[0] for r in results[:top_k]]

# ==============================
# 📩 HANDLER
# ==============================
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🧠 Analizando rostro...")

        # 📥 descargar imagen
        file = await update.message.photo[-1].get_file()
        query_path = "query.jpg"
        await file.download_to_drive(query_path)

        img = cv2.imread(query_path)
        if img is None:
            await update.message.reply_text("⚠️ Error leyendo la imagen")
            return

        app_face = get_face_app()
        faces = app_face.get(img)

        # ❌ sin rostro
        if not faces:
            await update.message.reply_text("❌ No se detectó rostro")
            return

        # 📊 cargar base (solo 1 vez)
        load_faces()

        query_emb = faces[0].embedding
        results = find_similar(query_emb)

        # ❌ cara distinta
        if len(results) == 0:
            await update.message.reply_text("❌ Cara no encontrada")
            return

        # ✅ enviar resultados
        for img_path in results:
            try:
                size = os.path.getsize(img_path)

                with open(img_path, "rb") as f:
                    if size > 10 * 1024 * 1024:
                        await update.message.reply_document(document=f)
                    else:
                        await update.message.reply_photo(photo=f)

            except Exception as e:
                print("Error enviando:", e)

    except Exception as e:
        print("ERROR GENERAL:", e)
        await update.message.reply_text("⚠️ Error procesando imagen")

# ==============================
# 🚀 START
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de reconocimiento facial activo")

# ==============================
# 🚀 INICIO
# ==============================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

print("🤖 Bot corriendo correctamente...")
app.run_polling(drop_pending_updates=True)
