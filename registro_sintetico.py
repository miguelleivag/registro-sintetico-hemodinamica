#!/usr/bin/env python3
"""Genera un registro sintetico de hemodinamica: casos 100 % inventados.

Para que sirve
--------------
Practicar el analisis de datos con IA (tarea 10 de «La Guia de los 10 Minutos»)
sin tocar un solo dato de paciente real. El fichero se comporta como un registro
de verdad: le faltan datos, tiene errores de tecleo y esconde una trampa de
interpretacion. Las siete trampas estan puestas a proposito y documentadas en el
README; `--solucionario` imprime la hoja de respuestas.

Uso
---
    python registro_sintetico.py                      # 200 casos -> registro_sintetico.csv
    python registro_sintetico.py --n 80               # version corta
    python registro_sintetico.py --solucionario       # ademas, la hoja de respuestas
    python registro_sintetico.py --separador ";"      # si tu Excel parte mal las columnas

Solo biblioteca estandar: no hay que instalar nada. Python 3.9 o superior.

Miguel Leiva - iadeguardia.com - Licencia MIT
"""

import argparse
import csv
import random
import statistics
import sys
from collections import Counter

# Sin acentos en cabeceras ni en valores: se abre igual en cualquier Excel,
# en cualquier idioma del sistema, sin sustos de codificacion.
CABECERA = ["id_caso", "fecha", "edad", "sexo", "indicacion", "acceso",
            "n_stents", "contraste_ml", "fluoroscopia_min", "complicacion"]

INDICACIONES = ["SCACEST", "SCASEST", "angina estable", "electiva"]
PESOS_INDICACION = [18, 32, 25, 25]

# Cuantos stents se implantan segun la indicacion. Este es el mecanismo real
# del que cuelga todo lo demas: es la trampa 7 (causa vs. asociacion).
PESOS_STENTS = {
    "SCACEST":        [2, 55, 33, 10],   # casi siempre se implanta
    "SCASEST":        [15, 50, 27, 8],
    "angina estable": [45, 40, 12, 3],   # muchas son solo diagnosticas
    "electiva":       [40, 43, 14, 3],
}

COMPLICACIONES = ["hematoma", "sangrado mayor", "nefropatia por contraste"]
PESOS_COMPLICACION = [70, 10, 20]
# Riesgo por via de acceso: la femoral sangra mas. Es cierto en la vida real y
# es cierto en este generador; lo que la demo ensena es que con unos 30 casos
# femorales ese porcentaje no se sostiene solo.
RIESGO = {"radial": 0.04, "femoral": 0.12}

# Actividad creciente a lo largo del ano: da sentido a la grafica de evolucion
# mensual y hace que la trampa de las fechas mezcladas tenga consecuencias.
PESOS_MES = [5, 5, 6, 7, 7, 8, 8, 9, 10, 11, 12, 12]


def genera_filas(n, semilla):
    """Devuelve las filas del registro, trampas incluidas."""
    rnd = random.Random(semilla)

    # Las trampas se colocan en posiciones proporcionales a n: con --n 80 o con
    # --n 500 el fichero sigue teniendo las siete.
    pos_edad_imposible = max(1, int(n * 0.185))
    pos_contraste_cero = max(1, int(n * 0.060))
    pos_duplicado = max(1, int(n * 0.300))
    pos_acceso_sucio = {max(1, int(n * f)): v for f, v in
                        ((0.040, "Radial"), (0.115, "radial "),
                         (0.220, "RADIAL"), (0.305, "Femoral"))}

    filas = []
    for i in range(1, n + 1):
        indicacion = rnd.choices(INDICACIONES, weights=PESOS_INDICACION)[0]
        n_stents = rnd.choices([0, 1, 2, 3], weights=PESOS_STENTS[indicacion])[0]
        acceso = rnd.choices(["radial", "femoral"], weights=[85, 15])[0]

        edad = rnd.randint(38, 92)
        sexo = rnd.choices(["M", "F"], weights=[62, 38])[0]

        # El contraste depende del numero de stents, NO de la indicacion.
        # La asociacion «la angina estable gasta menos contraste» que vera la IA
        # es real, pero esta explicada entera por los stents.
        contraste = max(35, round(rnd.gauss(70 + 38 * n_stents, 22)))
        fluoroscopia = round(max(2.0, rnd.gauss(6 + 4.5 * n_stents, 3.0)), 1)

        if rnd.random() < RIESGO[acceso]:
            complicacion = rnd.choices(COMPLICACIONES, weights=PESOS_COMPLICACION)[0]
        else:
            complicacion = "ninguna"

        mes = rnd.choices(range(1, 13), weights=PESOS_MES)[0]
        dia = rnd.randint(1, 28)
        # Trampa 3: dos formatos de fecha conviviendo, como en cualquier registro
        # rellenado por varias personas. Los dias llegan solo hasta 28 a proposito:
        # una fecha como 05/03/2026 es ambigua y una lectura ingenua la invierte.
        fecha = f"{dia:02d}/{mes:02d}/2026" if i % 3 == 0 else f"2026-{mes:02d}-{dia:02d}"

        # Trampa 2: ausentes. Nadie apunta el contraste el dia que se complica.
        if rnd.random() < 0.06:
            contraste = ""
        if rnd.random() < 0.03:
            fluoroscopia = ""

        # Trampa 1: valor imposible que salta a la vista.
        if i == pos_edad_imposible:
            edad = 340
        # Trampa 4: valor imposible que NO salta a la vista. Cero mililitros de
        # contraste con dos stents implantados no existe; para verlo hace falta
        # saber de que va el procedimiento. La IA suele pasarlo por alto.
        if i == pos_contraste_cero:
            n_stents, contraste = 2, 0
        # Trampa 5: la misma categoria escrita de cuatro maneras.
        if i in pos_acceso_sucio:
            acceso = pos_acceso_sucio[i]

        filas.append([f"CASO-{i:03d}", fecha, edad, sexo, indicacion, acceso,
                      n_stents, contraste, fluoroscopia, complicacion])

        # Trampa 6: un caso grabado dos veces. Las filas no son los casos.
        if i == pos_duplicado:
            filas.append(list(filas[-1]))

    return filas


def normaliza(valor):
    return str(valor).strip().lower()


def solucionario(filas):
    """La hoja de respuestas: lo que la IA deberia decir, y los numeros exactos
    contra los que comprobarlo. Se calcula sobre el fichero recien generado, no
    de memoria: si cambias --n o --semilla, estas cifras cambian con el."""
    col = {nombre: i for i, nombre in enumerate(CABECERA)}
    ids = [f[col["id_caso"]] for f in filas]
    duplicados = [k for k, v in Counter(ids).items() if v > 1]

    ausentes_contraste = sum(1 for f in filas if f[col["contraste_ml"]] == "")
    ausentes_fluoro = sum(1 for f in filas if f[col["fluoroscopia_min"]] == "")

    accesos_crudos = Counter(f[col["acceso"]] for f in filas)
    accesos_limpios = Counter(normaliza(f[col["acceso"]]) for f in filas)
    # Dos denominadores posibles, y esa es justo la gracia: con el duplicado
    # dentro o fuera, el porcentaje no es el mismo.
    vistos = set()
    unicas = [f for f in filas if not (f[col["id_caso"]] in vistos
                                       or vistos.add(f[col["id_caso"]]))]
    accesos_unicos = Counter(normaliza(f[col["acceso"]]) for f in unicas)
    pct_radial_filas = 100 * accesos_limpios["radial"] / len(filas)
    pct_radial_casos = 100 * accesos_unicos["radial"] / len(unicas)

    iso = sum(1 for f in filas if "-" in f[col["fecha"]])
    edades_imposibles = [f[col["id_caso"]] for f in filas if int(f[col["edad"]]) > 110]
    contraste_cero = [f[col["id_caso"]] for f in filas
                      if f[col["contraste_ml"]] != ""
                      and int(f[col["contraste_ml"]]) == 0
                      and int(f[col["n_stents"]]) > 0]

    def mediana_contraste(filtro):
        vals = [int(f[col["contraste_ml"]]) for f in filas
                if f[col["contraste_ml"]] != "" and int(f[col["contraste_ml"]]) > 0
                and filtro(f)]
        return statistics.median(vals) if vals else None

    print("\n" + "=" * 70)
    print("HOJA DE RESPUESTAS  ·  no la enseñes en la demo hasta el final")
    print("=" * 70)

    print("\n[1] LOS NUMEROS DE PARTIDA (comprobacion 1 de la tarea 10)")
    print(f"    Filas de datos escritas .......... {len(filas)}")
    print(f"    Casos unicos (id_caso) ........... {len(set(ids))}")
    print(f"    Ids repetidos .................... {', '.join(duplicados) or 'ninguno'}")
    print("    -> Si la IA dice que ha analizado tantos CASOS como FILAS, ya se ha equivocado.")

    print("\n[2] AUSENTES")
    print(f"    contraste_ml vacios .............. {ausentes_contraste} de {len(filas)}"
          f" ({100 * ausentes_contraste / len(filas):.1f} %)")
    print(f"    fluoroscopia_min vacios .......... {ausentes_fluoro}")
    print("    -> Pregunta obligada: ¿los ha descartado? ¿lo ha dicho? ¿con que criterio?")

    print("\n[3] VALORES IMPOSIBLES")
    print(f"    Edad > 110 ....................... {', '.join(edades_imposibles) or 'ninguno'}"
          "   (este lo caza casi siempre)")
    print(f"    Contraste 0 ml con stents ........ {', '.join(contraste_cero) or 'ninguno'}"
          "   (este casi nunca: hace falta saber de hemodinamica)")

    print("\n[4] CATEGORIAS SUCIAS (comprobacion 3: ¿suman el total?)")
    for valor, cuenta in sorted(accesos_crudos.items(), key=lambda x: -x[1]):
        print(f"    tal cual: {valor!r:>12} -> {cuenta}")
    print(f"    Ya normalizado: radial {accesos_limpios['radial']}, "
          f"femoral {accesos_limpios['femoral']}")
    print(f"    % radial sobre las {len(filas)} filas ..... {pct_radial_filas:.1f} %")
    print(f"    % radial sobre los {len(unicas)} casos .... {pct_radial_casos:.1f} %"
          "   <- este es el bueno")
    print("    -> Si tu recalculo a mano no coincide con el de la IA, mirad primero el")
    print("       denominador: casi siempre es eso, no el numerador.")

    print("\n[5] FECHAS")
    print(f"    Formato aaaa-mm-dd ............... {iso}")
    print(f"    Formato dd/mm/aaaa ............... {len(filas) - iso}")
    print("    -> Si la grafica mensual sale rara, es esto: los dias llegan solo hasta 28")
    print("       y una lectura a la americana convierte 05/03 en 3 de mayo.")

    print("\n[6] PARA RECALCULAR A MANO (comprobacion 2: dos cifras de distinto tipo)")
    print(f"    Mediana de contraste_ml .......... {mediana_contraste(lambda f: True):.0f} ml"
          "   (excluyendo vacios y el 0 imposible)")
    for acc in ("radial", "femoral"):
        n_acc = accesos_unicos[acc]          # sobre casos, sin el duplicado
        comp = sum(1 for f in unicas if normaliza(f[col["acceso"]]) == acc
                   and f[col["complicacion"]] != "ninguna")
        print(f"    Complicaciones en {acc:<8} ....... {comp} de {n_acc}"
              f" ({100 * comp / n_acc:.1f} %)")
    print("    -> La diferencia entre vias existe en el generador, pero con esos")
    print("       denominadores no se sostiene sola. Pide el numero de eventos, no el %.")

    print("\n[7] LA TRAMPA DE INTERPRETACION (causa vs. asociacion)")
    print("    Mediana de contraste por indicacion:")
    for ind in INDICACIONES:
        m = mediana_contraste(lambda f, ind=ind: f[col["indicacion"]] == ind)
        print(f"        {ind:<16} {m:.0f} ml")
    print("    Mediana de contraste por numero de stents:")
    for k in (0, 1, 2, 3):
        m = mediana_contraste(lambda f, k=k: int(f[col["n_stents"]]) == k)
        if m is not None:
            print(f"        {k} stents         {m:.0f} ml")
    print("    -> La IA dira «la angina estable gasta menos contraste». Es verdad y es")
    print("       enganoso: aqui el contraste depende SOLO de los stents, y la angina")
    print("       estable lleva menos stents. La indicacion no causa nada. Ese es el")
    print("       hallazgo que hay que saber devolver.\n")


def main():
    p = argparse.ArgumentParser(
        description="Genera un registro sintetico de hemodinamica (datos 100 % inventados).")
    p.add_argument("--n", type=int, default=200,
                   help="numero de casos (minimo 40; por defecto 200)")
    p.add_argument("--semilla", type=int, default=2026,
                   help="semilla aleatoria: la misma semilla da el mismo fichero (por defecto 2026)")
    p.add_argument("--salida", default="registro_sintetico.csv", help="fichero CSV de salida")
    p.add_argument("--separador", default=",",
                   help="separador de columnas; usa ';' si tu Excel lo mete todo en una columna")
    p.add_argument("--solucionario", action="store_true",
                   help="imprime la hoja de respuestas: las trampas y las cifras exactas")
    args = p.parse_args()

    if args.n < 40:
        p.error("--n minimo 40: por debajo no caben las siete trampas separadas.")

    filas = genera_filas(args.n, args.semilla)

    with open(args.salida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=args.separador)
        w.writerow(CABECERA)
        w.writerows(filas)

    print(f"{args.salida}: {args.n} casos ficticios, {len(filas)} filas de datos "
          f"(hay un duplicado a proposito). Semilla {args.semilla}.")
    print("Datos 100 % inventados: ni un paciente real, ni uno real «modificado».")

    if args.solucionario:
        solucionario(filas)


if __name__ == "__main__":
    try:                       # para que los acentos salgan bien en la consola de Windows
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    main()
