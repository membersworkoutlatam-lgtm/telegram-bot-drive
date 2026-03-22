import os
import gdown
import torch
import clip
import numpy as np
from PIL import Image

DRIVE_LINK = "https://drive.google.com/drive/folders/1eZw2CdmJLLn_zYh_ImNUQAOyjt1bdnv6"
LOCAL_FOLDER = "FOTOS"

# 📥 Descargar desde Drive
if not os.path.exists(LOCAL_FOLDER):
    os.makedirs(LOCAL_FOLDER)
    print("📥 Descargando desde Drive...")
    gdown.download_folder(DRIVE_LINK, output=LOCAL_FOLDER, quiet=False)

# 🧠 Cargar modelo
model, preprocess = clip.load("ViT-B/32")

image_paths = []
vectors = []

print("🧠 Generando vectores...")

for file in os.listdir(LOCAL_FOLDER):
    path = os.path.join(LOCAL_FOLDER, file)
    try:
        image = preprocess(Image.open(path)).unsqueeze(0)
        with torch.no_grad():
            vector = model.encode_image(image)
        vector = vector / vector.norm()

        image_paths.append(path)
        vectors.append(vector.numpy())
    except:
        continue

np.save("vectors.npy", vectors)
np.save("paths.npy", image_paths)

print(f"✅ {len(image_paths)} vectores generados")
