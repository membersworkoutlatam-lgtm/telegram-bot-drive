import os
import gdown
import torch
import clip
import numpy as np
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# =========================
# 🔐 CONFIGURACIÓN
# =========================
TOKEN = "8239387987:AAEbCTSNK3OQDglN5zz3fIJZY1b-G4Koxh4"
DRIVE_FOLDER_LINK = "https://drive.google.com/drive/folders/1eZw2CdmJLLn_zYh_ImNUQAOyjt1bdnv6"
LOCAL_FOLDER = "imagenes_drive"

# =========================
# 📥 DESCARGAR IMÁGENES
# =========================
if not os.path.exists(LOCAL_FOLDER):
    os.makedirs(LOCAL_FOLDER)
    print("📥 Descargando imágenes desde Google Drive...")
    gdown.download_folder(DRIVE_FOLDER_LINK, output=LOCAL_FOLDER, quiet=False, use_cookies=False)

# =========================
# 🧠 MODELO CLIP
# =========================
print("🧠 Cargando modelo IA...")
model, preprocess = clip.load("ViT-B/32")

image_db = []
image_vectors = []

def load_images():
    print("📸 Procesando imágenes...")
    for file in os.listdir(LOCAL_FOLDER):
        path = os.path.join(LOCAL_FOLDER, file)
        try:
            image = preprocess(Image.open(path)).unsqueeze(0)
            with torch.no_grad():
                vector = model.encode_image(image)
            image_db.append(path)
            image_vectors.append(vector / vector.norm())
        except:
            continue

load_images()
print(f"✅ {len(image_db)} imágenes cargadas")

# =========================
# 🔍 BUSCAR SIMILARES
# =========================
def find_similar(query_vector, top_k=5):
    sims = []
    for vec in image_vectors:
        sim = (query_vector @ vec.T).item()
        sims.append(sim)
    indices = np.argsort(sims)[-top_k:][::-1]
    return [image_db[i] for i in indices]

# =========================
# 📩 TELEGRAM HANDLER
# =========================
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Buscando imágenes similares...")

    file = await update.message.photo[-1].get_file()
    file_path = "query.jpg"
    await file.download_to_drive(file_path)

    image = preprocess(Image.open(file_path)).unsqueeze(0)
    with torch.no_grad():
        query_vector = model.encode_image(image)
    query_vector = query_vector / query_vector.norm()

    results = find_similar(query_vector)

    for img_path in results:
        await update.message.reply_photo(photo=open(img_path, 'rb'))

# =========================
# 🚀 INICIAR BOT
# =========================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

print("🤖 Bot corriendo...")
app.run_polling()
