import streamlit as st
import qrcode
from qrcode.image.styledpil import StyledPilImage
from PIL import Image, ImageDraw
import io

# ---------- Page config ----------
st.set_page_config(
    page_title="QR Code Generator",
    page_icon="📱",
    layout="centered",
)

# ---------- Custom CSS ----------
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f8fafc, #eef2ff, #faf5ff); }
    div[data-testid="stVerticalBlock"] > div { gap: 0.75rem; }
    .qr-header { text-align: center; margin-bottom: 1rem; }
    .qr-header h1 { font-size: 2rem; font-weight: 800; color: #1a1a2e; }
    .qr-header p { color: #6b7280; font-size: 0.95rem; }
    .badge {
        display: inline-block; background: #e0e7ff; color: #4338ca;
        padding: 4px 14px; border-radius: 20px; font-size: 0.75rem;
        font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .warning-box {
        background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
        padding: 10px 14px; font-size: 0.85rem; color: #92400e; margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("""
<div class="qr-header">
    <span class="badge">● QR Generator</span>
    <h1>QR Code Generator</h1>
    <p>Create QR codes for URLs, text, and contacts — with optional logo overlay.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Layout: two columns ----------
left_col, right_col = st.columns([1.1, 1], gap="large")

with left_col:
    # --- Input type tabs ---
    tab_url, tab_text, tab_contact = st.tabs(["🔗 URL", "📝 Text", "👤 Contact"])

    qr_data = ""

    with tab_url:
        url_input = st.text_input(
            "Website URL",
            placeholder="example.com or https://example.com",
            help="https:// is added automatically if omitted.",
        )
        if url_input.strip():
            u = url_input.strip()
            qr_data = u if u.lower().startswith(("http://", "https://")) else f"https://{u}"

    with tab_text:
        text_input = st.text_area(
            "Text Content",
            placeholder="Enter any text to encode...",
            height=120,
        )
        if text_input.strip():
            qr_data = text_input.strip()

    with tab_contact:
        c1, c2 = st.columns(2)
        first_name = c1.text_input("First Name", placeholder="John")
        last_name = c2.text_input("Last Name", placeholder="Doe")
        phone = st.text_input("Phone", placeholder="+1 (555) 123-4567")
        email = st.text_input("Email", placeholder="john@example.com")
        org = st.text_input("Organization", placeholder="Company Name")
        website = st.text_input("Website", placeholder="https://example.com")

        if any([first_name, last_name, phone, email]):
            lines = [
                "BEGIN:VCARD", "VERSION:3.0",
                f"N:{last_name};{first_name}",
                f"FN:{' '.join(filter(None, [first_name, last_name]))}",
            ]
            if phone:   lines.append(f"TEL:{phone}")
            if email:   lines.append(f"EMAIL:{email}")
            if org:      lines.append(f"ORG:{org}")
            if website:  lines.append(f"URL:{website}")
            lines.append("END:VCARD")
            qr_data = "\n".join(lines)

    st.divider()

    # --- Logo upload ---
    st.markdown("##### 🖼️ Logo Overlay")
    logo_file = st.file_uploader(
        "Upload a logo image",
        type=["png", "jpg", "jpeg", "svg", "webp"],
        help="The logo is placed in the center of the QR code.",
    )

    logo_size_pct = st.slider(
        "Logo Size",
        min_value=15, max_value=60, value=45, step=1,
        format="%d%%",
        help="Percentage of QR code area the logo occupies (longest side).",
    )

    if logo_file and not qr_data:
        st.info("Enter a URL, text, or contact info above to generate a QR code with your logo.")

    st.divider()

    # --- Output size ---
    st.markdown("##### 📐 Output Size")
    size_options = {
        "256px – Small": 256,
        "512px – Medium": 512,
        "1024px – Large": 1024,
        "1536px – XL": 1536,
        "2048px – XXL": 2048,
        "4096px – Print": 4096,
    }
    size_label = st.radio(
        "Download resolution",
        list(size_options.keys()),
        index=2,
        horizontal=True,
        label_visibility="collapsed",
    )
    qr_pixel_size = size_options[size_label]
    st.caption(f"Downloaded image will be **{qr_pixel_size} × {qr_pixel_size}** pixels.")

    st.divider()

    # --- QR Density (error correction) ---
    st.markdown("##### 🔳 QR Density")
    ec_options = {
        "Low (L) – Fewest dots · 7% recovery · Best for print": qrcode.constants.ERROR_CORRECT_L,
        "Medium (M) – Fewer dots · 15% recovery · Good balance": qrcode.constants.ERROR_CORRECT_M,
        "Quartile (Q) – More dots · 25% recovery · With small logo": qrcode.constants.ERROR_CORRECT_Q,
        "High (H) – Most dots · 30% recovery · With large logo": qrcode.constants.ERROR_CORRECT_H,
    }
    ec_label = st.radio(
        "Error correction level",
        list(ec_options.keys()),
        index=2,
        label_visibility="collapsed",
    )
    ec_level = ec_options[ec_label]

    if logo_file and "Low" in ec_label:
        st.markdown(
            '<div class="warning-box">⚠️ Low density with a logo may make the QR code unscannable. '
            "Consider Medium or higher.</div>",
            unsafe_allow_html=True,
        )


# ---------- Helper: generate QR with optional logo ----------
def generate_qr(data: str, size: int, ec: int, logo_bytes=None, logo_pct: int = 45) -> Image.Image:
    """Generate a QR code PIL image, optionally with a centered logo."""
    qr = qrcode.QRCode(
        version=None,  # auto-detect smallest version
        error_correction=ec,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1a1a2e", back_color="#ffffff").convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)

    if logo_bytes:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

        # Maintain aspect ratio
        nat_w, nat_h = logo.size
        aspect = nat_w / nat_h
        max_dim = int(size * logo_pct / 100)

        if aspect >= 1:
            lw = max_dim
            lh = int(max_dim / aspect)
        else:
            lh = max_dim
            lw = int(max_dim * aspect)

        logo = logo.resize((lw, lh), Image.LANCZOS)

        # White rounded-rect background
        pad = max(6, int(min(lw, lh) * 0.08))
        bg_w, bg_h = lw + pad * 2, lh + pad * 2
        bg = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
        bg_draw = ImageDraw.Draw(bg)
        radius = int(min(bg_w, bg_h) * 0.12)
        bg_draw.rounded_rectangle([0, 0, bg_w, bg_h], radius=radius, fill=(255, 255, 255, 255))

        # Paste logo onto background (centered)
        bg.paste(logo, (pad, pad), logo)

        # Paste onto QR
        pos_x = (size - bg_w) // 2
        pos_y = (size - bg_h) // 2
        img.paste(bg, (pos_x, pos_y), bg)

    return img.convert("RGB")


# ---------- Right column: preview & download ----------
with right_col:
    st.markdown("##### Preview")

    if qr_data:
        logo_bytes = logo_file.read() if logo_file else None
        qr_img = generate_qr(qr_data, qr_pixel_size, ec_level, logo_bytes, logo_size_pct)

        # Show preview (always display at reasonable size)
        st.image(qr_img, use_container_width=True, caption="Scan with any camera app")

        # Download button
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG", dpi=(300, 300))
        buf.seek(0)

        st.download_button(
            label="⬇️  Download QR Code",
            data=buf,
            file_name="qrcode.png",
            mime="image/png",
            use_container_width=True,
            type="primary",
        )

        # Show encoded data
        with st.expander("📋 Encoded Data"):
            st.code(qr_data, language=None)
    else:
        st.markdown(
            "<div style='text-align:center; padding:4rem 1rem; color:#9ca3af;'>"
            "<div style='font-size:3rem; margin-bottom:0.5rem;'>📱</div>"
            "Fill in the form to generate your QR code</div>",
            unsafe_allow_html=True,
        )

# ---------- Footer ----------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#9ca3af; font-size:0.8rem;'>"
    "No data stored · Works offline · Free to use</p>",
    unsafe_allow_html=True,
)
