"""Run Python regressions and Icarus RTL simulations, without programming a board."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sw"))
import assembler

def run(command, **kwargs):
    subprocess.run([str(x) for x in command], check=True, **kwargs)

def main():
    run([sys.executable, "-B", "-m", "unittest", "discover", "-s", ROOT/"tests", "-v"])
    iv = os.environ.get("IVERILOG") or shutil.which("iverilog")
    vp = os.environ.get("VVP") or shutil.which("vvp")
    if not iv and Path("C:/iverilog/bin/iverilog.exe").exists():
        iv, vp = "C:/iverilog/bin/iverilog.exe", "C:/iverilog/bin/vvp.exe"
    if not iv or not vp:
        raise SystemExit("Icarus missing: install iverilog/vvp or set IVERILOG and VVP")
    with tempfile.TemporaryDirectory(prefix="pochoco-tests-") as directory:
        work = Path(directory)
        words = assembler.ensamblar((ROOT/"tests/core.s").read_text())
        (work/"core.hex").write_text("".join(f"{w:08x}\n" for w in words + [0]*(512-len(words))))
        rtl = list((ROOT/"rtl").rglob("*.v"))
        model = ROOT/"tests/ram_model.v"
        for name in ["core", "periph", "spi", "decoder"]:
            output = work/(name+".vvp")
            run([iv,"-g2012","-s",name+"_tb","-o",output,*rtl,model,ROOT/"tests"/(name+"_tb.v")])
            run([vp,output],cwd=work)
        run([iv,"-g2012","-s","game_top","-o",work/"top.vvp",*rtl,model])

if __name__ == "__main__":
    main()
