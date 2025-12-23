import os
import io
import qrcode
from qrcode.image.styledpil import StyledPilImage
# Import VerticalBars atau GappedSquare jika ingin variasi lain, 
# tapi RoundedModuleDrawer dengan radius_ratio adalah solusi terbaik untuk 'soft edge'
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_qr_with_logo(data, logo_file):
    if len(data) > 500:
        raise ValueError("Teks terlalu panjang!")

    # Box size 20 sudah menghasilkan resolusi sangat tinggi (HD) tanpa file menjadi raksasa
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=20, 
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # --- PERBAIKAN UTAMA: Mengatur Radius Ratio ---
    # radius_ratio=0.1 s/d 0.3 membuat sudut tumpul halus (soft edge)
    # Jika dikosongkan, defaultnya adalah 1.0 (lingkaran penuh)
    qr_img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(radius_ratio=0.4), 
        fill_color="black",
        back_color="white"
    ).convert('RGB')
    
    logo = Image.open(logo_file)
    qr_width, qr_height = qr_img.size
    
    # Resize Logo
    max_logo_size = int(qr_width * 0.25)
    logo.thumbnail((max_logo_size, max_logo_size), Image.LANCZOS)
    logo_w, logo_h = logo.size

    # Kotak Putih Tengah
    padding = 30 
    white_box_w = logo_w + padding
    white_box_h = logo_h + padding
    
    left = (qr_width - white_box_w) // 2
    top = (qr_height - white_box_h) // 2
    right = (qr_width + white_box_w) // 2
    bottom = (qr_height + white_box_h) // 2

    draw = ImageDraw.Draw(qr_img)
    # Radius kotak putih dibuat 10-20 agar serasi dengan modul QR
    draw.rounded_rectangle(
        [left, top, right, bottom], 
        radius=5, 
        fill="white"
    )

    logo_pos = ((qr_width - logo_w) // 2, (qr_height - logo_h) // 2)
    
    if logo.mode == 'RGBA':
        qr_img.paste(logo, logo_pos, logo)
    else:
        qr_img.paste(logo, logo_pos)

    img_io = io.BytesIO()
    qr_img.save(img_io, 'PNG', quality=100)
    img_io.seek(0)
    return img_io

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.form.get('data')
        logo = request.files.get('logo')
        if not data or not logo or not allowed_file(logo.filename):
            return "Input tidak valid!", 400
        try:
            qr_file = create_qr_with_logo(data, logo)
            return send_file(qr_file, mimetype='image/png', as_attachment=True, download_name="qr_hd_soft.png")
        except Exception as e:
            return str(e), 400
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False, port=8080) # Menggunakan port 8080 untuk menghindari konflik macOS