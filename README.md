# Karel Reader

## Versión web (sin Python)

Abre [`index.html`](index.html) en un navegador moderno para jugar a Karel Club. La versión web está hecha con HTML, CSS y JavaScript, no necesita instalación ni servidor, e incluye seis niveles, bloques de programación, bucles, condiciones y ejecución paso a paso.

**Versión 2.1 — jerarquía visual mejorada, movimientos ilimitados y deshacer/rehacer.**

**Karel Reader** es un juego educativo de programación visual construido completamente con Python. El jugador organiza bloques para guiar a Karel, recoger y colocar marcadores, evitar muros y completar objetivos.

Toda la interfaz y todos los mensajes para el jugador están en español.

## Características

- Editor visual con bloques arrastrables.
- Guías de jerarquía, colores por profundidad e indicadores `PROGRAMA`, `NIVEL 1`, `NIVEL 2`, etc.
- Ruta estructural del bloque seleccionado y conteo de bloques interiores.
- Controles para expandir o contraer todas las estructuras.
- Historial de 50 cambios con **Deshacer** y **Rehacer**.
- Acciones, bucles por cantidad, bucles `Mientras` y decisiones `Si / si no`.
- Ramas visibles: **SI SE CUMPLE** y **SI NO SE CUMPLE**.
- Condiciones basadas en el estado actual del mundo de Karel.
- Ejecución animada, pausa, paso a paso, detención y velocidad ajustable.
- Resaltado de la condición, la rama elegida y la instrucción en ejecución.
- Cuatro niveles con muros, objetivos y marcadores, sin límite de movimientos.
- Motor separado de la interfaz y cubierto por pruebas unitarias.
- Sin paquetes de terceros: sólo usa la biblioteca estándar de Python.
- No usa `eval`, `exec` ni ejecuta código arbitrario del usuario.

## Requisitos

- Python 3.10 o superior.
- `tkinter`, incluido normalmente con Python.

En algunas distribuciones Linux, Tk debe instalarse por separado:

```bash
sudo apt install python3-tk
```

## Ejecutar el juego

Desde la carpeta del proyecto:

```bash
python3 main.py
```

En Windows también puedes usar:

```powershell
py main.py
```

## Cómo jugar

1. Selecciona un nivel.
2. Lee el objetivo situado encima del tablero.
3. Añade acciones, bucles o decisiones desde la paleta.
4. Organiza el programa arrastrando los bloques.
5. Pulsa **INICIAR EJECUCIÓN**.
6. Observa la instrucción y la rama resaltadas.
7. Usa **Pausar**, **Paso** o **Detener** cuando lo necesites.

## Arrastrar y soltar

- Arrastra un bloque arriba o abajo para cambiar su orden.
- Suelta sobre **CUERPO DEL BUCLE** para introducirlo en `Repetir` o `Mientras`.
- Suelta sobre **SI SE CUMPLE** para introducirlo en la rama verdadera.
- Suelta sobre **SI NO SE CUMPLE** para introducirlo en la rama alternativa.
- Arrastra un bloque anidado hacia el margen izquierdo para sacarlo al nivel exterior.
- No es posible introducir un bloque dentro de sí mismo ni dentro de sus descendientes.
- Los botones **Subir**, **Bajar** y **Sacar** siguen disponibles como alternativa al ratón.

## Comprender bloques dentro de bloques

- Cada bloque indica si está en `PROGRAMA`, `NIVEL 1`, `NIVEL 2` y así sucesivamente.
- Los colores cambian gradualmente según la profundidad.
- Las guías `├─`, `└─` y `│` muestran la relación entre contenedores, ramas e instrucciones.
- Los contenedores indican cuántos bloques interiores incluyen, incluso al estar contraídos.
- La barra **Ubicación** muestra una ruta como `Programa › Mientras › CUERPO › Si › SI SE CUMPLE › Avanzar`.
- Usa **Expandir** o **Contraer** para controlar estructuras grandes.

## Movimientos ilimitados

Los niveles no tienen un máximo de movimientos. El contador **Acciones ejecutadas** es informativo y puede crecer sin detener el programa. Continúan vigentes los errores propios del mundo, como intentar atravesar un muro o recoger un marcador inexistente.

## Bloques disponibles

| Bloque | Función |
|---|---|
| Avanzar | Mueve a Karel una casilla hacia delante. |
| Girar a la izquierda | Cambia su orientación 90° a la izquierda. |
| Girar a la derecha | Cambia su orientación 90° a la derecha. |
| Recoger marcador | Guarda en la mochila un marcador de la casilla. |
| Colocar marcador | Deja en la casilla un marcador de la mochila. |
| Repetir N veces | Ejecuta su cuerpo una cantidad específica de veces. |
| Mientras | Reevalúa una condición y repite el cuerpo mientras sea verdadera. |
| Si / si no | Ejecuta una sola rama según el resultado de la condición. |

Haz doble clic en `Repetir` para cambiar la cantidad. Haz doble clic en `Mientras` o `Si / si no` para cambiar su condición.

## Condiciones

Karel puede comprobar:

- Si el frente, la izquierda o la derecha están libres o bloqueados.
- Si hay o no hay un marcador en la casilla actual.
- Si hay marcadores en la mochila o si está vacía.
- Si mira o no mira al norte, sur, este u oeste.

### Funcionamiento de `Mientras`

La condición se evalúa antes de cada iteración. Si es verdadera, se ejecuta todo el cuerpo y se vuelve a comprobar. Si es falsa, el programa continúa con el siguiente bloque.

Un `Mientras` cuyo cuerpo no contenga acciones, o que no cambie el mundo mientras la condición siga siendo verdadera, se detiene con una explicación para evitar que la interfaz quede atrapada. Esta protección no impone un límite de movimientos.

### Funcionamiento de `Si / si no`

La condición se evalúa una sola vez al llegar al bloque:

- Si es verdadera, se ejecuta **SI SE CUMPLE**.
- Si es falsa, se ejecuta **SI NO SE CUMPLE**.

La rama **SI NO SE CUMPLE** puede dejarse vacía.

Estas reglas siguen los capítulos de Stanford Karel sobre `while` y condicionales:

- https://compedu.stanford.edu/karel-reader/docs/python/en/chapter6.html
- https://compedu.stanford.edu/karel-reader/docs/python/en/chapter7.html

## Atajos

| Atajo | Acción |
|---|---|
| `Ctrl` + `Enter` | Iniciar la ejecución. |
| `Ctrl` + `Z` | Deshacer el último cambio del programa. |
| `Ctrl` + `Y` | Rehacer un cambio. |
| `Ctrl` + `Mayús` + `Z` | Rehacer un cambio. |
| `F10` | Ejecutar un paso. |
| `Esc` | Detener la ejecución. |
| `Supr` / `Delete` | Eliminar el bloque seleccionado. |

## Ejecutar las pruebas

```bash
python3 -m unittest -v test_karel_reader.py
```

Las pruebas no necesitan una pantalla gráfica. Validan movimientos ilimitados, giros, muros, marcadores, las 18 condiciones, ambas ramas, `Mientras`, repeticiones, profundidad, rutas, conteos, historial, movimiento de bloques, protección contra ciclos estructurales y los cuatro niveles.

## Estructura

```text
karel_reader/
├── main.py                 # Motor, intérprete e interfaz gráfica
├── test_karel_reader.py    # Pruebas unitarias
└── README.md               # Instalación y uso
```

## Diseño técnico

- `MundoKarel` mantiene el estado y evalúa condiciones sin efectos secundarios.
- `Bloque` representa acciones o estructuras con cuerpo y rama alternativa.
- `Interprete` recorre el árbol mediante un generador para permitir animación y pausa.
- `mover_bloque_en_modelo` realiza movimientos seguros y evita ciclos.
- `HistorialPrograma` conserva copias seguras para deshacer y rehacer.
- `KarelReaderApp` sincroniza el árbol arrastrable, el mundo y los controles.

## Licencia

Puedes usar y adaptar este proyecto con fines educativos.
