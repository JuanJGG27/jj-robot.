"""Pruebas unitarias del motor y el intérprete de Karel Reader."""

import unittest

from main import (
    Bloque,
    CondicionKarel,
    Direccion,
    ErrorKarel,
    EstadoKarel,
    HistorialPrograma,
    Interprete,
    MundoKarel,
    Nivel,
    TipoBloque,
    agregar_muro,
    buscar_bloque,
    contar_bloques_interiores,
    crear_niveles,
    mover_bloque_en_modelo,
    profundidad_bloque,
    ruta_bloque,
)


def nivel_prueba(
    *,
    ancho=5,
    alto=5,
    inicio=None,
    marcadores=None,
    objetivos=None,
    meta=(4, 4),
    muros=None,
):
    return Nivel(
        nombre="Prueba",
        ancho=ancho,
        alto=alto,
        inicio=inicio or EstadoKarel(1, 1, Direccion.ESTE),
        marcadores=marcadores or {},
        objetivos=objetivos or {},
        meta=meta,
        muros=muros or set(),
        descripcion="Nivel de prueba",
    )


def ejecutar_programa(mundo, bloques):
    for paso in Interprete(mundo).ejecutar(bloques):
        paso.accion()


class PruebasDireccion(unittest.TestCase):
    def test_giros_forman_ciclo(self):
        direccion = Direccion.NORTE
        for _ in range(4):
            direccion = direccion.derecha()
        self.assertEqual(direccion, Direccion.NORTE)

        direccion = Direccion.NORTE
        for _ in range(4):
            direccion = direccion.izquierda()
        self.assertEqual(direccion, Direccion.NORTE)

    def test_giros_individuales(self):
        self.assertEqual(Direccion.NORTE.derecha(), Direccion.ESTE)
        self.assertEqual(Direccion.NORTE.izquierda(), Direccion.OESTE)


class PruebasMundo(unittest.TestCase):
    def test_avanzar_actualiza_posicion(self):
        mundo = MundoKarel(nivel_prueba())
        mundo.avanzar()
        self.assertEqual((mundo.karel.x, mundo.karel.y), (2, 1))
        self.assertEqual(mundo.acciones, 1)

    def test_no_puede_salir_del_tablero(self):
        mundo = MundoKarel(
            nivel_prueba(inicio=EstadoKarel(0, 0, Direccion.NORTE))
        )
        self.assertFalse(mundo.camino_libre())
        with self.assertRaisesRegex(ErrorKarel, "muro|tablero"):
            mundo.avanzar()

    def test_muro_bloquea_en_ambas_direcciones(self):
        muros = set()
        agregar_muro(muros, 1, 1, Direccion.ESTE)
        mundo = MundoKarel(nivel_prueba(muros=muros))
        self.assertFalse(mundo.camino_libre())
        mundo.karel = EstadoKarel(2, 1, Direccion.OESTE)
        self.assertFalse(mundo.camino_libre())

    def test_recoger_y_colocar_marcador(self):
        mundo = MundoKarel(nivel_prueba(marcadores={(1, 1): 2}))
        mundo.recoger()
        self.assertEqual(mundo.karel.mochila, 1)
        self.assertEqual(mundo.marcadores[(1, 1)], 1)
        mundo.avanzar()
        mundo.colocar()
        self.assertEqual(mundo.karel.mochila, 0)
        self.assertEqual(mundo.marcadores[(2, 1)], 1)

    def test_recoger_sin_marcador_da_error(self):
        mundo = MundoKarel(nivel_prueba())
        with self.assertRaisesRegex(ErrorKarel, "No hay"):
            mundo.recoger()

    def test_colocar_con_mochila_vacia_da_error(self):
        mundo = MundoKarel(nivel_prueba())
        with self.assertRaisesRegex(ErrorKarel, "vacía"):
            mundo.colocar()

    def test_no_hay_limite_de_acciones(self):
        mundo = MundoKarel(nivel_prueba())
        for _ in range(1000):
            mundo.girar_derecha()
        self.assertEqual(mundo.acciones, 1000)
        self.assertEqual(mundo.karel.direccion, Direccion.ESTE)

    def test_objetivo_requiere_meta_y_marcadores(self):
        mundo = MundoKarel(
            nivel_prueba(
                inicio=EstadoKarel(2, 2, Direccion.NORTE),
                meta=(2, 2),
                objetivos={(1, 1): 1},
            )
        )
        self.assertFalse(mundo.completado())
        mundo.marcadores[(1, 1)] = 1
        self.assertTrue(mundo.completado())

    def test_recargar_nivel_restaura_el_estado(self):
        nivel = nivel_prueba(marcadores={(1, 1): 1})
        mundo = MundoKarel(nivel)
        mundo.recoger()
        mundo.avanzar()
        mundo.cargar_nivel(nivel)
        self.assertEqual((mundo.karel.x, mundo.karel.y), (1, 1))
        self.assertEqual(mundo.karel.mochila, 0)
        self.assertEqual(mundo.marcadores, {(1, 1): 1})
        self.assertEqual(mundo.acciones, 0)


class PruebasInterprete(unittest.TestCase):
    def test_repetir_cantidad_especifica(self):
        mundo = MundoKarel(nivel_prueba(ancho=6))
        programa = [
            Bloque(
                TipoBloque.REPETIR,
                repeticiones=3,
                hijos=[Bloque(TipoBloque.AVANZAR)],
            )
        ]
        ejecutar_programa(mundo, programa)
        self.assertEqual((mundo.karel.x, mundo.karel.y), (4, 1))

    def test_mientras_reevalua_la_condicion(self):
        mundo = MundoKarel(
            nivel_prueba(ancho=5, inicio=EstadoKarel(1, 1, Direccion.ESTE))
        )
        programa = [
            Bloque(
                TipoBloque.MIENTRAS,
                condicion=CondicionKarel.FRENTE_LIBRE,
                hijos=[Bloque(TipoBloque.AVANZAR)],
            )
        ]
        ejecutar_programa(mundo, programa)
        self.assertEqual((mundo.karel.x, mundo.karel.y), (4, 1))
        self.assertFalse(mundo.camino_libre())

    def test_mientras_no_ejecuta_si_inicia_falso(self):
        mundo = MundoKarel(
            nivel_prueba(inicio=EstadoKarel(0, 0, Direccion.NORTE))
        )
        programa = [
            Bloque(
                TipoBloque.MIENTRAS,
                condicion=CondicionKarel.FRENTE_LIBRE,
                hijos=[Bloque(TipoBloque.AVANZAR)],
            )
        ]
        ejecutar_programa(mundo, programa)
        self.assertEqual(mundo.acciones, 0)

    def test_mientras_sin_acciones_se_detiene_con_error(self):
        mundo = MundoKarel(nivel_prueba())
        programa = [
            Bloque(
                TipoBloque.MIENTRAS,
                condicion=CondicionKarel.FRENTE_LIBRE,
                hijos=[Bloque(TipoBloque.REPETIR, repeticiones=2)],
            )
        ]
        with self.assertRaisesRegex(ErrorKarel, "no contiene acciones"):
            ejecutar_programa(mundo, programa)

    def test_mientras_sin_progreso_se_detiene_con_error(self):
        mundo = MundoKarel(nivel_prueba())
        programa = [
            Bloque(
                TipoBloque.MIENTRAS,
                condicion=CondicionKarel.FRENTE_LIBRE,
                hijos=[Bloque(TipoBloque.GIRAR_DERECHA) for _ in range(4)],
            )
        ]
        with self.assertRaisesRegex(ErrorKarel, "no modifica el mundo"):
            ejecutar_programa(mundo, programa)

    def test_condicional_ejecuta_rama_verdadera(self):
        mundo = MundoKarel(nivel_prueba(marcadores={(1, 1): 1}))
        programa = [
            Bloque(
                TipoBloque.SI,
                condicion=CondicionKarel.MARCADOR_PRESENTE,
                hijos=[Bloque(TipoBloque.RECOGER)],
                alternativa=[Bloque(TipoBloque.GIRAR_DERECHA)],
            )
        ]
        ejecutar_programa(mundo, programa)
        self.assertEqual(mundo.karel.mochila, 1)
        self.assertEqual(mundo.karel.direccion, Direccion.ESTE)

    def test_condicional_ejecuta_rama_falsa(self):
        mundo = MundoKarel(nivel_prueba())
        programa = [
            Bloque(
                TipoBloque.SI,
                condicion=CondicionKarel.MARCADOR_PRESENTE,
                hijos=[Bloque(TipoBloque.RECOGER)],
                alternativa=[Bloque(TipoBloque.GIRAR_DERECHA)],
            )
        ]
        ejecutar_programa(mundo, programa)
        self.assertEqual(mundo.karel.direccion, Direccion.SUR)
        self.assertEqual(mundo.acciones, 1)

    def test_condicional_sin_rama_alternativa(self):
        mundo = MundoKarel(nivel_prueba())
        programa = [
            Bloque(
                TipoBloque.SI,
                condicion=CondicionKarel.MARCADOR_PRESENTE,
                hijos=[Bloque(TipoBloque.RECOGER)],
            ),
            Bloque(TipoBloque.GIRAR_IZQUIERDA),
        ]
        ejecutar_programa(mundo, programa)
        self.assertEqual(mundo.karel.direccion, Direccion.NORTE)

    def test_programa_anidado(self):
        mundo = MundoKarel(nivel_prueba(ancho=7, alto=7))
        programa = [
            Bloque(
                TipoBloque.REPETIR,
                repeticiones=2,
                hijos=[
                    Bloque(
                        TipoBloque.REPETIR,
                        repeticiones=2,
                        hijos=[Bloque(TipoBloque.AVANZAR)],
                    ),
                    Bloque(TipoBloque.GIRAR_DERECHA),
                ],
            )
        ]
        ejecutar_programa(mundo, programa)
        self.assertEqual((mundo.karel.x, mundo.karel.y), (3, 3))
        self.assertEqual(mundo.karel.direccion, Direccion.OESTE)

    def test_interprete_produce_pasos_sin_ejecutarlos_anticipadamente(self):
        mundo = MundoKarel(nivel_prueba())
        generador = Interprete(mundo).ejecutar([Bloque(TipoBloque.AVANZAR)])
        paso = next(generador)
        self.assertEqual((mundo.karel.x, mundo.karel.y), (1, 1))
        paso.accion()
        self.assertEqual((mundo.karel.x, mundo.karel.y), (2, 1))

    def test_paso_condicional_informa_la_rama(self):
        mundo = MundoKarel(nivel_prueba())
        bloque = Bloque(
            TipoBloque.SI,
            condicion=CondicionKarel.SIN_MARCADOR,
            hijos=[Bloque(TipoBloque.GIRAR_DERECHA)],
        )
        paso = next(Interprete(mundo).ejecutar([bloque]))
        self.assertEqual(paso.rama, "si")
        self.assertIn("verdadera", paso.mensaje)


class PruebasCondiciones(unittest.TestCase):
    def test_condiciones_de_camino_en_tres_direcciones(self):
        muros = set()
        agregar_muro(muros, 1, 1, Direccion.NORTE)
        mundo = MundoKarel(nivel_prueba(muros=muros))
        self.assertTrue(mundo.evaluar_condicion(CondicionKarel.FRENTE_LIBRE))
        self.assertTrue(mundo.evaluar_condicion(CondicionKarel.IZQUIERDA_BLOQUEADA))
        self.assertTrue(mundo.evaluar_condicion(CondicionKarel.DERECHA_LIBRE))

    def test_condiciones_de_marcador_mochila_y_orientacion(self):
        mundo = MundoKarel(
            nivel_prueba(
                inicio=EstadoKarel(1, 1, Direccion.ESTE, mochila=2),
                marcadores={(1, 1): 1},
            )
        )
        verdaderas = {
            CondicionKarel.MARCADOR_PRESENTE,
            CondicionKarel.MARCADORES_EN_MOCHILA,
            CondicionKarel.MIRA_ESTE,
            CondicionKarel.NO_MIRA_NORTE,
        }
        for condicion in verdaderas:
            with self.subTest(condicion=condicion):
                self.assertTrue(mundo.evaluar_condicion(condicion))
        falsas = {
            CondicionKarel.SIN_MARCADOR,
            CondicionKarel.MOCHILA_VACIA,
            CondicionKarel.MIRA_NORTE,
            CondicionKarel.NO_MIRA_ESTE,
        }
        for condicion in falsas:
            with self.subTest(condicion=condicion):
                self.assertFalse(mundo.evaluar_condicion(condicion))

    def test_cada_condicion_tiene_resultado_booleano(self):
        mundo = MundoKarel(nivel_prueba())
        for condicion in CondicionKarel:
            with self.subTest(condicion=condicion):
                self.assertIsInstance(mundo.evaluar_condicion(condicion), bool)


class PruebasMovimientoDeBloques(unittest.TestCase):
    def setUp(self):
        self.a = Bloque(TipoBloque.AVANZAR, identificador="a")
        self.b = Bloque(TipoBloque.GIRAR_DERECHA, identificador="b")
        self.c = Bloque(TipoBloque.RECOGER, identificador="c")
        self.bucle = Bloque(
            TipoBloque.REPETIR,
            hijos=[self.b],
            identificador="bucle",
        )
        self.condicional = Bloque(
            TipoBloque.SI,
            hijos=[],
            alternativa=[self.c],
            identificador="si",
        )
        self.programa = [self.a, self.bucle, self.condicional]

    def test_reordenar_bloques(self):
        self.assertTrue(mover_bloque_en_modelo(self.programa, "si", self.programa, 0))
        self.assertEqual([b.identificador for b in self.programa], ["si", "a", "bucle"])

    def test_sacar_bloque_de_bucle(self):
        self.assertTrue(mover_bloque_en_modelo(self.programa, "b", self.programa, 2))
        self.assertEqual(self.bucle.hijos, [])
        self.assertIs(self.programa[2], self.b)

    def test_mover_entre_ramas(self):
        self.assertTrue(
            mover_bloque_en_modelo(self.programa, "c", self.condicional.hijos, 0)
        )
        self.assertEqual(self.condicional.alternativa, [])
        self.assertIs(self.condicional.hijos[0], self.c)

    def test_no_permite_mover_contenedor_dentro_de_si_mismo(self):
        self.assertFalse(
            mover_bloque_en_modelo(self.programa, "bucle", self.bucle.hijos, 0)
        )
        self.assertIsNotNone(buscar_bloque(self.programa, "bucle"))


class PruebasJerarquiaVisual(unittest.TestCase):
    def setUp(self):
        self.accion = Bloque(TipoBloque.AVANZAR, identificador="accion")
        self.repetir = Bloque(
            TipoBloque.REPETIR,
            repeticiones=3,
            hijos=[self.accion],
            identificador="repetir",
        )
        self.condicional = Bloque(
            TipoBloque.SI,
            hijos=[self.repetir],
            alternativa=[Bloque(TipoBloque.GIRAR_DERECHA, identificador="alternativa")],
            identificador="condicional",
        )
        self.programa = [self.condicional]

    def test_calcula_profundidad(self):
        self.assertEqual(profundidad_bloque(self.programa, "condicional"), 0)
        self.assertEqual(profundidad_bloque(self.programa, "repetir"), 1)
        self.assertEqual(profundidad_bloque(self.programa, "accion"), 2)

    def test_cuenta_todos_los_bloques_interiores(self):
        self.assertEqual(contar_bloques_interiores(self.repetir), 1)
        self.assertEqual(contar_bloques_interiores(self.condicional), 3)

    def test_ruta_indica_rama_y_contenedores(self):
        ruta = ruta_bloque(self.programa, "accion")
        self.assertIsNotNone(ruta)
        self.assertEqual(
            [(bloque.identificador, rama) for bloque, rama in ruta],
            [("condicional", "SI SE CUMPLE"), ("repetir", "CUERPO"), ("accion", "")],
        )

    def test_ruta_de_rama_alternativa(self):
        ruta = ruta_bloque(self.programa, "alternativa")
        self.assertIsNotNone(ruta)
        self.assertEqual(ruta[0][1], "SI NO SE CUMPLE")


class PruebasHistorialPrograma(unittest.TestCase):
    def test_deshacer_y_rehacer(self):
        historial = HistorialPrograma()
        programa = [Bloque(TipoBloque.AVANZAR, identificador="a")]
        historial.registrar(programa)
        programa.append(Bloque(TipoBloque.GIRAR_DERECHA, identificador="b"))

        anterior = historial.deshacer(programa)
        self.assertEqual([bloque.identificador for bloque in anterior], ["a"])

        siguiente = historial.rehacer(anterior)
        self.assertEqual([bloque.identificador for bloque in siguiente], ["a", "b"])

    def test_nuevo_cambio_borra_rehacer(self):
        historial = HistorialPrograma()
        programa = [Bloque(TipoBloque.AVANZAR, identificador="a")]
        historial.registrar(programa)
        programa.append(Bloque(TipoBloque.GIRAR_DERECHA, identificador="b"))
        anterior = historial.deshacer(programa)
        historial.registrar(anterior)
        self.assertIsNone(historial.rehacer(anterior))

    def test_respeta_maximo_de_estados(self):
        historial = HistorialPrograma(maximo=2)
        for indice in range(3):
            historial.registrar(
                [Bloque(TipoBloque.AVANZAR, identificador=str(indice))]
            )
        self.assertEqual(len(historial.deshacer_estados), 2)


class PruebasNivelesIncluidos(unittest.TestCase):
    def test_hay_cuatro_niveles_validos(self):
        niveles = crear_niveles()
        self.assertEqual(len(niveles), 4)
        for nivel in niveles:
            self.assertGreaterEqual(nivel.ancho, 1)
            self.assertGreaterEqual(nivel.alto, 1)
            self.assertTrue(0 <= nivel.inicio.x < nivel.ancho)
            self.assertTrue(0 <= nivel.inicio.y < nivel.alto)
            self.assertTrue(0 <= nivel.meta[0] < nivel.ancho)
            self.assertTrue(0 <= nivel.meta[1] < nivel.alto)
            self.assertFalse(hasattr(nivel, "limite_pasos"))

    def test_los_cuatro_niveles_tienen_solucion(self):
        niveles = crear_niveles()
        soluciones = [
            [Bloque(TipoBloque.AVANZAR) for _ in range(5)],
            [
                Bloque(TipoBloque.AVANZAR),
                Bloque(TipoBloque.AVANZAR),
                Bloque(TipoBloque.RECOGER),
                *[Bloque(TipoBloque.AVANZAR) for _ in range(3)],
                Bloque(TipoBloque.GIRAR_IZQUIERDA),
                *[Bloque(TipoBloque.AVANZAR) for _ in range(3)],
                Bloque(TipoBloque.COLOCAR),
            ],
            [
                Bloque(TipoBloque.AVANZAR),
                Bloque(TipoBloque.GIRAR_DERECHA),
                *[Bloque(TipoBloque.AVANZAR) for _ in range(4)],
                Bloque(TipoBloque.GIRAR_IZQUIERDA),
                Bloque(TipoBloque.AVANZAR),
                Bloque(TipoBloque.AVANZAR),
                Bloque(TipoBloque.GIRAR_DERECHA),
                Bloque(TipoBloque.AVANZAR),
                Bloque(TipoBloque.GIRAR_IZQUIERDA),
                Bloque(TipoBloque.AVANZAR),
                Bloque(TipoBloque.GIRAR_DERECHA),
                Bloque(TipoBloque.AVANZAR),
            ],
            [
                Bloque(
                    TipoBloque.REPETIR,
                    repeticiones=4,
                    hijos=[
                        Bloque(TipoBloque.AVANZAR),
                        Bloque(TipoBloque.COLOCAR),
                    ],
                ),
                Bloque(TipoBloque.AVANZAR),
            ],
        ]
        for nivel, solucion in zip(niveles, soluciones):
            with self.subTest(nivel=nivel.nombre):
                mundo = MundoKarel(nivel)
                ejecutar_programa(mundo, solucion)
                self.assertTrue(mundo.completado())


if __name__ == "__main__":
    unittest.main(verbosity=2)
