#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte as pecas de deliverables/social/ (PNG) para JPEG em img/.

A API de publicacao do Instagram so aceita JPEG. PNG e' recusado no momento de
criar o container, com uma mensagem generica que custa tempo para diagnosticar.
Por isso a conversao acontece aqui, uma vez, e nao no ar.

    python3 ferramentas/preparar_imagens.py

Regras que a API impoe e que este script respeita:
  - JPEG, sem canal alfa
  - proporcao entre 4:5 e 1.91:1
  - largura entre 320 e 1440 px
  - ate 8 MB
"""

import json
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta o Pillow. Rode: pip install Pillow")

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(AQUI, "img")

ORIGEM_PADRAO = os.path.join(
    os.path.expanduser("~"),
    "Claude", "Projects", "UNICORPOS", "deliverables", "social",
)

LARGURA_MAX = 1440
TAMANHO_MAX = 8 * 1024 * 1024


def converter(origem, nome):
    """Le a peca, achata sobre branco e grava JPEG. Devolve o caminho ou None."""
    for ext in (".png", ".jpg", ".jpeg"):
        caminho = os.path.join(origem, nome + ext)
        if os.path.exists(caminho):
            break
    else:
        return None

    im = Image.open(caminho)

    # PNG com transparencia vira preto ao salvar em JPEG. Achata sobre branco.
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fundo = Image.new("RGB", im.size, (255, 255, 255))
        fundo.paste(im, mask=im.split()[-1])
        im = fundo
    else:
        im = im.convert("RGB")

    if im.width > LARGURA_MAX:
        altura = round(im.height * LARGURA_MAX / im.width)
        im = im.resize((LARGURA_MAX, altura), Image.LANCZOS)

    proporcao = im.width / im.height
    aviso = ""
    if not (0.8 <= proporcao <= 1.91):
        aviso = "  <-- proporcao %.2f fora do aceito pela API (0.80 a 1.91)" % proporcao

    saida = os.path.join(DESTINO, nome + ".jpg")
    qualidade = 92
    while True:
        im.save(saida, "JPEG", quality=qualidade, optimize=True, progressive=True)
        if os.path.getsize(saida) <= TAMANHO_MAX or qualidade <= 60:
            break
        qualidade -= 8

    return saida, im.size, os.path.getsize(saida), aviso


def main():
    origem = sys.argv[1] if len(sys.argv) > 1 else ORIGEM_PADRAO
    if not os.path.isdir(origem):
        sys.exit("Pasta de origem nao encontrada: %s" % origem)

    os.makedirs(DESTINO, exist_ok=True)

    with open(os.path.join(AQUI, "calendario.json"), encoding="utf-8") as fh:
        cal = json.load(fh)

    nomes = sorted({d["arquivo"] for d in cal["dias"] if d.get("arquivo")})

    faltando = []
    for nome in nomes:
        r = converter(origem, nome)
        if r is None:
            faltando.append(nome)
            print("  FALTA   %s" % nome)
            continue
        saida, tam, bytes_, aviso = r
        print("  ok      %-22s %dx%d  %5.0f KB%s" % (
            nome, tam[0], tam[1], bytes_ / 1024, aviso))

    print("\n%d pecas em %s" % (len(nomes) - len(faltando), DESTINO))
    if faltando:
        print("Sem arquivo de origem: %s" % ", ".join(faltando))
        sys.exit(1)


if __name__ == "__main__":
    main()
