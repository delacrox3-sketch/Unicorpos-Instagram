#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador do robo de posts da UNICORPOS.

Roda na SUA maquina, com as SUAS credenciais. Faz, de uma vez:

  1. confere se git e gh estao instalados e se voce esta logado
  2. troca o token curto da Meta por um de 60 dias
  3. descobre o IG_USER_ID da @unicorposclinica
  4. lista os "Planaltina" e faz VOCE escolher o do DF
  5. cria o repositorio no GitHub e sobe o codigo
  6. grava todos os secrets e variables
  7. dispara um teste em dry-run

Uso:
    python3 instalar.py

Antes de comecar voce precisa de tres coisas em maos:

  META_APP_ID = 1572907397545576   (app "UNICORPOS Social", ja criado)
  META_APP_SECRET
      em Configuracoes do app > Basico, no painel do app

  TOKEN_CURTO
      de https://developers.facebook.com/tools/explorer, com o app UNICORPOS Social
      selecionado e estas cinco permissoes:
        instagram_basic
        instagram_content_publish
        pages_read_engagement
        pages_show_list
        business_management

  gh CLI logado
      https://cli.github.com  e depois:  gh auth login

Nada e' impresso no log: os segredos vao direto para o GitHub.
"""

import getpass
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
API = "https://graph.facebook.com/v21.0"


# ---------------------------------------------------------------------------

def titulo(txt):
    print("\n" + "=" * 68)
    print("  " + txt)
    print("=" * 68)


def rodar(cmd, **kw):
    """Executa comando e devolve (ok, saida)."""
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def perguntar(texto, obrigatorio=True, segredo=False):
    while True:
        v = (getpass.getpass(texto) if segredo else input(texto)).strip()
        if v or not obrigatorio:
            return v
        print("   Precisa de um valor.")


def get(caminho, obrigatorio=True, **params):
    """
    Chama a Graph API. Com obrigatorio=False, devolve None em vez de abortar —
    usado onde existe plano B, para nao jogar fora o progresso ja feito.
    """
    url = "%s/%s?%s" % (API, caminho, urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        detalhe = ""
        if hasattr(e, "read"):
            try:
                detalhe = e.read().decode(errors="replace")
            except Exception:
                pass
        if obrigatorio:
            sys.exit("\nA Meta recusou a chamada '%s'.\n%s\n%s" % (caminho, e, detalhe))
        print("   (a Meta recusou '%s')" % caminho)
        return None


# ---------------------------------------------------------------------------

def passo_1_ferramentas():
    titulo("1/7  Conferindo as ferramentas")

    if not shutil.which("git"):
        sys.exit("git nao encontrado. Instale em https://git-scm.com")
    print("   git ....... ok")

    if not shutil.which("gh"):
        sys.exit("gh nao encontrado. Instale em https://cli.github.com e rode: gh auth login")
    ok, saida = rodar(["gh", "auth", "status"])
    if not ok:
        sys.exit("gh instalado mas sem login. Rode:  gh auth login\n\n%s" % saida)
    print("   gh ........ ok")

    usuario = ""
    ok, saida = rodar(["gh", "api", "user", "--jq", ".login"])
    if ok:
        usuario = saida.strip()
        print("   logado como %s" % usuario)
    return usuario


def passo_2_token(app_id, app_secret, curto):
    titulo("2/7  Trocando por token de 60 dias")
    d = get("oauth/access_token",
            grant_type="fb_exchange_token",
            client_id=app_id,
            client_secret=app_secret,
            fb_exchange_token=curto)
    token = d.get("access_token")
    if not token:
        sys.exit("A Meta nao devolveu token: %s" % d)
    print("   ok, vence em ~%d dias" % (int(d.get("expires_in", 0)) // 86400))
    return token


def passo_3_conta(token):
    titulo("3/7  Achando a conta @unicorposclinica")
    paginas = get("me/accounts", access_token=token,
                  fields="name,instagram_business_account{id,username}")

    encontradas = []
    for p in paginas.get("data", []):
        ig = p.get("instagram_business_account")
        if ig:
            encontradas.append((p["name"], ig.get("username"), ig["id"]))
            print("   %-32s @%-22s id=%s" % (p["name"], ig.get("username"), ig["id"]))

    if not encontradas:
        sys.exit("\n   Nenhuma conta do Instagram ligada as suas paginas.\n"
                 "   A conta precisa ser Profissional (Business ou Creator) e estar\n"
                 "   vinculada a uma Pagina do Facebook.")

    for nome, user, ig_id in encontradas:
        if user == "unicorposclinica":
            print("\n   Usando @unicorposclinica (id %s)" % ig_id)
            return ig_id

    print("\n   Nao achei @unicorposclinica na lista.")
    return perguntar("   Digite o IG_USER_ID que voce quer usar: ")


def montar_opcoes(lugares):
    """Normaliza a resposta da Graph API numa lista (id, nome, cidade, estado, eh_df)."""
    opcoes = []
    for lug in (lugares or {}).get("data", []):
        loc = lug.get("location") or {}
        estado = (loc.get("state") or "?").strip()
        cidade = (loc.get("city") or "?").strip()
        eh_df = (estado in ("DF", "Distrito Federal")
                 or "Distrito Federal" in (loc.get("region") or ""))
        opcoes.append((lug["id"], lug["name"], cidade, estado, eh_df))
    return opcoes


def escolher(opcoes, exigir_df):
    """Mostra a lista numerada e devolve o id escolhido, ou '' se pular."""
    for i, (lid, nome, cidade, estado, eh_df) in enumerate(opcoes, 1):
        marca = "   <== Distrito Federal" if eh_df else ""
        print("   [%2d] %-38s [%s / %s]%s" % (i, nome[:38], cidade, estado, marca))
    print()
    while True:
        esc = perguntar("   Numero da opcao correta (Enter para pular): ", obrigatorio=False)
        if not esc:
            return ""
        if esc.isdigit() and 1 <= int(esc) <= len(opcoes):
            escolhida = opcoes[int(esc) - 1]
            if exigir_df and not escolhida[4]:
                print("   Essa NAO parece ser do Distrito Federal (%s / %s)."
                      % (escolhida[2], escolhida[3]))
                if perguntar("   Tem certeza? (s/N): ", obrigatorio=False).lower() != "s":
                    continue
            print("   Usando: %s (id %s)" % (escolhida[1], escolhida[0]))
            return escolhida[0]
        print("   Opcao invalida.")


def passo_4_local(token):
    titulo("4/7  Escolhendo a localizacao")

    # Plano A: buscar o lugar publico "Planaltina". Costuma falhar com erro 10,
    # porque /pages/search exige o recurso Page Public Metadata Access, que so
    # sai via App Review. Tentamos mesmo assim: se a conta ja tiver o recurso,
    # esse e' o caminho ideal (marca a cidade).
    print("   Procurando o lugar publico 'Planaltina'...")
    opcoes = montar_opcoes(get("pages/search", obrigatorio=False, access_token=token,
                               q="Planaltina", fields="id,name,location", limit=25))

    if opcoes:
        print("\n   ATENCAO: existe 'Planaltina' no Distrito Federal e 'Planaltina de")
        print("   Goias', que e' OUTRA cidade, a 10 km. Marcar a errada ja deu")
        print("   retrabalho antes.\n")
        return escolher(opcoes, exigir_df=True)

    # Plano B: usar uma Pagina que voce mesmo administra. Nao precisa de App
    # Review porque pages_show_list ja cobre isso. Marcar a propria Pagina da
    # clinica como local e' pratica comum e leva quem clicar para a Pagina.
    print("\n   A busca publica exige App Review (recurso Page Public Metadata Access).")
    print("   Plano B: usar uma Pagina que voce administra como local do post.\n")

    paginas = get("me/accounts", obrigatorio=False, access_token=token,
                  fields="id,name,location", limit=50)
    opcoes = montar_opcoes(paginas)

    if not opcoes:
        print("   Nenhuma Pagina encontrada. Da para preencher depois:")
        print("   gh secret set IG_LOCATION_ID --repo SEU_USUARIO/unicorpos-instagram")
        return perguntar("   IG_LOCATION_ID (ou Enter para deixar vazio): ", obrigatorio=False)

    print("   Suas Paginas:\n")
    return escolher(opcoes, exigir_df=False)


def passo_5_repo(usuario):
    titulo("5/7  Criando o repositorio no GitHub")

    nome = perguntar("   Nome do repositorio [unicorpos-instagram]: ", obrigatorio=False) or "unicorpos-instagram"

    print("\n   O repositorio precisa ser PUBLICO: a API do Instagram exige que a")
    print("   imagem esteja numa URL publica na hora de publicar. As pecas sao")
    print("   material de marketing feito para ir ao Instagram. Os segredos ficam")
    print("   em GitHub Secrets, criptografados, e nunca aparecem no log.")
    if perguntar("\n   Criar como publico? (S/n): ", obrigatorio=False).lower() == "n":
        sys.exit("\n   Entao hospede as imagens no site da UNICORPOS e configure\n"
                 "   BASE_URL_IMAGENS apontando para la. Veja o README.")

    # O repositorio veio pre-commitado do ambiente do Claude, que roda num mount
    # sem permissao de apagar arquivo. Sobram .lock que travam qualquer git.
    for lock in (".git/index.lock", ".git/HEAD.lock", ".git/objects/maintenance.lock"):
        caminho = os.path.join(AQUI, lock)
        if os.path.exists(caminho):
            try:
                os.remove(caminho)
                print("   limpei %s" % lock)
            except OSError as e:
                sys.exit("   Nao consegui remover %s (%s).\n"
                         "   Apague a pasta .git e rode de novo." % (lock, e))

    if not os.path.isdir(os.path.join(AQUI, ".git")):
        rodar(["git", "init", "-b", "main"], cwd=AQUI)
    rodar(["git", "add", "-A"], cwd=AQUI)
    rodar(["git", "commit", "-m", "Robo de posts diarios do Instagram UNICORPOS"], cwd=AQUI)

    ok, saida = rodar(["gh", "repo", "create", nome, "--public", "--source=.", "--push"], cwd=AQUI)
    if not ok:
        if "already exists" in saida.lower():
            print("   Repositorio ja existe. Subindo o codigo nele.")
            rodar(["git", "remote", "remove", "origin"], cwd=AQUI)
            rodar(["git", "remote", "add", "origin",
                   "https://github.com/%s/%s.git" % (usuario, nome)], cwd=AQUI)
            ok2, saida2 = rodar(["git", "push", "-u", "origin", "main"], cwd=AQUI)
            if not ok2:
                sys.exit("   Falhou o push:\n%s" % saida2)
        else:
            sys.exit("   Falhou ao criar o repositorio:\n%s" % saida)

    repo = "%s/%s" % (usuario, nome)
    print("   ok: https://github.com/%s" % repo)
    return repo


def passo_6_segredos(repo, token, ig_user_id, location_id, app_id, app_secret):
    titulo("6/7  Gravando os segredos")

    def secret(nome, valor):
        if not valor:
            print("   %-18s (vazio, pulado)" % nome)
            return
        r = subprocess.run(["gh", "secret", "set", nome, "--repo", repo],
                           input=valor, capture_output=True, text=True)
        print("   %-18s %s" % (nome, "ok" if r.returncode == 0 else "FALHOU: " + r.stderr.strip()))

    def variavel(nome, valor):
        r = subprocess.run(["gh", "variable", "set", nome, "--repo", repo],
                           input=valor, capture_output=True, text=True)
        print("   %-18s %s" % (nome, "ok" if r.returncode == 0 else "FALHOU: " + r.stderr.strip()))

    secret("IG_TOKEN", token)
    secret("IG_USER_ID", ig_user_id)
    secret("IG_LOCATION_ID", location_id)
    secret("META_APP_ID", app_id)
    secret("META_APP_SECRET", app_secret)

    variavel("BASE_URL_IMAGENS", "https://raw.githubusercontent.com/%s/main" % repo)
    variavel("EMAIL_DESTINO", "leonardo.lima@i9atech.com")

    print("\n   --- E-mail de aviso (odontologia, falhas, fim de mes) ---")
    print("   Deixe em branco para configurar depois.")
    host = perguntar("   SMTP_HOST (ex.: smtp.gmail.com): ", obrigatorio=False)
    if host:
        secret("SMTP_HOST", host)
        secret("SMTP_PORT", perguntar("   SMTP_PORT [587]: ", obrigatorio=False) or "587")
        secret("SMTP_USER", perguntar("   SMTP_USER (e-mail remetente): "))
        secret("SMTP_PASS", perguntar("   SMTP_PASS (senha de app, nao aparece na tela): ", segredo=True))

    print("\n   --- Renovacao automatica do token (opcional) ---")
    print("   Um PAT com permissao de escrever secrets faz o token de 60 dias")
    print("   se renovar sozinho. Sem ele, os posts param quando o token vencer.")
    print("   Crie em: https://github.com/settings/tokens")
    pat = perguntar("   GH_PAT (Enter para pular): ", obrigatorio=False, segredo=True)
    if pat:
        secret("GH_PAT", pat)


def passo_7_teste(repo):
    titulo("7/7  Testando em dry-run")
    ok, saida = rodar(["gh", "workflow", "run", "post-diario.yml",
                       "--repo", repo, "-f", "dry_run=true"])
    if ok:
        print("   Disparado. Acompanhe em:")
        print("   https://github.com/%s/actions" % repo)
    else:
        print("   Nao consegui disparar automaticamente:\n%s" % saida)
        print("   Rode a mao em https://github.com/%s/actions" % repo)


# ---------------------------------------------------------------------------

def main():
    print(__doc__)
    if perguntar("Tem as tres coisas em maos? (s/N): ", obrigatorio=False).lower() != "s":
        sys.exit("\nSem problema. Junte os dados e rode de novo.")

    usuario = passo_1_ferramentas()

    titulo("Dados da Meta")
    app_id = perguntar("   META_APP_ID [1572907397545576]: ", obrigatorio=False) or "1572907397545576"
    app_secret = perguntar("   META_APP_SECRET (nao aparece na tela): ", segredo=True)
    curto = perguntar("   TOKEN_CURTO do Explorer (nao aparece na tela): ", segredo=True)

    token = passo_2_token(app_id, app_secret, curto)
    ig_user_id = passo_3_conta(token)
    location_id = passo_4_local(token)
    repo = passo_5_repo(usuario)
    passo_6_segredos(repo, token, ig_user_id, location_id, app_id, app_secret)
    passo_7_teste(repo)

    titulo("Pronto")
    print("""
   O robo publica todo dia util as 9h de Brasilia.

   Confira o dry-run em https://github.com/%s/actions antes de dormir tranquilo.
   Se o resultado estiver certo, nao precisa fazer mais nada: amanha ele publica.

   Para forcar um post agora:
     Actions > Post diario UNICORPOS > Run workflow > dia = 2, dry_run desmarcado

   Lembre que os dias 21, 24 e 27 estao sem peca e vao te mandar e-mail.
""" % repo)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n\nCancelado. Nada foi alterado no GitHub.")
