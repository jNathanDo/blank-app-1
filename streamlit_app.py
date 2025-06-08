import streamlit as st
import math
import random
from PIL import Image, ImageDraw
import io
import zipfile
import tempfile
import numpy as np

# For advanced drag/resize support:
from streamlit_drawable_canvas import st_canvas

# Constants
CARD_SIZE = 500
MARGIN = 20
SYMBOL_SIZE_DEFAULT = 80

st.set_page_config(page_title="Spot It! Card Generator", layout="wide")
st.title("🎴 Spot It! Card Generator with Easy/Advanced Mode")

# Mode selection
mode = st.radio("Choose mode:", ["Easy (Auto placement)", "Advanced (Drag & Resize)"])

# Symbols per card
n = st.slider("Symbols per card (n):", 3, 6, 4)
total_symbols = n**2 - n + 1

# Upload images
uploaded_files = st.file_uploader(
    f"Upload at least {total_symbols} images (PNG/JPG). These will be used as symbols.",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if uploaded_files and len(uploaded_files) < total_symbols:
    st.warning(f"Please upload at least {total_symbols} images for n={n}. You uploaded {len(uploaded_files)}.")

def generate_spot_it_deck(n):
    cards = []
    for i in range(n):
        card = [0] + [i * (n - 1) + j + 1 for j in range(n - 1)]
        cards.append(card)
    for i in range(n - 1):
        for j in range(n - 1):
            card = [i + 1]
            for k in range(n - 1):
                val = n + (n - 1) * k + ((i * k + j) % (n - 1))
                card.append(val)
            cards.append(card)
    return cards

def draw_card_with_images(card_symbols, images, positions=None, sizes=None):
    img = Image.new("RGBA", (CARD_SIZE, CARD_SIZE), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw circle border
    draw.ellipse(
        [MARGIN, MARGIN, CARD_SIZE - MARGIN, CARD_SIZE - MARGIN],
        outline="black",
        width=3,
    )
    center = CARD_SIZE // 2
    radius = (CARD_SIZE - 2 * MARGIN) // 2

    # Default positions and sizes if None:
    if positions is None or sizes is None:
        positions = []
        sizes = []
        count = len(card_symbols)
        angle_step = 2 * math.pi / count
        for i in range(count):
            angle = i * angle_step
            x = center + int((radius - SYMBOL_SIZE_DEFAULT//2) * math.cos(angle))
            y = center + int((radius - SYMBOL_SIZE_DEFAULT//2) * math.sin(angle))
            positions.append([x, y])
            sizes.append(SYMBOL_SIZE_DEFAULT)

    # Draw all symbols with given positions and sizes
    for idx, sym_id in enumerate(card_symbols):
        im = images[sym_id].convert("RGBA")
        size_px = sizes[idx]
        im = im.resize((size_px, size_px))
        x, y = positions[idx]

        # Clamp images inside circle border
        left_bound = center - radius + size_px // 2
        right_bound = center + radius - size_px // 2
        top_bound = center - radius + size_px // 2
        bottom_bound = center + radius - size_px // 2
        x = max(left_bound, min(right_bound, x))
        y = max(top_bound, min(bottom_bound, y))

        img.paste(im, (int(x - size_px / 2), int(y - size_px / 2)), im)

    return img

if uploaded_files and len(uploaded_files) >= total_symbols:
    deck = generate_spot_it_deck(n)

    # Load images into memory
    images = []
    for file in uploaded_files[:total_symbols]:
        im = Image.open(file)
        images.append(im)

    if mode == "Easy (Auto placement)":
        st.success(f"Generated {len(deck)} cards with automatic layout.")
        cards = []
        for idx, card_symbols in enumerate(deck):
            st.markdown(f"### Card {idx+1}")
            card_img = draw_card_with_images(card_symbols, images)
            st.image(card_img, use_column_width=True)
            cards.append(card_img)

        if st.button("Export all cards as ZIP"):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = f"{tmpdir}/spot_it_cards.zip"
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for i, card_img in enumerate(cards):
                        buf = io.BytesIO()
                        card_img.save(buf, format="PNG")
                        zipf.writestr(f"card_{i+1}.png", buf.getvalue())
                with open(zip_path, "rb") as f:
                    st.download_button("Download ZIP", f, file_name="spot_it_cards.zip")

    else:
        # Advanced mode with interactive drag & resize per card
        st.info("Drag and resize symbols on each card. Positions and sizes are saved per session.")

        cards = []
        # Save positions and sizes in session state to persist between reruns
        if "positions" not in st.session_state:
            st.session_state.positions = {}
        if "sizes" not in st.session_state:
            st.session_state.sizes = {}

        for card_idx, card_symbols in enumerate(deck):
            st.markdown(f"### Card {card_idx + 1}")

            key_pos = f"positions_{card_idx}"
            key_size = f"sizes_{card_idx}"

            if key_pos not in st.session_state.positions:
                # Initialize positions on circle border
                center = CARD_SIZE // 2
                radius = (CARD_SIZE - 2 * MARGIN) // 2
                pos_init = []
                size_init = []
                count = len(card_symbols)
                angle_step = 2 * math.pi / count
                for i in range(count):
                    angle = i * angle_step
                    x = center + int((radius - SYMBOL_SIZE_DEFAULT//2) * math.cos(angle))
                    y = center + int((radius - SYMBOL_SIZE_DEFAULT//2) * math.sin(angle))
                    pos_init.append([x, y])
                    size_init.append(SYMBOL_SIZE_DEFAULT)
                st.session_state.positions[key_pos] = pos_init
                st.session_state.sizes[key_size] = size_init

            # Canvas setup
            canvas_result = st_canvas(
                fill_color="rgba(0, 0, 0, 0)",
                stroke_width=0,
                stroke_color="#000000",
                background_color="#ffffff",
                height=CARD_SIZE,
                width=CARD_SIZE,
                drawing_mode="transform",
                key=f"canvas_{card_idx}",
                initial_drawing=None,
                point_display_radius=0,
                # Only allow transform (move/resize) on these objects
                objects=[
                    {
                        "type": "image",
                        "left": st.session_state.positions[key_pos][i][0] - st.session_state.sizes[key_size][i] // 2,
                        "top": st.session_state.positions[key_pos][i][1] - st.session_state.sizes[key_size][i] // 2,
                        "width": st.session_state.sizes[key_size][i],
                        "height": st.session_state.sizes[key_size][i],
                        "src": images[card_symbols[i]]._repr_png_(),
                        "lockScalingFlip": True,
                    }
                    for i in range(len(card_symbols))
                ],
                display_toolbar=True,
                key_events={"transform": True}
            )

            # On change, update positions and sizes
            if canvas_result.json_data:
                objects = canvas_result.json_data.get("objects", [])
                new_positions = []
                new_sizes = []
                center = CARD_SIZE // 2
                radius = (CARD_SIZE - 2 * MARGIN) // 2
                for obj in objects:
                    # Clamp inside circle border
                    x_center = obj["left"] + obj["width"] / 2
                    y_center = obj["top"] + obj["height"] / 2
                    w = obj["width"]
                    h = obj["height"]
                    # Clamp x_center/y_center to stay fully inside circle border
                    left_bound = center - radius + w / 2
                    right_bound = center + radius - w / 2
                    top_bound = center - radius + h / 2
                    bottom_bound = center + radius - h / 2

                    x_clamped = max(left_bound, min(right_bound, x_center))
                    y_clamped = max(top_bound, min(bottom_bound, y_center))

                    new_positions.append([x_clamped, y_clamped])
                    new_sizes.append(int(max(w, h)))

                st.session_state.positions[key_pos] = new_positions
                st.session_state.sizes[key_size] = new_sizes

                # Draw the updated card image below canvas preview
                card_img = draw_card_with_images(card_symbols, images, new_positions, new_sizes)
                st.image(card_img, caption="Rendered Card", use_column_width=False, width=CARD_SIZE)
                cards.append(card_img)

        if cards and st.button("Export all edited cards as ZIP"):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = f"{tmpdir}/spot_it_cards.zip"
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for i, card_img in enumerate(cards):
                        buf = io.BytesIO()
                        card_img.save(buf, format="PNG")
                        zipf.writestr(f"card_{i+1}.png", buf.getvalue())
                with open(zip_path, "rb") as f:
                    st.download_button("Download ZIP", f, file_name="spot_it_cards.zip")

else:
    st.info(f"Upload at least {total_symbols} images to generate cards.")


