#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Banner de vaga (recrutamento) no padrao UNICORPOS — 1080x1350.

Pensado para disparo em WhatsApp (grupos e status): texto grande, poucas
linhas, contraste alto, tudo legivel na miniatura do chat.

Gabarito:
    y      0 -  264   faixa escura com a logo
    y    264 - 1230   corpo creme (chapeu, titulo, local, requisitos)
    y   1230 - 1350   faixa escura com o CTA

Paleta oficial, sem variacao:
    GOLD #B8902B   DARK #1F2A24   GRAY #595959   LIGHT_BG #FBF6E8

Uso:
    python3 ferramentas/gerar_banner_vaga.py SAIDA.png
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
LOGO = os.path.join(RAIZ, "assets", "brand", "UNICORPOS_logo.png")

GOLD = (184, 144, 43)
DARK = (31, 42, 36)
DARK_BAND = (46, 48, 45)
GRAY = (89, 89, 89)
LIGHT_BG = (251, 246, 232)

F = "/usr/share/fonts/truetype/crosextra/Carlito-%s.ttf"
W, H = 1080, 1350
TOPO = 264
RODAPE = 1170
X0, X1 = 78, W - 78

CHAPEU = "ESTAMOS CONTRATANDO"
TITULO = "Clínico(a) Médico(a)"
LOCAL = "Planaltina/DF · atendimento na clínica"
REQ_TITULO = "Requisitos"
REQUISITOS = [
    "Graduação em Medicina",
    "CRM-DF ativo e regular",
    "Experiência em atendimento ambulatorial",
    "Perfil acolhedor e trabalho em equipe",
]
CAIXA = "Vínculo e carga horária combinados na entrevista"
CTA = "Envie seu currículo"
CTA_WPP = "WhatsApp (61) 99578-9867"
CTA_MAIL = "crm@unicorpos.com.br"


def fonte(peso, tam):
    return ImageFont.truetype(F % peso, int(round(tam)))


def larg(d, t, f):
    a, _, c, _ = d.textbbox((0, 0), t, font=f)
    return c - a


def centro(d, y, t, f, cor):
    d.text(((W - larg(d, t, f)) / 2, y), t, font=f, fill=cor)


def tracking(d, y, t, f, cor, esp):
    total = sum(larg(d, c, f) + esp for c in t) - esp
    x = (W - total) / 2
    for c in t:
        d.text((x, y), c, font=f, fill=cor)
        x += larg(d, c, f) + esp


def montar(saida):
    card = Image.new("RGB", (W, H), LIGHT_BG)
    d = ImageDraw.Draw(card)

    # ---- faixa de topo + logo
    d.rectangle([0, 0, W, TOPO], fill=DARK_BAND)
    logo = Image.open(LOGO).convert("RGBA")
    lw = W - 60
    lh = int(round(lw * logo.height / logo.width))  # 4,13:1 preservado
    logo = logo.resize((lw, lh), Image.LANCZOS)
    card.paste(logo, ((W - lw) // 2, (TOPO - lh) // 2), logo)

    # ---- chapeu
    y = TOPO + 78
    tracking(d, y, CHAPEU, fonte("Bold", 30), GOLD, 8)
    y += 74

    # ---- titulo
    f_tit = fonte("Bold", 74)
    centro(d, y, TITULO, f_tit, DARK)
    y += 104

    d.rectangle([(W - 140) / 2, y, (W + 140) / 2, y + 4], fill=GOLD)
    y += 34

    centro(d, y, LOCAL, fonte("Italic", 30), GRAY)
    y += 96

    # ---- caixa de requisitos (padrao: fundo creme + borda dourada)
    f_req_tit = fonte("Bold", 32)
    f_req = fonte("Regular", 32)
    f_bu = fonte("Bold", 32)
    linha_h = 54
    bh = 44 + 46 + len(REQUISITOS) * linha_h + 20
    d.rounded_rectangle(
        [X0, y, X1, y + bh], radius=10, fill=(255, 252, 243), outline=GOLD, width=3
    )
    ty = y + 30
    d.text((X0 + 44, ty), REQ_TITULO, font=f_req_tit, fill=GOLD)
    ty += 60
    for item in REQUISITOS:
        d.text((X0 + 44, ty), "•", font=f_bu, fill=GOLD)
        d.text((X0 + 76, ty), item, font=f_req, fill=DARK)
        ty += linha_h
    y += bh + 56

    # ---- faixa escura de observacao
    d.rounded_rectangle([X0, y, X1, y + 76], radius=10, fill=DARK)
    centro(d, y + 21, CAIXA, fonte("Regular", 29), (233, 226, 208))

    # ---- rodape com CTA (WhatsApp + e-mail)
    d.rectangle([0, RODAPE, W, H], fill=DARK_BAND)
    d.rectangle([0, RODAPE, W, RODAPE + 5], fill=GOLD)
    centro(d, RODAPE + 26, CTA, fonte("Regular", 30), (198, 194, 180))
    centro(d, RODAPE + 68, CTA_WPP, fonte("Bold", 38), (233, 199, 108))
    centro(d, RODAPE + 118, CTA_MAIL, fonte("Regular", 31), (222, 216, 200))

    card.save(saida, "PNG", optimize=True)
    print("gerado:", saida, card.size)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    montar(sys.argv[1])
