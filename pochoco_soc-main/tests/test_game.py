"""Execute assembled machine words with MMIO and accelerated, deterministic time.
This functional model checks game rules; RTL timing is tested separately.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"sw"))
import assembler
MASK = 0xffffffff
HZ = 25_000_000

def signed(value, bits=32):
    return value-(1<<bits) if value & (1<<(bits-1)) else value

def bcd(value):
    value = min(99, value)
    return (value//10)*16 + value%10

class Machine:
    def __init__(self, seed_delay=0, start=0, long_response=False, timeout=False):
        source = (Path(__file__).resolve().parents[1]/"sw/game.s").read_text()
        self.labels, _ = assembler.analizar_programa(source.splitlines())
        self.words = assembler.ensamblar(source)
        self.reg = [0]*16
        self.pc = 0
        self.cycle = start
        self.ram = {}
        self.led_cycle = start
        self.prep_cycle = start
        self.targets = []
        self.measured = []
        self.displays = []
        self.warmup_pressed = False
        self.seed_delay = seed_delay
        self.press_at = self.release_at = 0
        self.mask = 0
        self.good = False
        self.long_response = long_response
        self.timeout = timeout

    def read(self, address):
        if address == 0x80000010:
            return self.led_cycle & MASK
        if address == 0x8000000c:
            if self.pc == self.labels["GOT_BTN"] and self.good:
                self.measured.append((self.cycle-self.led_cycle) & MASK)
            return self.cycle & MASK
        if address == 0x80000008:
            if not self.targets:
                if not self.warmup_pressed and self.cycle-self.prep_cycle >= 3*HZ+self.seed_delay:
                    self.warmup_pressed = True
                    return 1
                return 0
            return self.mask if self.press_at <= self.cycle < self.release_at else 0
        return self.ram.get(address, 0)

    def write(self, address, value):
        if address == 0x80000004:
            if value == 15:
                if self.targets:
                    assert self.cycle >= self.release_at, "new round while button held"
                self.prep_cycle = self.cycle
            elif value:
                assert self.cycle-self.prep_cycle >= 3*HZ, "preparation shorter than 3 seconds"
                assert value in (1,2,4,8)
                self.targets.append(value)
                n = len(self.targets)
                self.good = n != 4
                delay = int(HZ * (15.175 if self.long_response and n == 1 else .175+n*.021))
                if self.timeout and n == 4:
                    delay = 1 << 32
                self.press_at = self.cycle + delay
                self.release_at = self.press_at + 4*HZ
                if self.timeout and n == 4:
                    # No button is held in this attempt.
                    self.release_at = self.cycle
                self.mask = value if self.good else 15
            self.led_cycle = self.cycle
        elif address == 0x80000000:
            self.displays.append(value)
        else:
            self.ram[address] = value

    def run(self):
        for _ in range(300000):
            if self.pc == self.labels["HANG"]:
                return self
            word = self.words[self.pc//4]
            op, rd, f3 = word & 127, (word>>7)&31, (word>>12)&7
            ra, rb = (word>>15)&31, (word>>20)&31
            next_pc = self.pc + 4
            result = None
            if op == 0x37:
                result = word & 0xfffff000
            elif op == 0x13:
                assert f3 == 0
                result = self.reg[ra] + signed(word>>20,12)
            elif op == 0x33:
                a,b = self.reg[ra],self.reg[rb]
                if f3 == 0:
                    result = a-b if word>>30 & 1 else a+b
                elif f3 == 4:
                    result = a ^ b
                elif f3 == 7:
                    result = a & b
                else:
                    raise AssertionError(hex(word))
            elif op == 0x03:
                result = self.read((self.reg[ra]+signed(word>>20,12)) & MASK)
            elif op == 0x23:
                imm = ((word>>25)<<5) | ((word>>7)&31)
                self.write((self.reg[ra]+signed(imm,12)) & MASK,self.reg[rb])
            elif op == 0x63:
                imm = ((word>>31)<<12) | (((word>>7)&1)<<11) | (((word>>25)&63)<<5) | (((word>>8)&15)<<1)
                a,b = self.reg[ra],self.reg[rb]
                take = {0:a==b,1:a!=b,4:signed(a)<signed(b),5:signed(a)>=signed(b),6:a<b,7:a>=b}[f3]
                if take:
                    next_pc = self.pc + signed(imm,13)
            elif op == 0x6f:
                imm = ((word>>31)<<20) | (((word>>12)&255)<<12) | (((word>>20)&1)<<11) | (((word>>21)&1023)<<1)
                result = next_pc
                next_pc = self.pc + signed(imm,21)
            else:
                raise AssertionError(hex(word))
            if result is not None and rd:
                self.reg[rd] = result & MASK
            self.pc = next_pc
            self.cycle += 25000  # 1 ms/instruction; accelerate polling, not ISA semantics.
        raise AssertionError("game did not terminate")

class GameTests(unittest.TestCase):
    def verify_game(self, **kwargs):
        m = Machine(**kwargs).run()
        self.assertEqual(m.reg[2], 75_000_000)
        self.assertEqual(m.reg[3], 2_500_000)
        self.assertEqual(m.reg[8], 10)
        self.assertEqual(len(m.targets), 11)
        self.assertEqual(len(m.measured), 10)
        self.assertEqual(m.displays.count(0xee), 1)
        expected = [bcd(delta//(HZ//10)) for delta in m.measured]
        actual = [d for d in m.displays[:-1] if d != 0xee]
        self.assertEqual(actual, expected)
        self.assertEqual(m.displays[-1], bcd(sum(m.measured)//HZ))
        return m
    def test_ten_rounds_error_and_held_buttons(self):
        self.verify_game()
    def test_saturation_does_not_bias_average(self):
        self.verify_game(long_response=True)
    def test_counter_wrap(self):
        self.verify_game(start=MASK-2*HZ)
    def test_timeout_retries_without_scoring(self):
        self.verify_game(timeout=True)
    def test_human_timing_changes_sequence(self):
        first = self.verify_game(seed_delay=HZ//3)
        second = self.verify_game(seed_delay=2*HZ)
        self.assertNotEqual(first.targets, second.targets)

if __name__ == "__main__":
    unittest.main()
