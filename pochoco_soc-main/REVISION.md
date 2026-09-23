# Revision y pruebas

## Uso

Desde `pochoco_soc-main`:

```sh
python sw/assembler.py sw/game.s -o sw/game.hex
python -B tests/run_tests.py
make          # sintetiza y genera el bitstream; requiere herramientas FPGA
make prog     # programa explicitamente la placa
```

El assembler propio no requiere una toolchain RISC-V externa. Acepta registros
x0..x15, inmediatos decimales/hexadecimales, etiquetas, comentarios `#`, `.section
.text` y `.global`. Admite LUI, ADDI, SLTI/SLTIU, XORI/ORI/ANDI, ADD/SUB,
AND/OR/XOR, LW/SW, JAL/JALR y las seis comparaciones de salto. Rechaza instrucciones,
operandos, etiquetas e inmediatos invalidos antes de abrir la salida. Por ejemplo,
`ori x3,x2,15` produce `00f16193`. Reserva la ultima palabra de la RAM del juego:
maximo 511 instrucciones en 512 palabras. Los desplazamientos no estan implementados
en la ALU y se rechazan; el decoder anula los efectos de instrucciones ilegales
(sin excepciones ni traps, avanza a la siguiente instruccion).

## Juego

La Go Board usa directamente el oscilador de 25 MHz:
https://nandland.com/the-go-board/
La preparacion dura al menos 75,000,000 ciclos. Al arrancar se espera una pulsacion
y liberacion inicial para obtener una semilla humana. Cada ronda exige soltar todos
los botones; una pulsacion mantenida al terminar la preparacion reinicia esta fase. El LFSR avanza
32 pasos para mezclar tambien los bits que determinan el LED seleccionado.

El contador libre de 32 bits esta en `0x8000000c`; `0x80000010` contiene el ciclo
capturado en la ultima escritura a LEDs. La resta modular tolera cruzar el cero.
Si no hay respuesta durante 2^31 ciclos (~85.9 s), se muestra EE y se repite la ronda.
Una pulsacion incorrecta o simultanea tambien muestra EE y conserva el progreso.
Los botones se sincronizan y se exige estabilidad durante 10 ms: esa latencia y el
sondeo del procesador forman parte del tiempo medido. El final se lee al detectar
la respuesta en software; el inicio coincide con la escritura de LEDs en hardware.

Los displays muestran decimas truncadas y saturan en 99 (9.9 s). Se suman los
cocientes y restos de ciclos antes de dividir por diez; saturar el display no altera
el promedio. La palabra RAM 2044 almacena el resto, siempre menor que 2,500,000.
Tras diez aciertos se muestra el promedio y se apagan los LEDs; se reinicia apagando
y encendiendo la placa. El numero de rondas y las constantes estan en `sw/game.s`.

## RTL y construccion

Se conservan el banco de registros sincrono y el protocolo existente del procesador.
El decoder evita alias de x16..x31 y efectos de instrucciones ilegales. Los registros
MMIO de salida respetan el habilitador del byte bajo. SPI funciona en modo 0, MSB
primero, acepta bytes consecutivos con CS activo y recarga la respuesta por byte.
Las senales SPI pasan por sincronizadores: mantener cada semiciclo y el tiempo de
establecimiento de CS durante al menos cinco ciclos del reloj del sistema.

`make` depende de `sw/game.s`, el assembler y la imagen HEX. Elimina las restricciones
UART que no corresponden al modulo superior y solicita 25 MHz a nextpnr.
La copia `game.hex` en la raiz de este subproyecto es heredada; el RTL consume
exclusivamente `sw/game.hex`. Los binarios/JSON/ASC existentes son anteriores a esta
revision y deben regenerarse antes de programar.

## Alcance de la verificacion

`tests/run_tests.py` ejecuta pruebas de codificacion y rechazo de entradas, partidas
sobre codigo maquina (errores, botones mantenidos, diez rondas, promedio, saturacion,
wrap y semilla), y simulaciones Icarus del procesador, perifericos, SPI y decoder.
Tambien compila el modulo superior completo. La simulacion del banco de registros
usa un modelo del subconjunto MODE=0 de SB_RAM40_4K, no el modelo temporal del fabricante.
El modelo funcional del juego acelera el reloj respecto a las instrucciones y no
sustituye una simulacion ciclo a ciclo de una partida completa.

No se ha validado sintesis, ocupacion, cierre temporal a 25 MHz ni funcionamiento en
la FPGA fisica. Para eso se requieren Yosys, nextpnr, IceStorm y la placa.

Resultado local: 11 pruebas Python y cuatro bancos RTL aprobados; modulo superior
compilado con Icarus. `git diff --check` sin errores de espacios.
