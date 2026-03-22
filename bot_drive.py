import os
import gdown
from deepface import DeepFace

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# 🔐 TOKEN
TOKEN = os.getenv("TOKEN")

# 📁 CONFIG
DRIVE_FOLDER_LINK = "https://drive.google.com/drive/folders/1eZw2CdmJLLn_zYh_ImNUQAOyjt1bdnv6"
LOCAL_FOLDER = "FOTOS"

# 📥 DESCARGA
if not os.path.exists(LOCAL_FOLDER):
    os.makedirs(LOCAL_FOLDER)
    print("📥 Descargando imágenes...")
    try:
        gdown.download_folder(DRIVE_FOLDER_LINK, output=LOCAL_FOLDER, quiet=True)
    except Exception as e:
        print("Error descarga:", e)

# 📩 HANDLER
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🧠 Buscando rostro real...")

        file = await update.message.photo[-1].get_file()
        query_path = "query.jpg"
        await file.download_to_drive(query_path)

        matches = []

        for img_name in os.listdir(LOCAL_FOLDER):
            img_path = os.path.join(LOCAL_FOLDER, img_name)

            try:
                result = DeepFace.verify(
                    img1_path=query_path,
                    img2_path=img_path,
                    enforce_detection=False
                )

                if result["verified"]:
                    matches.append(img_path)

            except Exception as e:
                print("Error comparando:", e)

        if not matches:
            await update.message.reply_text("❌ No se encontró la misma persona")
            return

        # enviar coincidencias
        for img_path in matches[:5]:
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
        print("ERROR:", e)
        await update.message.reply_text("⚠️ Error procesando imagen")

# 🧪 TEST
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot de reconocimiento facial real activo")

# 🚀 BOT
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

print("🤖 Bot DeepFace corriendo...")
app.run_polling()
