import argparse
import re
from pathlib import Path

def registro(nombre):
    if not re.fullmatch(r"x(?:[0-9]|1[0-5])", nombre):
        raise ValueError(f"Registro RV32E invalido: {nombre}")
    return int(nombre[1:])

def codificar_lui(rd, inmediato):
    opcode = 0x37

    return (inmediato << 12) | (rd << 7) | opcode

def codificar_itype(rd, rs1, inmediato, funct3, opcode):
    inmediato &= 0xFFF

    return (
        (inmediato << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )


def codificar_addi(rd, rs1, inmediato):
    return codificar_itype(rd, rs1, inmediato, 0b000, 0x13)


def codificar_slti(rd, rs1, inmediato):
    return codificar_itype(rd, rs1, inmediato, 0b010, 0x13)


def codificar_sltiu(rd, rs1, inmediato):
    return codificar_itype(rd, rs1, inmediato, 0b011, 0x13)


def codificar_xori(rd, rs1, inmediato):
    return codificar_itype(rd, rs1, inmediato, 0b100, 0x13)


def codificar_ori(rd, rs1, inmediato):
    return codificar_itype(rd, rs1, inmediato, 0b110, 0x13)


def codificar_andi(rd, rs1, inmediato):
    return codificar_itype(rd, rs1, inmediato, 0b111, 0x13)


def codificar_slli(rd, rs1, shamt):
    shamt &= 0x1F
    return ((shamt << 20) | (rs1 << 15) | (0b001 << 12) | (rd << 7) | 0x13)


def codificar_srli(rd, rs1, shamt):
    shamt &= 0x1F
    return ((shamt << 20) | (rs1 << 15) | (0b101 << 12) | (rd << 7) | 0x13)


def codificar_srai(rd, rs1, shamt):
    shamt &= 0x1F
    return ((0x400 | shamt) << 20 | (rs1 << 15) | (0b101 << 12) | (rd << 7) | 0x13)


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
    etiquetas, instrucciones = {}, []
    direccion = 0
    for numero, linea in enumerate(lineas, 1):
        linea = linea.split("#", 1)[0].strip()
        while ":" in linea:
            nombre, linea = (parte.strip() for parte in linea.split(":", 1))
            if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", nombre):
                raise ValueError(f"Linea {numero}: etiqueta invalida: {nombre}")
            if nombre in etiquetas:
                raise ValueError(f"Linea {numero}: etiqueta duplicada: {nombre}")
            etiquetas[nombre] = direccion
        if not linea:
            continue
        if linea == ".section .text" or re.fullmatch(r"\.global\s+[A-Za-z_][A-Za-z_0-9]*", linea):
            continue
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

def _codificar_instruccion(instruccion, direccion_actual, etiquetas):
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

    if nombre in {"slti", "sltiu", "xori", "ori", "andi"}:
        rd = registro(partes[1])
        rs1 = registro(partes[2])
        inmediato = int(partes[3], 0)

        if nombre == "slti":
            return codificar_slti(rd, rs1, inmediato)
        if nombre == "sltiu":
            return codificar_sltiu(rd, rs1, inmediato)
        if nombre == "xori":
            return codificar_xori(rd, rs1, inmediato)
        if nombre == "ori":
            return codificar_ori(rd, rs1, inmediato)
        return codificar_andi(rd, rs1, inmediato)

    if nombre in {"slli", "srli", "srai"}:
        rd = registro(partes[1])
        rs1 = registro(partes[2])
        shamt = int(partes[3], 0)

        if nombre == "slli":
            return codificar_slli(rd, rs1, shamt)
        if nombre == "srli":
            return codificar_srli(rd, rs1, shamt)
        return codificar_srai(rd, rs1, shamt)

    if nombre == "jalr":
        rd = registro(partes[1])
        offset_base = partes[2]
        inmediato = int(offset_base.split("(")[0], 0)
        rs1 = registro(offset_base.split("(")[1].replace(")", ""))
        return codificar_itype(rd, rs1, inmediato, 0b000, 0x67)

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

    if nombre == "blt":
        rs1 = registro(partes[1])
        rs2 = registro(partes[2])
        etiqueta = partes[3]

        offset = etiquetas[etiqueta] - direccion_actual

        return codificar_branch(rs1, rs2, offset, 0b100)

    if nombre == "bge":
        rs1 = registro(partes[1])
        rs2 = registro(partes[2])
        etiqueta = partes[3]

        offset = etiquetas[etiqueta] - direccion_actual

        return codificar_branch(rs1, rs2, offset, 0b101)

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



def codificar_instruccion(instruccion, direccion_actual, etiquetas):
    partes = instruccion.replace(",", " ").split()
    if not partes:
        raise ValueError("Instruccion vacia")
    nombre = partes[0]
    registros = {"add", "sub", "and", "or", "xor"}
    inmediatos = {"addi", "slti", "sltiu", "xori", "ori", "andi"}
    branches = {"beq", "bne", "blt", "bge", "bltu", "bgeu"}
    if nombre in {"slli", "srli", "srai", "sll", "srl", "sra"}:
        raise ValueError("Espino no implementa desplazamientos en la ALU")
    cuenta = 4 if nombre in registros | inmediatos | branches else 3
    if nombre not in registros | inmediatos | branches | {"lui", "lw", "sw", "jal", "jalr"}:
        raise ValueError(f"Instruccion no soportada: {nombre}")
    if len(partes) != cuenta:
        raise ValueError(f"{nombre}: se esperaban {cuenta-1} operandos")
    registro(partes[1])
    if nombre in registros | inmediatos | branches:
        registro(partes[2])
    if nombre in registros:
        registro(partes[3])
    if nombre in inmediatos:
        validar_rango(int(partes[3], 0), -2048, 2047)
    if nombre == "lui":
        validar_rango(int(partes[2], 0), 0, 0xfffff)
    if nombre in {"lw", "sw", "jalr"}:
        memoria = re.fullmatch(r"([^()]+)\((x[0-9]+)\)", partes[2])
        if not memoria:
            raise ValueError("Se esperaba offset(xN)")
        validar_rango(int(memoria[1], 0), -2048, 2047)
        registro(memoria[2])
    if nombre in branches | {"jal"}:
        destino = partes[-1]
        if destino not in etiquetas:
            raise ValueError(f"Etiqueta inexistente: {destino}")
        offset = etiquetas[destino] - direccion_actual
        limite = 4096 if nombre in branches else 1048576
        validar_rango(offset, -limite, limite-1)
        if offset % 4:
            raise ValueError("Salto no alineado a 4 bytes")
    return _codificar_instruccion(" ".join(partes), direccion_actual, etiquetas)


def validar_rango(valor, minimo, maximo):
    if not minimo <= valor <= maximo:
        raise ValueError(f"Inmediato {valor} fuera de rango [{minimo}, {maximo}]")


def ensamblar(texto, max_words=511):
    etiquetas, instrucciones = analizar_programa(texto.splitlines())
    if len(instrucciones) > max_words:
        raise ValueError(f"Programa excede {max_words} palabras disponibles")
    codigos = []
    for direccion, instruccion in instrucciones:
        try:
            codigos.append(codificar_instruccion(instruccion, direccion, etiquetas))
        except ValueError as exc:
            raise ValueError(f"PC 0x{direccion:04x}, {instruccion}: {exc}") from exc
    return codigos


def main():
    parser = argparse.ArgumentParser(description="Assembler del subconjunto Espino RV32E")
    parser.add_argument("source", nargs="?", type=Path, default=Path(__file__).with_name("game.s"))
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    try:
        words = ensamblar(args.source.read_text(encoding="utf-8"))
        output = args.output or args.source.with_suffix(".hex")
        output.write_text("".join(f"{word:08x}\n" for word in words), encoding="ascii")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(f"{output}: {len(words)} palabras")


if __name__ == "__main__":
    main()
