"""Gera a apresentação (PPTX) e a versão em PDF.

1. node presentation/gerar_slides.js  -> Apresentacao_Nyquist.pptx (pptxgenjs)
2. remove entradas de diretório do ZIP (atrapalham abrir pela nuvem)
3. converte para PDF com o PowerPoint (COM), se disponível

Uso: python presentation/construir.py   (NODE_PATH deve apontar para um node_modules com pptxgenjs)
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PPTX = AQUI / "Apresentacao_Nyquist.pptx"
PDF = AQUI / "Apresentacao_Nyquist.pdf"


def limpa_zip(arq: Path):
    fd, nome = tempfile.mkstemp(suffix=".pptx")
    os.close(fd)
    tmp = Path(nome)
    with zipfile.ZipFile(arq) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if not item.filename.endswith("/"):
                zout.writestr(item, zin.read(item.filename))
    shutil.move(tmp, arq)


def para_pdf(src: Path, dst: Path):
    ps = (f"$pp = New-Object -ComObject PowerPoint.Application; "
          f"$p = $pp.Presentations.Open('{src}', $true, $false, $false); "
          f"$p.SaveAs('{dst}', 32); $p.Close(); $pp.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


if __name__ == "__main__":
    subprocess.run(["node", str(AQUI / "gerar_slides.js")], check=True, env=os.environ)
    limpa_zip(PPTX)
    if sys.platform == "win32":
        para_pdf(PPTX, PDF)
        print("PDF:", PDF)
