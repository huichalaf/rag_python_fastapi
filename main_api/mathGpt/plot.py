import numpy as np
import matplotlib.pyplot as plt
import time as tm 
from sympy import symbols, simplify, sympify
import sys
import io
import math

def graficar_funcion(user, funcion, intervalo_inferior, intervalo_superior, expresion):
    # Generar puntos equidistantes en el intervalo dado
    try:
        os.system("rm images/"+user+".png")
    except:
        pass
    y = []
    x = []
    i=intervalo_inferior
    incremento_ciclo = (intervalo_superior-intervalo_inferior)/100
    print("incremento_ciclo: ", incremento_ciclo)
    while i <= intervalo_superior:
        try:
            y.append(float(funcion(i)))
            x.append(i)
            i+=incremento_ciclo
        except Exception as e:
            i+=incremento_ciclo
    # Graficar la función
    plt.plot(x, y)
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title(f'Gráfico de la función {expresion}')
    plt.grid(True)
    #plt.show()
    plt.savefig(f"images/{user}.png")
    
def crear_funcion(expresion):
    x = symbols('x')
    expresion = expresion.replace("^", "**")
    
    funcion = sympify(expresion)  # Convierte la expresión en una expresión simbólica
    funcion_simplificada = simplify(funcion)  # Simplifica la expresión, si es posible

    # Creamos una función de Python a partir de la expresión simbólica
    def funcion_resultado(x_valor):
        return funcion_simplificada.subs(x, x_valor).evalf()

    return funcion_resultado

def create_graph(expresion, intervalo_inferior, intervalo_superior, user):
    print("expresion: ", expresion)
    if intervalo_inferior > intervalo_superior:
        temporal = intervalo_inferior
        intervalo_inferior = intervalo_superior
        intervalo_superior = temporal
    if intervalo_inferior == intervalo_superior:
        intervalo_inferior = -1
        intervalo_superior = 1

    print("intervalo_inferior: ", intervalo_inferior)
    print("intervalo_superior: ", intervalo_superior)
    intervalo_inferior = float(intervalo_inferior)
    intervalo_superior = float(intervalo_superior)
    try:
        mi_funcion = crear_funcion(expresion)
        print("funcion: ", mi_funcion)
        start = tm.time()
        graficar_funcion(user, mi_funcion, intervalo_inferior, intervalo_superior, expresion)
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.clf()
        #print("Tiempo de ejecución: ", tm.time() - start)
        # Devolver la imagen
        image = (b'--frame\r\n'
                b'Content-Type: image/png\r\n\r\n' + buffer.getvalue() + b'\r\n')
        return True
    except Exception as e:
        print(e)
        return False

if __name__ == '__main__':
    expresion = sys.argv[1]
    create_graph(expresion, float(sys.argv[2]), float(sys.argv[3]))