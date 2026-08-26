#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera as pecas de feed que faltavam no calendario (dias 21, 24 e 27).

Reproduz o gabarito dos cards que ja existem em deliverables/social/, medido a
partir de 14_como_funciona.png:

    y    0 - 264   faixa escura com a logo centralizada
    y  264 - 1004  corpo claro
    y 1004 - 1080  rodape escuro com contato

Paleta oficial UNICORPOS, sem variacao:
    GOLD #B8902B   DARK #1F2A24   GRAY #595959   LIGHT_BG #FBF6E8

Tipografia: Carlito (metricamente identica a Calibri, que e' a fonte da marca).

O layout e' MEDIDO ANTES DE DESENHAR: a funcao montar() calcula a altura total
do conteudo e vai reduzindo a escala ate caber acima do rodape. Sem isso, uma
caixa a mais invade a faixa escura — foi o que aconteceu na primeira versao.

    python3 ferramentas/gerar_pecas.py
"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Falta o Pillow. Rode: pip install Pillow")

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(os.path.dirname(AQUI))

SOCIAL = os.path.join(RAIZ, "deliverables", "social")
LOGO = os.path.join(RAIZ, "assets", "brand", "UNICORPOS_logo.png")

GOLD = (184, 144, 43)
DARK = (31, 42, 36)
DARK_BAND = (46, 48, 45)
GRAY = (89, 89, 89)
LIGHT_BG = (251, 246, 232)
WHITE = (254, 253, 250)

F = "/usr/share/fonts/truetype/crosextra/Carlito-%s.ttf"
LADO = 1080
TOPO = 264
RODAPE = 1004
MARGEM_INFERIOR = 24          # respiro minimo entre o conteudo e o rodape
X0, X1 = 90, LADO - 90


def fonte(peso, tam):
    return ImageFont.truetype(F % peso, int(round(tam)))


def largura(d, texto, f):
    a, _, c, _ = d.textbbox((0, 0), texto, font=f)
    return c - a


def centralizar(d, y, texto, f, cor):
    d.text(((LADO - largura(d, texto, f)) / 2, y), texto, font=f, fill=cor)


def quebrar(d, texto, f, limite):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if largura(d, teste, f) <= limite:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def base():
    """Fundo, faixa escura com logo no topo e rodape com contato."""
    im = Image.new("RGB", (LADO, LADO), WHITE)
    d = ImageDraw.Draw(im)

    d.rectangle([0, 0, LADO, TOPO], fill=DARK_BAND)

    logo = Image.open(LOGO).convert("RGBA")
    alvo_l = 560
    logo = logo.resize((alvo_l, round(logo.height * alvo_l / logo.width)), Image.LANCZOS)
    im.paste(logo, ((LADO - logo.width) // 2, (TOPO - logo.height) // 2), logo)

    d.rectangle([0, TOPO - 4, LADO, TOPO], fill=GOLD)

    d.rectangle([0, RODAPE, LADO, LADO], fill=DARK)
    centralizar(d, RODAPE + 26,
                "Planaltina/DF  ·  WhatsApp (61) 99578-9867  ·  @unicorposclinica",
                fonte("Regular", 22), (200, 195, 185))
    return im, d


def montar(kicker, titulo, caixas, nota):
    """
    Desenha a peca inteira. Mede primeiro; se nao couber, reduz a escala em
    passos de 4% ate caber. Devolve a imagem.
    """
    im, d = base()

    for passo in range(14):
        e = 1.0 - passo * 0.04           # escala

        f_k = fonte("Bold", 26 * e)
        f_t = fonte("Bold", 58 * e)
        f_ct = fonte("Bold", 34 * e)
        f_cc = fonte("Regular", 30 * e)
        f_n = fonte("Italic", 24 * e)

        pad = 40 * e                      # respiro interno da caixa
        lh_c = 40 * e                      # altura de linha do corpo
        lh_t = 70 * e                      # altura de linha do titulo
        gap = 26 * e                       # espaco entre caixas

        linhas_titulo = quebrar(d, titulo, f_t, 900)
        blocos = [(t, quebrar(d, c, f_cc, (X1 - X0) - 2 * pad)) for t, c in caixas]
        linhas_nota = quebrar(d, nota, f_n, X1 - X0)

        alturas = [pad * 0.7 + 50 * e + len(ls) * lh_c + pad * 0.75 for _, ls in blocos]

        total = (54 * e                                   # kicker
                 + len(linhas_titulo) * lh_t + 14 * e     # titulo
                 + sum(alturas) + gap * len(blocos)       # caixas
                 + 16 * e + len(linhas_nota) * (lh_c * 0.8))   # nota

        y0 = TOPO + 46 * e
        if y0 + total <= RODAPE - MARGEM_INFERIOR or passo == 13:
            break

    # --- desenha ------------------------------------------------------------
    y = y0
    centralizar(d, y, "  ".join(kicker.upper()), f_k, GOLD)
    y += 54 * e

    for linha in linhas_titulo:
        centralizar(d, y, linha, f_t, DARK)
        y += lh_t
    y += 14 * e

    for (t, linhas), h in zip(blocos, alturas):
        d.rectangle([X0, y, X1, y + h], fill=LIGHT_BG, outline=GOLD, width=3)
        d.text((X0 + pad, y + pad * 0.7), t, font=f_ct, fill=GOLD)
        yy = y + pad * 0.7 + 50 * e
        for linha in linhas:
            d.text((X0 + pad, yy), linha, font=f_cc, fill=DARK)
            yy += lh_c
        y += h + gap

    y += 16 * e
    for linha in linhas_nota:
        centralizar(d, y, linha, f_n, GRAY)
        y += lh_c * 0.8

    assert y <= RODAPE, "conteudo invadiu o rodape (y=%.0f)" % y
    return im


# ---------------------------------------------------------------------------
# As tres pecas
# ---------------------------------------------------------------------------

PECAS = [
    ("17_pos_laser", dict(
        kicker="Cuidados",
        titulo="Depois da sessão de laser",
        caixas=[
            ("Nas primeiras 24 horas",
             "Evite sol direto, água muito quente, sauna e atividade física intensa."),
            ("Todo dia, sem falta",
             "Protetor solar na área tratada, mesmo em dia nublado."),
            ("Pode acontecer",
             "Vermelhidão leve por algumas horas. Se persistir, fale com a gente."),
        ],
        nota="Cada pele responde de um jeito — a orientação final é a da sua avaliação.")),

    ("18_primeira_fisio", dict(
        kicker="Primeira vez",
        titulo="Nunca fez fisioterapia?",
        caixas=[
            ("1 · Avaliação",
             "Uma conversa e testes de movimento para entender sua queixa e seu objetivo."),
            ("2 · Plano de sessões",
             "Você fica sabendo quantas sessões, com que frequência e quanto custa."),
            ("3 · Atendimento individual",
             "Uma pessoa por vez, com hora marcada. Sem sala cheia."),
        ],
        nota="RT: Mario Sergio Fernandes de Lima — CREFITO-11 nº 442563-F")),

    ("19_biosseguranca", dict(
        kicker="Bastidores",
        titulo="O que você não vê",
        caixas=[
            ("Entre um atendimento e outro",
             "Maca, aparelhos e superfícies higienizados a cada paciente."),
            ("Material descartável",
             "O que é de uso único é descartado na sua frente."),
            ("Salas individuais",
             "Climatizadas e ventiladas, uma pessoa por vez."),
        ],
        nota="Biossegurança não é diferencial. É obrigação.")),
]


def main():
    if not os.path.exists(LOGO):
        sys.exit("Logo nao encontrada em %s" % LOGO)
    os.makedirs(SOCIAL, exist_ok=True)

    for nome, args in PECAS:
        im = montar(**args)
        destino = os.path.join(SOCIAL, nome + ".png")
        im.save(destino)
        print("  ok  %-22s %dx%d  %5.0f KB" % (
            nome, im.width, im.height, os.path.getsize(destino) / 1024))

    print("\n%d pecas em %s" % (len(PECAS), SOCIAL))


if __name__ == "__main__":
    main()
