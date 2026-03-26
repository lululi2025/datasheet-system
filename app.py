"""Datasheet PDF Generator — Flask Web App."""
import os

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response

from config import BASE_DIR, OUTPUT_DIR, WEB_TEMPLATE_DIR
from services.data_loader import load_product, list_available_products
from services.pdf_generator import render_html
from services.version_manager import (
    get_current_version, get_history,
    get_all_products,
)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.secret_key = os.environ.get("APP_SECRET", "dev-secret-key")


@app.route("/")
def dashboard():
    products = list_available_products()
    versions = get_all_products()

    product_details = {}
    for model_name in products:
        try:
            p = load_product(model_name)
            product_details[model_name] = {
                "product_line": p.product_line,
                "category": p.category,
            }
        except Exception:
            product_details[model_name] = {}

    return render_template(
        "web/dashboard.html",
        products=products,
        versions=versions,
        product_details=product_details,
    )


@app.route("/product/<model_name>")
def product_page(model_name):
    try:
        product = load_product(model_name)
    except (FileNotFoundError, ValueError) as e:
        flash(f"Product {model_name} not found: {e}", "error")
        return redirect(url_for("dashboard"))

    current_version = get_current_version(model_name)
    history = get_history(model_name)

    return render_template(
        "web/product.html",
        product=product,
        current_version=current_version,
        history=history,
    )


@app.route("/preview/<model_name>")
def preview(model_name):
    """Render HTML preview — use browser Print to save as PDF."""
    try:
        product = load_product(model_name)
    except (FileNotFoundError, ValueError) as e:
        flash(f"Product {model_name} not found: {e}", "error")
        return redirect(url_for("dashboard"))

    current_version = get_current_version(model_name) or "draft"
    html = render_html(product, current_version)
    return html


@app.route("/drive-image/<file_id>")
def drive_image(file_id):
    """Proxy Google Drive images through the server (handles auth).

    Supports optional ?trim=1 query param to auto-crop whitespace.
    """
    from services.drive_images import download_file
    from services.image_utils import auto_trim
    try:
        data, mime_type = download_file(file_id)

        # Auto-trim whitespace if requested
        if request.args.get("trim") == "1":
            data = auto_trim(data)
            mime_type = "image/png"

        return Response(data, mimetype=mime_type, headers={
            "Cache-Control": "public, max-age=86400",
        })
    except Exception:
        return "", 404


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
