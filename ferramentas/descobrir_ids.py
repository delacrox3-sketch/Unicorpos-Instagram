#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descobre, uma unica vez, os tres numeros que o robo precisa:

  1. IG_USER_ID       — o id da conta @unicorposclinica
  2. IG_LOCATION_ID   — o id do lugar "Planaltina (Distrito Federal)"
  3. token de 60 dias — trocado a partir do token curto do Explorer

Rode na sua maquina, nao no GitHub:

    META_APP_ID=... META_APP_SECRET=... TOKEN_CURTO=... python3 ferramentas/descobrir_ids.py

O TOKEN_CURTO sai de https://developers.facebook.com/tools/explorer, com o app
"UNICORPOS Social" (ID 1572907397545576) selecionado e as permissoes
instagram_basic, instagram_content_publish, pages_read_engagement,
pages_show_list e business_management.

ATENCAO ao passo 2: existe "Planaltina" no Distrito Federal e "Planaltina de
Goias", que e' outra cidade, a 10 km de distancia. O script mostra as duas para
voce escolher com os olhos. Marcar a errada ja custou retrabalho antes.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0"


def get(caminho, **params):
    url = "%s/%s?%s" % (API, caminho, urllib.parse.urlencode(params))
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    app_id = os.environ.get("META_APP_ID")
    app_secret = os.environ.get("META_APP_SECRET")
    curto = os.environ.get("TOKEN_CURTO")
    if not (app_id and app_secret and curto):
        sys.exit(__doc__)

    # ---- 1. token de 60 dias ----------------------------------------------
    print("== Trocando por token de longa duracao ==")
    d = get("oauth/access_token",
            grant_type="fb_exchange_token",
            client_id=app_id,
            client_secret=app_secret,
            fb_exchange_token=curto)
    token = d["access_token"]
    print("   ok, vence em ~%d dias\n" % (int(d.get("expires_in", 0)) // 86400))

    # ---- 2. IG_USER_ID -----------------------------------------------------
    print("== Contas do Instagram ligadas as suas paginas ==")
    paginas = get("me/accounts", access_token=token,
                  fields="name,instagram_business_account{id,username}")
    ig_id = None
    for p in paginas.get("data", []):
        ig = p.get("instagram_business_account")
        if ig:
            print("   Pagina: %-30s  @%s  id=%s" % (p["name"], ig.get("username"), ig["id"]))
            if ig.get("username") == "unicorposclinica":
                ig_id = ig["id"]
    if not ig_id:
        print("\n   Nao achei @unicorposclinica. A conta precisa ser Profissional")
        print("   (Business ou Creator) e estar ligada a uma Pagina do Facebook.")
    print()

    # ---- 3. IG_LOCATION_ID -------------------------------------------------
    # `type=place` e' obrigatorio. Sem ele, a busca devolve Paginas do Facebook
    # sem endereco fisico, e a API de publicacao recusa esses IDs com o subcode
    # 2207019 — foi o que derrubou o post do dia 10 em 26/08/2026.
    # O `center`/`distance` em volta de Planaltina/DF ainda exclui Planaltina de
    # Goias, que fica ~20 km ao norte.
    print("== Lugares chamados 'Planaltina' (só locais físicos, raio de 15 km) ==")
    print("   ESCOLHA O DO DISTRITO FEDERAL. 'Planaltina de Goias' e' outra cidade.\n")
    lugares = get("pages/search", access_token=token, q="Planaltina",
                  type="place", center="-15.6214,-47.6489", distance=15000,
                  fields="id,name,location", limit=50)
    for lug in lugares.get("data", []):
        loc = lug.get("location") or {}
        estado = loc.get("state") or "?"
        cidade = loc.get("city") or "?"
        marca = "  <== provavelmente este" if estado in ("DF", "Distrito Federal") else ""
        print("   id=%-18s %-38s [%s / %s]%s" % (
            lug["id"], lug["name"][:38], cidade, estado, marca))
    print("\n   Antes de gravar o secret, VALIDE o id escolhido:")
    print("     python3 ferramentas/achar_local.py")
    print("   Ele cria um container de teste com aquele local e diz se a Meta aceita.")

    print("\n" + "=" * 62)
    print("Guarde no repositorio, em Settings > Secrets and variables > Actions:")
    print("  Secret   IG_TOKEN         = (o token longo; nao imprimi aqui de proposito)")
    print("  Secret   IG_USER_ID       = %s" % (ig_id or "(veja a lista acima)"))
    print("  Secret   IG_LOCATION_ID   = (o id do Planaltina do DF, da lista acima)")
    print("  Secret   META_APP_ID      = %s" % app_id)
    print("  Secret   META_APP_SECRET  = (o mesmo que voce usou aqui)")
    print("  Variable BASE_URL_IMAGENS = https://raw.githubusercontent.com/USUARIO/REPO/main")
    print("  Variable EMAIL_DESTINO    = suporte@unicorpos.com.br")
    print("=" * 62)
    print("\nO token longo esta abaixo. Copie e feche o terminal depois:\n")
    print(token)


if __name__ == "__main__":
    main()
