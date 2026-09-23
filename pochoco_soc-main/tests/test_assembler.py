import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sw"))
import assembler as a

class AssemblerTests(unittest.TestCase):
    def test_known_encodings(self):
        cases = {"lui x1, 0x80000": 0x800000b7,
                 "addi x2, x0, -1": 0xfff00113,
                 "ori x3, x2, 15": 0x00f16193,
                 "sw x3, 4(x1)": 0x0030a223,
                 "lw x4, 4(x1)": 0x0040a203,
                 "sub x3, x2, x1": 0x401101b3,
                 "jalr x0, 0(x1)": 0x00008067}
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(a.ensamblar(source), [expected])
    def test_labels_and_branches(self):
        self.assertEqual(a.ensamblar("loop: addi x1,x0,1\nbne x1,x0,loop\njal x0,loop"),
                         [0x00100093, 0xfe009ee3, 0xff9ff06f])
    def test_invalid_input(self):
        for source in ["ori x1,x0,4096", "addi x16,x0,0", "addi a0,x0,0",
                       "add x1,x0", "add x1,x0,x0,extra", "mul x1,x2,x3",
                       "bad: add x1,x0,x0\nbad:", "jal x0,missing", ".word 0",
                       "slli x1,x1,2", "lw x1,2048(x2)", "lw x1,4x2",
                       "lui x1,0x100000", "addi x1,x0,-2049"]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                a.ensamblar(source)
    def test_branch_bounds(self):
        for target in [4096, -4100, 2]:
            with self.subTest(target=target), self.assertRaises(ValueError):
                a.codificar_instruccion("beq x0,x0,target",0,{"target":target})
    def test_capacity(self):
        with self.assertRaises(ValueError):
            a.ensamblar("addi x0,x0,0\n" * 512)
    def test_all_programs(self):
        for source in (Path(__file__).resolve().parents[1]/"sw").glob("*.s"):
            with self.subTest(source=source):
                self.assertTrue(a.ensamblar(source.read_text(encoding="utf-8")))

if __name__ == "__main__":
    unittest.main()
