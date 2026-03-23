import os
import gdown
import numpy as np
import cv2
import asyncio

from insightface.app import FaceAnalysis
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ==============================
# 🔐 TOKEN
# ==============================
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ TOKEN no configurado")

# ==============================
# 📁 CONFIG
# ==============================
DRIVE_FOLDER_LINK = "https://drive.google.com/drive/folders/1eZw2CdmJLLn_zYh_ImNUQAOyjt1bdnv6"
LOCAL_FOLDER = "FOTOS"

# ==============================
# 📥 DESCARGA
# ==============================
if not os.path.exists(LOCAL_FOLDER):
    os.makedirs(LOCAL_FOLDER)
    print("📥 Descargando imágenes...")
    try:
        gdown.download_folder(DRIVE_FOLDER_LINK, output=LOCAL_FOLDER, quiet=True)
    except Exception as e:
        print("⚠️ Error descargando:", e)

# ==============================
# 🧠 MODELO
# ==============================
print("🧠 Cargando modelo facial...")
face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(ctx_id=0)

# ==============================
# 📊 BASE DE DATOS
# ==============================
face_db = []
face_embeddings = []

def load_faces():
    print("📸 Procesando base de rostros...")

    for file in os.listdir(LOCAL_FOLDER):
        path = os.path.join(LOCAL_FOLDER, file)

        try:
            img = cv2.imread(path)
            if img is None:
                continue

            faces = face_app.get(img)

            if faces:
                emb = faces[0].embedding
                face_db.append(path)
                face_embeddings.append(emb)

        except Exception as e:
            print("Error:", e)

    print(f"✅ {len(face_db)} rostros cargados")

# 🔥 CARGAR AL INICIO (CLAVE)
load_faces()

# ==============================
# 🔍 SIMILITUD
# ==============================
def find_similar(query_emb, threshold=0.6, top_k=3):
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

        file = await update.message.photo[-1].get_file()
        query_path = "query.jpg"
        await file.download_to_drive(query_path)

        img = cv2.imread(query_path)
        if img is None:
            await update.message.reply_text("⚠️ Error leyendo imagen")
            return

        faces = face_app.get(img)

        if not faces:
            await update.message.reply_text("❌ No se detectó rostro")
            return

        await update.message.reply_text("🔍 Buscando coincidencias...")

        query_emb = faces[0].embedding
        results = find_similar(query_emb)

        if not results:
            await update.message.reply_text("❌ Cara no encontrada")
            return

        await update.message.reply_text(f"✅ Encontré {len(results)} coincidencias")

        for img_path in results:
            try:
                with open(img_path, "rb") as f:
                    await update.message.reply_photo(photo=f)
            except Exception as e:
                print("Error enviando:", e)

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("⚠️ Error procesando imagen")

# ==============================
# 🚀 START
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot listo. Envíame una foto")

# ==============================
# 🚀 APP
# ==============================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

# ==============================
# 🚀 RUN (SIN asyncio.run)
# ==============================
print("🚀 PID:", os.getpid())
print("🤖 Bot corriendo...")

# limpiar webhook
asyncio.get_event_loop().run_until_complete(
    app.bot.delete_webhook(drop_pending_updates=True)
)

app.run_polling(drop_pending_updates=True)
