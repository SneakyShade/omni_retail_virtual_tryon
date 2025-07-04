# 🛍️ Omni Retail Virtual Try-On

A real-time virtual try-on web application that lets users try Walmart products like glasses and hats using their webcam. Built with **Streamlit**, **OpenCV**, and **MediaPipe**, this app overlays fashion accessories on live video feed based on facial landmark detection.

## 🔥 Features
- Try-on mode for both **glasses** and **hats**
- Real-time webcam integration
- Accurate placement using MediaPipe Face Mesh
- Product cards with price and "Buy on Walmart" link
- Clean, responsive UI with product images
- Scrollable or paginated layout (based on product count)

## 🛠️ Tech Stack
- `Streamlit` for frontend
- `OpenCV` for image manipulation
- `MediaPipe` for face landmark detection
- `NumPy`, `Pillow` for processing
- Products are fetched from local folders and mapped with metadata (price, name, link)

## 📦 Installation

```bash
git clone https://github.com/SneakyShade/omni_retail_virtual_tryon.git
cd omni_retail_virtual_tryon
pip install -r requirements.txt
streamlit run app.py
