
import pygame
import os
import sys
import json
import random

pygame.init()

LARGURA = 960
ALTURA = 640
FPS = 60
VELOCIDADE = 2.8
VELOCIDADE_CORRIDA = 4.5
ESCALA_MAPA = 3.0
TAMANHO_CELULA = 12
CELULA_MUNDO = TAMANHO_CELULA * ESCALA_MAPA
LARGURA_PERSONAGEM = 90
ALTURA_PERSONAGEM = 110
HITBOX_LARGURA = 22
HITBOX_ALTURA = 25

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Between Two Worlds")
RELOGIO = pygame.time.Clock()

FONTE = pygame.font.SysFont("arial", 20)
FONTE_PEQUENA = pygame.font.SysFont("arial", 16)

PASTA = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(PASTA, "assets")

ARQ_COLISOES = os.path.join(PASTA, "collision_map.json")
ARQ_PORTAS = os.path.join(PASTA, "doors.json")
ARQ_BAUS = os.path.join(PASTA, "chests.json")
ARQ_INVENTARIO = os.path.join(PASTA, "inventory.json")


def caminho(nome):
    return os.path.join(ASSETS, nome)


def carregar_json(arquivo, padrao):
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return padrao


def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def carregar_imagem(arquivo, tamanho=None):
    try:
        imagem = pygame.image.load(caminho(arquivo)).convert_alpha()
        if tamanho:
            imagem = pygame.transform.scale(imagem, tamanho)
        return imagem
    except (pygame.error, FileNotFoundError):
        return None


def encontrar_mapa():
    ignorar = {
        "player.png",
        "player_back.png",
        "player_sheet.png",
        "front_walk.png",
        "front_run.png",
        "back_walk.png",
        "back_run.png",
        "left_walk.png",
        "left_run.png",
        "right_walk.png",
        "right_run.png"
    }

    if not os.path.isdir(ASSETS):
        return None

    candidatos = []

    for nome in os.listdir(ASSETS):
        if not nome.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            continue

        if nome.lower() in ignorar:
            continue

        if any(
            nome.lower().startswith(direcao + "_")
            and any(tipo in nome.lower() for tipo in ("walk", "run"))
            for direcao in ("front", "back", "left", "right")
        ):
            continue

        try:
            imagem = pygame.image.load(caminho(nome))
            largura, altura = imagem.get_size()

            if largura * altura > 200000:
                candidatos.append((largura * altura, nome))
        except pygame.error:
            pass

    if not candidatos:
        return None

    candidatos.sort(reverse=True)
    return candidatos[0][1]


nome_mapa = encontrar_mapa()

if nome_mapa is None:
    pygame.quit()
    print("Não encontrei o mapa dentro da pasta assets.")
    print("Coloque a imagem do mapa em assets e execute novamente.")
    sys.exit()

MAPA_ORIGINAL = pygame.image.load(caminho(nome_mapa)).convert()
MAPA = pygame.transform.scale_by(MAPA_ORIGINAL, ESCALA_MAPA)
MAPA_LARGURA = MAPA.get_width()
MAPA_ALTURA = MAPA.get_height()

print("Mapa carregado:", nome_mapa)
print("Tamanho do mapa:", MAPA_LARGURA, "x", MAPA_ALTURA)


def carregar_animacao(direcao_animacao, acao):
    frames = []

    for numero in range(1, 7):
        nome = (
            direcao_animacao
            + "_"
            + acao
            + "_"
            + str(numero)
            + ".png"
        )

        try:
            imagem = pygame.image.load(
                caminho(nome)
            ).convert_alpha()
        except (pygame.error, FileNotFoundError):
            continue

        largura_original, altura_original = imagem.get_size()

        if largura_original <= 0 or altura_original <= 0:
            continue

        if (
            largura_original == LARGURA_PERSONAGEM
            and altura_original == ALTURA_PERSONAGEM
        ):
            quadro_final = imagem.copy()
        else:
            escala = min(
                LARGURA_PERSONAGEM / largura_original,
                ALTURA_PERSONAGEM / altura_original
            )

            nova_largura = max(
                1,
                round(largura_original * escala)
            )
            nova_altura = max(
                1,
                round(altura_original * escala)
            )

            imagem = pygame.transform.scale(
                imagem,
                (nova_largura, nova_altura)
            )

            quadro_final = pygame.Surface(
                (LARGURA_PERSONAGEM, ALTURA_PERSONAGEM),
                pygame.SRCALPHA
            )

            pos_x = (LARGURA_PERSONAGEM - nova_largura) // 2
            pos_y = ALTURA_PERSONAGEM - nova_altura

            quadro_final.blit(imagem, (pos_x, pos_y))

        frames.append(quadro_final)

    return frames


animacoes = {}

for direcao_animacao in ("front", "back", "left", "right"):
    animacoes[(direcao_animacao, "walk")] = carregar_animacao(
        direcao_animacao,
        "walk"
    )

    animacoes[(direcao_animacao, "run")] = carregar_animacao(
        direcao_animacao,
        "run"
    )


player_frente = carregar_imagem(
    "player.png",
    (LARGURA_PERSONAGEM, ALTURA_PERSONAGEM)
)

player_costas = carregar_imagem(
    "player_back.png",
    (LARGURA_PERSONAGEM, ALTURA_PERSONAGEM)
)

if player_frente is None:
    pygame.quit()
    print("Não encontrei assets/player.png.")
    sys.exit()

if player_costas is None:
    player_costas = player_frente


def imagem_personagem(direcao, correndo, andando, quadro):
    acao = "run" if correndo else "walk"
    frames = animacoes.get((direcao, acao), [])

    if not frames and correndo:
        frames = animacoes.get((direcao, "walk"), [])

    if andando and frames:
        return frames[quadro % len(frames)]

    if direcao == "back":
        return player_costas

    if direcao == "front":
        return player_frente

    if frames:
        return frames[0]

    return player_frente


def carregar_colisoes():
    dados = carregar_json(ARQ_COLISOES, [])

    if isinstance(dados, dict):
        dados = dados.get(
            "colisoes",
            dados.get("collisions", [])
        )

    resultado = set()

    if isinstance(dados, list):
        for item in dados:
            try:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    resultado.add((int(item[0]), int(item[1])))
                elif isinstance(item, dict):
                    resultado.add(
                        (int(item["x"]), int(item["y"]))
                    )
            except (ValueError, TypeError, KeyError):
                pass

    return resultado


colisoes = carregar_colisoes()


def salvar_colisoes():
    salvar_json(
        ARQ_COLISOES,
        [list(c) for c in sorted(colisoes)]
    )


portas = carregar_json(ARQ_PORTAS, [])
baus = carregar_json(ARQ_BAUS, [])
inventario = carregar_json(ARQ_INVENTARIO, [])

if not isinstance(portas, list):
    portas = []

if not isinstance(baus, list):
    baus = []

if not isinstance(inventario, list):
    inventario = []

inventario_normalizado = []

for item in inventario:
    if isinstance(item, str):
        inventario_normalizado.append({
            "nome": item,
            "quantidade": 1
        })
    elif isinstance(item, dict) and "nome" in item:
        try:
            quantidade = int(item.get("quantidade", 1))
        except (ValueError, TypeError):
            quantidade = 1

        inventario_normalizado.append({
            "nome": str(item["nome"]),
            "quantidade": quantidade
        })

inventario = inventario_normalizado


def salvar_portas():
    salvar_json(ARQ_PORTAS, portas)


def salvar_baus():
    salvar_json(ARQ_BAUS, baus)


def salvar_inventario():
    salvar_json(ARQ_INVENTARIO, inventario)


player_x = min(
    1200,
    max(0, MAPA_LARGURA - LARGURA_PERSONAGEM)
)

player_y = min(
    900,
    max(0, MAPA_ALTURA - ALTURA_PERSONAGEM)
)

camera_x = 0
camera_y = 0

direcao = "front"
quadro = 0
tempo_animacao = 0

estamina = 100.0
ESTAMINA_MAXIMA = 100.0
DRENAGEM_ESTAMINA = 25.0
RECUPERACAO_ESTAMINA = 15.0

editor_colisoes = False
editor_portas = False
editor_baus = False

inventario_aberto = False
bau_aberto = None
item_selecionado = 0

mensagem = ""
tempo_mensagem = 0


def mostrar_mensagem(texto):
    global mensagem, tempo_mensagem
    mensagem = texto
    tempo_mensagem = 180


def celula_mundo(cx, cy):
    return pygame.Rect(
        int(cx * CELULA_MUNDO),
        int(cy * CELULA_MUNDO),
        int(CELULA_MUNDO),
        int(CELULA_MUNDO)
    )


def retangulo_porta(porta):
    base = celula_mundo(
        int(porta.get("x", 0)),
        int(porta.get("y", 0))
    )

    return pygame.Rect(
        base.x,
        base.y,
        int(CELULA_MUNDO * 2),
        int(CELULA_MUNDO * 2)
    )


def retangulo_bau(bau):
    base = celula_mundo(
        int(bau.get("x", 0)),
        int(bau.get("y", 0))
    )

    return pygame.Rect(
        base.x,
        base.y,
        int(CELULA_MUNDO),
        int(CELULA_MUNDO)
    )


def hitbox_jogador(x=None, y=None):
    if x is None:
        x = player_x

    if y is None:
        y = player_y

    return pygame.Rect(
        int(x + (LARGURA_PERSONAGEM - HITBOX_LARGURA) / 2),
        int(y + ALTURA_PERSONAGEM - HITBOX_ALTURA - 5),
        HITBOX_LARGURA,
        HITBOX_ALTURA
    )


def tem_colisao(x, y):
    caixa = hitbox_jogador(x, y)

    if caixa.left < 0 or caixa.top < 0:
        return True

    if (
        caixa.right > MAPA_LARGURA
        or caixa.bottom > MAPA_ALTURA
    ):
        return True

    cx1 = int(caixa.left // CELULA_MUNDO)
    cy1 = int(caixa.top // CELULA_MUNDO)
    cx2 = int((caixa.right - 1) // CELULA_MUNDO)
    cy2 = int((caixa.bottom - 1) // CELULA_MUNDO)

    for cx in range(cx1, cx2 + 1):
        for cy in range(cy1, cy2 + 1):
            if (cx, cy) in colisoes:
                return True

    for porta in portas:
        if not porta.get("aberta", False):
            if caixa.colliderect(retangulo_porta(porta)):
                return True

    for bau in baus:
        if caixa.colliderect(retangulo_bau(bau)):
            return True

    return False


def adicionar_item(nome):
    for item in inventario:
        if item["nome"] == nome:
            item["quantidade"] += 1
            salvar_inventario()
            return

    inventario.append({
        "nome": nome,
        "quantidade": 1
    })

    salvar_inventario()


def objeto_mais_proximo(
    lista,
    funcao_retangulo,
    distancia_maxima=95
):
    centro = hitbox_jogador().center
    mais_proximo = None
    menor_distancia = distancia_maxima

    for objeto in lista:
        ret = funcao_retangulo(objeto)

        dx = centro[0] - ret.centerx
        dy = centro[1] - ret.centery
        distancia = (dx * dx + dy * dy) ** 0.5

        if distancia < menor_distancia:
            menor_distancia = distancia
            mais_proximo = objeto

    return mais_proximo


def interagir():
    global bau_aberto, item_selecionado

    porta = objeto_mais_proximo(
        portas,
        retangulo_porta
    )

    if porta is not None:
        porta["aberta"] = not porta.get("aberta", False)
        salvar_portas()

        mostrar_mensagem(
            "Porta aberta."
            if porta["aberta"]
            else "Porta fechada."
        )
        return

    bau = objeto_mais_proximo(
        baus,
        retangulo_bau
    )

    if bau is not None:
        if bau.get("aberto", False):
            bau["aberto"] = False
            bau_aberto = None
            salvar_baus()
        else:
            bau["aberto"] = True
            bau_aberto = bau
            item_selecionado = 0

            if "itens" not in bau:
                bau["itens"] = [
                    "Poção antiga",
                    "Chave enferrujada",
                    "Moeda de prata"
                ]

            salvar_baus()

        return

    mostrar_mensagem(
        "Não há nada próximo para interagir."
    )


def desenhar_texto(
    texto,
    x,
    y,
    cor=(255, 255, 255),
    fonte=FONTE
):
    imagem = fonte.render(str(texto), True, cor)
    TELA.blit(imagem, (x, y))


def desenhar_barra_estamina():
    pygame.draw.rect(
        TELA,
        (25, 25, 25),
        (20, 20, 204, 24)
    )

    largura = int(
        200 * estamina / ESTAMINA_MAXIMA
    )

    pygame.draw.rect(
        TELA,
        (190, 170, 65),
        (22, 22, largura, 20)
    )

    pygame.draw.rect(
        TELA,
        (220, 220, 220),
        (20, 20, 204, 24),
        2
    )

    desenhar_texto(
        "ESTAMINA",
        230,
        21,
        (235, 235, 235),
        FONTE_PEQUENA
    )


def desenhar_editor():
    if editor_colisoes:
        desenhar_texto(
            "EDITOR DE COLISOES: clique esquerdo adiciona | direito remove | P/F2 salva",
            20,
            ALTURA - 30,
            (255, 230, 100),
            FONTE_PEQUENA
        )

        for cx, cy in colisoes:
            ret = celula_mundo(cx, cy)
            ret.x -= int(camera_x)
            ret.y -= int(camera_y)

            if TELA.get_rect().colliderect(ret):
                pygame.draw.rect(
                    TELA,
                    (255, 0, 0),
                    ret,
                    2
                )

    if editor_portas:
        desenhar_texto(
            "EDITOR DE PORTAS: esquerdo adiciona | direito remove | F4/F6 salva",
            20,
            ALTURA - 30,
            (255, 230, 100),
            FONTE_PEQUENA
        )

    if editor_baus:
        desenhar_texto(
            "EDITOR DE BAUS: esquerdo adiciona | direito remove | F5/B salva",
            20,
            ALTURA - 30,
            (255, 230, 100),
            FONTE_PEQUENA
        )


def desenhar_inventario():
    pygame.draw.rect(
        TELA,
        (15, 13, 18),
        (220, 100, 520, 430)
    )

    pygame.draw.rect(
        TELA,
        (160, 145, 115),
        (220, 100, 520, 430),
        3
    )

    desenhar_texto(
        "INVENTARIO",
        245,
        120,
        (230, 210, 160)
    )

    if not inventario:
        desenhar_texto(
            "Seu inventario esta vazio.",
            245,
            170
        )
    else:
        y = 170

        for item in inventario:
            desenhar_texto(
                item["nome"] + " x" + str(item["quantidade"]),
                250,
                y
            )
            y += 30

    desenhar_texto(
        "Pressione I ou ESC para fechar",
        245,
        485,
        (190, 190, 190),
        FONTE_PEQUENA
    )


def desenhar_bau():
    if bau_aberto is None:
        return

    pygame.draw.rect(
        TELA,
        (18, 14, 12),
        (250, 170, 460, 300)
    )

    pygame.draw.rect(
        TELA,
        (190, 150, 80),
        (250, 170, 460, 300),
        3
    )

    desenhar_texto(
        "BAU",
        275,
        190,
        (235, 200, 125)
    )

    itens = bau_aberto.get("itens", [])

    if not itens:
        desenhar_texto(
            "O bau esta vazio.",
            280,
            235
        )
    else:
        for indice, item in enumerate(itens):
            cor = (
                (255, 230, 130)
                if indice == item_selecionado
                else (230, 230, 230)
            )

            prefixo = (
                "> "
                if indice == item_selecionado
                else "  "
            )

            desenhar_texto(
                prefixo + str(item),
                280,
                235 + indice * 30,
                cor
            )

    desenhar_texto(
        "Setas: selecionar | ENTER: pegar item",
        275,
        400,
        (190, 190, 190),
        FONTE_PEQUENA
    )

    desenhar_texto(
        "E ou ESC: fechar",
        275,
        430,
        (190, 190, 190),
        FONTE_PEQUENA
    )


def pegar_item_bau():
    global item_selecionado, bau_aberto

    if bau_aberto is None:
        return

    itens = bau_aberto.get("itens", [])

    if not itens:
        mostrar_mensagem("O bau esta vazio.")
        return

    if (
        item_selecionado < 0
        or item_selecionado >= len(itens)
    ):
        item_selecionado = 0
        return

    item = itens.pop(item_selecionado)

    adicionar_item(str(item))
    salvar_baus()

    if not itens:
        bau_aberto["aberto"] = False
        bau_aberto = None

        mostrar_mensagem(
            "Item coletado. Bau vazio."
        )
    else:
        item_selecionado = min(
            item_selecionado,
            len(itens) - 1
        )

        mostrar_mensagem(
            "Item coletado: " + str(item)
        )


def posicao_mouse_mundo():
    mouse_x, mouse_y = pygame.mouse.get_pos()

    mundo_x = mouse_x + camera_x
    mundo_y = mouse_y + camera_y

    cx = int(mundo_x // CELULA_MUNDO)
    cy = int(mundo_y // CELULA_MUNDO)

    return cx, cy


def salvar_todos():
    salvar_colisoes()
    salvar_portas()
    salvar_baus()
    salvar_inventario()


executando = True

while executando:
    dt = min(
        RELOGIO.tick(FPS) / 1000.0,
        0.05
    )

    tempo_animacao += dt * 1000

    if tempo_mensagem > 0:
        tempo_mensagem -= 1

    andando = False
    correndo = False

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            salvar_todos()
            executando = False

        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                if bau_aberto is not None:
                    bau_aberto["aberto"] = False
                    bau_aberto = None
                    salvar_baus()

                elif inventario_aberto:
                    inventario_aberto = False

                elif (
                    editor_colisoes
                    or editor_portas
                    or editor_baus
                ):
                    editor_colisoes = False
                    editor_portas = False
                    editor_baus = False
                    salvar_todos()

                else:
                    salvar_todos()
                    executando = False

            elif evento.key in (
                pygame.K_p,
                pygame.K_F2
            ):
                editor_colisoes = not editor_colisoes
                editor_portas = False
                editor_baus = False
                salvar_todos()

            elif evento.key in (
                pygame.K_F4,
                pygame.K_F6
            ):
                editor_portas = not editor_portas
                editor_colisoes = False
                editor_baus = False
                salvar_todos()

            elif evento.key in (
                pygame.K_F5,
                pygame.K_b
            ):
                editor_baus = not editor_baus
                editor_colisoes = False
                editor_portas = False
                salvar_todos()

            elif (
                evento.key == pygame.K_i
                and bau_aberto is None
            ):
                inventario_aberto = not inventario_aberto

            elif evento.key == pygame.K_e:
                if bau_aberto is not None:
                    bau_aberto["aberto"] = False
                    bau_aberto = None
                    salvar_baus()

                elif not inventario_aberto and not (
                    editor_colisoes
                    or editor_portas
                    or editor_baus
                ):
                    interagir()

            elif bau_aberto is not None:
                itens_bau = bau_aberto.get("itens", [])

                if evento.key in (
                    pygame.K_UP,
                    pygame.K_w
                ):
                    if itens_bau:
                        item_selecionado = (
                            item_selecionado - 1
                        ) % len(itens_bau)

                elif evento.key in (
                    pygame.K_DOWN,
                    pygame.K_s
                ):
                    if itens_bau:
                        item_selecionado = (
                            item_selecionado + 1
                        ) % len(itens_bau)

                elif evento.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE
                ):
                    pegar_item_bau()

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if (
                editor_colisoes
                or editor_portas
                or editor_baus
            ):
                cx, cy = posicao_mouse_mundo()

                if evento.button == 1:
                    if editor_colisoes:
                        colisoes.add((cx, cy))
                        salvar_colisoes()

                    elif editor_portas:
                        existe = any(
                            int(p.get("x", -1)) == cx
                            and int(p.get("y", -1)) == cy
                            for p in portas
                        )

                        if not existe:
                            portas.append({
                                "x": cx,
                                "y": cy,
                                "aberta": False
                            })
                            salvar_portas()

                    elif editor_baus:
                        existe = any(
                            int(b.get("x", -1)) == cx
                            and int(b.get("y", -1)) == cy
                            for b in baus
                        )

                        if not existe:
                            baus.append({
                                "x": cx,
                                "y": cy,
                                "aberto": False,
                                "itens": [
                                    "Pocao antiga",
                                    "Chave enferrujada",
                                    "Moeda de prata"
                                ]
                            })
                            salvar_baus()

                elif evento.button == 3:
                    if editor_colisoes:
                        colisoes.discard((cx, cy))
                        salvar_colisoes()

                    elif editor_portas:
                        for porta in portas[:]:
                            if (
                                int(porta.get("x", -1)) == cx
                                and int(porta.get("y", -1)) == cy
                            ):
                                portas.remove(porta)

                        salvar_portas()

                    elif editor_baus:
                        for bau in baus[:]:
                            if (
                                int(bau.get("x", -1)) == cx
                                and int(bau.get("y", -1)) == cy
                            ):
                                baus.remove(bau)

                        salvar_baus()

    if not executando:
        break

    teclas = pygame.key.get_pressed()

    if not (
        inventario_aberto
        or bau_aberto is not None
        or editor_colisoes
        or editor_portas
        or editor_baus
    ):
        dx = 0
        dy = 0

        if (
            teclas[pygame.K_LEFT]
            or teclas[pygame.K_a]
        ):
            dx -= 1
            direcao = "left"

        if (
            teclas[pygame.K_RIGHT]
            or teclas[pygame.K_d]
        ):
            dx += 1
            direcao = "right"

        if (
            teclas[pygame.K_UP]
            or teclas[pygame.K_w]
        ):
            dy -= 1

            if dx == 0:
                direcao = "back"

        if (
            teclas[pygame.K_DOWN]
            or teclas[pygame.K_s]
        ):
            dy += 1

            if dx == 0:
                direcao = "front"

        andando = dx != 0 or dy != 0

        correndo = (
            teclas[pygame.K_LSHIFT]
            or teclas[pygame.K_RSHIFT]
        ) and andando and estamina > 0

        velocidade = (
            VELOCIDADE_CORRIDA
            if correndo
            else VELOCIDADE
        )

        if correndo:
            estamina -= DRENAGEM_ESTAMINA * dt
        else:
            estamina += RECUPERACAO_ESTAMINA * dt

        estamina = max(
            0,
            min(ESTAMINA_MAXIMA, estamina)
        )

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        movimento_x = dx * velocidade * dt * 60
        movimento_y = dy * velocidade * dt * 60

        if movimento_x != 0:
            novo_x = player_x + movimento_x

            if not tem_colisao(novo_x, player_y):
                player_x = novo_x

        if movimento_y != 0:
            novo_y = player_y + movimento_y

            if not tem_colisao(player_x, novo_y):
                player_y = novo_y

        if andando:
            intervalo = 75 if correndo else 125

            if tempo_animacao >= intervalo:
                quadro += 1
                tempo_animacao = 0
        else:
            quadro = 0
            tempo_animacao = 0

    centro_x = player_x + LARGURA_PERSONAGEM / 2
    centro_y = player_y + ALTURA_PERSONAGEM / 2

    camera_x = centro_x - LARGURA / 2
    camera_y = centro_y - ALTURA / 2

    camera_x = max(
        0,
        min(camera_x, MAPA_LARGURA - LARGURA)
    )

    camera_y = max(
        0,
        min(camera_y, MAPA_ALTURA - ALTURA)
    )

    TELA.fill((0, 0, 0))

    TELA.blit(
        MAPA,
        (-int(camera_x), -int(camera_y))
    )

    if editor_colisoes:
        for cx, cy in colisoes:
            ret = celula_mundo(cx, cy)

            ret.x -= int(camera_x)
            ret.y -= int(camera_y)

            if TELA.get_rect().colliderect(ret):
                pygame.draw.rect(
                    TELA,
                    (220, 30, 30),
                    ret,
                    2
                )

    for porta in portas:
        ret = retangulo_porta(porta)

        ret.x -= int(camera_x)
        ret.y -= int(camera_y)

        cor = (
            (100, 160, 100)
            if porta.get("aberta", False)
            else (125, 75, 35)
        )

        pygame.draw.rect(TELA, cor, ret)
        pygame.draw.rect(
            TELA,
            (45, 30, 20),
            ret,
            3
        )

        if editor_portas:
            pygame.draw.rect(
                TELA,
                (255, 220, 70),
                ret,
                2
            )

    for bau in baus:
        ret = retangulo_bau(bau)

        ret.x -= int(camera_x)
        ret.y -= int(camera_y)

        pygame.draw.rect(
            TELA,
            (130, 75, 30),
            ret
        )

        pygame.draw.rect(
            TELA,
            (210, 175, 95),
            ret,
            2
        )

        if bau.get("aberto", False):
            pygame.draw.line(
                TELA,
                (255, 220, 140),
                ret.topleft,
                ret.bottomright,
                2
            )

        if editor_baus:
            pygame.draw.rect(
                TELA,
                (255, 220, 70),
                ret,
                2
            )

    sprite = imagem_personagem(
        direcao,
        correndo,
        andando,
        quadro
    )

    TELA.blit(
        sprite,
        (
            int(player_x - camera_x),
            int(player_y - camera_y)
        )
    )

    desenhar_barra_estamina()
    desenhar_editor()

    if inventario_aberto:
        desenhar_inventario()

    if bau_aberto is not None:
        desenhar_bau()

    if tempo_mensagem > 0 and mensagem:
        pygame.draw.rect(
            TELA,
            (20, 20, 20),
            (20, ALTURA - 65, 480, 35)
        )

        desenhar_texto(
            mensagem,
            30,
            ALTURA - 60,
            (240, 230, 200),
            FONTE_PEQUENA
        )

    pygame.display.flip()


salvar_todos()
pygame.quit()
sys.exit()
