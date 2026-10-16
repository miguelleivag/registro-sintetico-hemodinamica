# Registro sintético de hemodinámica

**Un registro clínico falso que se comporta como uno de verdad.** 200 casos inventados con los defectos que tiene cualquier hoja de cálculo real: datos que faltan, un error de tecleo, fechas en dos formatos, la misma palabra escrita de cuatro maneras y una trampa de interpretación. Sirve para practicar el análisis de datos con IA **sin tocar un solo dato de paciente**.

Es el material de la **tarea 10** de [«La Guía de los 10 Minutos»](https://iadeguardia.com) y de la demo «El registro que habla».

---

## Por qué existe

La tarea que más miedo da delegar en una IA es el análisis de datos, y con razón: un análisis tiene mucha más superficie de error que un texto y **falla en silencio**. Un número mal no se lee como un número mal; se lee como un número.

Así que no se aprende con el registro propio. Se aprende con este, que tiene las trampas puestas a propósito y una hoja de respuestas para comprobar si las has cazado. Cuando el procedimiento te salga solo, entonces sí: tu registro, sin identificadores, y en una herramienta con contrato de tratamiento de datos.

> **Este fichero es 🟢 (sintético): vale cualquier herramienta.**
> **Tu registro real no lo es.** Un registro clínico despojado de identificadores sigue siendo 🟡 como mínimo — herramienta que no entrene con lo que escribes y en la que puedas borrar la conversación — y si lleva iniciales, fechas de nacimiento o números de historia, es 🟠 y solo va en sistemas autorizados por tu organización. La escalera completa está en la Guía.

## Cómo se usa

Necesitas Python 3.9 o superior. No hay que instalar nada más: solo biblioteca estándar.

```bash
python registro_sintetico.py                  # 200 casos -> registro_sintetico.csv
python registro_sintetico.py --n 80           # versión corta, si la herramienta va lenta
python registro_sintetico.py --semilla 7      # otro fichero distinto, igual de reproducible
python registro_sintetico.py --separador ";"  # si tu Excel lo mete todo en una columna
python registro_sintetico.py --solucionario   # la hoja de respuestas (ver abajo)
```

**Y si no quieres tocar Python**, en este repositorio está el CSV ya generado: [`registro_sintetico.csv`](registro_sintetico.csv). Descárgalo y sube ese.

La misma semilla da siempre exactamente el mismo fichero. Por eso una demo grabada con `--semilla 2026` se puede reproducir en casa, cifra a cifra.

## Qué contiene

| Columna | Qué es |
|---|---|
| `id_caso` | Identificador ficticio, `CASO-001`… |
| `fecha` | Fecha del procedimiento, año 2026 |
| `edad` | Años |
| `sexo` | `M` / `F` |
| `indicacion` | `SCACEST`, `SCASEST`, `angina estable`, `electiva` |
| `acceso` | `radial` / `femoral` |
| `n_stents` | 0–3 |
| `contraste_ml` | Mililitros de contraste |
| `fluoroscopia_min` | Minutos de escopia |
| `complicacion` | `ninguna`, `hematoma`, `sangrado mayor`, `nefropatia por contraste` |

Sin acentos en cabeceras ni valores, a propósito: así se abre igual en cualquier Excel y en cualquier idioma del sistema.

## El prompt

```
Analiza este CSV: (a) perfil de los datos y valores ausentes; (b) 4 gráficas:
evolución mensual de la actividad, distribución por indicación, contraste por
número de stents y complicaciones por vía de acceso; (c) 3 hallazgos con su
magnitud exacta; (d) 3 limitaciones de estos datos; (e) valores imposibles o
incoherentes entre columnas, indicando el número de fila — búscalos
activamente, no supongas que el fichero está limpio. Ejecuta código: no estimes
a ojo.
```

Hace falta una IA que **ejecute código** de verdad (análisis de datos), no una que estime a ojo.

## Las siete trampas

Están puestas a propósito. No mires esta lista hasta que hayas hecho el análisis una vez.

<details>
<summary><b>Ábreme cuando ya tengas tus resultados</b></summary>

1. **Una edad imposible.** Un caso con 340 años. Es el error de tecleo clásico y casi cualquier IA lo caza. Sirve de calentamiento.
2. **Valores ausentes.** Alrededor del 6 % de `contraste_ml` y un 3 % de `fluoroscopia_min` están vacíos. La pregunta no es si los descarta: es **si te lo dice** y con qué criterio.
3. **Dos formatos de fecha.** Un tercio de las filas va en `dd/mm/aaaa` y el resto en `aaaa-mm-dd`. Los días no pasan del 28 a propósito: `05/03/2026` es ambigua, y una lectura a la americana la convierte en 3 de mayo. Si la gráfica mensual sale rara, es esto.
4. **Un valor imposible que no salta a la vista.** Un caso con **0 ml de contraste y dos stents implantados**. Eso no existe. Ninguna IA lo marca, porque para verlo hay que saber de qué va el procedimiento. Es la trampa que demuestra por qué el criterio clínico no es delegable.
5. **Categorías sucias.** `acceso` aparece como `radial`, `Radial`, `RADIAL`, `radial ` (con espacio) y `Femoral`. Si se cuentan tal cual, las categorías no suman el total.
6. **Un caso duplicado.** Una fila grabada dos veces con el mismo `id_caso`. El fichero tiene **201 filas y 200 casos**: si la IA dice haber analizado tantos casos como filas, ya se ha equivocado, y todos los porcentajes llevan el denominador mal.
7. **Causa y asociación.** La IA dirá que *«la angina estable gasta menos contraste»*. Es verdad y es engañoso: en este generador el contraste depende **solo** del número de stents, y la angina estable lleva menos stents. La indicación no causa nada. Este es el hallazgo que hay que saber devolver — y el que más se parece a lo que pasa con datos reales.

</details>

## La hoja de respuestas

`--solucionario` imprime, calculadas sobre el fichero que acabas de generar: el recuento de filas y de casos, los ausentes, los ids de las trampas, los valores crudos de cada categoría, el porcentaje correcto de acceso radial (con los dos denominadores posibles), la mediana de contraste y las complicaciones por vía **con su número de eventos**, no solo el porcentaje.

Es lo que necesitas para las cuatro comprobaciones de la tarea 10:

1. **¿Cuántas filas dice haber analizado?** ¿Coincide? ¿Descartó filas y lo dijo?
2. **Recalcula dos cifras a mano**, de distinto tipo: una proporción y una mediana. Los errores de media van solos; los de denominador arrastran a todo.
3. **Lee las gráficas contra su propio dato:** ejes rotulados, categorías que suman el total, ninguna barra que contradiga los hallazgos.
4. **Pídele el código** y échale un ojo aunque no programes: se ve a simple vista si filtró algo que no le pediste.

## Aviso

Datos **100 % inventados**, generados por código: ni un paciente real, ni uno real «modificado un poco». Las distribuciones son verosímiles pero no representan la práctica de ningún centro. No sirven para investigación, ni para estimar nada, ni para citarlos: sirven para aprender a comprobar.

## Licencia

MIT — ver [LICENSE](LICENSE). Úsalo, cámbialo y enséñalo con quien quieras, también en clase.

---

Miguel Leiva · Cardiólogo intervencionista · [iadeguardia.com](https://iadeguardia.com) · newsletter *IA de guardia*
