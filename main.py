#!/usr/bin/env python3
"""Karel Reader: juego visual de programación por bloques, hecho sólo con Python."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generator, Iterable, Optional
import copy
import sys

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
except ImportError:  # Permite probar el motor en entornos sin interfaz gráfica.
    tk = None  # type: ignore[assignment]
    messagebox = simpledialog = ttk = None  # type: ignore[assignment]


class Direccion(Enum):
    NORTE = (0, -1)
    ESTE = (1, 0)
    SUR = (0, 1)
    OESTE = (-1, 0)

    @property
    def delta(self) -> tuple[int, int]:
        return self.value

    def izquierda(self) -> "Direccion":
        orden = [Direccion.NORTE, Direccion.OESTE, Direccion.SUR, Direccion.ESTE]
        return orden[(orden.index(self) + 1) % 4]

    def derecha(self) -> "Direccion":
        orden = [Direccion.NORTE, Direccion.ESTE, Direccion.SUR, Direccion.OESTE]
        return orden[(orden.index(self) + 1) % 4]

    def opuesta(self) -> "Direccion":
        return self.derecha().derecha()


class CondicionKarel(Enum):
    FRENTE_LIBRE = "frente_libre"
    FRENTE_BLOQUEADO = "frente_bloqueado"
    IZQUIERDA_LIBRE = "izquierda_libre"
    IZQUIERDA_BLOQUEADA = "izquierda_bloqueada"
    DERECHA_LIBRE = "derecha_libre"
    DERECHA_BLOQUEADA = "derecha_bloqueada"
    MARCADOR_PRESENTE = "marcador_presente"
    SIN_MARCADOR = "sin_marcador"
    MARCADORES_EN_MOCHILA = "marcadores_en_mochila"
    MOCHILA_VACIA = "mochila_vacia"
    MIRA_NORTE = "mira_norte"
    NO_MIRA_NORTE = "no_mira_norte"
    MIRA_SUR = "mira_sur"
    NO_MIRA_SUR = "no_mira_sur"
    MIRA_ESTE = "mira_este"
    NO_MIRA_ESTE = "no_mira_este"
    MIRA_OESTE = "mira_oeste"
    NO_MIRA_OESTE = "no_mira_oeste"


NOMBRES_CONDICIONES: dict[CondicionKarel, str] = {
    CondicionKarel.FRENTE_LIBRE: "hay camino al frente",
    CondicionKarel.FRENTE_BLOQUEADO: "el frente está bloqueado",
    CondicionKarel.IZQUIERDA_LIBRE: "hay camino a la izquierda",
    CondicionKarel.IZQUIERDA_BLOQUEADA: "la izquierda está bloqueada",
    CondicionKarel.DERECHA_LIBRE: "hay camino a la derecha",
    CondicionKarel.DERECHA_BLOQUEADA: "la derecha está bloqueada",
    CondicionKarel.MARCADOR_PRESENTE: "hay un marcador aquí",
    CondicionKarel.SIN_MARCADOR: "no hay marcador aquí",
    CondicionKarel.MARCADORES_EN_MOCHILA: "hay marcadores en la mochila",
    CondicionKarel.MOCHILA_VACIA: "la mochila está vacía",
    CondicionKarel.MIRA_NORTE: "Karel mira al norte",
    CondicionKarel.NO_MIRA_NORTE: "Karel no mira al norte",
    CondicionKarel.MIRA_SUR: "Karel mira al sur",
    CondicionKarel.NO_MIRA_SUR: "Karel no mira al sur",
    CondicionKarel.MIRA_ESTE: "Karel mira al este",
    CondicionKarel.NO_MIRA_ESTE: "Karel no mira al este",
    CondicionKarel.MIRA_OESTE: "Karel mira al oeste",
    CondicionKarel.NO_MIRA_OESTE: "Karel no mira al oeste",
}


@dataclass
class EstadoKarel:
    x: int
    y: int
    direccion: Direccion
    mochila: int = 0


@dataclass
class Nivel:
    nombre: str
    ancho: int
    alto: int
    inicio: EstadoKarel
    marcadores: dict[tuple[int, int], int]
    objetivos: dict[tuple[int, int], int]
    meta: tuple[int, int]
    muros: set[tuple[int, int, Direccion]]
    descripcion: str


def agregar_muro(
    muros: set[tuple[int, int, Direccion]],
    x: int,
    y: int,
    direccion: Direccion,
) -> None:
    """Añade un muro en ambos lados de una frontera entre celdas."""
    muros.add((x, y, direccion))
    dx, dy = direccion.delta
    opuesta = {
        Direccion.NORTE: Direccion.SUR,
        Direccion.SUR: Direccion.NORTE,
        Direccion.ESTE: Direccion.OESTE,
        Direccion.OESTE: Direccion.ESTE,
    }[direccion]
    muros.add((x + dx, y + dy, opuesta))


def crear_niveles() -> list[Nivel]:
    niveles: list[Nivel] = []

    niveles.append(
        Nivel(
            nombre="1. Primeros pasos",
            ancho=8,
            alto=6,
            inicio=EstadoKarel(1, 3, Direccion.ESTE),
            marcadores={},
            objetivos={},
            meta=(6, 5),
            muros=set(),
            descripcion="Lleva a Karel hasta la estrella. Prueba «Avanzar» y «Repetir».",
        )
    )

    muros_entrega: set[tuple[int, int, Direccion]] = set()
    agregar_muro(muros_entrega, 4, 3, Direccion.ESTE)
    agregar_muro(muros_entrega, 4, 2, Direccion.ESTE)
    niveles.append(
        Nivel(
            nombre="2. Recoge y entrega",
            ancho=8,
            alto=6,
            inicio=EstadoKarel(1, 4, Direccion.ESTE),
            marcadores={(3, 4): 1},
            objetivos={(6, 1): 1},
            meta=(6, 1),
            muros=muros_entrega,
            descripcion="Recoge el marcador azul, evita el muro, déjalo sobre el objetivo y termina en la estrella.",
        )
    )

    muros_laberinto: set[tuple[int, int, Direccion]] = set()
    # Corredor escalonado: obliga a girar y favorece el uso de condiciones.
    for y in range(0, 6):
        if y != 4:
            agregar_muro(muros_laberinto, 2, y, Direccion.ESTE)
    for x in range(2, 7):
        if x != 5:
            agregar_muro(muros_laberinto, x, 3, Direccion.SUR)
    agregar_muro(muros_laberinto, 5, 1, Direccion.ESTE)
    niveles.append(
        Nivel(
            nombre="3. El laberinto",
            ancho=9,
            alto=7,
            inicio=EstadoKarel(1, 5, Direccion.NORTE),
            marcadores={(1, 2): 1},
            objetivos={},
            meta=(7, 1),
            muros=muros_laberinto,
            descripcion="Llega a la estrella. Usa «Si hay camino al frente» para tomar decisiones seguras.",
        )
    )

    muros_patron: set[tuple[int, int, Direccion]] = set()
    agregar_muro(muros_patron, 3, 1, Direccion.SUR)
    agregar_muro(muros_patron, 3, 2, Direccion.ESTE)
    niveles.append(
        Nivel(
            nombre="4. Siembra el jardín",
            ancho=8,
            alto=6,
            inicio=EstadoKarel(1, 4, Direccion.ESTE, mochila=4),
            marcadores={},
            objetivos={(2, 4): 1, (3, 4): 1, (4, 4): 1, (5, 4): 1},
            meta=(6, 4),
            muros=muros_patron,
            descripcion="Coloca un marcador en cada objetivo verde y después llega a la estrella.",
        )
    )

        # Nivel 4: Laberinto en zigzag
    muros_laberinto_4: set[tuple[int, int, Direccion]] = set()
    for y in range(0, 7, 2):
        agregar_muro(muros_laberinto_4, 3, y, Direccion.ESTE)
    for x in range(3, 8, 2):
        agregar_muro(muros_laberinto_4, x, 4, Direccion.SUR)
    niveles.append(
        Nivel(
            nombre="4. Laberinto en zigzag",
            ancho=10,
            alto=8,
            inicio=EstadoKarel(1, 6, Direccion.NORTE),
            marcadores={(2, 2): 1},
            objetivos={},
            meta=(8, 1),
            muros=muros_laberinto_4,
            descripcion="Sigue el camino en zigzag para llegar a la meta.",
        )
    )

    # Nivel 5: Laberinto con múltiples caminos
    muros_laberinto_5: set[tuple[int, int, Direccion]] = set()
    for y in range(1, 6):
        agregar_muro(muros_laberinto_5, 4, y, Direccion.ESTE)
    for x in range(2, 7):
        if x != 5:
            agregar_muro(muros_laberinto_5, x, 2, Direccion.SUR)
    agregar_muro(muros_laberinto_5, 6, 4, Direccion.ESTE)
    niveles.append(
        Nivel(
            nombre="5. Laberinto con múltiples caminos",
            ancho=10,
            alto=7,
            inicio=EstadoKarel(1, 5, Direccion.NORTE),
            marcadores={(3, 3): 1},
            objetivos={},
            meta=(7, 2),
            muros=muros_laberinto_5,
            descripcion="Encuentra el camino correcto entre múltiples opciones.",
        )
    )


    return niveles


class ErrorKarel(Exception):
    """Error de ejecución comprensible para el jugador."""


class MundoKarel:
    def __init__(self, nivel: Nivel):
        self.cargar_nivel(nivel)

    def cargar_nivel(self, nivel: Nivel) -> None:
        self.nivel = copy.deepcopy(nivel)
        self.karel = copy.deepcopy(nivel.inicio)
        self.marcadores = dict(nivel.marcadores)
        self.acciones = 0

    def dentro(self, x: int, y: int) -> bool:
        return 0 <= x < self.nivel.ancho and 0 <= y < self.nivel.alto

    def camino_libre_en(self, direccion: Direccion) -> bool:
        x, y = self.karel.x, self.karel.y
        if (x, y, direccion) in self.nivel.muros:
            return False
        dx, dy = direccion.delta
        return self.dentro(x + dx, y + dy)

    def camino_libre(self) -> bool:
        return self.camino_libre_en(self.karel.direccion)

    def camino_libre_a_la_izquierda(self) -> bool:
        return self.camino_libre_en(self.karel.direccion.izquierda())

    def camino_libre_a_la_derecha(self) -> bool:
        return self.camino_libre_en(self.karel.direccion.derecha())

    def marcador_presente(self) -> bool:
        return self.marcadores.get((self.karel.x, self.karel.y), 0) > 0

    def evaluar_condicion(self, condicion: CondicionKarel) -> bool:
        evaluadores: dict[CondicionKarel, Callable[[], bool]] = {
            CondicionKarel.FRENTE_LIBRE: self.camino_libre,
            CondicionKarel.FRENTE_BLOQUEADO: lambda: not self.camino_libre(),
            CondicionKarel.IZQUIERDA_LIBRE: self.camino_libre_a_la_izquierda,
            CondicionKarel.IZQUIERDA_BLOQUEADA: lambda: not self.camino_libre_a_la_izquierda(),
            CondicionKarel.DERECHA_LIBRE: self.camino_libre_a_la_derecha,
            CondicionKarel.DERECHA_BLOQUEADA: lambda: not self.camino_libre_a_la_derecha(),
            CondicionKarel.MARCADOR_PRESENTE: self.marcador_presente,
            CondicionKarel.SIN_MARCADOR: lambda: not self.marcador_presente(),
            CondicionKarel.MARCADORES_EN_MOCHILA: lambda: self.karel.mochila > 0,
            CondicionKarel.MOCHILA_VACIA: lambda: self.karel.mochila == 0,
            CondicionKarel.MIRA_NORTE: lambda: self.karel.direccion == Direccion.NORTE,
            CondicionKarel.NO_MIRA_NORTE: lambda: self.karel.direccion != Direccion.NORTE,
            CondicionKarel.MIRA_SUR: lambda: self.karel.direccion == Direccion.SUR,
            CondicionKarel.NO_MIRA_SUR: lambda: self.karel.direccion != Direccion.SUR,
            CondicionKarel.MIRA_ESTE: lambda: self.karel.direccion == Direccion.ESTE,
            CondicionKarel.NO_MIRA_ESTE: lambda: self.karel.direccion != Direccion.ESTE,
            CondicionKarel.MIRA_OESTE: lambda: self.karel.direccion == Direccion.OESTE,
            CondicionKarel.NO_MIRA_OESTE: lambda: self.karel.direccion != Direccion.OESTE,
        }
        return evaluadores[condicion]()

    def _registrar_accion(self) -> None:
        self.acciones += 1

    def avanzar(self) -> None:
        self._registrar_accion()
        if not self.camino_libre():
            raise ErrorKarel("Karel no puede avanzar: hay un muro o termina el tablero.")
        dx, dy = self.karel.direccion.delta
        self.karel.x += dx
        self.karel.y += dy

    def girar_izquierda(self) -> None:
        self._registrar_accion()
        self.karel.direccion = self.karel.direccion.izquierda()

    def girar_derecha(self) -> None:
        self._registrar_accion()
        self.karel.direccion = self.karel.direccion.derecha()

    def recoger(self) -> None:
        self._registrar_accion()
        posicion = (self.karel.x, self.karel.y)
        cantidad = self.marcadores.get(posicion, 0)
        if cantidad <= 0:
            raise ErrorKarel("No hay ningún marcador para recoger en esta casilla.")
        if cantidad == 1:
            self.marcadores.pop(posicion)
        else:
            self.marcadores[posicion] = cantidad - 1
        self.karel.mochila += 1

    def colocar(self) -> None:
        self._registrar_accion()
        if self.karel.mochila <= 0:
            raise ErrorKarel("La mochila de Karel está vacía.")
        posicion = (self.karel.x, self.karel.y)
        self.marcadores[posicion] = self.marcadores.get(posicion, 0) + 1
        self.karel.mochila -= 1

    def completado(self) -> bool:
        if (self.karel.x, self.karel.y) != self.nivel.meta:
            return False
        return all(
            self.marcadores.get(posicion, 0) >= cantidad
            for posicion, cantidad in self.nivel.objetivos.items()
        )


class TipoBloque(Enum):
    AVANZAR = "avanzar"
    GIRAR_IZQUIERDA = "girar_izquierda"
    GIRAR_DERECHA = "girar_derecha"
    RECOGER = "recoger"
    COLOCAR = "colocar"
    REPETIR = "repetir"
    MIENTRAS = "mientras"
    SI = "si"


@dataclass
class Bloque:
    tipo: TipoBloque
    repeticiones: int = 2
    hijos: list["Bloque"] = field(default_factory=list)
    alternativa: list["Bloque"] = field(default_factory=list)
    condicion: CondicionKarel = CondicionKarel.FRENTE_LIBRE
    identificador: str = ""

    @property
    def es_contenedor(self) -> bool:
        return self.tipo in {
            TipoBloque.REPETIR,
            TipoBloque.MIENTRAS,
            TipoBloque.SI,
        }


def buscar_bloque(
    bloques: Iterable[Bloque], identificador: str
) -> Optional[Bloque]:
    for bloque in bloques:
        if bloque.identificador == identificador:
            return bloque
        encontrado = buscar_bloque(bloque.hijos, identificador)
        if encontrado:
            return encontrado
        encontrado = buscar_bloque(bloque.alternativa, identificador)
        if encontrado:
            return encontrado
    return None


def buscar_lista_padre(
    bloques: list[Bloque], identificador: str
) -> Optional[list[Bloque]]:
    for bloque in bloques:
        if bloque.identificador == identificador:
            return bloques
        encontrada = buscar_lista_padre(bloque.hijos, identificador)
        if encontrada is not None:
            return encontrada
        encontrada = buscar_lista_padre(bloque.alternativa, identificador)
        if encontrada is not None:
            return encontrada
    return None


def lista_dentro_de_bloque(bloque: Bloque, destino: list[Bloque]) -> bool:
    if destino is bloque.hijos or destino is bloque.alternativa:
        return True
    return any(lista_dentro_de_bloque(hijo, destino) for hijo in bloque.hijos) or any(
        lista_dentro_de_bloque(hijo, destino) for hijo in bloque.alternativa
    )


def mover_bloque_en_modelo(
    programa: list[Bloque],
    identificador: str,
    destino: list[Bloque],
    indice: int,
) -> bool:
    """Mueve un bloque sin permitir ciclos estructurales."""
    bloque = buscar_bloque(programa, identificador)
    origen = buscar_lista_padre(programa, identificador)
    if bloque is None or origen is None or lista_dentro_de_bloque(bloque, destino):
        return False
    indice_origen = origen.index(bloque)
    if origen is destino and indice > indice_origen:
        indice -= 1
    origen.remove(bloque)
    destino.insert(max(0, min(indice, len(destino))), bloque)
    return True


def contar_bloques_interiores(bloque: Bloque) -> int:
    return sum(
        1 + contar_bloques_interiores(hijo)
        for hijo in [*bloque.hijos, *bloque.alternativa]
    )


def profundidad_bloque(
    programa: list[Bloque], identificador: str, profundidad: int = 0
) -> Optional[int]:
    for bloque in programa:
        if bloque.identificador == identificador:
            return profundidad
        hallada = profundidad_bloque(bloque.hijos, identificador, profundidad + 1)
        if hallada is not None:
            return hallada
        hallada = profundidad_bloque(bloque.alternativa, identificador, profundidad + 1)
        if hallada is not None:
            return hallada
    return None


def ruta_bloque(
    programa: list[Bloque], identificador: str
) -> Optional[list[tuple[Bloque, str]]]:
    """Devuelve contenedores, ramas y bloque final para la barra de ubicación."""
    for bloque in programa:
        if bloque.identificador == identificador:
            return [(bloque, "")]
        hallada = ruta_bloque(bloque.hijos, identificador)
        if hallada is not None:
            rama = "SI SE CUMPLE" if bloque.tipo == TipoBloque.SI else "CUERPO"
            return [(bloque, rama), *hallada]
        hallada = ruta_bloque(bloque.alternativa, identificador)
        if hallada is not None:
            return [(bloque, "SI NO SE CUMPLE"), *hallada]
    return None


class HistorialPrograma:
    def __init__(self, maximo: int = 50):
        self.maximo = maximo
        self.deshacer_estados: list[list[Bloque]] = []
        self.rehacer_estados: list[list[Bloque]] = []

    def registrar(self, programa: list[Bloque]) -> None:
        self.deshacer_estados.append(copy.deepcopy(programa))
        if len(self.deshacer_estados) > self.maximo:
            self.deshacer_estados.pop(0)
        self.rehacer_estados.clear()

    def registrar_estado(self, estado: list[Bloque]) -> None:
        self.deshacer_estados.append(copy.deepcopy(estado))
        if len(self.deshacer_estados) > self.maximo:
            self.deshacer_estados.pop(0)
        self.rehacer_estados.clear()

    def deshacer(self, programa: list[Bloque]) -> Optional[list[Bloque]]:
        if not self.deshacer_estados:
            return None
        self.rehacer_estados.append(copy.deepcopy(programa))
        return self.deshacer_estados.pop()

    def rehacer(self, programa: list[Bloque]) -> Optional[list[Bloque]]:
        if not self.rehacer_estados:
            return None
        self.deshacer_estados.append(copy.deepcopy(programa))
        return self.rehacer_estados.pop()


NOMBRES_BLOQUES: dict[TipoBloque, str] = {
    TipoBloque.AVANZAR: "Avanzar",
    TipoBloque.GIRAR_IZQUIERDA: "Girar a la izquierda",
    TipoBloque.GIRAR_DERECHA: "Girar a la derecha",
    TipoBloque.RECOGER: "Recoger marcador",
    TipoBloque.COLOCAR: "Colocar marcador",
    TipoBloque.REPETIR: "Repetir N veces",
    TipoBloque.MIENTRAS: "Mientras se cumpla una condición",
    TipoBloque.SI: "Si / si no",
}

COLORES_BLOQUES: dict[TipoBloque, str] = {
    TipoBloque.AVANZAR: "#2563eb",
    TipoBloque.GIRAR_IZQUIERDA: "#7c3aed",
    TipoBloque.GIRAR_DERECHA: "#7c3aed",
    TipoBloque.RECOGER: "#0891b2",
    TipoBloque.COLOCAR: "#0891b2",
    TipoBloque.REPETIR: "#d97706",
    TipoBloque.MIENTRAS: "#c2410c",
    TipoBloque.SI: "#059669",
}


@dataclass
class PasoPrograma:
    bloque: Bloque
    accion: Callable[[], None]
    mensaje: str = ""
    rama: str = ""


class Interprete:
    """Convierte un árbol de bloques en pasos ejecutables, sin eval ni exec."""

    def __init__(self, mundo: MundoKarel):
        self.mundo = mundo

    def _contiene_accion(self, bloques: Iterable[Bloque]) -> bool:
        for bloque in bloques:
            if bloque.tipo in {
                TipoBloque.AVANZAR,
                TipoBloque.GIRAR_IZQUIERDA,
                TipoBloque.GIRAR_DERECHA,
                TipoBloque.RECOGER,
                TipoBloque.COLOCAR,
            }:
                return True
            if self._contiene_accion(bloque.hijos):
                return True
            if self._contiene_accion(bloque.alternativa):
                return True
        return False

    def _firma_del_mundo(self) -> tuple[object, ...]:
        karel = self.mundo.karel
        return (
            karel.x,
            karel.y,
            karel.direccion,
            karel.mochila,
            tuple(sorted((x, y, cantidad) for (x, y), cantidad in self.mundo.marcadores.items())),
        )

    def ejecutar(self, bloques: Iterable[Bloque]) -> Generator[PasoPrograma, None, None]:
        for bloque in bloques:
            if bloque.tipo == TipoBloque.REPETIR:
                for _ in range(bloque.repeticiones):
                    yield from self.ejecutar(bloque.hijos)
            elif bloque.tipo == TipoBloque.MIENTRAS:
                while self.mundo.evaluar_condicion(bloque.condicion):
                    if not self._contiene_accion(bloque.hijos):
                        raise ErrorKarel(
                            "El bucle «Mientras» no puede avanzar porque su cuerpo no contiene acciones."
                        )
                    estado_antes = self._firma_del_mundo()
                    yield PasoPrograma(
                        bloque,
                        lambda: None,
                        f"La condición es verdadera: se ejecuta el cuerpo de «Mientras {NOMBRES_CONDICIONES[bloque.condicion]}».",
                        "cuerpo",
                    )
                    yield from self.ejecutar(bloque.hijos)
                    if (
                        self._firma_del_mundo() == estado_antes
                        and self.mundo.evaluar_condicion(bloque.condicion)
                    ):
                        raise ErrorKarel(
                            "El bucle «Mientras» no modifica el mundo y su condición sigue siendo verdadera."
                        )
                yield PasoPrograma(
                    bloque,
                    lambda: None,
                    f"La condición es falsa: termina «Mientras {NOMBRES_CONDICIONES[bloque.condicion]}».",
                    "fin",
                )
            elif bloque.tipo == TipoBloque.SI:
                resultado = self.mundo.evaluar_condicion(bloque.condicion)
                rama = "si" if resultado else "sino"
                mensaje = (
                    f"La condición es verdadera: se ejecuta «SI SE CUMPLE»."
                    if resultado
                    else "La condición es falsa: se ejecuta «SI NO SE CUMPLE»."
                )
                yield PasoPrograma(bloque, lambda: None, mensaje, rama)
                yield from self.ejecutar(bloque.hijos if resultado else bloque.alternativa)
            else:
                accion = {
                    TipoBloque.AVANZAR: self.mundo.avanzar,
                    TipoBloque.GIRAR_IZQUIERDA: self.mundo.girar_izquierda,
                    TipoBloque.GIRAR_DERECHA: self.mundo.girar_derecha,
                    TipoBloque.RECOGER: self.mundo.recoger,
                    TipoBloque.COLOCAR: self.mundo.colocar,
                }[bloque.tipo]
                yield PasoPrograma(bloque, accion, f"Ejecutando: {NOMBRES_BLOQUES[bloque.tipo]}")


if tk is not None:
    class KarelReaderApp(tk.Tk):
        FONDO = "#0f172a"
        PANEL = "#172033"
        PANEL_CLARO = "#1e293b"
        TEXTO = "#f8fafc"
        TEXTO_SUAVE = "#cbd5e1"
        ACENTO = "#38bdf8"
        EXITO = "#22c55e"
        ERROR = "#ef4444"

        def __init__(self) -> None:
            super().__init__()
            self.title("Karel Reader 2.1 — Programa, ejecuta y aprende")
            self.geometry("1280x790")
            self.minsize(1060, 680)
            self.configure(bg=self.FONDO)

            self.niveles = crear_niveles()
            self.indice_nivel = 0
            self.mundo = MundoKarel(self.niveles[0])
            self.programa: list[Bloque] = []
            self.contador_bloques = 0
            self.generador: Optional[Generator[PasoPrograma, None, None]] = None
            self.ejecutando = False
            self.pausado = False
            self.trabajo_pendiente: Optional[str] = None
            self.bloque_arrastrado: Optional[str] = None
            self.destino_arrastre: Optional[str] = None
            self.historial = HistorialPrograma(maximo=50)

            self._configurar_estilos()
            self._crear_interfaz()
            self._registrar_atajos()
            self._actualizar_nivel()

        def _configurar_estilos(self) -> None:
            estilo = ttk.Style(self)
            estilo.theme_use("clam")
            estilo.configure(
                "TCombobox",
                fieldbackground="#263449",
                background="#263449",
                foreground=self.TEXTO,
                arrowcolor=self.TEXTO,
            )
            estilo.configure(
                "Treeview",
                background="#101827",
                fieldbackground="#101827",
                foreground=self.TEXTO,
                rowheight=34,
                borderwidth=0,
                font=("Segoe UI", 10, "bold"),
            )
            estilo.map(
                "Treeview",
                background=[("selected", "#fde047")],
                foreground=[("selected", "#0f172a")],
            )
            estilo.configure(
                "Treeview.Heading",
                background="#263449",
                foreground=self.TEXTO,
                borderwidth=0,
            )

        def _crear_interfaz(self) -> None:
            encabezado = tk.Frame(self, bg=self.FONDO, padx=18, pady=12)
            encabezado.pack(fill="x")
            tk.Label(
                encabezado,
                text="KAREL READER",
                font=("Segoe UI", 22, "bold"),
                fg=self.ACENTO,
                bg=self.FONDO,
            ).pack(side="left")
            tk.Label(
                encabezado,
                text="  Aprende a programar guiando a Karel",
                font=("Segoe UI", 12),
                fg=self.TEXTO_SUAVE,
                bg=self.FONDO,
            ).pack(side="left", pady=(8, 0))

            self.etiqueta_estado = tk.Label(
                encabezado,
                text="Listo",
                font=("Segoe UI", 10, "bold"),
                fg=self.TEXTO,
                bg="#334155",
                padx=12,
                pady=6,
            )
            self.etiqueta_estado.pack(side="right")

            principal = tk.PanedWindow(
                self,
                orient="horizontal",
                bg=self.FONDO,
                sashwidth=6,
                bd=0,
            )
            principal.pack(fill="both", expand=True, padx=14, pady=(0, 14))

            panel_mundo = tk.Frame(principal, bg=self.PANEL, padx=14, pady=12)
            panel_programa = tk.Frame(principal, bg=self.PANEL, padx=14, pady=12)
            principal.add(panel_mundo, minsize=520, stretch="always")
            principal.add(panel_programa, minsize=460, stretch="always")

            self._crear_panel_mundo(panel_mundo)
            self._crear_panel_programa(panel_programa)

        def _crear_panel_mundo(self, padre: tk.Widget) -> None:
            barra_nivel = tk.Frame(padre, bg=self.PANEL)
            barra_nivel.pack(fill="x", pady=(0, 8))
            tk.Label(
                barra_nivel,
                text="Nivel:",
                font=("Segoe UI", 11, "bold"),
                fg=self.TEXTO,
                bg=self.PANEL,
            ).pack(side="left")
            self.selector_nivel = ttk.Combobox(
                barra_nivel,
                state="readonly",
                values=[nivel.nombre for nivel in self.niveles],
                width=26,
            )
            self.selector_nivel.current(0)
            self.selector_nivel.pack(side="left", padx=8)
            self.selector_nivel.bind("<<ComboboxSelected>>", self._seleccionar_nivel)
            self._boton(barra_nivel, "Reiniciar nivel", self.reiniciar_nivel, "#475569").pack(
                side="right"
            )

            self.etiqueta_objetivo = tk.Label(
                padre,
                text="",
                font=("Segoe UI", 10),
                fg=self.TEXTO_SUAVE,
                bg=self.PANEL,
                justify="left",
                wraplength=540,
                anchor="w",
            )
            self.etiqueta_objetivo.pack(fill="x", pady=(0, 10))

            self.canvas = tk.Canvas(
                padre,
                bg="#e2e8f0",
                bd=0,
                highlightthickness=0,
                width=580,
                height=500,
            )
            self.canvas.pack(fill="both", expand=True)
            self.canvas.bind("<Configure>", lambda _evento: self.dibujar_mundo())

            datos = tk.Frame(padre, bg=self.PANEL, pady=8)
            datos.pack(fill="x")
            self.etiqueta_mochila = tk.Label(
                datos,
                text="Mochila: 0",
                font=("Segoe UI", 10, "bold"),
                fg=self.TEXTO,
                bg=self.PANEL,
            )
            self.etiqueta_mochila.pack(side="left")
            self.etiqueta_acciones = tk.Label(
                datos,
                text="Acciones: 0",
                font=("Segoe UI", 10, "bold"),
                fg=self.TEXTO,
                bg=self.PANEL,
            )
            self.etiqueta_acciones.pack(side="right")

        def _crear_panel_programa(self, padre: tk.Widget) -> None:
            tk.Label(
                padre, text="1. Elige un bloque", font=("Segoe UI", 13, "bold"),
                fg=self.TEXTO, bg=self.PANEL, anchor="w",
            ).pack(fill="x")

            paleta = tk.Frame(padre, bg=self.PANEL)
            paleta.pack(fill="x", pady=(5, 7))
            categorias = [
                ("ACCIONES", [
                    TipoBloque.AVANZAR, TipoBloque.GIRAR_IZQUIERDA,
                    TipoBloque.GIRAR_DERECHA, TipoBloque.RECOGER, TipoBloque.COLOCAR,
                ]),
                ("BUCLES Y DECISIONES", [
                    TipoBloque.REPETIR, TipoBloque.MIENTRAS, TipoBloque.SI,
                ]),
            ]
            fila = 0
            for titulo, tipos in categorias:
                tk.Label(
                    paleta, text=titulo, font=("Segoe UI", 8, "bold"),
                    fg=self.TEXTO_SUAVE, bg=self.PANEL, anchor="w",
                ).grid(row=fila, column=0, columnspan=2, sticky="ew", padx=3, pady=(3, 1))
                fila += 1
                for indice, tipo in enumerate(tipos):
                    self._boton(
                        paleta, f"＋ {NOMBRES_BLOQUES[tipo]}",
                        lambda t=tipo: self.agregar_bloque(t), COLORES_BLOQUES[tipo],
                    ).grid(
                        row=fila + indice // 2, column=indice % 2,
                        sticky="ew", padx=3, pady=2,
                    )
                fila += (len(tipos) + 1) // 2
            paleta.grid_columnconfigure(0, weight=1)
            paleta.grid_columnconfigure(1, weight=1)

            tk.Label(
                padre, text="2. Construye tu programa", font=("Segoe UI", 13, "bold"),
                fg=self.TEXTO, bg=self.PANEL, anchor="w",
            ).pack(fill="x", pady=(3, 2))
            tk.Label(
                padre,
                text=("Arrastra para reordenar. Suelta sobre CUERPO, SI SE CUMPLE o "
                      "SI NO SE CUMPLE para anidar; arrastra a la izquierda para sacar."),
                font=("Segoe UI", 9), fg=self.TEXTO_SUAVE, bg=self.PANEL,
                justify="left", wraplength=470, anchor="w",
            ).pack(fill="x", pady=(0, 5))

            marco_arbol = tk.Frame(padre, bg="#101827")
            marco_arbol.pack(fill="both", expand=True)
            self.arbol = ttk.Treeview(marco_arbol, show="tree", selectmode="browse")
            barra = ttk.Scrollbar(marco_arbol, orient="vertical", command=self.arbol.yview)
            barra_horizontal = ttk.Scrollbar(
                marco_arbol, orient="horizontal", command=self.arbol.xview
            )
            self.arbol.configure(
                yscrollcommand=barra.set, xscrollcommand=barra_horizontal.set
            )
            barra_horizontal.pack(side="bottom", fill="x")
            barra.pack(side="right", fill="y")
            self.arbol.pack(side="left", fill="both", expand=True)
            self.arbol.bind("<Double-1>", self._editar_bloque)
            self.arbol.bind("<ButtonPress-1>", self._iniciar_arrastre, add="+")
            self.arbol.bind("<B1-Motion>", self._actualizar_arrastre)
            self.arbol.bind("<ButtonRelease-1>", self._finalizar_arrastre)
            self.arbol.bind("<<TreeviewSelect>>", self._actualizar_ruta_seleccion)

            for tipo, color in COLORES_BLOQUES.items():
                self.arbol.tag_configure(tipo.value, foreground="#ffffff", background=color)
            self.arbol.tag_configure("zona_cuerpo", foreground="#fed7aa", background="#431407")
            self.arbol.tag_configure("zona_si", foreground="#bbf7d0", background="#064e3b")
            self.arbol.tag_configure("zona_sino", foreground="#fecaca", background="#7f1d1d")
            self.arbol.tag_configure("activo", foreground="#0f172a", background="#fde047")
            self.arbol.tag_configure("activo_rama", foreground="#0f172a", background="#86efac")
            self.arbol.tag_configure("destino", foreground="#ffffff", background="#0284c7")
            colores_nivel = ["#172554", "#312e81", "#4c1d95", "#581c87", "#701a75"]
            for indice, color in enumerate(colores_nivel, start=1):
                self.arbol.tag_configure(
                    f"nivel_{indice}", foreground="#ffffff", background=color
                )

            self.etiqueta_ruta = tk.Label(
                padre,
                text="Ubicación: Programa",
                font=("Segoe UI", 9, "bold"),
                fg="#bae6fd",
                bg="#0c4a6e",
                justify="left",
                anchor="w",
                wraplength=470,
                padx=8,
                pady=6,
            )
            self.etiqueta_ruta.pack(fill="x", pady=(5, 0))

            historial_y_vista = tk.Frame(padre, bg=self.PANEL, pady=4)
            historial_y_vista.pack(fill="x")
            self._boton(historial_y_vista, "↶ Deshacer", self.deshacer, "#334155").pack(side="left", padx=2)
            self._boton(historial_y_vista, "↷ Rehacer", self.rehacer, "#334155").pack(side="left", padx=2)
            self._boton(historial_y_vista, "⊟ Contraer", self.contraer_todo, "#0f766e").pack(side="right", padx=2)
            self._boton(historial_y_vista, "⊞ Expandir", self.expandir_todo, "#0f766e").pack(side="right", padx=2)

            herramientas = tk.Frame(padre, bg=self.PANEL, pady=3)
            herramientas.pack(fill="x")
            self._boton(herramientas, "↑ Subir", self.subir_bloque, "#475569").pack(side="left", padx=2)
            self._boton(herramientas, "↓ Bajar", self.bajar_bloque, "#475569").pack(side="left", padx=2)
            self._boton(herramientas, "← Sacar", self.sacar_bloque, "#475569").pack(side="left", padx=2)
            self._boton(herramientas, "Eliminar", self.eliminar_bloque, "#b91c1c").pack(side="right", padx=2)
            self._boton(herramientas, "Limpiar", self.limpiar_programa, "#7f1d1d").pack(side="right", padx=2)

            tk.Label(
                padre, text="3. Ejecuta y observa", font=("Segoe UI", 13, "bold"),
                fg=self.TEXTO, bg=self.PANEL, anchor="w",
            ).pack(fill="x", pady=(3, 3))
            self.boton_iniciar = self._boton(
                padre, "▶ INICIAR EJECUCIÓN", self.ejecutar_programa, "#15803d"
            )
            self.boton_iniciar.configure(font=("Segoe UI", 11, "bold"), pady=9)
            self.boton_iniciar.pack(fill="x", pady=(0, 4))

            controles = tk.Frame(padre, bg=self.PANEL)
            controles.pack(fill="x")
            self.boton_pausa = self._boton(controles, "⏸ Pausar", self.alternar_pausa, "#a16207")
            self.boton_pausa.pack(side="left", padx=2)
            self._boton(controles, "Paso", self.ejecutar_paso, "#0369a1").pack(side="left", padx=2)
            self._boton(controles, "■ Detener", self.detener_ejecucion, "#b91c1c").pack(side="left", padx=2)

            velocidad = tk.Frame(padre, bg=self.PANEL, pady=5)
            velocidad.pack(fill="x")
            tk.Label(
                velocidad,
                text="Velocidad:",
                font=("Segoe UI", 9, "bold"),
                fg=self.TEXTO_SUAVE,
                bg=self.PANEL,
            ).pack(side="left")
            self.valor_velocidad = tk.IntVar(value=500)
            tk.Scale(
                velocidad,
                from_=1000,
                to=100,
                resolution=100,
                orient="horizontal",
                variable=self.valor_velocidad,
                showvalue=False,
                bg=self.PANEL,
                fg=self.TEXTO,
                troughcolor="#334155",
                activebackground=self.ACENTO,
                highlightthickness=0,
            ).pack(side="left", fill="x", expand=True, padx=8)
            tk.Label(
                velocidad,
                text="lenta                         rápida",
                font=("Segoe UI", 8),
                fg=self.TEXTO_SUAVE,
                bg=self.PANEL,
            ).pack(side="right")

        def _boton(
            self,
            padre: tk.Widget,
            texto: str,
            comando: Callable[[], None],
            color: str,
        ) -> tk.Button:
            return tk.Button(
                padre,
                text=texto,
                command=comando,
                bg=color,
                fg="#ffffff",
                activebackground=color,
                activeforeground="#ffffff",
                relief="flat",
                cursor="hand2",
                padx=9,
                pady=7,
                font=("Segoe UI", 9, "bold"),
            )

        def _registrar_atajos(self) -> None:
            self.bind("<Control-Return>", lambda _e: self.ejecutar_programa())
            self.bind("<Control-z>", lambda _e: self.deshacer())
            self.bind("<Control-y>", lambda _e: self.rehacer())
            self.bind("<Control-Shift-Z>", lambda _e: self.rehacer())
            self.bind("<F10>", lambda _e: self.ejecutar_paso())
            self.bind("<Escape>", lambda _e: self.detener_ejecucion())
            self.bind("<Delete>", lambda _e: self.eliminar_bloque())

        def _seleccionar_nivel(self, _evento: object = None) -> None:
            self.indice_nivel = self.selector_nivel.current()
            self._actualizar_nivel()

        def _actualizar_nivel(self) -> None:
            self.detener_ejecucion(mensaje=False)
            self.mundo.cargar_nivel(self.niveles[self.indice_nivel])
            nivel = self.mundo.nivel
            self.etiqueta_objetivo.configure(text=f"Objetivo: {nivel.descripcion}")
            self._establecer_estado("Nivel preparado", self.ACENTO)
            self.dibujar_mundo()

        def reiniciar_nivel(self) -> None:
            self._actualizar_nivel()

        def _establecer_estado(self, texto: str, color: str) -> None:
            self.etiqueta_estado.configure(text=texto, bg=color)

        def dibujar_mundo(self) -> None:
            if not hasattr(self, "canvas"):
                return
            self.canvas.delete("all")
            ancho_canvas = max(self.canvas.winfo_width(), 400)
            alto_canvas = max(self.canvas.winfo_height(), 350)
            nivel = self.mundo.nivel
            margen = 28
            celda = min(
                (ancho_canvas - 2 * margen) / nivel.ancho,
                (alto_canvas - 2 * margen) / nivel.alto,
            )
            origen_x = (ancho_canvas - celda * nivel.ancho) / 2
            origen_y = (alto_canvas - celda * nivel.alto) / 2

            for y in range(nivel.alto):
                for x in range(nivel.ancho):
                    x1 = origen_x + x * celda
                    y1 = origen_y + y * celda
                    x2, y2 = x1 + celda, y1 + celda
                    relleno = "#f8fafc" if (x + y) % 2 == 0 else "#e8eef5"
                    if (x, y) in nivel.objetivos:
                        relleno = "#bbf7d0"
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill=relleno, outline="#cbd5e1", width=1
                    )

            mx, my = nivel.meta
            centro_meta = (
                origen_x + (mx + 0.5) * celda,
                origen_y + (my + 0.5) * celda,
            )
            self.canvas.create_text(
                *centro_meta,
                text="★",
                fill="#f59e0b",
                font=("Segoe UI Symbol", max(18, int(celda * 0.5)), "bold"),
            )

            for (x, y), cantidad in self.mundo.marcadores.items():
                cx = origen_x + (x + 0.5) * celda
                cy = origen_y + (y + 0.5) * celda
                radio = celda * 0.18
                self.canvas.create_oval(
                    cx - radio,
                    cy - radio,
                    cx + radio,
                    cy + radio,
                    fill="#0ea5e9",
                    outline="#075985",
                    width=2,
                )
                if cantidad > 1:
                    self.canvas.create_text(
                        cx,
                        cy,
                        text=str(cantidad),
                        fill="#ffffff",
                        font=("Segoe UI", max(9, int(celda * 0.18)), "bold"),
                    )

            grosor_muro = max(4, int(celda * 0.08))
            for x, y, direccion in nivel.muros:
                if not self.mundo.dentro(x, y):
                    continue
                x1 = origen_x + x * celda
                y1 = origen_y + y * celda
                x2, y2 = x1 + celda, y1 + celda
                puntos = {
                    Direccion.NORTE: (x1, y1, x2, y1),
                    Direccion.SUR: (x1, y2, x2, y2),
                    Direccion.OESTE: (x1, y1, x1, y2),
                    Direccion.ESTE: (x2, y1, x2, y2),
                }[direccion]
                self.canvas.create_line(*puntos, fill="#334155", width=grosor_muro)

            karel = self.mundo.karel
            cx = origen_x + (karel.x + 0.5) * celda
            cy = origen_y + (karel.y + 0.5) * celda
            radio = celda * 0.30
            dx, dy = karel.direccion.delta
            frente_x = cx + dx * radio
            frente_y = cy + dy * radio
            perp_x, perp_y = -dy, dx
            atras_x = cx - dx * radio * 0.72
            atras_y = cy - dy * radio * 0.72
            puntos = [
                frente_x,
                frente_y,
                atras_x + perp_x * radio * 0.72,
                atras_y + perp_y * radio * 0.72,
                atras_x - perp_x * radio * 0.72,
                atras_y - perp_y * radio * 0.72,
            ]
            self.canvas.create_polygon(
                puntos, fill="#ef4444", outline="#7f1d1d", width=2
            )
            self.canvas.create_text(
                cx,
                cy,
                text="K",
                fill="#ffffff",
                font=("Segoe UI", max(10, int(celda * 0.22)), "bold"),
            )
            self.etiqueta_mochila.configure(text=f"Mochila: {karel.mochila}")
            self.etiqueta_acciones.configure(
                text=f"Acciones ejecutadas: {self.mundo.acciones}"
            )

        def _nuevo_id(self) -> str:
            self.contador_bloques += 1
            return f"bloque_{self.contador_bloques}"

        def _elegir_condicion(
            self,
            titulo: str,
            actual: CondicionKarel = CondicionKarel.FRENTE_LIBRE,
        ) -> Optional[CondicionKarel]:
            dialogo = tk.Toplevel(self)
            dialogo.title(titulo)
            dialogo.configure(bg=self.PANEL)
            dialogo.resizable(False, False)
            dialogo.transient(self)
            dialogo.grab_set()
            resultado: list[Optional[CondicionKarel]] = [None]
            por_nombre = {nombre: condicion for condicion, nombre in NOMBRES_CONDICIONES.items()}
            variable = tk.StringVar(value=NOMBRES_CONDICIONES[actual])

            tk.Label(
                dialogo,
                text="Elige la condición que Karel evaluará:",
                font=("Segoe UI", 11, "bold"),
                fg=self.TEXTO,
                bg=self.PANEL,
                padx=18,
                pady=12,
            ).pack(fill="x")
            selector = ttk.Combobox(
                dialogo,
                state="readonly",
                textvariable=variable,
                values=list(por_nombre),
                width=38,
            )
            selector.pack(fill="x", padx=18, pady=(0, 14))
            selector.focus_set()

            botones = tk.Frame(dialogo, bg=self.PANEL, padx=15, pady=10)
            botones.pack(fill="x")

            def aceptar() -> None:
                resultado[0] = por_nombre[variable.get()]
                dialogo.destroy()

            self._boton(botones, "Cancelar", dialogo.destroy, "#475569").pack(side="right", padx=3)
            self._boton(botones, "Aceptar", aceptar, "#15803d").pack(side="right", padx=3)
            dialogo.bind("<Return>", lambda _evento: aceptar())
            dialogo.bind("<Escape>", lambda _evento: dialogo.destroy())
            self.wait_window(dialogo)
            return resultado[0]

        def agregar_bloque(self, tipo: TipoBloque) -> None:
            if self.ejecutando:
                self._establecer_estado("Detén la ejecución antes de editar", self.ERROR)
                return
            repeticiones = 2
            condicion = CondicionKarel.FRENTE_LIBRE
            if tipo == TipoBloque.REPETIR:
                valor = simpledialog.askinteger(
                    "Repetir una cantidad específica",
                    "¿Cuántas veces debe repetirse?",
                    initialvalue=2,
                    minvalue=1,
                    maxvalue=99,
                    parent=self,
                )
                if valor is None:
                    return
                repeticiones = valor
            elif tipo in {TipoBloque.MIENTRAS, TipoBloque.SI}:
                elegida = self._elegir_condicion(
                    "Condición del bucle" if tipo == TipoBloque.MIENTRAS else "Condición de la decisión"
                )
                if elegida is None:
                    return
                condicion = elegida

            bloque = Bloque(
                tipo=tipo,
                repeticiones=repeticiones,
                condicion=condicion,
                identificador=self._nuevo_id(),
            )
            self._guardar_para_deshacer()
            destino, indice = self._destino_para_agregar()
            destino.insert(indice, bloque)
            self._refrescar_arbol(bloque.identificador)
            self._establecer_estado("Bloque añadido; puedes arrastrarlo para moverlo", COLORES_BLOQUES[tipo])

        def _destino_para_agregar(self) -> tuple[list[Bloque], int]:
            seleccion = self.arbol.selection()
            if not seleccion:
                return self.programa, len(self.programa)
            item = seleccion[0]
            datos_zona = self._datos_zona(item)
            if datos_zona:
                lista = self._lista_de_zona(*datos_zona)
                return lista, len(lista)
            bloque = self._buscar_bloque(item)
            if bloque and bloque.es_contenedor:
                return bloque.hijos, len(bloque.hijos)
            lista = self._buscar_lista_padre(item)
            if lista is not None and bloque is not None:
                return lista, lista.index(bloque) + 1
            return self.programa, len(self.programa)

        def _id_zona(self, identificador: str, rama: str) -> str:
            return f"zona::{identificador}::{rama}"

        def _datos_zona(self, identificador: str) -> Optional[tuple[str, str]]:
            if not identificador.startswith("zona::"):
                return None
            partes = identificador.split("::", 2)
            return (partes[1], partes[2]) if len(partes) == 3 else None

        def _lista_de_zona(self, identificador: str, rama: str) -> list[Bloque]:
            bloque = self._buscar_bloque(identificador)
            if bloque is None:
                return self.programa
            return bloque.alternativa if rama == "sino" else bloque.hijos

        def _refrescar_arbol(self, seleccionar: Optional[str] = None) -> None:
            for item in self.arbol.get_children(""):
                self.arbol.delete(item)
            self._insertar_bloques_en_arbol(self.programa, "", 0)
            if seleccionar and self.arbol.exists(seleccionar):
                self.arbol.selection_set(seleccionar)
                self.arbol.focus(seleccionar)
                self.arbol.see(seleccionar)
            self._actualizar_ruta_seleccion()

        def _insertar_bloques_en_arbol(
            self, bloques: Iterable[Bloque], padre: str, profundidad: int
        ) -> None:
            for bloque in bloques:
                nivel = max(1, min(profundidad, 5))
                prefijo = "PROGRAMA" if profundidad == 0 else f"NIVEL {profundidad}"
                self.arbol.insert(
                    padre,
                    "end",
                    iid=bloque.identificador,
                    text=f"  {prefijo}  │  {self._texto_bloque(bloque)}",
                    open=True,
                    tags=(bloque.tipo.value,) if profundidad == 0 else (f"nivel_{nivel}",),
                )
                if bloque.tipo in {TipoBloque.REPETIR, TipoBloque.MIENTRAS}:
                    zona = self._id_zona(bloque.identificador, "cuerpo")
                    self.arbol.insert(
                        bloque.identificador,
                        "end",
                        iid=zona,
                        text=f"  └─ CUERPO DEL BUCLE  ·  {len(bloque.hijos)} bloque(s)",
                        open=True,
                        tags=("zona_cuerpo",),
                    )
                    self._insertar_bloques_en_arbol(bloque.hijos, zona, profundidad + 1)
                elif bloque.tipo == TipoBloque.SI:
                    zona_si = self._id_zona(bloque.identificador, "si")
                    zona_sino = self._id_zona(bloque.identificador, "sino")
                    self.arbol.insert(
                        bloque.identificador,
                        "end",
                        iid=zona_si,
                        text=f"  ├─ ✓ SI SE CUMPLE  ·  {len(bloque.hijos)} bloque(s)",
                        open=True,
                        tags=("zona_si",),
                    )
                    self._insertar_bloques_en_arbol(bloque.hijos, zona_si, profundidad + 1)
                    self.arbol.insert(
                        bloque.identificador,
                        "end",
                        iid=zona_sino,
                        text=f"  └─ ✗ SI NO SE CUMPLE  ·  {len(bloque.alternativa)} bloque(s)",
                        open=True,
                        tags=("zona_sino",),
                    )
                    self._insertar_bloques_en_arbol(
                        bloque.alternativa, zona_sino, profundidad + 1
                    )

        def _texto_bloque(self, bloque: Bloque) -> str:
            if bloque.tipo == TipoBloque.REPETIR:
                return (
                    f"🔁 Repetir {bloque.repeticiones} veces"
                    f"  —  {contar_bloques_interiores(bloque)} bloque(s) interior(es)"
                )
            if bloque.tipo == TipoBloque.MIENTRAS:
                return (
                    f"⟳ Mientras {NOMBRES_CONDICIONES[bloque.condicion]}"
                    f"  —  {contar_bloques_interiores(bloque)} bloque(s) interior(es)"
                )
            if bloque.tipo == TipoBloque.SI:
                return (
                    f"◆ Si {NOMBRES_CONDICIONES[bloque.condicion]} / si no"
                    f"  —  {contar_bloques_interiores(bloque)} bloque(s) interior(es)"
                )
            return NOMBRES_BLOQUES[bloque.tipo]

        def _buscar_bloque(self, identificador: str) -> Optional[Bloque]:
            return buscar_bloque(self.programa, identificador)

        def _buscar_lista_padre(self, identificador: str) -> Optional[list[Bloque]]:
            return buscar_lista_padre(self.programa, identificador)

        def _buscar_dueno_de_lista(
            self,
            destino: list[Bloque],
            bloques: Optional[list[Bloque]] = None,
        ) -> Optional[tuple[Bloque, list[Bloque], str]]:
            lista = self.programa if bloques is None else bloques
            for bloque in lista:
                if destino is bloque.hijos:
                    return bloque, lista, "hijos"
                if destino is bloque.alternativa:
                    return bloque, lista, "alternativa"
                hallado = self._buscar_dueno_de_lista(destino, bloque.hijos)
                if hallado:
                    return hallado
                hallado = self._buscar_dueno_de_lista(destino, bloque.alternativa)
                if hallado:
                    return hallado
            return None

        def _guardar_para_deshacer(self) -> None:
            self.historial.registrar(self.programa)

        def _registrar_estado_anterior(self, estado: list[Bloque]) -> None:
            self.historial.registrar_estado(estado)

        def deshacer(self) -> None:
            if self.ejecutando:
                self._establecer_estado("Detén la ejecución antes de deshacer", self.ERROR)
                return
            programa_anterior = self.historial.deshacer(self.programa)
            if programa_anterior is None:
                self._establecer_estado("No hay cambios para deshacer", "#475569")
                return
            self.programa = programa_anterior
            self._refrescar_arbol()
            self._establecer_estado("Cambio deshecho", "#334155")

        def rehacer(self) -> None:
            if self.ejecutando:
                self._establecer_estado("Detén la ejecución antes de rehacer", self.ERROR)
                return
            programa_siguiente = self.historial.rehacer(self.programa)
            if programa_siguiente is None:
                self._establecer_estado("No hay cambios para rehacer", "#475569")
                return
            self.programa = programa_siguiente
            self._refrescar_arbol()
            self._establecer_estado("Cambio rehecho", "#334155")

        def expandir_todo(self) -> None:
            for item in self._todos_los_items(""):
                self.arbol.item(item, open=True)
            self._establecer_estado("Todas las estructuras están expandidas", "#0f766e")

        def contraer_todo(self) -> None:
            for item in self._todos_los_items(""):
                if self.arbol.get_children(item):
                    self.arbol.item(item, open=False)
            self._establecer_estado(
                "Estructuras contraídas; el resumen indica cuántos bloques contienen",
                "#0f766e",
            )

        def _actualizar_ruta_seleccion(self, _evento: object = None) -> None:
            if not hasattr(self, "etiqueta_ruta"):
                return
            seleccion = self.arbol.selection()
            if not seleccion:
                self.etiqueta_ruta.configure(text="Ubicación: Programa")
                return
            item = seleccion[0]
            zona = self._datos_zona(item)
            identificador = zona[0] if zona else item
            ruta = ruta_bloque(self.programa, identificador)
            if ruta is None:
                self.etiqueta_ruta.configure(text="Ubicación: Programa")
                return
            partes = ["Programa"]
            for indice, (bloque, rama) in enumerate(ruta):
                partes.append(self._texto_bloque(bloque).split("  —  ")[0])
                if indice < len(ruta) - 1 and rama:
                    partes.append(rama)
            if zona:
                partes.append(
                    {"cuerpo": "CUERPO", "si": "SI SE CUMPLE", "sino": "SI NO SE CUMPLE"}[zona[1]]
                )
            profundidad = profundidad_bloque(self.programa, identificador) or 0
            self.etiqueta_ruta.configure(
                text=(
                    "Ubicación: " + " › ".join(partes)
                    + f"\nEste bloque está dentro de {profundidad} estructura(s)."
                )
            )

        def _editar_bloque(self, _evento: object = None) -> None:
            seleccion = self.arbol.selection()
            if not seleccion or self.ejecutando or self._datos_zona(seleccion[0]):
                return
            bloque = self._buscar_bloque(seleccion[0])
            if bloque is None:
                return
            if bloque.tipo == TipoBloque.REPETIR:
                valor = simpledialog.askinteger(
                    "Editar repetición",
                    "Nuevo número de repeticiones:",
                    initialvalue=bloque.repeticiones,
                    minvalue=1,
                    maxvalue=99,
                    parent=self,
                )
                if valor is not None:
                    self._guardar_para_deshacer()
                    bloque.repeticiones = valor
                    self._refrescar_arbol(bloque.identificador)
            elif bloque.tipo in {TipoBloque.MIENTRAS, TipoBloque.SI}:
                elegida = self._elegir_condicion("Editar condición", bloque.condicion)
                if elegida is not None:
                    self._guardar_para_deshacer()
                    bloque.condicion = elegida
                    self._refrescar_arbol(bloque.identificador)

        def eliminar_bloque(self) -> None:
            if self.ejecutando:
                return
            seleccion = self.arbol.selection()
            if not seleccion or self._datos_zona(seleccion[0]):
                self._establecer_estado("Selecciona un bloque para eliminar", self.ERROR)
                return
            identificador = seleccion[0]
            lista = self._buscar_lista_padre(identificador)
            bloque = self._buscar_bloque(identificador)
            if lista is not None and bloque is not None:
                self._guardar_para_deshacer()
                lista.remove(bloque)
                self._refrescar_arbol()
                self._establecer_estado("Bloque eliminado", "#b91c1c")

        def limpiar_programa(self) -> None:
            if self.ejecutando or not self.programa:
                return
            if messagebox.askyesno(
                "Limpiar programa", "¿Quieres eliminar todos los bloques?", parent=self
            ):
                self._guardar_para_deshacer()
                self.programa.clear()
                self._refrescar_arbol()
                self._establecer_estado("Programa vacío", "#475569")

        def subir_bloque(self) -> None:
            self._mover_bloque(-1)

        def bajar_bloque(self) -> None:
            self._mover_bloque(1)

        def _mover_bloque(self, cambio: int) -> None:
            if self.ejecutando:
                return
            seleccion = self.arbol.selection()
            if not seleccion or self._datos_zona(seleccion[0]):
                return
            identificador = seleccion[0]
            lista = self._buscar_lista_padre(identificador)
            bloque = self._buscar_bloque(identificador)
            if lista is None or bloque is None:
                return
            actual = lista.index(bloque)
            nuevo = actual + cambio
            if 0 <= nuevo < len(lista):
                self._guardar_para_deshacer()
                lista[actual], lista[nuevo] = lista[nuevo], lista[actual]
                self._refrescar_arbol(identificador)

        def _sacar_bloque_id(self, identificador: str) -> bool:
            origen = self._buscar_lista_padre(identificador)
            if origen is None or origen is self.programa:
                return False
            dueno = self._buscar_dueno_de_lista(origen)
            if dueno is None:
                return False
            contenedor, lista_exterior, _rama = dueno
            return mover_bloque_en_modelo(
                self.programa,
                identificador,
                lista_exterior,
                lista_exterior.index(contenedor) + 1,
            )

        def sacar_bloque(self) -> None:
            if self.ejecutando:
                return
            seleccion = self.arbol.selection()
            if not seleccion or self._datos_zona(seleccion[0]):
                return
            identificador = seleccion[0]
            origen = self._buscar_lista_padre(identificador)
            if origen is not None and origen is not self.programa:
                self._guardar_para_deshacer()
            if self._sacar_bloque_id(identificador):
                self._refrescar_arbol(identificador)
                self._establecer_estado("Bloque movido al nivel exterior", "#475569")
            else:
                self._establecer_estado("El bloque ya está en el nivel principal", "#475569")

        def _iniciar_arrastre(self, evento: tk.Event) -> None:
            if self.ejecutando:
                return
            item = self.arbol.identify_row(evento.y)
            if item and not self._datos_zona(item) and self._buscar_bloque(item):
                self.bloque_arrastrado = item
                self.destino_arrastre = None
                self.arbol.selection_set(item)

        def _actualizar_arrastre(self, evento: tk.Event) -> None:
            if not self.bloque_arrastrado:
                return
            item = self.arbol.identify_row(evento.y)
            self._quitar_resaltado()
            if item and item != self.bloque_arrastrado:
                self.destino_arrastre = item
                self.arbol.item(item, tags=("destino",))
                if self._datos_zona(item):
                    self._establecer_estado("Suelta aquí para insertar en esta sección", "#0284c7")
                else:
                    self._establecer_estado("Suelta para cambiar el orden", "#0284c7")
            else:
                self.destino_arrastre = item or ""
            self.arbol.configure(cursor="fleur")

        def _finalizar_arrastre(self, evento: tk.Event) -> None:
            origen_id = self.bloque_arrastrado
            self.bloque_arrastrado = None
            self.arbol.configure(cursor="")
            if not origen_id:
                return
            caja_origen = self.arbol.bbox(origen_id)
            if caja_origen and evento.x < max(8, caja_origen[0] - 18):
                estado_anterior = copy.deepcopy(self.programa)
                movido = self._sacar_bloque_id(origen_id)
                if movido:
                    self._registrar_estado_anterior(estado_anterior)
                self._refrescar_arbol(origen_id)
                self._establecer_estado(
                    "Bloque sacado al nivel exterior" if movido else "El bloque ya está en el nivel principal",
                    "#475569",
                )
                return

            destino_id = self.arbol.identify_row(evento.y)
            if not destino_id:
                lista_destino, indice = self.programa, len(self.programa)
            else:
                zona = self._datos_zona(destino_id)
                if zona:
                    lista_destino = self._lista_de_zona(*zona)
                    indice = len(lista_destino)
                else:
                    bloque_destino = self._buscar_bloque(destino_id)
                    lista_destino = self._buscar_lista_padre(destino_id) or self.programa
                    if bloque_destino is None:
                        self._refrescar_arbol(origen_id)
                        return
                    caja = self.arbol.bbox(destino_id)
                    despues = bool(caja and evento.y >= caja[1] + caja[3] / 2)
                    indice = lista_destino.index(bloque_destino) + int(despues)

            estado_anterior = copy.deepcopy(self.programa)
            movido = mover_bloque_en_modelo(
                self.programa, origen_id, lista_destino, indice
            )
            if movido:
                self._registrar_estado_anterior(estado_anterior)
            self._refrescar_arbol(origen_id)
            self._establecer_estado(
                "Bloque movido" if movido else "Ese destino no es válido",
                "#0284c7" if movido else self.ERROR,
            )

        def _tag_base(self, item: str) -> str:
            zona = self._datos_zona(item)
            if zona:
                return {
                    "cuerpo": "zona_cuerpo",
                    "si": "zona_si",
                    "sino": "zona_sino",
                }[zona[1]]
            bloque = self._buscar_bloque(item)
            if bloque is None:
                return ""
            profundidad = profundidad_bloque(self.programa, item) or 0
            return (
                bloque.tipo.value
                if profundidad == 0
                else f"nivel_{max(1, min(profundidad, 5))}"
            )

        def _quitar_resaltado(self) -> None:
            for item in self._todos_los_items(""):
                tag = self._tag_base(item)
                if tag:
                    self.arbol.item(item, tags=(tag,))

        def _todos_los_items(self, padre: str) -> Generator[str, None, None]:
            for item in self.arbol.get_children(padre):
                yield item
                yield from self._todos_los_items(item)

        def _resaltar(self, bloque: Bloque, rama: str = "") -> None:
            self._quitar_resaltado()
            if self.arbol.exists(bloque.identificador):
                self.arbol.item(bloque.identificador, tags=("activo",))
                self.arbol.see(bloque.identificador)
                self.arbol.selection_set(bloque.identificador)
            if rama in {"cuerpo", "si", "sino"}:
                zona = self._id_zona(bloque.identificador, rama)
                if self.arbol.exists(zona):
                    self.arbol.item(zona, tags=("activo_rama",))
                    self.arbol.see(zona)

        def _crear_generador(self) -> bool:
            if not self.programa:
                self._establecer_estado("Añade al menos un bloque", self.ERROR)
                return False
            self.generador = Interprete(self.mundo).ejecutar(self.programa)
            return True

        def ejecutar_programa(self) -> None:
            if self.ejecutando and self.pausado:
                self.alternar_pausa()
                return
            if self.ejecutando:
                return
            if not self._crear_generador():
                return
            self.ejecutando = True
            self.pausado = False
            self.boton_iniciar.configure(state="disabled", text="● EJECUCIÓN EN CURSO")
            self.boton_pausa.configure(text="⏸ Pausar")
            self._establecer_estado("Ejecutando…", "#15803d")
            self._programar_siguiente(0)

        def ejecutar_paso(self) -> None:
            if self.ejecutando and not self.pausado:
                self._establecer_estado("Pausa antes de avanzar paso a paso", "#a16207")
                return
            if self.generador is None:
                if not self._crear_generador():
                    return
            self.ejecutando = True
            self.pausado = True
            self.boton_iniciar.configure(state="disabled", text="● EJECUCIÓN EN CURSO")
            self.boton_pausa.configure(text="▶ Continuar")
            self._ejecutar_siguiente(continuar=False)

        def alternar_pausa(self) -> None:
            if not self.ejecutando:
                self._establecer_estado("No hay un programa en ejecución", "#475569")
                return
            self.pausado = not self.pausado
            if self.pausado:
                if self.trabajo_pendiente:
                    self.after_cancel(self.trabajo_pendiente)
                    self.trabajo_pendiente = None
                self.boton_pausa.configure(text="▶ Continuar")
                self._establecer_estado("En pausa", "#a16207")
            else:
                self.boton_pausa.configure(text="⏸ Pausar")
                self._establecer_estado("Ejecutando…", "#15803d")
                self._programar_siguiente(0)

        def _programar_siguiente(self, demora: Optional[int] = None) -> None:
            if self.pausado or not self.ejecutando:
                return
            espera = self.valor_velocidad.get() if demora is None else demora
            self.trabajo_pendiente = self.after(
                espera, lambda: self._ejecutar_siguiente(continuar=True)
            )

        def _ejecutar_siguiente(self, continuar: bool) -> None:
            self.trabajo_pendiente = None
            if self.generador is None:
                return
            try:
                paso = next(self.generador)
                self._resaltar(paso.bloque, paso.rama)
                paso.accion()
                self.dibujar_mundo()
                self._establecer_estado(paso.mensaje, "#15803d")
                if self.mundo.completado():
                    self._nivel_completado()
                    return
                if continuar:
                    self._programar_siguiente()
            except StopIteration:
                self._finalizar_programa()
            except ErrorKarel as error:
                self.detener_ejecucion(mensaje=False)
                self.dibujar_mundo()
                self._establecer_estado(str(error), self.ERROR)
                messagebox.showerror("Karel se detuvo", str(error), parent=self)

        def _finalizar_programa(self) -> None:
            self.ejecutando = False
            self.pausado = False
            self.generador = None
            self.boton_iniciar.configure(state="normal", text="▶ INICIAR EJECUCIÓN")
            self.boton_pausa.configure(text="⏸ Pausar")
            self._quitar_resaltado()
            if self.mundo.completado():
                self._nivel_completado()
            else:
                self._establecer_estado(
                    "Programa terminado; el objetivo aún no está completo", "#a16207"
                )

        def _nivel_completado(self) -> None:
            self.detener_ejecucion(mensaje=False)
            self._establecer_estado("¡Nivel completado!", self.EXITO)
            ultimo = self.indice_nivel == len(self.niveles) - 1
            texto = (
                "¡Excelente! Completaste todos los niveles de Karel Reader."
                if ultimo
                else "¡Muy bien! Karel completó el objetivo. Puedes pasar al siguiente nivel."
            )
            messagebox.showinfo("¡Nivel completado!", texto, parent=self)

        def detener_ejecucion(self, mensaje: bool = True) -> None:
            if self.trabajo_pendiente:
                try:
                    self.after_cancel(self.trabajo_pendiente)
                except tk.TclError:
                    pass
            self.trabajo_pendiente = None
            self.ejecutando = False
            self.pausado = False
            self.generador = None
            if hasattr(self, "boton_iniciar"):
                self.boton_iniciar.configure(state="normal", text="▶ INICIAR EJECUCIÓN")
            if hasattr(self, "boton_pausa"):
                self.boton_pausa.configure(text="⏸ Pausar")
            if hasattr(self, "arbol"):
                self._quitar_resaltado()
            if mensaje and hasattr(self, "etiqueta_estado"):
                self._establecer_estado("Ejecución detenida", "#475569")


def main() -> int:
    if tk is None:
        print(
            "No se pudo iniciar la interfaz gráfica porque Tk no está instalado.\n"
            "Instala el paquete Tk de tu distribución (por ejemplo, python3-tk) "
            "o usa una instalación estándar de Python que incluya tkinter.",
            file=sys.stderr,
        )
        return 1
    app = KarelReaderApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
