import os
from product_data import product_links, product_names, product_prices
import cv2
import numpy as np
import streamlit as st
import base64
from PIL import Image
import mediapipe as mp
import streamlit.components.v1 as components

st.set_page_config(page_title="🛍️ Walmart Virtual Try-On", layout="wide")

# ---- UI & Product Data ----
folder_map = {
    "Glasses": "assets/glasses",
    "Hats": "assets/hats"
}

# ---- UI Header ----
st.markdown("<h1 style='text-align:center;'>🛒 Walmart Virtual Try-On</h1>", unsafe_allow_html=True)
st.markdown("### 🕶️🧢Top Glasses and Hats On Sale @Walmart")
category = st.radio("Choose Category", ["Glasses", "Hats"], horizontal=True)
folder = folder_map[category]

# ---- Display Product Cards ----
products = []
for file in os.listdir(folder):
    if file.endswith(".png"):
        with open(os.path.join(folder, file), "rb") as img:
            data_url = base64.b64encode(img.read()).decode()
            image_src = f"data:image/png;base64,{data_url}"
        name = product_names.get(file, file.split(".")[0].title())
        price = product_prices.get(file, "NaN")
        buy_link = product_links[category].get(file, "#")
        products.append({
            "name": name,
            "filename": file,
            "price": price,
            "img": image_src,
            "buy": buy_link
        })

clicked_item = None
for i in range(0, len(products), 4):
    row = st.columns(4)
    for j, p in enumerate(products[i:i + 4]):
        with row[j]:
            st.markdown(f"<img src='{p['img']}' style='width:100%; border-radius:12px;'>",
                     unsafe_allow_html=True)
            st.markdown(f"**{p['name']}**")
            st.markdown(f"🛒 *{p['price']}*")
            if st.button("Try Now", key=f"try_{i + j}"):
                clicked_item = p['filename']
            st.markdown(f"[Buy on Walmart]({p['buy']})", unsafe_allow_html=True)

if clicked_item:
    st.session_state['selected_item'] = clicked_item

selected_item = st.session_state.get("selected_item", None)

# ---- Try-On with File Upload ----
if selected_item:
    st.subheader("📤 Upload your image for Virtual Try-On")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        image_path = os.path.join(folder, selected_item)
        try:
            overlay = Image.open(image_path).convert("RGBA")
            overlay = np.array(overlay)
            
        except:
            st.error("Couldn't load the selected item.")

        input_image = Image.open(uploaded_file).convert("RGB")
        frame = np.array(input_image)

        h, w, _ = frame.shape
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True)
        rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        result = face_mesh.process(rgb)

        if result.multi_face_landmarks:
            for face_landmarks in result.multi_face_landmarks:
                if category == "Glasses":
                    left = face_landmarks.landmark[33]
                    right = face_landmarks.landmark[263]
                    top = face_landmarks.landmark[168]
                else:
                    left = face_landmarks.landmark[234]
                    right = face_landmarks.landmark[454]
                    top = face_landmarks.landmark[10]

                x1, y1 = int(left.x * w), int(left.y * h)
                x2, y2 = int(right.x * w), int(right.y * h)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                dx, dy = x2 - x1, y2 - y1
                angle = np.degrees(np.arctan2(dy, dx))
                scale = int(((dx ** 2 + dy ** 2) ** 0.5) * 2.0)

                try:
                    resized = cv2.resize(overlay, (scale, int(overlay.shape[0] * scale / overlay.shape[1])))
                    M = cv2.getRotationMatrix2D((resized.shape[1] // 2, resized.shape[0] // 2), angle, 1.0)
                    rotated = cv2.warpAffine(resized, M, (resized.shape[1], resized.shape[0]),
                                             flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

                    if category == "Glasses":
                        x_offset = cx - rotated.shape[1] // 2
                        y_offset = cy - rotated.shape[0] // 2
                    else:
                        x_offset = cx - rotated.shape[1] // 2
                        y_offset = int(top.y * h) - int(rotated.shape[0] * 0.8)

                    for i in range(rotated.shape[0]):
                        for j in range(rotated.shape[1]):
                            if 0 <= y_offset + i < h and 0 <= x_offset + j < w:
                                alpha = rotated[i, j, 3] / 255.0
                                if alpha > 0:
                                    frame[y_offset + i, x_offset + j] = (
                                        (1 - alpha) * frame[y_offset + i, x_offset + j] + alpha * rotated[i, j, :3]
                                    )
                except Exception as e:
                    st.warning(f"Overlay Error: {e}")
        if isinstance(frame,np.ndarray):
            frame_rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            st.image(frame, caption="🧢 Try-On Result", use_container_width=True)
        else:
            st.warning("No face detected. Please upload a clearer image.")
