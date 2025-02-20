from fastapi import FastAPI
from typing import Dict #forma parar indicar que voy a devolver un diccionario 
import uvicorn
import re

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

#---------------------------------------
def convertir_expresion(expresion: str) -> str:
    """Convierte la expresión lógica a operadores de Python"""
    conversiones = {
        "∧": "and",  # Y lógico
        "∨": "or",   # O lógico
        "¬": "not",  # No lógico
        "&": "and",  # AND en simbolo
        "|": "or",   # OR en simbolo
        "~": "not"   # NOT en simbolo
    }
    
    # Reemplazamos cada símbolo por su equivalente en Python
    for simbolo, reemplazo in conversiones.items():
        expresion = expresion.replace(simbolo, reemplazo)
    
    return expresion


def generar_tabla_verdad(expresion: str) -> Dict:
    """Genera una tabla de verdad para p y q"""
    variables = ["p", "q"]
    resultados = []

    #Se evalúa la expresión lógica con todos los valores posibles de p y q
    for p in [False, True]:
        for q in [False, True]:
            contexto = {"p": p, "q": q}
            try:
                #Evaluamos la expresión convertida, usando eval en un entorno controlado
                resultado = eval(expresion, {}, contexto)
                resultados.append({"p": p, "q": q, "resultado": resultado})
            except Exception as e:
                return {"error": f"Expresión inválida: {str(e)}"}

    return resultados



@app.post("/tabla_verdad")
def obtener_tabla_verdad(data: Dict[str, str]):
    expresion_original = data.get("expresion", "")
    expresion_convertida = convertir_expresion(expresion_original)
    tabla = generar_tabla_verdad(expresion_convertida)
    
    return {
        "expresion_original": expresion_original,
        "expresion_convertida": expresion_convertida,
        "tabla_verdad": tabla
    }

if __name__ == "__main__":  
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
