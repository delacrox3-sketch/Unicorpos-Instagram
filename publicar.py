#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publica o post do dia no Instagram da UNICORPOS (@unicorposclinica).

Roda no GitHub Actions, um disparo por dia util. Nao usa IA: as legendas ja estao
escritas no calendario.json. O robo so escolhe a linha certa e publica.

Decisoes que ele toma sozinho:
  - dia nao util ou feriado  -> nao faz nada
  - peca de odontologia      -> nao publica, manda e-mail para aprovacao (CFO)
  - dia sem peca no calendario -> manda e-mail avisando
  - passou do dia 30         -> manda e-mail de fim de mes

Modo de teste, sem tocar na rede:
    python3 publicar.py --dry-run --data 2026-09-08
"""

import argparse
import datetime
import json
import os
import random
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage

AQUI = os.path.dirname(os.path.abspath(__file__))
API = "https://graph.facebook.com/v21.0"

# Feriados nacionais e do DF. So precisam cobrir a janela do calendario, mas
# deixei o ano inteiro para nao dar trabalho em 2027.
FERIADOS = {
    # 2026
    "2026-01-01", "2026-02-16", "2026-02-17", "2026-04-03", "2026-04-21",
    "2026-05-01", "2026-06-04", "2026-09-07", "2026-10-12", "2026-11-02",
    "2026-11-15", "2026-11-20", "2026-11-30", "2026-12-25",
    # 2027
    "2027-01-01", "2027-02-08", "2027-02-09", "2027-03-26", "2027-04-21",
    "2027-05-01", "2027-05-27", "2027-09-07", "2027-10-12", "2027-11-02",
    "2027-11-15", "2027-11-20", "2027-11-30", "2027-12-25",
}


# ---------------------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------------------

def eh_dia_util(d):
    return d.weekday() < 5 and d.isoformat() not in FERIADOS


def numero_do_dia(hoje, dia_1):
    """
    Quantos dias uteis se passaram desde o Dia 1, contando o proprio Dia 1.
    Devolve None se hoje nao for dia util.
    """
    if not eh_dia_util(hoje) or hoje < dia_1:
        return None
    n = 0
    d = dia_1
    while d <= hoje:
        if eh_dia_util(d):
            n += 1
        d += datetime.timedelta(days=1)
    return n


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

def chamar(url, dados=None, tentativas=3):
    """POST ou GET na Graph API, com uma repeticao curta em erro de rede."""
    corpo = urllib.parse.urlencode(dados).encode() if dados else None
    ultimo = None
    for tentativa in range(tentativas):
        try:
            req = urllib.request.Request(url, data=corpo, method="POST" if dados else "GET")
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detalhe = e.read().decode(errors="replace")
            # 4xx e' erro nosso (token, permissao, parametro). Repetir nao ajuda.
            if 400 <= e.code < 500:
                raise RuntimeError("API respondeu %s: %s" % (e.code, detalhe))
            ultimo = RuntimeError("API respondeu %s: %s" % (e.code, detalhe))
        except Exception as e:  # rede instavel
            ultimo = e
        if tentativa < tentativas - 1:
            time.sleep(5 * (tentativa + 1))
    raise ultimo


# Subcode que a Meta devolve quando o location_id nao existe, nao e' um local
# fisico ou nao pode ser visto pela conta. Ver ferramentas/achar_local.py.
SUBCODE_LOCAL_INVALIDO = 2207019


def erro_de_localizacao(e):
    texto = str(e)
    return str(SUBCODE_LOCAL_INVALIDO) in texto or "localiza" in texto.lower()


def publicar_imagem(ig_user_id, token, image_url, legenda, alt_text, location_id):
    """
    Publicacao em dois passos, como a API exige:
      1. cria o container de midia
      2. publica o container
    """
    campos = {
        "image_url": image_url,
        "caption": legenda,
        "access_token": token,
    }
    if alt_text:
        campos["alt_text"] = alt_text[:1000]
    if location_id:
        campos["location_id"] = location_id

    container = chamar("%s/%s/media" % (API, ig_user_id), campos)
    creation_id = container.get("id")
    if not creation_id:
        raise RuntimeError("A API nao devolveu id de container: %s" % container)

    # O container leva alguns segundos para ficar pronto. Publicar cedo demais
    # devolve erro 9007. Espera ate FINISHED.
    for _ in range(20):
        estado = chamar("%s/%s?fields=status_code&access_token=%s" % (
            API, creation_id, urllib.parse.quote(token)))
        if estado.get("status_code") == "FINISHED":
            break
        if estado.get("status_code") == "ERROR":
            raise RuntimeError("Container falhou no processamento: %s" % estado)
        time.sleep(5)

    resultado = chamar("%s/%s/media_publish" % (API, ig_user_id), {
        "creation_id": creation_id,
        "access_token": token,
    })
    return resultado.get("id")


# ---------------------------------------------------------------------------
# E-mail
# ---------------------------------------------------------------------------

def enviar_email(assunto, corpo):
    """Avisa o Leonardo. Se o SMTP nao estiver configurado, so registra no log."""
    host = os.environ.get("SMTP_HOST")
    usuario = os.environ.get("SMTP_USER")
    senha = os.environ.get("SMTP_PASS")
    destino = os.environ.get("EMAIL_DESTINO", "suporte@unicorpos.com.br")

    if not (host and usuario and senha):
        print("[e-mail nao configurado] %s\n%s" % (assunto, corpo))
        return False

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = usuario
    msg["To"] = destino
    msg.set_content(corpo)

    porta = int(os.environ.get("SMTP_PORT", "587"))
    contexto = ssl.create_default_context()
    try:
        if porta == 465:
            with smtplib.SMTP_SSL(host, porta, context=contexto, timeout=30) as s:
                s.login(usuario, senha)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, porta, timeout=30) as s:
                s.starttls(context=contexto)
                s.login(usuario, senha)
                s.send_message(msg)
        print("E-mail enviado para %s" % destino)
        return True
    except Exception as e:
        print("Falhou o envio de e-mail: %s" % e)
        return False


# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true",
                   help="mostra o que faria, sem chamar a API nem enviar e-mail")
    p.add_argument("--data", help="finge que hoje e' esta data (AAAA-MM-DD)")
    p.add_argument("--dia", type=int, help="forca um numero de dia do calendario")
    args = p.parse_args()

    with open(os.path.join(AQUI, "calendario.json"), encoding="utf-8") as fh:
        cal = json.load(fh)

    dia_1 = datetime.date.fromisoformat(cal["dia_1"])

    if args.data:
        hoje = datetime.date.fromisoformat(args.data)
    else:
        # O runner do GitHub roda em UTC. Brasilia e' UTC-3 o ano todo.
        agora_utc = datetime.datetime.now(datetime.timezone.utc)
        hoje = (agora_utc - datetime.timedelta(hours=3)).date()

    n = args.dia if args.dia else numero_do_dia(hoje, dia_1)

    print("Hoje: %s (%s)" % (hoje.isoformat(), hoje.strftime("%A")))
    if n is None:
        print("Nao e' dia util em Brasilia. Nada a fazer.")
        return 0
    print("Dia %d do calendario." % n)

    dias = {d["dia"]: d for d in cal["dias"]}

    # --- fim do mes 1 -------------------------------------------------------
    if n > 30:
        if n == 31 and not args.dry_run:
            enviar_email(
                "UNICORPOS Instagram: mes 1 encerrado",
                "O calendario de 30 dias acabou.\n\n"
                "Hora de revisar alcance, salvamentos e conversas iniciadas, e montar "
                "o mes 2. Peca ao Claude o balanco e o novo calendario, rode\n"
                "  python3 ferramentas/gerar_calendario.py\n"
                "e faca commit do calendario.json novo.\n"
            )
        print("Passou do dia 30. Mes 1 encerrado.")
        return 0

    item = dias.get(n)
    if not item:
        print("Dia %d nao esta no calendario." % n)
        return 0

    acao = item.get("acao")
    print("Acao: %s" % acao)

    # --- dias que nao publicam ---------------------------------------------
    if acao == "publicado_manualmente":
        print("Peca do dia %d ja foi publicada a mao. Nada a fazer." % n)
        return 0

    if acao == "nao_publicado":
        print("Dia %d passou sem post e nao sera republicado. %s"
              % (n, item.get("observacao", "")))
        return 0

    if acao == "balanco":
        if not args.dry_run:
            enviar_email("UNICORPOS Instagram: dia 30, balanco do mes",
                         item.get("observacao", ""))
        print("Dia de balanco.")
        return 0

    if acao == "avisar":
        corpo = ("Dia %d do calendario nao tem peca definida.\n\n%s\n\n"
                 "Nada foi publicado hoje." % (n, item.get("observacao", "")))
        if not args.dry_run:
            enviar_email("UNICORPOS Instagram: dia %d precisa de voce" % n, corpo)
        print(corpo)
        return 0

    if acao == "aprovar":
        corpo = (
            "Dia %d e' peca de ODONTOLOGIA — nao publiquei sozinho, conforme combinado.\n\n"
            "Peca: %s\nImagem: img/%s.jpg\n\n"
            "--- LEGENDA (copiar e colar) ---\n%s\n\n"
            "--- TEXTO ALTERNATIVO ---\n%s\n\n"
            "Lembretes: localizacao 'Planaltina (Distrito Federal)', nunca 'Planaltina de Goias'.\n"
            "Sem tabela de precos em peca de odontologia (CFO).\n"
            "RT: Dra. Mayra Gabriela Alves Cardona — CRO-DF n CD-10122.\n"
        ) % (n, item["arquivo"], item["arquivo"], item["legenda"], item["alt_text"])
        if not args.dry_run:
            enviar_email("UNICORPOS Instagram: aprovar post de odontologia (dia %d)" % n, corpo)
        print(corpo)
        return 0

    # Qualquer acao que nao seja exatamente "publicar" para aqui. Sem este
    # guarda, um valor novo ou digitado errado no calendario.json cairia no
    # trecho de publicacao abaixo e iria ao ar sozinho.
    if acao != "publicar":
        corpo = ("Dia %d tem acao desconhecida no calendario.json: %r\n\n"
                 "Nao publiquei nada, por seguranca. Corrija o calendario.json."
                 % (n, acao))
        if not args.dry_run:
            enviar_email("UNICORPOS Instagram: acao desconhecida no dia %d" % n, corpo)
        print(corpo)
        return 1

    # --- publicar -----------------------------------------------------------
    base = os.environ.get("BASE_URL_IMAGENS", "").rstrip("/")
    ig_user_id = os.environ.get("IG_USER_ID", "")
    token = os.environ.get("IG_TOKEN", "")
    location_id = os.environ.get("IG_LOCATION_ID", "")

    image_url = "%s/%s" % (base, item["imagem"]) if base else "(BASE_URL_IMAGENS vazio)"

    print("Peca:     %s" % item["arquivo"])
    print("Imagem:   %s" % image_url)
    print("Categoria:%s" % item["categoria"])
    if item.get("substituido"):
        print("Nota:     %s" % item.get("observacao", ""))
    print("--- legenda ---\n%s\n---------------" % item["legenda"])
    print("alt: %s" % item["alt_text"])

    if args.dry_run:
        print("\n[dry-run] Nada foi publicado.")
        return 0

    faltando = [k for k, v in [("BASE_URL_IMAGENS", base),
                               ("IG_USER_ID", ig_user_id),
                               ("IG_TOKEN", token)] if not v]
    if faltando:
        print("Faltam segredos: %s" % ", ".join(faltando))
        return 1

    if not location_id:
        # Nao e' fatal, mas e' exatamente o erro que ja deu retrabalho antes.
        print("AVISO: IG_LOCATION_ID vazio — o post vai sem localizacao.")

    # ---- espera aleatoria -------------------------------------------------
    # O portfolio da UNICORPOS ja foi restringido pela Meta em 09/06/2026 por
    # "automacao que nao segue as regras". Publicar as 09:00:00 cravadas, todo
    # dia, e' assinatura de maquina. Um atraso aleatorio de ate 90 minutos faz
    # o horario variar como o de uma pessoa. Nao e' truque para enganar
    # ninguem: e' 1 post por dia util, pela API oficial, so sem a regularidade
    # de relogio que nenhum humano tem.
    jitter_max = int(os.environ.get("JITTER_MAX_MIN", "90"))
    if jitter_max > 0:
        espera = random.randint(0, jitter_max * 60)
        print("Esperando %d min %d s antes de publicar." % (espera // 60, espera % 60))
        time.sleep(espera)

    sem_local = os.environ.get("PERMITIR_SEM_LOCALIZACAO", "1") != "0"
    try:
        media_id = publicar_imagem(ig_user_id, token, image_url,
                                   item["legenda"], item["alt_text"], location_id)
    except Exception as e:
        # Localizacao recusada nao deveria custar o dia inteiro. Em 26/08/2026 o
        # post do dia 10 morreu exatamente assim, porque o IG_LOCATION_ID era um
        # id de Pagina e nao de local fisico. Melhor um post sem geotag, com
        # aviso alto, do que dia perdido em silencio.
        if location_id and sem_local and erro_de_localizacao(e):
            print("A Meta recusou o IG_LOCATION_ID. Republicando SEM localizacao.")
            try:
                media_id = publicar_imagem(ig_user_id, token, image_url,
                                           item["legenda"], item["alt_text"], None)
            except Exception as e2:
                corpo = ("Falhei ao publicar o dia %d (%s), com e sem localizacao.\n\n"
                         "Erro com localizacao: %s\n\nErro sem localizacao: %s\n\n"
                         "Publique a mao, se der tempo. A legenda esta no calendario.json."
                         % (n, item["arquivo"], e, e2))
                enviar_email("UNICORPOS Instagram: FALHOU o post do dia %d" % n, corpo)
                print(corpo)
                return 1
            corpo = (
                "O post do dia %d (%s) foi publicado, mas SEM a localizacao.\n\n"
                "A Meta recusou o IG_LOCATION_ID atual:\n%s\n\n"
                "Marque 'Planaltina (Distrito Federal)' a mao neste post e corrija o\n"
                "secret. Para achar e validar o id certo, rode na sua maquina:\n\n"
                "  IG_USER_ID=... IG_TOKEN=... BASE_URL_IMAGENS=... \\\n"
                "  python3 ferramentas/achar_local.py\n\n"
                "Enquanto o secret nao for corrigido, todo post vai sair sem geotag.\n"
                % (n, item["arquivo"], e))
            enviar_email("UNICORPOS Instagram: dia %d publicado SEM localizacao" % n, corpo)
            print(corpo)
            print("Publicado sem localizacao. media_id=%s" % media_id)
            return 0

        corpo = ("Falhei ao publicar o dia %d (%s).\n\nErro: %s\n\n"
                 "Publique a mao, se der tempo. A legenda esta no calendario.json."
                 % (n, item["arquivo"], e))
        enviar_email("UNICORPOS Instagram: FALHOU o post do dia %d" % n, corpo)
        print(corpo)
        return 1

    print("Publicado. media_id=%s" % media_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
