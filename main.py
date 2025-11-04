import os
from dotenv import load_dotenv
from flask import Flask, render_template, request
from utils import similarity
from utils import upload

app = Flask(__name__, template_folder="Templates")


@app.route("/", methods=["GET", "POST"])
def main_page() -> str:
    """Render and return main page."""
    return render_template("index.html")


@app.route("/report", methods=["POST", "GET"])
# def report_page() -> str:
#     """Render and return report page."""
#     result = request.form["text"]
#     return render_template("report.html") + similarity.return_table(
#         similarity.report(str(result)),
#     )
def report_page() -> str:
    text_input = request.form.get("text", "").strip()
    uploaded_file = request.files.get("file")

    if uploaded_file and uploaded_file.filename:
        result = upload.extract_text(uploaded_file)
    else:
        result = text_input

    return render_template("report.html") + similarity.return_table(
        similarity.report(result)
    )



if __name__ == "__main__":
    # Loading consts from .env
    load_dotenv()

    IS_DEBUG = os.getenv("DEBUG").lower() == "true"
    HOST = os.getenv("HOST")
    PORT = os.getenv("PORT")

    # Starting flask app
    app.run(debug=IS_DEBUG, host=HOST, port=PORT)
