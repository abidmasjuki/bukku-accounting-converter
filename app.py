"""
Bukku Accounting Converter - Online Web Application
Flask backend serving the web UI, conversion API, and direct template downloads.
Version: 1.1.0
"""

import os
import io
from flask import Flask, render_template, request, jsonify, send_file
from config import VERSION, APP_NAME, BUKKU_COLUMNS
from converter import BukkuStatementConverter, StatementParseResult

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32MB max upload

@app.route("/")
def index():
    return render_template("index.html", version=VERSION, app_name=APP_NAME)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "app": APP_NAME,
        "version": VERSION
    })

@app.route("/api/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "Empty filename"}), 400

    date_format = request.form.get("date_format", "ymd")
    ref_style = request.form.get("ref_style", "standard")
    fill_desc = request.form.get("fill_desc", "true").lower() in ["true", "1", "yes"]

    try:
        content = file.read()
        converter = BukkuStatementConverter(
            fill_empty_description=fill_desc,
            ref_style=ref_style,
            date_format=date_format
        )
        parsed = converter.parse_content(content)
        summary = parsed.to_summary_dict()

        # Month and year label
        month_names_en = {
            1: "Jan", 2: "Feb", 3: "March", 4: "April", 5: "May", 6: "June",
            7: "July", 8: "Ogos", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        label = ""
        if parsed.from_date:
            if "/" in parsed.from_date:
                parts = parsed.from_date.split("/")
                if len(parts) == 3:
                    m = int(parts[1])
                    y = parts[2]
                    label = f"{month_names_en.get(m, str(m))} {y}"
            elif "-" in parsed.from_date:
                parts = parsed.from_date.split("-")
                if len(parts) == 3:
                    m = int(parts[1])
                    y = parts[0]
                    label = f"{month_names_en.get(m, str(m))} {y}"

        if not label:
            label = os.path.splitext(file.filename)[0]

        return jsonify({
            "success": True,
            "summary": summary,
            "label": label,
            "preview": parsed.transactions[:100],
            "total_transactions": len(parsed.transactions)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/download", methods=["POST"])
def download():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    export_fmt = request.form.get("format", "csv").lower()
    date_format = request.form.get("date_format", "ymd")
    ref_style = request.form.get("ref_style", "standard")
    fill_desc = request.form.get("fill_desc", "true").lower() in ["true", "1", "yes"]

    try:
        content = file.read()
        converter = BukkuStatementConverter(
            fill_empty_description=fill_desc,
            ref_style=ref_style,
            date_format=date_format
        )
        parsed = converter.parse_content(content)

        month_names_en = {
            1: "Jan", 2: "Feb", 3: "March", 4: "April", 5: "May", 6: "June",
            7: "July", 8: "Ogos", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        label = ""
        if parsed.from_date:
            if "/" in parsed.from_date:
                parts = parsed.from_date.split("/")
                if len(parts) == 3:
                    m = int(parts[1])
                    y = parts[2]
                    label = f"{month_names_en.get(m, str(m))} {y}"
            elif "-" in parsed.from_date:
                parts = parsed.from_date.split("-")
                if len(parts) == 3:
                    m = int(parts[1])
                    y = parts[0]
                    label = f"{month_names_en.get(m, str(m))} {y}"

        if not label:
            label = os.path.splitext(file.filename)[0]

        if export_fmt == "xlsx":
            xlsx_buf = converter.get_bukku_xlsx_bytes(parsed)
            filename = f"Bukku-statement-template ({label}).xlsx"
            return send_file(
                xlsx_buf,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name=filename
            )
        else:
            csv_bytes = converter.get_bukku_csv_bytes(parsed)
            filename = f"Bukku-statement-template ({label}).csv"
            return send_file(
                io.BytesIO(csv_bytes),
                mimetype="text/csv",
                as_attachment=True,
                download_name=filename
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
