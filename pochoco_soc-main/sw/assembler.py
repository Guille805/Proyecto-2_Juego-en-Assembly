def registro(nombre):
    return int(nombre[1:])

def codificar_lui(rd, inmediato):
    opcode = 0x37

    return (inmediato << 12) | (rd << 7) | opcode

def codificar_addi(rd, rs1, inmediato):
    opcode = 0x13
    funct3 = 0b000

    inmediato &= 0xFFF

    return (
        (inmediato << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )

def codificar_jal(rd, offset):
    opcode = 0x6F

    offset &= 0x1FFFFF

    imm20 = (offset >> 20) & 0x1
    imm10_1 = (offset >> 1) & 0x3FF
    imm11 = (offset >> 11) & 0x1
    imm19_12 = (offset >> 12) & 0xFF

    return (
        (imm20 << 31)
        | (imm19_12 << 12)
        | (imm11 << 20)
        | (imm10_1 << 21)
        | (rd << 7)
        | opcode
    )

def analizar_programa(lineas):
    etiquetas = {}
    instrucciones = []

    direccion = 0

    for linea in lineas:
        linea = linea.split("#")[0].strip()

        if not linea:
            continue

        if linea.endswith(":"):
            nombre = linea[:-1].strip()
            etiquetas[nombre] = direccion
        else:
            instrucciones.append((direccion, linea))
            direccion += 4

    return etiquetas, instrucciones

def calcular_offset_jal(direccion_jal, etiqueta, etiquetas):
    direccion_destino = etiquetas[etiqueta]
    return direccion_destino - direccion_jal

def codificar_sw(rs2, rs1, inmediato):
    opcode = 0x23
    funct3 = 0b010

    inmediato &= 0xFFF

    imm_11_5 = (inmediato >> 5) & 0x7F
    imm_4_0 = inmediato & 0x1F

    return (
        (imm_11_5 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (imm_4_0 << 7)
        | opcode
    )

def codificar_lw(rd, rs1, inmediato):
    opcode = 0x03
    funct3 = 0b010

    inmediato &= 0xFFF

    return (
        (inmediato << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )

def codificar_and(rd, rs1, rs2):
    opcode = 0x33
    funct3 = 0b111
    funct7 = 0b0000000

    return (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )

def codificar_or(rd, rs1, rs2):
    opcode = 0x33
    funct3 = 0b110
    funct7 = 0b0000000

    return (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )

def codificar_add(rd, rs1, rs2):
    opcode = 0x33
    funct3 = 0b000
    funct7 = 0b0000000

    return (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )

def codificar_sub(rd, rs1, rs2):
    opcode = 0x33
    funct3 = 0b000
    funct7 = 0b0100000

    return (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )

def codificar_xor(rd, rs1, rs2):
    opcode = 0x33
    funct3 = 0b100
    funct7 = 0b0000000

    return (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )

def codificar_branch(rs1, rs2, offset, funct3):
    opcode = 0x63

    offset &= 0x1FFF

    imm12 = (offset >> 12) & 0x1
    imm10_5 = (offset >> 5) & 0x3F
    imm4_1 = (offset >> 1) & 0xF
    imm11 = (offset >> 11) & 0x1

    return (
        (imm12 << 31)
        | (imm10_5 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (imm4_1 << 8)
        | (imm11 << 7)
        | opcode
    )

def codificar_instruccion(instruccion, direccion_actual, etiquetas):
    partes = instruccion.replace(",", "").split()

    nombre = partes[0]

    if nombre == "lui":
        rd = registro(partes[1])
        inmediato = int(partes[2], 0)

        return codificar_lui(rd, inmediato)

    if nombre == "addi":
        rd = registro(partes[1])
        rs1 = registro(partes[2])
        inmediato = int(partes[3], 0)

        return codificar_addi(rd, rs1, inmediato)

    if nombre == "lw":
        rd = registro(partes[1])

        offset_base = partes[2]
        inmediato = int(offset_base.split("(")[0], 0)
        rs1 = registro(offset_base.split("(")[1].replace(")", ""))

        return codificar_lw(rd, rs1, inmediato)
    if nombre == "sw":
        rs2 = registro(partes[1])

        offset_base = partes[2]
        inmediato = int(offset_base.split("(")[0], 0)
        rs1 = registro(offset_base.split("(")[1].replace(")", ""))

        return codificar_sw(rs2, rs1, inmediato)
    if nombre == "jal":
        rd = registro(partes[1])
        etiqueta = partes[2]

        return codificar_jal(
            rd,
            etiquetas[etiqueta] - direccion_actual
        )

    if nombre == "add":
        rd = registro(partes[1])
        rs1 = registro(partes[2])
        rs2 = registro(partes[3])

        return codificar_add(rd, rs1, rs2)
    
    if nombre == "sub":
        rd = registro(partes[1])
        rs1 = registro(partes[2])
        rs2 = registro(partes[3])

        return codificar_sub(rd, rs1, rs2)
    
    if nombre == "and":
        rd = registro(partes[1])
        rs1 = registro(partes[2])
        rs2 = registro(partes[3])

        return codificar_and(rd, rs1, rs2)
    
    if nombre == "or":
        rd = registro(partes[1])
        rs1 = registro(partes[2])
        rs2 = registro(partes[3])

        return codificar_or(rd, rs1, rs2)
    
    if nombre == "xor":
        rd = registro(partes[1])
        rs1 = registro(partes[2])
        rs2 = registro(partes[3])

        return codificar_xor(rd, rs1, rs2)
    
    if nombre == "beq":
        rs1 = registro(partes[1])
        rs2 = registro(partes[2])
        etiqueta = partes[3]

        offset = etiquetas[etiqueta] - direccion_actual

        return codificar_branch(rs1, rs2, offset, 0b000)

    if nombre == "bne":
        rs1 = registro(partes[1])
        rs2 = registro(partes[2])
        etiqueta = partes[3]

        offset = etiquetas[etiqueta] - direccion_actual

        return codificar_branch(rs1, rs2, offset, 0b001)

    if nombre == "bltu":
        rs1 = registro(partes[1])
        rs2 = registro(partes[2])
        etiqueta = partes[3]

        offset = etiquetas[etiqueta] - direccion_actual

        return codificar_branch(rs1, rs2, offset, 0b110)

    if nombre == "bgeu":
        rs1 = registro(partes[1])
        rs2 = registro(partes[2])
        etiqueta = partes[3]

        offset = etiquetas[etiqueta] - direccion_actual

        return codificar_branch(rs1, rs2, offset, 0b111)

    return None


with open("game.s", "r") as archivo:
    programa = archivo.readlines()

etiquetas, instrucciones = analizar_programa(programa)

print("Etiquetas:")
print(etiquetas)

print("\nInstrucciones:")
for direccion, instruccion in instrucciones:
    print(direccion, instruccion)

for direccion, instruccion in instrucciones:
    partes = instruccion.split()

    if partes[0] == "jal":
        etiqueta = partes[2]
        offset = calcular_offset_jal(direccion, etiqueta, etiquetas)

        print("\nOffset del jal:")
        print(offset)

        codigo = codificar_jal(0, offset)
        print(f"Código: {codigo:08x}")

print("\nPrueba de instrucciones:")

codigos = []

for direccion, instruccion in instrucciones:
    codigo = codificar_instruccion(instruccion, direccion, etiquetas)

    if codigo is not None:
        codigos.append(codigo)
        print(f"{direccion:02d} {instruccion} -> {codigo:08x}")
        print("\nCódigos generados:")

with open("game.hex", "w") as archivo:
    for codigo in codigos:
        archivo.write(f"{codigo:08x}\n")

print("\nArchivo game.hex generado.")
    