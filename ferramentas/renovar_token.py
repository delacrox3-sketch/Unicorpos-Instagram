#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Troca o token de longa duracao do Instagram por um novo, com mais 60 dias.

Roda no workflow renovar-token.yml, todo dia 1. Tambem pode rodar na mao:

    META_APP_ID=... META_APP_SECRET=... IG_TOKEN=... python3 ferramentas/renovar_token.py

Escreve o token novo em GITHUB_OUTPUT para o workflow guardar no segredo IG_TOKEN.
Nunca imprime o token no log.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0"


def main():
    app_id = os.environ.get("META_APP_ID")
    app_secret = os.environ.get("META_APP_SECRET")
    token = os.environ.get("IG_TOKEN")

    faltando = [k for k, v in [("META_APP_ID", app_id),
                               ("META_APP_SECRET", app_secret),
                               ("IG_TOKEN", token)] if not v]
    if faltando:
        sys.exit("Faltam variaveis: %s" % ", ".join(faltando))

    url = "%s/oauth/access_token?%s" % (API, urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": token,
    }))

    with urllib.request.urlopen(url, timeout=30) as r:
        dados = json.loads(r.read().decode())

    novo = dados.get("access_token")
    if not novo:
        sys.exit("A Meta nao devolveu token novo: %s" % dados)

    dias = int(dados.get("expires_in", 0)) // 86400
    print("Token novo obtido. Vence em aproximadamente %d dias." % dias)

    saida = os.environ.get("GITHUB_OUTPUT")
    if saida:
        with open(saida, "a") as fh:
            fh.write("token=%s\n" % novo)
    else:
        print("\nSem GITHUB_OUTPUT. Copie o token abaixo para o segredo IG_TOKEN:\n")
        print(novo)


if __name__ == "__main__":
    main()
