from fastapi import FastAPI
from typing import Dict, List #forma parar indicar que voy a devolver un diccionario 
import uvicorn
import re
from itertools import product
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Origen del frontend
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos los headers
)

#-----------------------Version de produccionv2-----------------------

def normalizar_espacios(expresion: str) -> str:
    """Agrega espacios alrededor de los operadores lógicos si no los tiene y elimina paréntesis"""
    operadores = ["∧", "∨", "¬", "&", "|", "~", "and", "or", "not", "^", "v", "-", "→", "↔"]
    for operador in operadores:
        expresion = expresion.replace(operador, f" {operador} ")
    # Eliminar paréntesis
    expresion = expresion.replace("(", "").replace(")", "")
    return " ".join(expresion.split())


def convertir_expresion(expresion: str) -> str:
    """Convierte símbolos a palabras clave estándar"""
    expresion = normalizar_espacios(expresion)
    conversiones = {
        "∧": "and", "∨": "or", "¬": "not", "&": "and", "|": "or",
        "~": "not", "^": "and", "v": "or", "-": "not"
    }
    for simbolo, reemplazo in conversiones.items():
        expresion = expresion.replace(simbolo, reemplazo)
    return expresion

def extraer_variables(expresion: str) -> list:
    """Extrae las variables (p, q, r, etc.) de la expresión"""
    palabras = normalizar_espacios(expresion).split()
    variables = set()
    for palabra in palabras:
        if re.match(r"^[a-z]$", palabra):
            variables.add(palabra)
    return sorted(list(variables))

def identificar_subexpresiones(expresion: str) -> List[str]:
    """Identifica las subexpresiones relevantes para mostrar pasos intermedios"""
    subexpresiones = []
    expresion = normalizar_espacios(expresion)
    
    # Manejar negaciones
    palabras = expresion.split()
    i = 0
    while i < len(palabras):
        if palabras[i] in ["not", "~", "¬", "-"] and i + 1 < len(palabras):
            if palabras[i+1] not in ["and", "or", "∧", "∨", "→", "↔"]:
                subexp = f"{palabras[i]} {palabras[i+1]}"
                if subexp not in subexpresiones:
                    subexpresiones.append(subexp)
            i += 1
        else:
            i += 1
    
    # Manejar paréntesis
    stack = []
    inicio = 0
    for i, char in enumerate(expresion):
        if char == "(":
            if not stack:
                inicio = i
            stack.append(char)
        elif char == ")":
            if stack:
                stack.pop()
                if not stack and i > inicio:
                    subexpresion = expresion[inicio:i+1].strip()
                    if subexpresion not in subexpresiones:
                        subexpresiones.append(subexpresion)
    
    # Manejar operadores binarios
    palabras = expresion.split()
    for i in range(1, len(palabras)-1):
        if palabras[i] in ["and", "or", "∧", "∨", "&", "|", "^", "v", "→", "↔"]:
            # Verificar si hay negación previa
            if i > 1 and palabras[i-2] in ["not", "~", "¬", "-"]:
                subexp = f"{palabras[i-2]} {palabras[i-1]} {palabras[i]} {palabras[i+1]}"
            else:
                subexp = f"{palabras[i-1]} {palabras[i]} {palabras[i+1]}"
            
            if subexp not in subexpresiones:
                subexpresiones.append(subexp)
    
    # Agregar la expresión completa
    if expresion not in subexpresiones:
        subexpresiones.append(expresion)
    
    return subexpresiones

def evaluar_expresion(expresion: str, contexto: Dict[str, bool]) -> bool:
    """Evalúa una expresión lógica sin usar eval()"""
    expresion = convertir_expresion(expresion)
    tokens = expresion.split()
    
    # Procesar negaciones primero
    i = 0
    while i < len(tokens):
        if tokens[i] in ["not", "~", "¬", "-"]:
            siguiente = tokens[i+1] if i+1 < len(tokens) else None
            if siguiente in contexto:
                tokens[i:i+2] = [not contexto[siguiente]]
            elif siguiente in ["True", "False"]:
                tokens[i:i+2] = [not (siguiente == "True")]
            else:
                i += 1
        else:
            i += 1
    
    # Pila para manejar paréntesis y evaluación
    pila = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if isinstance(token, bool):
            pila.append(token)
        elif token == "(":
            pila.append(token)
        elif token == ")":
            # Evaluar subexpresión dentro de paréntesis
            subpila = []
            while pila and pila[-1] != "(":
                subpila.append(pila.pop())
            if pila:
                pila.pop()  # Quitar el "("
            resultado = evaluar_subpila(subpila[::-1], contexto)
            pila.append(resultado)
        elif token in contexto:
            pila.append(contexto[token])
        elif token in ["True", "False"]:
            pila.append(token == "True")
        else:
            pila.append(token)
        i += 1
    
    # Evaluar lo que queda en la pila
    return evaluar_subpila(pila, contexto)

def evaluar_subpila(subpila: List, contexto: Dict[str, bool]) -> bool:
    """Evalúa una subpila de tokens"""
    if not subpila:
        return True
    
    # Convertir tokens a valores booleanos
    valores = []
    for token in subpila:
        if isinstance(token, bool):
            valores.append(token)
        elif token in contexto:
            valores.append(contexto[token])
        elif token in ["True", "False"]:
            valores.append(token == "True")
        else:
            valores.append(token)
    
    # Procesar operadores en orden de precedencia
    # 1. Negaciones (ya procesadas en evaluar_expresion)
    # 2. AND
    i = 1
    while i < len(valores) - 1:
        if valores[i] in ["and", "∧", "&", "^"]:
            if isinstance(valores[i-1], bool) and isinstance(valores[i+1], bool):
                valores[i-1:i+2] = [valores[i-1] and valores[i+1]]
                i = 1  # Reiniciar
            else:
                i += 2
        else:
            i += 2
    
    # 3. OR
    i = 1
    while i < len(valores) - 1:
        if valores[i] in ["or", "∨", "|", "v"]:
            if isinstance(valores[i-1], bool) and isinstance(valores[i+1], bool):
                valores[i-1:i+2] = [valores[i-1] or valores[i+1]]
                i = 1  # Reiniciar
            else:
                i += 2
        else:
            i += 2
    
    # 4. Implicación
    i = 1
    while i < len(valores) - 1:
        if valores[i] == "→":
            if isinstance(valores[i-1], bool) and isinstance(valores[i+1], bool):
                valores[i-1:i+2] = [not valores[i-1] or valores[i+1]]
                i = 1  # Reiniciar
            else:
                i += 2
        else:
            i += 2
    
    # 5. Equivalencia
    i = 1
    while i < len(valores) - 1:
        if valores[i] == "↔":
            if isinstance(valores[i-1], bool) and isinstance(valores[i+1], bool):
                valores[i-1:i+2] = [valores[i-1] == valores[i+1]]
                i = 1  # Reiniciar
            else:
                i += 2
        else:
            i += 2
    
    if len(valores) == 1 and isinstance(valores[0], bool):
        return valores[0]
    else:
        return None  # Error

def validar_expresion(expresion: str) -> str:
    """Valida la sintaxis de la expresión lógica."""
    expresion = expresion.replace(" ", "")
    
    # Validar balanceo de paréntesis
    balance = 0
    for char in expresion:
        if char == "(":
            balance += 1
        elif char == ")":
            balance -= 1
        if balance < 0:
            return "Error: Paréntesis no balanceados."
    if balance != 0:
        return "Error: Paréntesis no balanceados."
    
    # Validar operadores mal escritos o símbolos no reconocidos
    if re.search(r"[^a-z∧∨¬&|~andornot^v\-→↔() ]", expresion):
        return "Error: La expresión contiene caracteres no válidos."
    
    return "OK"


def generar_tabla_verdad(expresion: str) -> Dict:
    """Genera una tabla de verdad con pasos intermedios sin eval()"""
    validacion = validar_expresion(expresion)
    if validacion != "OK":
        return {"error": validacion}
    
    variables = extraer_variables(expresion)
    
    if not variables:
        return {"error": "No se encontraron variables válidas en la expresión"}
    
    if len(variables) == 1 and expresion.strip() in variables:
        return {"error": "La expresión no es válida, debe contener al menos un operador lógico"}
    
    if len(variables) > 5:
        return {"error": "La expresión contiene más de 5 variables"}
    
    subexpresiones = identificar_subexpresiones(expresion)
    resultados = []
    combinaciones = list(product([False, True], repeat=len(variables)))
    
    for combinacion in combinaciones:
        contexto = dict(zip(variables, combinacion))
        fila = dict(contexto)
        pasos = {}
        
        for subexp in subexpresiones:
            try:
                resultado = evaluar_expresion(subexp, contexto)
                pasos[subexp] = resultado
                if subexp == expresion:
                    fila["resultado"] = resultado
            except Exception as e:
                return {"error": f"Error en subexpresión {subexp}: {str(e)}"}
        
        fila["pasos"] = pasos
        resultados.append(fila)
    
    return {"variables": variables, "subexpresiones": subexpresiones, "tabla": resultados}



@app.post("/tabla_verdad")
def obtener_tabla_verdad(data: Dict[str, List[str]]):
    expresiones = data.get("expresiones", [])
    if not expresiones:
        return {"error": "No se proporcionaron expresiones"}
    
    respuesta = []
    for expresion_original in expresiones:
        expresion_convertida = convertir_expresion(expresion_original)
        tabla = generar_tabla_verdad(expresion_original)
        
        if "error" in tabla:
            respuesta.append(tabla)
        else:
            respuesta.append({
                "expresion_original": expresion_original,
                "expresion_convertida": expresion_convertida,
                "variables": tabla["variables"],
                "subexpresiones": tabla["subexpresiones"],
                "tabla_verdad": tabla["tabla"]
            })
    
    return {"resultados": respuesta}


if __name__ == "__main__":  
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
