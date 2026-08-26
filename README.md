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

### Caminho curto

Junte três coisas e rode um comando:

```bash
pip install Pillow openpyxl
python3 instalar.py
```

O `instalar.py` troca o token, acha o `IG_USER_ID`, lista os "Planaltina" para você
escolher o do DF, cria o repositório, sobe o código, grava todos os secrets e
dispara um teste em dry-run. As três coisas que ele vai pedir:

1. **META_APP_ID** e **META_APP_SECRET** — de um app tipo *Business* com o produto
   *Instagram*, em [developers.facebook.com/apps](https://developers.facebook.com/apps)
2. **Token curto** do [Graph API Explorer](https://developers.facebook.com/tools/explorer),
   com `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`,
   `pages_show_list` e `business_management`
3. **`gh` CLI logado** — [cli.github.com](https://cli.github.com), depois `gh auth login`

Nenhum segredo aparece na tela nem fica em arquivo: vão direto para o GitHub Secrets.

O passo a passo manual, caso prefira fazer com as próprias mãos, está abaixo.

---

### 1. Conta do Instagram

Precisa ser **Profissional** (Business ou Creator) e estar ligada a uma Página do
Facebook. Conta pessoal não publica por API.

### 2. App na Meta — já criado

**UNICORPOS Social — App ID `1572907397545576`**, criado em 25/08/2026.

Configurado com o caso de uso *Gerenciar mensagens e conteúdo no Instagram*, na rota
**"Configuração da API com login do Facebook"**. Essa rota é a que permite marcar
localização no post (`location_id`); a rota de login do Instagram não permite, e
localização é requisito fixo aqui.

O app **não está ligado a nenhum portfólio empresarial**, de propósito: o portfólio
*Unicorpos Especializacao* está restringido e recusa reivindicar apps. Veja a seção
"Postura conservadora".

Permissões já concedidas (status *Pronto para teste*):

```
instagram_basic
instagram_content_publish
pages_read_engagement
pages_show_list
business_management
```

Como a conta é sua, **não há App Review.** A própria tela de criação confirmou
"nenhum requisito identificado". Aquele processo de 2 a 4 semanas só vale para apps
que publicam em contas de terceiros.

O **App Secret** está em *Configurações do app → Básico*.

### 3. Descobrir os IDs

No [Graph API Explorer](https://developers.facebook.com/tools/explorer), selecione o
app **UNICORPOS Social** e gere um token com as cinco permissões acima.

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

## Postura conservadora — leia antes de ligar

O portfólio **Unicorpos Especializacao (1517938625875994) foi restringido pela Meta
em 09/06/2026** por "automação que não segue nossas regras", sob os Padrões de
Publicidade de integridade da conta. O recurso foi analisado e **negado na mesma
data**. Consequências ativas: não pode criar ou veicular anúncios, nem usar ou
compartilhar públicos.

Publicar pela API oficial de Conteúdo do Instagram é uma via sancionada pela Meta e
é coisa diferente do que motivou a restrição. Mas a conta já tem um histórico, e o
robô foi ajustado para não parecer o que ela já foi acusada de ser:

- **Um post por dia útil.** Nunca em lote.
- **Horário variável.** O cron dispara 09:07 e o script espera de 0 a 90 minutos
  antes de publicar. O post cai entre 09:07 e 10:37, diferente todo dia.
  Ajuste com a variável `JITTER_MAX_MIN` (0 desliga).
- **Legendas escritas por humano**, versionadas em git. Nada gerado na hora.
- **Só publicação.** Não segue, não curte, não comenta, não manda DM.

Regras de operação que o código não consegue garantir sozinho:

- **Não rode nenhuma outra ferramenta de automação** na `@unicorposclinica` — nada
  de bot de seguidor, DM em massa ou agendador não oficial. Foi provavelmente algo
  assim que gerou a restrição de junho.
- **Se a Meta enviar qualquer aviso novo, desligue o workflow primeiro** e pergunte
  depois. Desativar é um clique; recuperar um perfil é outra história.
- O que está em risco não é o robô: é o perfil `@unicorposclinica` e a Página
  vinculada a ele.

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
