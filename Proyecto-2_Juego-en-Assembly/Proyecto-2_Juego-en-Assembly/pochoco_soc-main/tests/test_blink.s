# Test blink: parpadear LEDs cada 0.5 segundos
# Objetivo: validar que CPU, memoria, contador de ciclos y LEDs funcionan

lui   x1, 0x80000      # x1 = dirección base MMIO (0x80000000)
addi  x1, x1, 0

# 12,500,000 ciclos = 0.5 segundos a 25 MHz
lui   x2, 0x2FAF
addi  x2, x2, 0x080

addi  x3, x0, 0        # Patrón de LEDs

LOOP:
# Escribir patrón actual a LEDs (offset +4)
sw    x3, 4(x1)

# Leer tiempo actual
lw    x10, 12(x1)

# Calcular tiempo objetivo = ahora + 0.5s
add   x11, x10, x2

WAIT:
    lw    x10, 12(x1)
    bne   x10, x11, WAIT

# Siguiente patrón (0->1->2->...->15->0)
addi  x3, x3, 1
andi  x3, x3, 0xF

jal   x0, LOOP
