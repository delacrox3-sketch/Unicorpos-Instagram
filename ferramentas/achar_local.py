#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acha e VALIDA o IG_LOCATION_ID de Planaltina (Distrito Federal).

Por que este script existe
--------------------------
O descobrir_ids.py usava `pages/search` sem `type=place`. Esse endpoint devolve
Paginas do Facebook — inclusive paginas de comunidade e de "interesse", que nao
tem endereco fisico. A API de publicacao do Instagram recusa esses IDs com:

    OAuthException code 100, subcode 2207019
    "A identificacao de localizacao a seguir e invalida, nao pode ser vista
     ou nao existe"

Foi exatamente o que derrubou o post do dia 10 em 26/08/2026.

Duas correcoes aqui:
  1. busca com `type=place` e `center`/`distance` em volta de Planaltina/DF,
     o que ja exclui Planaltina de Goias por distancia;
  2. valida cada candidato de verdade — cria um container de midia com aquele
     location_id e le a resposta. Container criado e' o unico teste que prova
     que o ID serve. Nada e' publicado: containers nao publicados expiram em
     24h sozinhos.

Como rodar (na sua maquina, nao no GitHub)
------------------------------------------
    IG_USER_ID=...  IG_TOKEN=...  \
    BASE_URL_IMAGENS=https://raw.githubusercontent.com/delacrox3-sketch/Unicorpos-Instagram/main \
    python3 ferramentas/achar_local.py

Opcoes:
    --q "Planaltina"     termo de busca (padrao: Planaltina)
    --centro LAT,LON     centro da busca (padrao: Planaltina/DF)
    --raio METROS        raio da busca (padrao: 15000)
    --validar N          quantos candidatos testar (padrao: 8)
    --sem-validar        so lista, nao cria container nenhum

No fim ele imprime o ID aprovado. Guarde em Settings > Secrets and variables >
Actions > IG_LOCATION_ID.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0"

# Planaltina/DF, Setor Tradicional. Aproximado de proposito: serve so para
# centrar a busca. Planaltina de Goias fica ~20 km ao norte, entao um raio de
# 15 km ja resolve a confusao que sempre deu retrabalho.
CENTRO_PADRAO = "-15.6214,-47.6489"


def chamar(caminho, **params):
    url = "%s/%s?%s" % (API, caminho, urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode(errors="replace")
        try:
            return None, json.loads(detalhe).get("error", {})
        except Exception:
            return None, {"message": detalhe, "code": e.code}


def postar(caminho, **campos):
    url = "%s/%s" % (API, caminho)
    corpo = urllib.parse.urlencode(campos).encode()
    try:
        req = urllib.request.Request(url, data=corpo, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode(errors="replace")
        try:
            return None, json.loads(detalhe).get("error", {})
        except Exception:
            return None, {"message": detalhe, "code": e.code}


def eh_df(loc):
    estado = (loc.get("state") or "").strip().lower()
    cidade = (loc.get("city") or "").strip().lower()
    if "goi" in cidade or "goi" in estado:
        return False
    return estado in ("df", "distrito federal") or "bras" in cidade or "planaltina" in cidade


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--q", default="Planaltina")
    p.add_argument("--centro", default=os.environ.get("CENTRO_BUSCA", CENTRO_PADRAO))
    p.add_argument("--raio", type=int, default=15000)
    p.add_argument("--validar", type=int, default=8)
    p.add_argument("--sem-validar", action="store_true")
    args = p.parse_args()

    token = os.environ.get("IG_TOKEN")
    ig_user_id = os.environ.get("IG_USER_ID")
    base = (os.environ.get("BASE_URL_IMAGENS") or "").rstrip("/")
    if not token:
        sys.exit("Falta IG_TOKEN no ambiente.\n\n" + __doc__)
    if not args.sem_validar and not (ig_user_id and base):
        sys.exit("Para validar preciso de IG_USER_ID e BASE_URL_IMAGENS.\n"
                 "Ou rode com --sem-validar para so listar.\n\n" + __doc__)

    # ---- busca -------------------------------------------------------------
    print("== Locais fisicos perto de Planaltina/DF ==")
    print("   busca: q=%r  centro=%s  raio=%dm  type=place\n" % (
        args.q, args.centro, args.raio))

    dados, erro = chamar("pages/search",
                         access_token=token,
                         q=args.q,
                         type="place",
                         center=args.centro,
                         distance=args.raio,
                         fields="id,name,location,link,is_permanently_closed",
                         limit=50)
    if erro:
        print("   A busca falhou: %s" % erro.get("message"))
        print("   Se falar em permissao, o token precisa de pages_read_engagement.")
        return 1

    itens = dados.get("data", [])
    if not itens:
        print("   Nenhum local encontrado. Tente aumentar o --raio ou mudar o --q.")
        return 1

    candidatos = []
    for lug in itens:
        loc = lug.get("location") or {}
        if lug.get("is_permanently_closed"):
            continue
        candidatos.append({
            "id": lug["id"],
            "nome": lug.get("name") or "?",
            "cidade": loc.get("city") or "?",
            "estado": loc.get("state") or "?",
            "rua": loc.get("street") or "",
            "cep": loc.get("zip") or "",
            "df": eh_df(loc),
        })

    # DF primeiro, para o que interessa aparecer no topo
    candidatos.sort(key=lambda c: (not c["df"], c["nome"]))

    for i, c in enumerate(candidatos, 1):
        marca = "" if c["df"] else "   [FORA DO DF — nao use]"
        print("  %2d. id=%-18s %-34s" % (i, c["id"], c["nome"][:34]))
        print("      %s / %s   %s %s%s" % (c["cidade"], c["estado"], c["rua"], c["cep"], marca))

    if args.sem_validar:
        print("\n(--sem-validar: nao testei nenhum ID)")
        return 0

    # ---- validacao ---------------------------------------------------------
    # O unico teste confiavel: criar um container com aquele location_id.
    # Se a Meta aceitar, o ID serve para publicar. O container NAO e' publicado.
    imagem = "%s/img/F2_laser.jpg" % base
    print("\n== Validando (cria container de teste, nao publica) ==")
    print("   imagem de teste: %s\n" % imagem)

    aprovados = []
    testar = [c for c in candidatos if c["df"]][:args.validar]
    if not testar:
        print("   Nenhum candidato no DF para testar.")
        return 1

    for c in testar:
        res, erro = postar("%s/media" % ig_user_id,
                           image_url=imagem,
                           caption="teste de localizacao — nao publicado",
                           location_id=c["id"],
                           access_token=token)
        if res and res.get("id"):
            print("   OK      id=%-18s %s" % (c["id"], c["nome"][:40]))
            aprovados.append(c)
        else:
            sub = (erro or {}).get("error_subcode")
            msg = (erro or {}).get("error_user_msg") or (erro or {}).get("message") or "?"
            rotulo = "LOCAL INVALIDO" if sub == 2207019 else "ERRO"
            print("   %-14s id=%-18s %s" % (rotulo, c["id"], msg[:70]))

    print("\n" + "=" * 68)
    if aprovados:
        escolhido = aprovados[0]
        print("IG_LOCATION_ID = %s" % escolhido["id"])
        print("   %s — %s / %s" % (escolhido["nome"], escolhido["cidade"], escolhido["estado"]))
        if len(aprovados) > 1:
            print("\nOutros que tambem passaram:")
            for c in aprovados[1:]:
                print("   %s  %s (%s / %s)" % (c["id"], c["nome"], c["cidade"], c["estado"]))
            print("Escolha com os olhos qual descreve melhor a clinica.")
        print("\nGuarde em Settings > Secrets and variables > Actions > IG_LOCATION_ID.")
    else:
        print("Nenhum candidato passou.")
        print("Tente --raio 30000, ou --q 'Planaltina Distrito Federal'.")
        print("Se nada passar, publique sem localizacao: o robo ja faz isso")
        print("sozinho e te avisa por e-mail (PERMITIR_SEM_LOCALIZACAO).")
    print("=" * 68)
    return 0 if aprovados else 1


if __name__ == "__main__":
    sys.exit(main())
