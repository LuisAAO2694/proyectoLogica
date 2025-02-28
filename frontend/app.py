from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

API_URL = "http://127.0.0.1:8000"  # URL del backend FastAPI

@app.route("/")
def menu():
    return render_template("index.html")  # Menú principal

@app.route("/ping")
def ping():
    response = requests.get(f"{API_URL}/ping")
    data = response.json()
    return render_template("ping.html", message=data["message"])

@app.route("/boton")
def boton():
    response = requests.get(f"{API_URL}/contador")
    data = response.json()
    return render_template("boton.html", contador=data["contador"])

@app.route("/incrementar", methods=["POST"])
def incrementar():
    response = requests.post(f"{API_URL}/incrementar")
    data = response.json()
    return jsonify(data)  # Devuelve el nuevo contador en JSON

@app.route("/front")
def front():
    return render_template("front.html")  # Menú principal
    

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
