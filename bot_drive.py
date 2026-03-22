import os
import gdown
from PIL import Image
import imagehash
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("8239387987:AAEbCTSNK3OQDglN5zz3fIJZY1b-G4Koxh4")
DRIVE_FOLDER_LINK = "https://drive.google.com/drive/folders/1eZw2CdmJLLn_zYh_ImNUQAOyjt1bdnv6"
LOCAL_FOLDER = "FOTOS"

# Descargar imágenes
if not os.path.exists(LOCAL_FOLDER):
    os.makedirs(LOCAL_FOLDER)
    gdown.download_folder(DRIVE_FOLDER_LINK, output=LOCAL_FOLDER, quiet=False, use_cookies=False)

# Cargar hashes
image_db = []
image_hashes = []

def load_images():
    for file in os.listdir(LOCAL_FOLDER):
        path = os.path.join(LOCAL_FOLDER, file)
        try:
            img = Image.open(path)
            h = imagehash.phash(img)
            image_db.append(path)
            image_hashes.append(h)
        except:
            continue

load_images()

def find_similar(query_hash, top_k=5):
    sims = []
    for h in image_hashes:
        sims.append(query_hash - h)  # menor = más similar
    indices = np.argsort(sims)[:top_k]
    return [image_db[i] for i in indices]

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Buscando imágenes similares...")

    file = await update.message.photo[-1].get_file()
    file_path = "query.jpg"
    await file.download_to_drive(file_path)

    query_img = Image.open(file_path)
    query_hash = imagehash.phash(query_img)

    results = find_similar(query_hash)

    for img_path in results:
        await update.message.reply_photo(photo=open(img_path, 'rb'))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

print("🤖 Bot liviano corriendo...")
app.run_polling()
