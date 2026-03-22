import os
import gdown
import numpy as np
from PIL import Image
import face_recognition

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# 🔐 TOKEN desde Railway
TOKEN = os.getenv("TOKEN")

# 📁 CONFIG
DRIVE_FOLDER_LINK = "https://drive.google.com/drive/folders/1eZw2CdmJLLn_zYh_ImNUQAOyjt1bdnv6"
LOCAL_FOLDER = "FOTOS"

# 📥 DESCARGAR IMÁGENES (máx 50)
if not os.path.exists(LOCAL_FOLDER):
    os.makedirs(LOCAL_FOLDER)
    print("📥 Descargando imágenes...")
    try:
        gdown.download_folder(DRIVE_FOLDER_LINK, output=LOCAL_FOLDER, quiet=True)
    except Exception as e:
        print("⚠️ Error descargando:", e)

# 🧠 BASE DE DATOS DE ROSTROS
face_db = []
face_encodings = []

def load_images():
    print("🧠 Procesando rostros...")

    for file in os.listdir(LOCAL_FOLDER):
        path = os.path.join(LOCAL_FOLDER, file)

        try:
            img = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(img)

            if encodings:
                face_db.append(path)
                face_encodings.append(encodings[0])

        except Exception as e:
            print("Error cargando:", e)

load_images()
print(f"✅ {len(face_db)} rostros cargados")

# 🔍 BUSCAR SIMILARES
def find_similar_faces(query_encoding, top_k=5):
    if not face_encodings:
        return []

    distances = face_recognition.face_distance(face_encodings, query_encoding)
    indices = np.argsort(distances)[:top_k]
    return [face_db[i] for i in indices]

# 📩 HANDLER IMAGEN
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🔍 Buscando rostro...")

        file = await update.message.photo[-1].get_file()
        file_path = "query.jpg"
        await file.download_to_drive(file_path)

        img = face_recognition.load_image_file(file_path)
        encodings = face_recognition.face_encodings(img)

        if not encodings:
            await update.message.reply_text("❌ No se detectó ningún rostro")
            return

        query_encoding = encodings[0]
        results = find_similar_faces(query_encoding)

        print("RESULTADOS:", results)

        if not results:
            await update.message.reply_text("❌ No se encontraron coincidencias")
            return

        for img_path in results:
            try:
                size = os.path.getsize(img_path)

                with open(img_path, 'rb') as f:
                    if size > 10 * 1024 * 1024:
                        await update.message.reply_document(document=f)
                    else:
                        await update.message.reply_photo(photo=f)

            except Exception as e:
                print("Error enviando:", e)

    except Exception as e:
        print("ERROR GENERAL:", e)
        await update.message.reply_text("⚠️ Error procesando imagen")

# 🧪 TEST
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot con reconocimiento facial activo")

# 🚀 BOT
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

print("🤖 Bot con IA facial corriendo...")
app.run_polling()
