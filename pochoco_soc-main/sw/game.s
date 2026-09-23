
# Juego de reflejos en Espino Core / Pochoco SoC
# Restricciones del hardware/assembler (documentar en el informe):
#   - RV32E: registros x0..x15 (x0 = cero fijo)
#   - No hay jalr -> no existen subrutinas con retorno variable.
#     Todo el programa es codigo plano; los bloques que se
#     necesitan mas de una vez (division, empaquetado BCD) estan
#     duplicados a proposito.
#   - No hay shift (sll/srl/sra): "x << 1" se hace con "add x,x,x".
#   - No hay mul/div: division por resta repetida (bltu + sub).
#   - No hay andi/slt: "and" solo registro-registro; las pruebas
#     de signo/bit31 se hacen con bgeu/bltu (comparacion sin signo).
#
# Mapa de memoria (pochoco_periph, base 0x80000000):
#   +0x00 DIGIT  (escritura) byte con 2 nibbles hex -> 7 segmentos
#   +0x04 LED    (escritura) 4 bits, one-hot
#   +0x08 BTN    (lectura)   4 bits, one-hot
#   +0x0C CYCLES (lectura)   contador libre de 32 bits, +1 por ciclo
#
# Base de tiempo (CLK_HZ = 12 MHz):
#   CICLOS_3S         = 3 * CLK_HZ        = 36 000 000
#   CYCLES_PER_TENTH  = CLK_HZ / 10       =  1 200 000
#   decimas = round(delta_ciclos / CYCLES_PER_TENTH)
#           = (delta_ciclos + CYCLES_PER_TENTH/2) / CYCLES_PER_TENTH
#
# Mapa de registros (fijos durante todo el programa):
#   x1 = PERIPH_BASE (0x80000000). Tambien se reutiliza como
#        constante de comparacion "bit31 en 1" para el LFSR.
#   x2 = CICLOS_3S      (36 000 000)
#   x3 = CYCLES_PER_TENTH (1 200 000)
#   x4 = mascara 3 (0b11), para extraer los 2 bits bajos del LFSR
#   x5 = polinomio del LFSR (0x04C11DB7, CRC-32, tap maximal)
#   x6 = estado del LFSR (semilla no nula al inicio)
#   x7 = RONDAS objetivo (10)
#   x8 = rondas correctas acumuladas
#   x9 = suma de decimas acumuladas (para el promedio)
#   x10..x15 = temporales, reutilizados libremente entre bloques
# ============================================================

# --- constantes iniciales ---
lui   x1, 0x80000
addi  x1, x1, 0            # x1 = PERIPH_BASE = 0x80000000

lui   x2, 0x2255
addi  x2, x2, 0x100        # x2 = CICLOS_3S = 36 000 000

lui   x3, 0x125
addi  x3, x3, -128         # x3 = CYCLES_PER_TENTH = 1 200 000

addi  x4, x0, 3            # x4 = mascara 0b11

lui   x5, 0x4C12
addi  x5, x5, -585         # x5 = 0x04C11DB7 (polinomio LFSR)

addi  x6, x0, 1            # x6 = semilla LFSR (no nula, arbitraria)

addi  x7, x0, 10           # x7 = RONDAS
addi  x8, x0, 0            # x8 = rondas correctas
addi  x9, x0, 0            # x9 = suma de decimas

# ============================================================
# Ronda 0 de 11 (no cuenta para el puntaje ni para el promedio):
# se ve identica a una ronda normal (4 LEDs, 3 segundos), pero
# no elige un LED objetivo real -- solo sirve para inyectar
# entropia humana ANTES de elegir el primer LED de verdad. Sin
# esto, el LED objetivo de la ronda 1 seria identico en cada
# partida, porque todo lo anterior (power-on-reset + espera de
# constantes + WAIT3S) es completamente determinista en ciclos
# de reloj. Como todavia no hay objetivo, se acepta CUALQUIER
# boton como valido para pasar a la ronda 1.
# ============================================================
WARMUP:
    addi  x10, x0, 15
    sw    x10, 4(x1)          # 4 LEDs, igual que cualquier ronda

    lw    x10, 12(x1)          # marca de inicio de la espera de 3s

WARMUP_WAIT3S:
    lw    x11, 12(x1)
    sub   x12, x11, x10
    bltu  x12, x2, WARMUP_WAIT3S   # misma espera de 3s que las rondas reales

WARMUP_BTN:
    lw    x10, 8(x1)
    beq   x10, x0, WARMUP_BTN     # esperar cualquier pulsacion (no hay objetivo)

    lw    x10, 12(x1)              # CYCLES en el instante de la pulsacion humana
    xor   x6, x6, x10                # primera mezcla real de entropia

WARMUP_RELEASE:
    lw    x10, 8(x1)
    bne   x10, x0, WARMUP_RELEASE    # esperar a que suelte el boton

# ============================================================
ROUND_START:
    addi  x10, x0, 15
    sw    x10, 4(x1)        # 4 LEDs encendidos

    lw    x10, 12(x1)       # marca de inicio de la espera

WAIT3S:
    lw    x11, 12(x1)
    sub   x12, x11, x10
    bltu  x12, x2, WAIT3S    # mientras delta < CICLOS_3S, seguir

    # --- sembrar con timing humano y avanzar el LFSR (3 pasos) ---
    lw    x10, 12(x1)
    xor   x6, x6, x10

    bgeu  x6, x1, TAP1
    add   x6, x6, x6
    jal   x0, NOTAP1
TAP1:
    add   x6, x6, x6
    xor   x6, x6, x5
NOTAP1:

    bgeu  x6, x1, TAP2
    add   x6, x6, x6
    jal   x0, NOTAP2
TAP2:
    add   x6, x6, x6
    xor   x6, x6, x5
NOTAP2:

    bgeu  x6, x1, TAP3
    add   x6, x6, x6
    jal   x0, NOTAP3
TAP3:
    add   x6, x6, x6
    xor   x6, x6, x5
NOTAP3:

    and   x10, x6, x4        # x10 = indice LED objetivo (0-3)

    # --- indice -> patron one-hot ---
    addi  x11, x0, 0
    beq   x10, x11, PAT0
    addi  x11, x0, 1
    beq   x10, x11, PAT1
    addi  x11, x0, 2
    beq   x10, x11, PAT2
    addi  x12, x0, 8          # indice == 3
    jal   x0, PATSET
PAT0:
    addi  x12, x0, 1
    jal   x0, PATSET
PAT1:
    addi  x12, x0, 2
    jal   x0, PATSET
PAT2:
    addi  x12, x0, 4
PATSET:
    sw    x12, 4(x1)          # solo el LED objetivo encendido

    lw    x13, 12(x1)         # inicio de la medicion de reaccion

WAIT_BTN:
    lw    x14, 8(x1)
    beq   x14, x0, WAIT_BTN    # sin pulsacion, seguir esperando

    lw    x15, 12(x1)          # fin de la medicion
    bne   x14, x12, ERROR       # boton distinto del objetivo -> error
                                 # (tambien cubre dos botones a la vez,
                                 #  porque BTN ya no seria one-hot valido)

    sub   x10, x15, x13          # delta de ciclos de reaccion

    # redondeo: + CYCLES_PER_TENTH/2 (600 000)
    lui   x11, 0x92
    addi  x11, x11, 1984
    add   x10, x10, x11

    # division por CYCLES_PER_TENTH (x3), resta repetida
    addi  x11, x0, 0
DIV_TENTH:
    bltu  x10, x3, DIV_TENTH_END
    sub   x10, x10, x3
    addi  x11, x11, 1
    jal   x0, DIV_TENTH
DIV_TENTH_END:
    # x11 = decimas de esta ronda

    # saturar a 99 (display de 2 digitos)
    addi  x14, x0, 99
    bltu  x14, x11, SATURATE
    jal   x0, NOSAT
SATURATE:
    add   x11, x0, x14
NOSAT:

    add   x9, x9, x11           # acumular para el promedio

    # --- empaquetar x11 (0-99) como 2 nibbles hex para el display ---
    addi  x12, x0, 0            # decenas
    add   x14, x11, x0          # copia de trabajo
    addi  x15, x0, 10
DIV10_A:
    bltu  x14, x15, DIV10_A_END
    sub   x14, x14, x15
    addi  x12, x12, 1
    jal   x0, DIV10_A
DIV10_A_END:
    # x12 = decenas, x14 = unidades

    add   x10, x12, x0
    add   x10, x10, x10          # x2
    add   x10, x10, x10          # x4
    add   x10, x10, x10          # x8
    add   x10, x10, x10          # x16 -> decenas * 16
    add   x10, x10, x14          # + unidades
    sw    x10, 0(x1)              # muestra el tiempo de reaccion

    addi  x8, x8, 1               # rondas correctas++
    bne   x8, x7, ROUND_START      # si faltan rondas, otra vuelta

    jal   x0, END_GAME

ERROR:
    addi  x10, x0, 0xEE
    sw    x10, 0(x1)                # muestra "EE"

    lw    x10, 12(x1)
ERROR_WAIT:
    lw    x11, 12(x1)
    sub   x12, x11, x10
    bltu  x12, x2, ERROR_WAIT        # deja "EE" visible unos segundos

    jal   x0, ROUND_START             # reinicia LA RONDA; x8 y x9 intactos

END_GAME:
    # promedio = x9 / RONDAS(x7), resta repetida
    addi  x11, x0, 0
DIV_AVG:
    bltu  x9, x7, DIV_AVG_END
    sub   x9, x9, x7
    addi  x11, x11, 1
    jal   x0, DIV_AVG
DIV_AVG_END:
    # x11 = promedio en decimas

    addi  x12, x0, 0
    addi  x15, x0, 10
DIV10_B:
    bltu  x11, x15, DIV10_B_END
    sub   x11, x11, x15
    addi  x12, x12, 1
    jal   x0, DIV10_B
DIV10_B_END:
    add   x10, x12, x0
    add   x10, x10, x10
    add   x10, x10, x10
    add   x10, x10, x10
    add   x10, x10, x10
    add   x10, x10, x11
    sw    x10, 0(x1)                 # muestra el promedio final

HANG:
    jal   x0, HANG
