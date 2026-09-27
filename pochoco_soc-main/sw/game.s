# Juego de reflejos en Espino Core / Pochoco SoC
# RV32E: se evita completamente bltu y bgeu.
# Las comparaciones de tiempos se hacen con bge/blt.
# x1=MMIO, x2=75.000.000 ciclos, x3=2.500.000 ciclos,
# x4=3, x5=polinomio LFSR, x6=semilla, x7=rondas,
# x8=aciertos, x9=suma de decimas.

lui   x1, 0x80000
addi  x1, x1, 0
lui   x2, 0x4787
addi  x2, x2, -1856
lui   x3, 0x262
addi  x3, x3, 1440
addi  x4, x0, 3
lui   x5, 0x4C12
addi  x5, x5, -585
addi  x6, x0, 1
addi  x7, x0, 10
addi  x8, x0, 0
addi  x9, x0, 0
sw    x0, 2044(x0)

# Ronda de calentamiento: introduce entropia humana.
WARMUP:
    addi  x10, x0, 15
    sw    x10, 4(x1)
    lw    x10, 12(x1)
WARMUP_WAIT3S:
    lw    x11, 12(x1)
    sub   x12, x11, x10
    bge   x12, x2, WARMUP_WAIT3S_END
    jal   x0, WARMUP_WAIT3S
WARMUP_WAIT3S_END:
WARMUP_BTN:
    lw    x10, 8(x1)
    beq   x10, x0, WARMUP_BTN
    lw    x10, 12(x1)
    xor   x6, x6, x10
WARMUP_RELEASE:
    lw    x10, 8(x1)
    bne   x10, x0, WARMUP_RELEASE

ROUND_START:
    lw    x10, 8(x1)
    bne   x10, x0, ROUND_START
    addi  x10, x0, 15
    sw    x10, 4(x1)
    lw    x10, 12(x1)
WAIT3S:
    lw    x11, 12(x1)
    sub   x12, x11, x10
    bge   x12, x2, WAIT3S_END
    jal   x0, WAIT3S
WAIT3S_END:
    lw    x10, 8(x1)
    bne   x10, x0, ROUND_START

    # Semilla LFSR. Se usa blt signed para revisar el bit 31;
    # x6 nunca necesita interpretarse como numero signed aqui.
    lw    x10, 12(x1)
    xor   x6, x6, x10
    bne   x6, x0, SEED_OK
    addi  x6, x0, 1
SEED_OK:
    addi  x11, x0, 32
RNG_STEP:
    blt   x6, x0, RNG_TAP
    add   x6, x6, x6
    jal   x0, RNG_NEXT
RNG_TAP:
    add   x6, x6, x6
    xor   x6, x6, x5
RNG_NEXT:
    addi  x11, x11, -1
    bne   x11, x0, RNG_STEP

    and   x10, x6, x4
    addi  x11, x0, 0
    beq   x10, x11, PAT0
    addi  x11, x0, 1
    beq   x10, x11, PAT1
    addi  x11, x0, 2
    beq   x10, x11, PAT2
    addi  x12, x0, 8
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
    sw    x12, 4(x1)
    lw    x13, 16(x1)

WAIT_BTN:
    lw    x14, 8(x1)
    bne   x14, x0, GOT_BTN
    lw    x15, 12(x1)
    sub   x10, x15, x13
    # Si delta tiene bit 31 activo, es negativo signed: timeout.
    blt   x10, x0, ERROR
    jal   x0, WAIT_BTN
GOT_BTN:
    lw    x15, 12(x1)
    bne   x14, x12, ERROR
    sub   x10, x15, x13

    # x11 = x10 / x3, dejando el resto en x10.
    addi  x11, x0, 0
DIV_TENTH:
    bge   x10, x3, DIV_TENTH_CONT
    jal   x0, DIV_TENTH_END
DIV_TENTH_CONT:
    sub   x10, x10, x3
    addi  x11, x11, 1
    jal   x0, DIV_TENTH
DIV_TENTH_END:
    lw    x14, 2044(x0)
    add   x14, x14, x10
    bge   x14, x3, REMAINDER_OK
    jal   x0, REMAINDER_SKIP
REMAINDER_OK:
    sub   x14, x14, x3
    addi  x9, x9, 1
REMAINDER_SKIP:
    sw    x14, 2044(x0)
    add   x9, x9, x11

    # Saturacion del valor mostrado, no del promedio.
    addi  x14, x0, 99
    bge   x14, x11, NOSAT
    add   x11, x0, x14
NOSAT:
    addi  x12, x0, 0
    add   x14, x11, x0
    addi  x15, x0, 10
DIV10_A:
    bge   x14, x15, DIV10_A_CONT
    jal   x0, DIV10_A_END
DIV10_A_CONT:
    sub   x14, x14, x15
    addi  x12, x12, 1
    jal   x0, DIV10_A
DIV10_A_END:
    add   x10, x12, x0
    add   x10, x10, x10
    add   x10, x10, x10
    add   x10, x10, x10
    add   x10, x10, x10
    add   x10, x10, x14
    sw    x10, 0(x1)

    addi  x8, x8, 1
    bne   x8, x7, ROUND_START
    jal   x0, END_GAME

ERROR:
    addi  x10, x0, 0xEE
    sw    x10, 0(x1)
    lw    x10, 12(x1)
ERROR_WAIT:
    lw    x11, 12(x1)
    sub   x12, x11, x10
    bge   x12, x2, ERROR_WAIT_END
    jal   x0, ERROR_WAIT
ERROR_WAIT_END:
    jal   x0, ROUND_START

END_GAME:
    addi  x11, x0, 0
DIV_AVG:
    bge   x9, x7, DIV_AVG_CONT
    jal   x0, DIV_AVG_END
DIV_AVG_CONT:
    sub   x9, x9, x7
    addi  x11, x11, 1
    jal   x0, DIV_AVG
DIV_AVG_END:
    addi  x14, x0, 99
    bge   x14, x11, AVG_DISPLAY
    addi  x11, x0, 99
AVG_DISPLAY:
    sw    x0, 4(x1)
    addi  x12, x0, 0
    addi  x15, x0, 10
DIV10_B:
    bge   x11, x15, DIV10_B_CONT
    jal   x0, DIV10_B_END
DIV10_B_CONT:
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
    sw    x10, 0(x1)
HANG:
    jal   x0, HANG
