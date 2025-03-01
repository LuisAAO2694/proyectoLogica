from fastapi import FastAPI
from typing import Dict, List #forma parar indicar que voy a devolver un diccionario 
import uvicorn
import re
from itertools import product

app = FastAPI()

def normalizar_espacios(expresion: str) -> str:
    """Agrega espacios alrededor de los operadores lógicos si no los tiene"""
    operadores = ["∧", "∨", "¬", "&", "|", "~", "and", "or", "not", "^", "v", "-"]
    for operador in operadores:
        expresion = expresion.replace(operador, f" {operador} ")
    return " ".join(expresion.split())

def convertir_expresion(expresion: str) -> str:
    """Convierte la expresión lógica a operadores de Python"""
    expresion = normalizar_espacios(expresion)
    conversiones = {
        "∧": "and", #Y lógico
        "∨": "or", #O lógico
        "¬": "not", #No lógico
        "&": "and", #AND en símbolo
        "|": "or", #OR en símbolo
        "~": "not", #NOT en símbolo
        "and": "and", #AND en notación alternativa
        "or": "or", #OR en notación alternativa
        "not": "not", #NOT en notación alternativa
        "^": "and", #Otro simbolo equivalente para and
        "v": "or", #Otro simbolo equivalente para or  
        "-": "not" #Otro simbolo equivalente para not
    }
    for simbolo, reemplazo in conversiones.items():
        expresion = expresion.replace(simbolo, reemplazo)
    return expresion

def extraer_variables(expresion: str) -> list:
    """Extrae las variables (p, q, r, etc.) de la expresión"""
    # Busca letras individuales que no formen parte de palabras como "and", "or", "not"
    palabras = normalizar_espacios(expresion).split()
    variables = set()
    for palabra in palabras:
        if re.match(r"^[a-z]$", palabra):  # Solo letras individuales de a-z
            variables.add(palabra)
    return sorted(list(variables))  # Ordenadas para consistencia

def generar_tabla_verdad(expresion: str) -> Dict:
    """Genera una tabla de verdad para la expresión dada"""
    variables = extraer_variables(expresion)
    if not variables:
        return {"error": "No se encontraron variables válidas en la expresión"}
    if len(variables) > 5:  # Limitamos a 5 por el requerimiento base
        return {"error": "La expresión contiene más de 5 variables"}

    resultados = []
    expresion_convertida = convertir_expresion(expresion)

    # Generar todas las combinaciones posibles de valores de verdad
    combinaciones = list(product([False, True], repeat=len(variables)))

    for combinacion in combinaciones:
        contexto = dict(zip(variables, combinacion))  # Asocia cada variable con su valor
        try:
            resultado = eval(expresion_convertida, {}, contexto)
            fila = {**contexto, "resultado": resultado}
            resultados.append(fila)
        except Exception as e:
            return {"error": f"Expresión inválida: {str(e)}"}

    return {"variables": variables, "tabla": resultados}

@app.post("/tabla_verdad")
def obtener_tabla_verdad(data: Dict[str, str]):
    expresion_original = data.get("expresion", "")
    if not expresion_original:
        return {"error": "No se proporcionó una expresión"}
    
    expresion_convertida = convertir_expresion(expresion_original)
    tabla = generar_tabla_verdad(expresion_original)
    
    if "error" in tabla:
        return tabla  # Devolver el error si lo hay
    
    return {
        "expresion_original": expresion_original,
        "expresion_convertida": expresion_convertida,
        "variables": tabla["variables"],
        "tabla_verdad": tabla["tabla"]
    }

if __name__ == "__main__":  
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
