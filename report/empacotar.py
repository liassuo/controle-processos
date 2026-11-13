"""Gera uma cópia autocontida do artigo (caminhos achatados), pronta para compilar
fora do repositório ou no Overleaf. Uso: python report/empacotar.py <pasta_destino>"""
import shutil
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REP = RAIZ / "report"


def empacota(destino: Path) -> Path:
    if destino.exists():
        shutil.rmtree(destino)
    (destino / "figuras").mkdir(parents=True)
    (destino / "tabelas").mkdir()
    for f in (RAIZ / "results/figuras").glob("*.pdf"):
        shutil.copy2(f, destino / "figuras" / f.name)
    for f in (RAIZ / "results/tinkercad").glob("*.png"):
        shutil.copy2(f, destino / "figuras" / f.name)
    for f in (RAIZ / "results/tabelas").glob("*.tex"):
        shutil.copy2(f, destino / "tabelas" / f.name)
    for nome in ("referencias.bib", "sbc-template.sty", "sbc.bst", "artigo.pdf"):
        if (REP / nome).exists():
            shutil.copy2(REP / nome, destino / nome)
    for f in REP.glob("*.tex"):
        linhas = []
        for linha in f.read_text(encoding="utf-8").split("\n"):
            if linha.startswith("\\graphicspath"):
                linha = "\\graphicspath{{figuras/}}"
            linhas.append(linha.replace("../results/tabelas/", "tabelas/"))
        (destino / f.name).write_text("\n".join(linhas), encoding="utf-8")
    zip_path = destino.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in destino.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(destino))
    return zip_path


if __name__ == "__main__":
    print(empacota(Path(sys.argv[1]).resolve()))
