from fastapi import FastAPI

app = FastAPI()

contador = 0  # Variable para el contador

@app.get("/ping")
def ping():
    return {"message": "pong desde FastAPI"}

@app.get("/contador")
def obtener_contador():
    return {"contador": contador}

@app.post("/incrementar")
def incrementar_contador():
    global contador
    contador += 1
    return {"contador": contador}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
