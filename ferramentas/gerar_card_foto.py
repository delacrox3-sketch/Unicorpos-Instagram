#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera card de feed 1080x1350 (4:5) com FOTO + identidade UNICORPOS.

Gabarito (mesma faixa de topo dos cards 1080x1080 ja existentes, para a logo
sair do mesmo tamanho na grade do perfil):

    y      0 -  264   faixa escura com a logo centralizada
    y    264 -  900   foto (crop 1080x636, centralizado no ponto de interesse)
    y    900 - 1274   bloco creme com titulo e itens
    y   1274 - 1350   rodape escuro com contato

Paleta oficial, sem variacao:
    GOLD #B8902B   DARK #1F2A24   GRAY #595959   LIGHT_BG #FBF6E8

Tipografia: Carlito (metricamente identica a Calibri, fonte da marca).

Uso:
    python3 ferramentas/gerar_card_foto.py FOTO.jpg SAIDA.png
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
LOGO = os.path.join(RAIZ, "assets", "brand", "UNICORPOS_logo.png")

GOLD = (184, 144, 43)
DARK = (31, 42, 36)
DARK_BAND = (46, 48, 45)
GRAY = (89, 89, 89)
LIGHT_BG = (251, 246, 232)
WHITE = (254, 253, 250)

F = "/usr/share/fonts/truetype/crosextra/Carlito-%s.ttf"
W, H = 1080, 1350
TOPO = 264
FOTO_FIM = 840
RODAPE = 1274
X0, X1 = 78, W - 78

EYEBROW = "BEM-ESTAR"
TITULO = "Massagens e terapias corporais"
SUB = "Para quem precisa desacelerar"
ITENS = [
    "Massagem relaxante",
    "Massagem modeladora",
    "Drenagem linfática",
    "Liberação miofascial",
]
CAIXA = "Atendemos também aos sábados"
CONTATO = "Agende pelo WhatsApp (61) 99578-9867"


def fonte(peso, tam):
    return ImageFont.truetype(F % peso, int(round(tam)))


def larg(d, t, f):
    a, _, c, _ = d.textbbox((0, 0), t, font=f)
    return c - a


def centro(d, y, t, f, cor):
    d.text(((W - larg(d, t, f)) / 2, y), t, font=f, fill=cor)


def cobrir(img, alvo_w, alvo_h, foco_y=0.42):
    """Redimensiona cobrindo a area e corta mantendo proporcao."""
    escala = max(alvo_w / img.width, alvo_h / img.height)
    novo = img.resize(
        (int(round(img.width * escala)), int(round(img.height * escala))),
        Image.LANCZOS,
    )
    x = (novo.width - alvo_w) // 2
    y = int(round((novo.height - alvo_h) * foco_y))
    y = max(0, min(y, novo.height - alvo_h))
    return novo.crop((x, y, x + alvo_w, y + alvo_h))


def montar(caminho_foto, saida):
    card = Image.new("RGB", (W, H), LIGHT_BG)
    d = ImageDraw.Draw(card)

    # ---- faixa de topo + logo
    d.rectangle([0, 0, W, TOPO], fill=DARK_BAND)
    logo = Image.open(LOGO).convert("RGBA")
    lw = W - 60
    lh = int(round(lw * logo.height / logo.width))  # 4,13:1 preservado
    logo = logo.resize((lw, lh), Image.LANCZOS)
    card.paste(logo, ((W - lw) // 2, (TOPO - lh) // 2), logo)

    # ---- foto
    foto = Image.open(caminho_foto).convert("RGB")
    foto = cobrir(foto, W, FOTO_FIM - TOPO)
    card.paste(foto, (0, TOPO))

    # filete dourado separando foto e conteudo
    d.rectangle([0, FOTO_FIM - 4, W, FOTO_FIM], fill=GOLD)

    # ---- bloco de conteudo
    y = FOTO_FIM + 34
    f_eye = fonte("Bold", 26)
    d.text(
        ((W - larg(d, EYEBROW, f_eye) - 7 * len(EYEBROW)) / 2, y),
        EYEBROW,
        font=f_eye,
        fill=GOLD,
        # espacamento entre letras manual
    )
    # redesenha com tracking (Pillow nao tem letter-spacing nativo)
    d.rectangle([0, y - 4, W, y + 34], fill=LIGHT_BG)
    tracking = 7
    total = sum(larg(d, c, f_eye) + tracking for c in EYEBROW) - tracking
    x = (W - total) / 2
    for c in EYEBROW:
        d.text((x, y), c, font=f_eye, fill=GOLD)
        x += larg(d, c, f_eye) + tracking
    y += 46

    f_tit = fonte("Bold", 52)
    centro(d, y, TITULO, f_tit, DARK)
    y += 68

    d.rectangle([(W - 120) / 2, y, (W + 120) / 2, y + 3], fill=GOLD)
    y += 22

    f_sub = fonte("Italic", 28)
    centro(d, y, SUB, f_sub, GRAY)
    y += 54

    # ---- itens em duas colunas com bullet dourado
    f_it = fonte("Regular", 30)
    f_bu = fonte("Bold", 30)
    col_x = [X0 + 18, W // 2 + 18]
    linha_h = 46
    for i, item in enumerate(ITENS):
        cx = col_x[i % 2]
        cy = y + (i // 2) * linha_h
        d.text((cx, cy), "•", font=f_bu, fill=GOLD)
        d.text((cx + 26, cy), item, font=f_it, fill=DARK)
    y += 2 * linha_h + 20

    # ---- caixa de destaque padrao
    cx0, cx1 = X0, X1
    cy0 = y
    cy1 = y + 62
    d.rounded_rectangle(
        [cx0, cy0, cx1, cy1], radius=8, fill=(255, 252, 243), outline=GOLD, width=2
    )
    f_cx = fonte("Regular", 28)
    centro(d, cy0 + 15, CAIXA, f_cx, DARK)

    # ---- rodape
    d.rectangle([0, RODAPE, W, H], fill=DARK_BAND)
    marca = Image.open(LOGO).convert("RGBA")
    marca = marca.crop((0, 0, 1234, 1234))  # simbolo (bonecos) do lado esquerdo
    mh = 46
    mw = int(round(marca.width * mh / marca.height))
    marca = marca.resize((mw, mh), Image.LANCZOS)
    card.paste(marca, (X0 - 30, RODAPE + (H - RODAPE - mh) // 2), marca)
    f_rod = fonte("Regular", 27)
    d.text(
        (X0 + mw - 8, RODAPE + (H - RODAPE - 34) // 2),
        CONTATO,
        font=f_rod,
        fill=(226, 218, 196),
    )

    card.save(saida, "PNG", optimize=True)
    print("gerado:", saida, card.size)


def montar_story(caminho_foto, saida):
    """Versao 9:16 (1080x1920) para Stories.

    Areas de seguranca do Instagram: 250 px no topo (nome do perfil) e 250 px
    na base (campo de resposta). Todo o texto fica entre y=420 e y=1620.
    """
    SW, SH = 1080, 1920
    FOTO_Y0, FOTO_Y1 = 530, 1130
    story = Image.new("RGB", (SW, SH), DARK)
    d = ImageDraw.Draw(story)

    # ---- logo dentro da area segura do topo
    logo = Image.open(LOGO).convert("RGBA")
    lw = 820
    lh = int(round(lw * logo.height / logo.width))
    logo = logo.resize((lw, lh), Image.LANCZOS)
    story.paste(logo, ((SW - lw) // 2, 270), logo)

    # ---- faixa da foto (mantem a composicao original, sem zoom excessivo)
    foto = Image.open(caminho_foto).convert("RGB")
    story.paste(cobrir(foto, SW, FOTO_Y1 - FOTO_Y0, foco_y=0.45), (0, FOTO_Y0))
    d.rectangle([0, FOTO_Y0 - 4, SW, FOTO_Y0], fill=GOLD)
    d.rectangle([0, FOTO_Y1, SW, FOTO_Y1 + 4], fill=GOLD)

    # ---- texto
    y = 1190
    f_eye = fonte("Bold", 30)
    tracking = 8
    total = sum(larg(d, c, f_eye) + tracking for c in EYEBROW) - tracking
    x = (SW - total) / 2
    for c in EYEBROW:
        d.text((x, y), c, font=f_eye, fill=GOLD)
        x += larg(d, c, f_eye) + tracking
    y += 55

    f_tit = fonte("Bold", 62)
    for linha in ["Massagens e terapias", "corporais"]:
        d.text(((SW - larg(d, linha, f_tit)) / 2, y), linha, font=f_tit, fill=WHITE)
        y += 76
    y += 14

    d.rectangle([(SW - 140) / 2, y, (SW + 140) / 2, y + 4], fill=GOLD)
    y += 32

    f_it = fonte("Regular", 34)
    for linha in [
        "Relaxante  ·  Modeladora",
        "Drenagem linfática  ·  Liberação miofascial",
    ]:
        d.text(
            ((SW - larg(d, linha, f_it)) / 2, y), linha, font=f_it, fill=(226, 218, 196)
        )
        y += 52
    y += 26

    # ---- CTA (acima da area de resposta do Instagram)
    f_cta = fonte("Bold", 34)
    t = "WhatsApp (61) 99578-9867"
    tw = larg(d, t, f_cta)
    bx0, bx1 = (SW - tw) / 2 - 46, (SW + tw) / 2 + 46
    d.rounded_rectangle([bx0, y, bx1, y + 76], radius=38, fill=GOLD)
    d.text(((SW - tw) / 2, y + 18), t, font=f_cta, fill=(255, 253, 246))

    story.save(saida, "PNG", optimize=True)
    print("gerado:", saida, story.size)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    if "--story" in sys.argv:
        args = [a for a in sys.argv[1:] if a != "--story"]
        montar_story(args[0], args[1])
    else:
        montar(sys.argv[1], sys.argv[2])
