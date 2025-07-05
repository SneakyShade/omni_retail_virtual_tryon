import os
from product_data import product_links, product_names, product_prices
import cv2
import numpy as np
import streamlit as st
import base64
from PIL import Image
import mediapipe as mp

st.set_page_config(page_title="🛍️ Walmart Virtual Try-On", layout="wide")
st.markdown("""
    <style>
    .stButton > button {
        background-color: #007bff;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 8px 16px;
        margin-top: 10px;
        cursor: pointer;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

# ---- UI & Product Data ----
folder_map = {
    "Glasses": "assets/glasses",
    "Hats": "assets/hats"
}

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
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color:#ffffff; padding:15px; border-radius:10px; 
                                box-shadow: 2px 2px 6px rgba(0,0,0,0.1); text-align:center">
                        <img src="{p['img']}" style="width:100%; border-radius:8px;" />
                        <h4 style="margin:10px 0; color:black;">{p['name']}</h4>
                        <p style="color:black;">🛒 {p['price']}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button("Try Now", key=f"try_{i + j}"):
                    clicked_item = p['filename']
                st.markdown(
                    f"<div style='text-align:center; margin-top:10px;'>"
                    f"<a href='{p['buy']}' target='_blank' style='color:#007bff; font-weight:bold;'>Buy on Walmart</a>"
                    f"</div>", unsafe_allow_html=True
                )
    st.markdown("<br>", unsafe_allow_html=True)  # Add space between rows

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
            overlay = cv2.cvtColor(overlay, cv2.COLOR_RGBA2BGRA)
        except:
            st.error("Couldn't load the selected item.")
            st.stop()

        input_image = Image.open(uploaded_file).convert("RGB")
        frame = np.array(input_image)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        h, w, _ = frame.shape

        mp_face_mesh = mp.solutions.face_mesh
        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True,
                                   min_detection_confidence=0.5) as face_mesh:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            result = face_mesh.process(rgb_frame)

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

                st.markdown("<h2 style='color:#ff6666;'>🎚️ Adjust Size</h2>", unsafe_allow_html=True)
                scale_factor = st.slider("", min_value=1.0, max_value=2.0, value=1.45, step=0.05)
                scale = int(((dx ** 2 + dy ** 2) ** 0.5) * scale_factor)

                try:
                    resized = cv2.resize(overlay, (scale, int(overlay.shape[0] * scale / overlay.shape[1])))
                    M = cv2.getRotationMatrix2D((resized.shape[1] // 2, resized.shape[0] // 2), angle, 1.0)
                    rotated = cv2.warpAffine(resized, M, (resized.shape[1], resized.shape[0]),
                                             flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT,
                                             borderValue=(0, 0, 0, 0))

                    if category == "Glasses":
                        x_offset = cx - rotated.shape[1] // 2
                        y_offset = cy - rotated.shape[0] // 2
                    else:
                        x_offset = cx - rotated.shape[1] // 2
                        y_offset = int(top.y * h) - int(rotated.shape[0] * 0.75)

                    x_offset = max(0, min(x_offset, w - rotated.shape[1]))
                    y_offset = max(0, min(y_offset, h - rotated.shape[0]))

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

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.image(frame_rgb, caption="🧢 Try-On Result", use_container_width=True)
        else:
            st.warning("😕 No face detected. Try another image with clearer facial visibility.")
