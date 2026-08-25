# Robô de posts — Instagram UNICORPOS

Publica sozinho, todo dia útil às 9h de Brasília, no `@unicorposclinica`.

Não usa IA. As legendas já estão escritas no `calendario.json` — o robô só encontra a
linha do dia, monta o post e publica. Isso é de propósito: nada de texto inventado
indo ao ar sem ninguém ter lido antes.

---

## O que ele faz em cada dia

| Situação | O que acontece |
|---|---|
| Dia útil com peça pronta | Publica: imagem + legenda + localização + texto alternativo |
| Peça de **odontologia** (dias 7 e 28) | **Não publica.** Manda e-mail para você aprovar |
| Dia de story que dependia de conteúdo seu | Publica uma peça do banco de reserva |
| Banco de reserva esgotado (dias 21, 24, 27) | Manda e-mail pedindo uma peça |
| Sábado, domingo ou feriado | Não faz nada |
| Passou do dia 30 | Manda e-mail avisando que o mês 1 acabou |
| Deu erro na publicação | Manda e-mail com a legenda, para você publicar à mão |

Feriados já cadastrados para 2026 e 2027, incluindo os do DF (30/11, Dia do
Evangélico). **7 de setembro de 2026 cai numa segunda** e é pulado — o calendário
anda um dia.

---

## Instalação

### 1. Conta do Instagram

Precisa ser **Profissional** (Business ou Creator) e estar ligada a uma Página do
Facebook. Conta pessoal não publica por API.

### 2. App na Meta

Em [developers.facebook.com](https://developers.facebook.com) crie um app do tipo
*Business* e adicione o produto **Instagram**. Anote o **App ID** e o **App Secret**.

Como a conta é sua, **você não precisa de App Review.** Aquele processo de 2 a 4
semanas só vale para apps que publicam em contas de terceiros. Com você como
administrador do app e dono da conta, o acesso padrão já basta.

### 3. Descobrir os IDs

No [Graph API Explorer](https://developers.facebook.com/tools/explorer), selecione seu
app e gere um token com estas permissões:

```
instagram_business_basic
instagram_business_content_publish
pages_show_list
pages_read_engagement
```

Depois, na sua máquina:

```bash
pip install Pillow openpyxl
META_APP_ID=...  META_APP_SECRET=...  TOKEN_CURTO=...  python3 ferramentas/descobrir_ids.py
```

Ele devolve o `IG_USER_ID`, um token de 60 dias e a lista de lugares chamados
"Planaltina".

> **Escolha o do Distrito Federal.** A lista vai mostrar também *Planaltina de
> Goiás*, que é outra cidade a 10 km. Marcar a errada é o erro que já deu
> retrabalho antes — o script marca o provável, mas confira com os olhos.

### 4. Subir para o GitHub

```bash
cd automacao/instagram-bot
git init && git add . && git commit -m "robô de posts UNICORPOS"
gh repo create unicorpos-instagram --public --source=. --push
```

**Por que repositório público:** a API do Instagram exige que a imagem esteja numa
URL pública no momento da publicação. As peças são material de marketing feito para
ir ao Instagram — não há nada sigiloso nelas. O que é secreto (token, senha de
e-mail) fica em *GitHub Secrets*, que são criptografados mesmo em repositório
público e nunca aparecem no log.

Se preferir repositório privado, as imagens precisam ser hospedadas em outro lugar
com URL pública — o site da UNICORPOS serve. Aí é só apontar o `BASE_URL_IMAGENS`
para lá.

### 5. Configurar os segredos

Em **Settings → Secrets and variables → Actions**:

*Secrets:*

| Nome | O que é |
|---|---|
| `IG_TOKEN` | Token de 60 dias |
| `IG_USER_ID` | ID da conta `@unicorposclinica` |
| `IG_LOCATION_ID` | ID de Planaltina **(Distrito Federal)** |
| `META_APP_ID` | App ID |
| `META_APP_SECRET` | App Secret |
| `GH_PAT` | Token do GitHub com permissão de escrever secrets (para a renovação automática) |
| `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASS` | Servidor de e-mail |

*Variables:*

| Nome | Valor |
|---|---|
| `BASE_URL_IMAGENS` | `https://raw.githubusercontent.com/SEU_USUARIO/unicorpos-instagram/main` |
| `EMAIL_DESTINO` | `leonardo.lima@i9atech.com` |

### 6. Testar antes de soltar

Em **Actions → Post diário UNICORPOS → Run workflow**, marque `dry_run`. Ele mostra
exatamente o que publicaria, sem publicar. Rode uma vez com `dry_run` desmarcado e
`dia = 2` para ver um post real sair.

---

## Uso no dia a dia

**Trocar a legenda de um dia:** edite o `calendario.json` e faça commit. O robô lê
o JSON, não a planilha.

**Montar o mês 2:** peça o novo calendário ao Claude, atualize a planilha e rode:

```bash
python3 ferramentas/gerar_calendario.py
python3 ferramentas/preparar_imagens.py
git add . && git commit -m "mês 2" && git push
```

**Peças novas:** salve o PNG em `deliverables/social/`, adicione o texto alternativo
e a categoria em `ferramentas/gerar_calendario.py`, e rode os dois scripts acima.

---

## O que o robô **não** faz

- **Stories.** A API não cria enquete, caixinha de pergunta nem figurinha
  interativa. Story continua manual.
- **Reels.** Dá para automatizar, mas não está montado aqui.
- **Responder comentário ou Direct.** Fora do escopo.
- **Escrever legenda.** Por decisão de projeto.

---

## Manutenção

**O token vence a cada 60 dias.** É a causa número um de robô de Instagram parar
em silêncio. O workflow `renovar-token.yml` renova todo dia 1º e manda e-mail se
falhar. Ainda assim, vale conferir o perfil de vez em quando.

**Limite da API:** 25 posts publicados por API a cada 24h. Um por dia útil não
chega perto.

**Se o GitHub Actions ficar 60 dias sem rodar** em repositório sem atividade, o
cron é desativado. Um commit qualquer reativa.

---

## Pendências

Três dias do calendário ficaram sem peça — **21, 24 e 27** — porque eram dias de
story com conteúdo humano (Estrutura, Enquete, Bastidores) e o banco de reserva só
tinha cinco peças livres para oito dias. Nesses dias o robô manda e-mail em vez de
publicar. Para o mês ficar 100% automático, faltam três peças novas.

---

## Conformidade

- Localização sempre **Planaltina (Distrito Federal)**, nunca Planaltina de Goiás.
- Texto alternativo preenchido em toda peça de feed.
- Odontologia nunca publica sozinha e nunca leva tabela de preços — vedação do
  Código de Ética Odontológica (CFO).
- RT odontologia: Dra. Mayra Gabriela Alves Cardona — CRO-DF nº CD-10122.
- RT fisioterapia: Mario Sergio Fernandes de Lima — CREFITO-11 nº 442563-F.

As regras de publicidade do CFO e do CREFITO mudam com o tempo, e publicação
automática reduz a chance de alguém revisar antes. Vale uma leitura das resoluções
vigentes junto a quem cuida da parte jurídica da clínica antes de deixar rodando
por meses.
