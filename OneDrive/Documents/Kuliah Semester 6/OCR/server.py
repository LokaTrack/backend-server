import os
import re
import pytesseract
from flask import Flask, request, jsonify
from PIL import Image

#Path ke Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
def parse_qty_return(val):
    val = val.lower().replace(',', '.')
    val = val.replace('l', '1').replace('o', '0')
    val = re.sub(r'[^0-9.]', '', val)
    try:
        if val.startswith('0') and len(val) == 2:
            return float(f"0.{val[1]}")
        return float(val)
    except:
        return 0.0
# ============
# ROUTE 1: Upload biasa dan ambil Order No
# ============
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file uploaded"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    text = pytesseract.image_to_string(Image.open(filepath))
    print("=== OCR TEXT START ===")
    print(text)
    print("=== OCR TEXT END ===")

    #Regex untuk ambil Order No
    order_no_match = re.search(r'Order\s*No\s*[:\-]?\s*([A-Z0-9O]{2}/[0-9O]{2}-[0-9O]{4}/[0-9O]{3})', text, re.IGNORECASE)
    
    if order_no_match:
        extracted_order_no = order_no_match.group(1).replace("O3", "03")
    else:
        extracted_order_no = "Not found"

    return jsonify({
        "message": "File uploaded successfully",
        "filename": file.filename,
        "order_no": extracted_order_no
    }), 200

# ============
# ROUTE 2: OCR Return Barang
# ============
@app.route('/return-ocr', methods=['POST'])
def return_ocr():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist('file')
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    all_text = ""
    result = []

    for file in files:
        if file.filename == '':
            continue

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # OCR per file
        text = pytesseract.image_to_string(Image.open(filepath))
        all_text += text + "\n"

    lines = all_text.splitlines()

    for line in lines:
        if not line.strip() or 'item' in line.lower():
            continue

        # Pattern 1: Ada return (Qty Return)
        match_return = re.match(r'^(\d+)\s+(.+?)\s+([0-9loiOIl,\.]+)\s+([0-9loiOIl,\.]+)\s+Rp', line)

        # Pattern 2: Tidak ada return (Qty langsung ke harga)
        match_no_return = re.match(r'^(\d+)\s+(.+?)\s+([0-9loiOIl,\.]+)\s+Rp', line)

        if match_return:
            no = int(match_return.group(1))
            item = match_return.group(2).strip()
            qty = parse_qty_return(match_return.group(3))
            ret = parse_qty_return(match_return.group(4))

            result.append({
                "No": no,
                "Item": item,
                "Qty": qty,
                "Return": ret
            })
        elif match_no_return:
            no = int(match_no_return.group(1))
            item = match_no_return.group(2).strip()
            qty = parse_qty_return(match_no_return.group(3))

            result.append({
                "No": no,
                "Item": item,
                "Qty": qty,
                "Return": 0.0
            })

    return jsonify({
        "message": "All item data processed (including non-returned)",
        "data": result,
        "raw_text": all_text
    }), 200


# ============
# ROUTE 3: Only show returned items (return > 0)
# ============
@app.route('/return-only', methods=['POST'])
def return_only():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist('file')
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    all_text = ""
    result = []

    for file in files:
        if file.filename == '':
            continue

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        text = pytesseract.image_to_string(Image.open(filepath))
        all_text += text + "\n"

    lines = all_text.splitlines()

    for line in lines:
        if not line.strip():
            continue

        # Pattern: No Item Qty Return Rp Harga Rp Total
        match = re.match(r'^(\d+)\s+(.+?)\s+([0-9loiOIl,\.]+)\s+([0-9loiOIl,\.]+)\s+Rp', line)
        if match:
            no = int(match.group(1))
            item = match.group(2).strip()
            qty = parse_qty_return(match.group(3))
            ret = parse_qty_return(match.group(4))

            if ret > 0:
                result.append({
                    "No": no,
                    "Item": item,
                    "Qty": qty,
                    "Return": ret
                })

    return jsonify({
        "message": "Returned items only",
        "returned_data": result,
        "raw_text": all_text
    }), 200


if __name__ == '__main__':
    app.run(debug=True)
