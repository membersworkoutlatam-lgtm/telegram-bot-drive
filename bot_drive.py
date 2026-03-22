import os
import gdown
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

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

# 🧠 MODELO CLIP
print("🧠 Cargando modelo IA...")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 📊 BASE DE DATOS
image_db = []
image_embeddings = []

def load_images():
    print("📸 Generando embeddings...")

    for file in os.listdir(LOCAL_FOLDER):
        path = os.path.join(LOCAL_FOLDER, file)

        try:
            image = Image.open(path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")

            with torch.no_grad():
                embedding = model.get_image_features(**inputs)

            embedding = embedding / embedding.norm(p=2)
            image_db.append(path)
            image_embeddings.append(embedding.numpy()[0])

        except Exception as e:
            print("Error:", e)

    print(f"✅ {len(image_db)} imágenes procesadas")

load_images()

# 🔍 SIMILITUD
def find_similar(query_embedding, top_k=5):
    sims = []

    for emb in image_embeddings:
        sim = np.dot(query_embedding, emb)
        sims.append(sim)

    indices = np.argsort(sims)[::-1][:top_k]

    return [image_db[i] for i in indices]

# 📩 HANDLER
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🧠 Analizando imagen con IA...")

        file = await update.message.photo[-1].get_file()
        file_path = "query.jpg"
        await file.download_to_drive(file_path)

        image = Image.open(file_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")

        with torch.no_grad():
            embedding = model.get_image_features(**inputs)

        embedding = embedding / embedding.norm(p=2)
        query_embedding = embedding.numpy()[0]

        results = find_similar(query_embedding)

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
        print("ERROR:", e)
        await update.message.reply_text("⚠️ Error procesando imagen")

# 🧪 TEST
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot con IA avanzada activo")

# 🚀 BOT
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

print("🤖 Bot IA PRO corriendo...")
app.run_polling()
