import pygame
import cv2
import os
import sys
import json
import random
import math

# Configuracoes dos meteoros da fase 2
FASE2_VELOCIDADE_OBSTACULO = 350
FASE2_INTERVALO_SPAWN = 0.2
FASE2_TAMANHO_OBSTACULO = 46
FASE2_TAMANHO_METEORO = 70

FASE2_LARGURA_PERSONAGEM = 90
FASE2_ALTURA_PERSONAGEM = 110

FASE2_VELOCIDADE = 150
FASE2_VELOCIDADE_CORRIDA = 250


def carregar_imagem_fase2(pasta_assets, nome, tamanho=None):
    caminho_arquivo = os.path.join(pasta_assets, nome)

    try:
        imagem = pygame.image.load(caminho_arquivo).convert_alpha()
        if tamanho:
            imagem = pygame.transform.scale(imagem, tamanho)
        return imagem
    except (pygame.error, FileNotFoundError):
        return None


def carregar_animacao_fase2(pasta_assets, direcao, acao):
    frames = []

    for numero in range(1, 7):
        nome = f"{direcao}_{acao}_{numero}.png"
        caminho_arquivo = os.path.join(pasta_assets, nome)

        try:
            imagem = pygame.image.load(caminho_arquivo).convert_alpha()
        except (pygame.error, FileNotFoundError):
            continue

        largura_original, altura_original = imagem.get_size()
        if largura_original <= 0 or altura_original <= 0:
            continue

        escala = min(
            FASE2_LARGURA_PERSONAGEM / largura_original,
            FASE2_ALTURA_PERSONAGEM / altura_original
        )

        nova_largura = max(1, round(largura_original * escala))
        nova_altura = max(1, round(altura_original * escala))
        imagem = pygame.transform.scale(imagem, (nova_largura, nova_altura))

        quadro = pygame.Surface(
            (FASE2_LARGURA_PERSONAGEM, FASE2_ALTURA_PERSONAGEM),
            pygame.SRCALPHA
        )
        pos_x = (FASE2_LARGURA_PERSONAGEM - nova_largura) // 2
        pos_y = FASE2_ALTURA_PERSONAGEM - nova_altura
        quadro.blit(imagem, (pos_x, pos_y))
        frames.append(quadro)

    return frames


def executar_fase2(TELA, RELOGIO, LARGURA, ALTURA):
    pasta = os.path.dirname(os.path.abspath(__file__))
    pasta_assets = os.path.join(pasta, "assets")
    caminho_mapa = os.path.join(pasta, "mapa_2.jpeg")

    try:
        mapa = pygame.image.load(caminho_mapa).convert()
    except (pygame.error, FileNotFoundError):
        raise FileNotFoundError("Nao encontrei o arquivo mapa_2.jpeg na pasta principal.")

    mapa = pygame.transform.scale(mapa, (LARGURA, ALTURA))
    animacoes_fase2 = {}

    for direcao_animacao in ("front", "back", "left", "right"):
        animacoes_fase2[(direcao_animacao, "walk")] = carregar_animacao_fase2(
            pasta_assets, direcao_animacao, "walk"
        )
        animacoes_fase2[(direcao_animacao, "run")] = carregar_animacao_fase2(
            pasta_assets, direcao_animacao, "run"
        )

    player_frente_fase2 = carregar_imagem_fase2(
        pasta_assets, "player.png",
        (FASE2_LARGURA_PERSONAGEM, FASE2_ALTURA_PERSONAGEM)
    )
    player_costas_fase2 = carregar_imagem_fase2(
        pasta_assets, "player_back.png",
        (FASE2_LARGURA_PERSONAGEM, FASE2_ALTURA_PERSONAGEM)
    )
    meteoro_sprite = carregar_imagem_fase2(
        pasta_assets, "meteoro.png",
        (FASE2_TAMANHO_METEORO, FASE2_TAMANHO_METEORO)
    )

    if player_frente_fase2 is None:
        raise FileNotFoundError("Nao encontrei assets/player.png")
    if player_costas_fase2 is None:
        player_costas_fase2 = player_frente_fase2
    if meteoro_sprite is None:
        raise FileNotFoundError("Nao encontrei assets/meteoro.png")

    def imagem_personagem_fase2(direcao, correndo, andando, quadro):
        acao = "run" if correndo else "walk"
        frames = animacoes_fase2.get((direcao, acao), [])

        if not frames and correndo:
            frames = animacoes_fase2.get((direcao, "walk"), [])

        if andando and frames:
            return frames[quadro % len(frames)]
        if direcao == "back":
            return player_costas_fase2
        if direcao == "front":
            return player_frente_fase2
        if frames:
            return frames[0]
        return player_frente_fase2

    jogador_x = float((LARGURA - FASE2_LARGURA_PERSONAGEM) // 2)
    jogador_y = 250.0
    jogador = pygame.Rect(
        int(jogador_x), int(jogador_y),
        FASE2_LARGURA_PERSONAGEM, FASE2_ALTURA_PERSONAGEM
    )

    direcao = "front"
    quadro = 0
    tempo_animacao = 0
    acao_animacao_anterior = "walk"

    executando_fase = True
    obstaculos = []
    tempo_spawn = 0
    morreu = False
    tempo_sobrevivencia = 0
    TEMPO_LIMITE = 60

    while executando_fase and not morreu:
        dt = min(RELOGIO.tick(60) / 1000, 0.05)
        tempo_sobrevivencia += dt
        tempo_animacao += dt * 1000

        if tempo_sobrevivencia >= TEMPO_LIMITE:
            executando_fase = False

        andando = False
        correndo = False

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return None
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                executando_fase = False

        teclas = pygame.key.get_pressed()
        dx = 0
        dy = 0

        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            dx -= 1
            direcao = "left"
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            dx += 1
            direcao = "right"

        andando = dx != 0 or dy != 0
        correndo = (
            teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
        ) and andando

        velocidade = FASE2_VELOCIDADE_CORRIDA if correndo else FASE2_VELOCIDADE

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        jogador_x += dx * velocidade * dt
        jogador_y += dy * velocidade * dt
        jogador.x = round(jogador_x)
        jogador.y = round(jogador_y)
        jogador.clamp_ip(pygame.Rect(0, 0, LARGURA, ALTURA))
        jogador_x = float(jogador.x)
        jogador_y = float(jogador.y)

        acao_atual = "run" if correndo else "walk"
        if acao_atual != acao_animacao_anterior:
            quadro = 0
            tempo_animacao = 0
            acao_animacao_anterior = acao_atual

        if andando:
            intervalo = 75 if correndo else 125
            if tempo_animacao >= intervalo:
                quadro += 1
                tempo_animacao = 0
        else:
            quadro = 0
            tempo_animacao = 0

        sprite = imagem_personagem_fase2(direcao, correndo, andando, quadro)

        tempo_spawn += dt
        if tempo_spawn >= FASE2_INTERVALO_SPAWN:
            tempo_spawn = 0
            x = random.randint(0, LARGURA - FASE2_TAMANHO_OBSTACULO)
            obstaculos.append(pygame.Rect(
                x, -FASE2_TAMANHO_OBSTACULO,
                FASE2_TAMANHO_OBSTACULO, FASE2_TAMANHO_OBSTACULO
            ))

        for obstaculo in obstaculos[:]:
            obstaculo.y += int(FASE2_VELOCIDADE_OBSTACULO * dt)

            # Hitbox menor que o desenho do meteoro.
            hitbox_obstaculo = obstaculo.inflate(-22, -30)
            if jogador.colliderect(hitbox_obstaculo):
                morreu = True

            if obstaculo.top > ALTURA:
                obstaculos.remove(obstaculo)

        TELA.blit(mapa, (0, 0))

        for obstaculo in obstaculos:
            pos_meteoro = meteoro_sprite.get_rect(center=obstaculo.center)
            TELA.blit(meteoro_sprite, pos_meteoro)

        TELA.blit(sprite, jogador.topleft)
        pygame.display.flip()

    if morreu:
        fonte = pygame.font.Font(None, 70)
        texto = fonte.render("VOCE MORREU!", True, (255, 0, 0))
        TELA.fill((0, 0, 0))
        TELA.blit(texto, texto.get_rect(center=(LARGURA // 2, ALTURA // 2)))
        pygame.display.flip()
        pygame.time.delay(2000)
        return False

    if tempo_sobrevivencia >= TEMPO_LIMITE:
        fonte = pygame.font.Font(None, 54)
        texto = fonte.render(
            "O jogo acabou! Obrigado por jogar!",
            True, (255, 255, 255)
        )
        TELA.fill((0, 0, 0))
        TELA.blit(texto, texto.get_rect(center=(LARGURA // 2, ALTURA // 2)))
        pygame.display.flip()
        pygame.time.delay(3000)
        return True

    # Sair com ESC nao conta como vitoria.
    return False


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
PASTA = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(PASTA, "assets")

# Arquivos de video e audio salvos na pasta assets.
CAMINHO_VIDEO_INTRO = os.path.join(ASSETS, "VideoIntrodução.mp4")
CAMINHO_AUDIO_ABERTURA = os.path.join(ASSETS, "audio_abertura.wav")
CAMINHO_VIDEO_FINAL = os.path.join(ASSETS, "VideoFinal.mp4")

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Between Two Worlds")
RELOGIO = pygame.time.Clock()


def reproduzir_video(caminho_video, caminho_audio=None):
    """Reproduz um MP4 na janela do Pygame. ESC pula o video.

    Retorna True quando o video termina ou e pulado; False quando a
    janela e fechada. O audio separado e opcional.
    """
    if not os.path.isfile(caminho_video):
        raise FileNotFoundError("Video nao encontrado: " + caminho_video)

    captura = cv2.VideoCapture(caminho_video)
    if not captura.isOpened():
        captura.release()
        raise RuntimeError("Nao foi possivel abrir o video: " + caminho_video)

    canal_audio = None
    som_audio = None

    try:
        if caminho_audio and os.path.isfile(caminho_audio):
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                som_audio = pygame.mixer.Sound(caminho_audio)
                canal_audio = som_audio.play()
            except pygame.error as erro:
                print("Nao foi possivel tocar o audio da abertura:", erro)

        fps_video = captura.get(cv2.CAP_PROP_FPS)
        if not fps_video or fps_video <= 0:
            fps_video = 30
        fps_video = max(1, min(60, round(fps_video)))
        relogio_video = pygame.time.Clock()

        while True:
            for evento_video in pygame.event.get():
                if evento_video.type == pygame.QUIT:
                    return False
                if (evento_video.type == pygame.KEYDOWN
                        and evento_video.key == pygame.K_ESCAPE):
                    return True

            sucesso, quadro_video = captura.read()
            if not sucesso:
                break

            quadro_video = cv2.cvtColor(quadro_video, cv2.COLOR_BGR2RGB)
            superficie_video = pygame.surfarray.make_surface(
                quadro_video.swapaxes(0, 1)
            )

            largura_video, altura_video = superficie_video.get_size()
            escala = min(LARGURA / largura_video, ALTURA / altura_video)
            novo_tamanho = (
                max(1, int(largura_video * escala)),
                max(1, int(altura_video * escala))
            )
            superficie_video = pygame.transform.smoothscale(
                superficie_video, novo_tamanho
            )

            TELA.fill((0, 0, 0))
            posicao = (
                (LARGURA - novo_tamanho[0]) // 2,
                (ALTURA - novo_tamanho[1]) // 2
            )
            TELA.blit(superficie_video, posicao)
            pygame.display.flip()
            relogio_video.tick(fps_video)

        return True

    finally:
        captura.release()
        if canal_audio is not None:
            canal_audio.stop()

# MENU 
CAMINHO_MENU = os.path.join(ASSETS, "menu.png")
MENU = pygame.image.load(CAMINHO_MENU).convert()
MENU = pygame.transform.scale(MENU, (LARGURA, ALTURA))

ESCALA_X = LARGURA / 928
ESCALA_Y = ALTURA / 632

def criar_botao(x, y, largura, altura):
    return pygame.Rect(
        int(x * ESCALA_X),
        int(y * ESCALA_Y),
        int(largura * ESCALA_X),
        int(altura * ESCALA_Y)
    )

botoes_menu = {
    "jogar": criar_botao(105, 340, 270, 40),
    "continuar": criar_botao(105, 380, 270, 40),
    "novo_jogo": criar_botao(105, 420, 270, 40),
    "opcoes": criar_botao(105, 460, 270, 40),
    "sair": criar_botao(105, 500, 270, 40)
}

botao_voltar = criar_botao(30, 550, 180, 50)
botao_iniciar_fase2 = pygame.Rect(350, 390, 260, 70)

tela_atual = "menu"

FONTE = pygame.font.SysFont("arial", 20)
FONTE_PEQUENA = pygame.font.SysFont("arial", 16)


CAMINHO_MUSICA_EASTER_EGG = os.path.join(ASSETS, "MusicaEasterEgg.wav")
CAMINHO_MUSICA_PRINCIPAL = os.path.join(ASSETS, "trilha_principal.ogg")
CAMINHO_MUSICA_MENU = os.path.join(ASSETS, "SomDoMenu.ogg")

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
        "right_run.png",
        "menu.png",
        "combate.jpeg",
        "personagem.png",
        "goblin.png",
        "meteoro.png",

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


nome_mapa = "mapa.png"

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

goblin_sprite = carregar_imagem(
    "goblin.png",
    (80, 90)
)

if goblin_sprite is None:
    raise FileNotFoundError("Não encontrei assets/goblin.png")

personagem = carregar_imagem(
    "personagem.png",
    (LARGURA_PERSONAGEM, ALTURA_PERSONAGEM))

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

# Bloqueia a corrida quando a estamina zera ate recuperar 25%.
corrida_bloqueada = False
PERCENTUAL_RETORNO_CORRIDA = 0.25

editor_colisoes = False
editor_portas = False
editor_baus = False

inventario_aberto = False
bau_aberto = None
item_selecionado = 0

#config inimigo
TAMANHO_INIMIGO = 28
VELOCIDADE_INIMIGO = 2.0
ALCANCE_PERSEGUICAO = 300
DISTANCIA_SPAWN_INIMIGO = 300
inimigo = pygame.Rect(
    0, 0,
    TAMANHO_INIMIGO,
    TAMANHO_INIMIGO
)
inimigo_ativo = True
segunda_fase_liberada = False
hp_jogador = 100
hp_inimigo = 100
defendendo = False
bonus_dano = False
mensagem_combate = ""

mensagem = ""
tempo_mensagem = 0

# EASTER EGG config 
proxima_estatua = 1
estatuas_ativadas = set()
mensagem_enigma = []
tempo_enigma = 0
easter_egg_concluido = False
aura_protetora_ativa = False
mensagem_aura_pendente = False
tempo_mensagem_aura = 0

ESTATUAS = {
    1: {"x": 3849, "y": 2442, "raio": 100, "altura_texto": 255},
    2: {"x": 1860, "y": 2637, "raio": 100, "altura_texto": 210},
    3: {"x": 1245, "y": 1530, "raio": 100, "altura_texto": 280},
    4: {"x": 2487, "y": 2637, "raio": 100, "altura_texto": 210}
}

ENIGMAS_ESTATUAS = {
    1: [
        "Duas figuras pequenas guardam o salão,",
        "mas e a da esquerda que chama tua atenção.",
        "Entre pilares e sombras, ela esta a esperar;",
        "segue pelo lado esquerdo para a encontrar."
    ],
    2: [
        "Procura no jardim, entre folhas cor de sangue,",
        "uma figura de pedra que a escuridão esconde.",
        "Com as asas abertas, ela parece vigiar;",
        "entre as árvores vermelhas, você vai encontrar."
    ],
    3: [
        "A busca esta quase no fim, falta pouco para encontrar;",
        "duas pequenas figuras ainda vais avistar.",
        "A primeira ja encontraste, não precisas retornar;",
        "procura a da direita, pois e lá que deves chegar."
    ]
}


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

#INIMIGOOO!!!!!
def tem_colisao_inimigo(retangulo):
    if retangulo.left < 0 or retangulo.top < 0:
        return True
    if retangulo.right > MAPA_LARGURA or retangulo.bottom > MAPA_ALTURA:
        return True

    cx1 = int(retangulo.left // CELULA_MUNDO)
    cy1 = int(retangulo.top // CELULA_MUNDO)
    cx2 = int((retangulo.right - 1) // CELULA_MUNDO)
    cy2 = int((retangulo.bottom - 1) // CELULA_MUNDO)

    for cx in range(cx1, cx2 + 1):
        for cy in range(cy1, cy2 + 1):
            if (cx, cy) in colisoes:
                return True

    for porta in portas:
        if not porta.get("aberta", False) and retangulo.colliderect(retangulo_porta(porta)):
            return True

    for bau in baus:
        if retangulo.colliderect(retangulo_bau(bau)):
            return True

    return False


def posicionar_inimigo_longe():
    global inimigo

    centro_jogador = hitbox_jogador().center

    posicoes = [
        (DISTANCIA_SPAWN_INIMIGO, 0),
        (-DISTANCIA_SPAWN_INIMIGO, 0),
        (0, DISTANCIA_SPAWN_INIMIGO),
        (0, -DISTANCIA_SPAWN_INIMIGO),
        (DISTANCIA_SPAWN_INIMIGO, DISTANCIA_SPAWN_INIMIGO),
        (-DISTANCIA_SPAWN_INIMIGO, DISTANCIA_SPAWN_INIMIGO),
        (DISTANCIA_SPAWN_INIMIGO, -DISTANCIA_SPAWN_INIMIGO),
        (-DISTANCIA_SPAWN_INIMIGO, -DISTANCIA_SPAWN_INIMIGO)
    ]

    for dx, dy in posicoes:
        candidato = pygame.Rect(
            centro_jogador[0] + dx - TAMANHO_INIMIGO // 2,
            centro_jogador[1] + dy - TAMANHO_INIMIGO // 2,
            TAMANHO_INIMIGO,
            TAMANHO_INIMIGO
        )

        if not tem_colisao_inimigo(candidato):
            inimigo = candidato
            return False

    return False


def iniciar_combate():
    global hp_jogador, hp_inimigo, defendendo, bonus_dano, mensagem_combate
    hp_jogador = 100
    hp_inimigo = 100
    defendendo = False
    bonus_dano = False
    mensagem_combate = "Um inimigo apareceu!"


def atualizar_inimigo(dt):
    global tela_atual

    if not inimigo_ativo:
        return

    centro_jogador = hitbox_jogador().center
    dx = centro_jogador[0] - inimigo.centerx
    dy = centro_jogador[1] - inimigo.centery
    distancia = math.hypot(dx, dy)

    if distancia <= ALCANCE_PERSEGUICAO and distancia > 0:
        movimento_x = (dx / distancia) * VELOCIDADE_INIMIGO * dt * 60
        movimento_y = (dy / distancia) * VELOCIDADE_INIMIGO * dt * 60

        novo = inimigo.copy()
        novo.x = round(inimigo.x + movimento_x)
        if not tem_colisao_inimigo(novo):
            inimigo.x = novo.x

        novo = inimigo.copy()
        novo.y = round(inimigo.y + movimento_y)
        if not tem_colisao_inimigo(novo):
            inimigo.y = novo.y

    if inimigo.colliderect(hitbox_jogador()):
        iniciar_combate()
        tela_atual = "combate"


def carregar_recurso_combate(nome):
    caminhos = [os.path.join(ASSETS, nome), os.path.join(PASTA, nome)]
    for arquivo in caminhos:
        if os.path.isfile(arquivo):
            try:
                return pygame.image.load(arquivo).convert_alpha()
            except pygame.error:
                pass
    return None


def cor_vida(vida):
    if vida > 60:
        return (0, 220, 0)
    if vida > 30:
        return (240, 210, 0)
    return (230, 40, 40)


def barra_vida_combate(x, y, vida, nome):
    pygame.draw.rect(TELA, (50, 50, 50), (x, y, 300, 25))
    pygame.draw.rect(TELA, cor_vida(vida), (x, y, max(0, int(300 * vida / 100)), 25))
    pygame.draw.rect(TELA, (230, 230, 230), (x, y, 300, 25), 2)
    desenhar_texto(nome + ": " + str(vida) + "/100", x, y - 28, (255, 255, 255), FONTE)


FUNDO_COMBATE = carregar_recurso_combate("combate.jpeg")
if FUNDO_COMBATE is None:
    FUNDO_COMBATE = carregar_recurso_combate("combate.jpg")
if FUNDO_COMBATE is not None:
    FUNDO_COMBATE = pygame.transform.scale(FUNDO_COMBATE, (LARGURA, ALTURA))


def desenhar_menu_combate():
    if FUNDO_COMBATE is not None:
        TELA.blit(FUNDO_COMBATE, (0, 0))
    else:
        TELA.fill((28, 20, 30))

    #personagem no combate
    personagem_combate = pygame.transform.scale(personagem, (150, 220))
    inimigo_combate = pygame.transform.scale(goblin_sprite, (180, 220))
    TELA.blit(personagem_combate, (50, 300))
    TELA.blit(inimigo_combate, (600, 300))

    barra_vida_combate(45, 55, hp_jogador, "personagem")
    barra_vida_combate(615, 55, hp_inimigo, "inimigo")

    botoes = [
        (pygame.Rect(100, 550, 200, 55), "ATACAR"),
        (pygame.Rect(380, 550, 200, 55), "DEFENDER"),
        (pygame.Rect(660, 550, 200, 55), "FUGIR")
    ]
    for ret, texto in botoes:
        pygame.draw.rect(TELA, (80, 80, 80), ret)
        pygame.draw.rect(TELA, (220, 220, 220), ret, 2)
        imagem = FONTE.render(texto, True, (255, 255, 255))
        TELA.blit(imagem, imagem.get_rect(center=ret.center))

    if mensagem_combate:
        desenhar_texto(mensagem_combate, 100, 485, (255, 255, 255), FONTE)

    if hp_inimigo <= 0:
        desenhar_texto("VOCE VENCEU!", 390, 220, (255, 255, 255), FONTE)
    elif hp_jogador <= 0:
        desenhar_texto("VOCE PERDEU!", 390, 220, (255, 255, 255), FONTE)


def processar_clique_combate(pos):
    global hp_jogador, hp_inimigo, defendendo, bonus_dano, mensagem_combate
    global tela_atual, inimigo_ativo, executando, segunda_fase_liberada

    if hp_jogador <= 0 or hp_inimigo <= 0:
        # A fase 2 só é liberada se a personagem derrotar o inimigo.
        if hp_inimigo <= 0 and hp_jogador > 0:
            inimigo_ativo = False
            segunda_fase_liberada = True
            tela_atual = "segunda_fase_menu"
        else:
            # Se a personagem perder, a fase 2 continua bloqueada.
            inimigo_ativo = True
            tela_atual = "jogo"
        return

    botao_atacar = pygame.Rect(100, 550, 200, 55)
    botao_defender = pygame.Rect(380, 550, 200, 55)
    botao_fugir = pygame.Rect(660, 550, 200, 55)

    if botao_atacar.collidepoint(pos):
        dano = random.randint(5, 20)
        if bonus_dano:
            dano += 10
            bonus_dano = False
        hp_inimigo = max(0, hp_inimigo - dano)
        mensagem_combate = "Voce atacou! Dano: " + str(dano)

        if hp_inimigo > 0:
            dano_inimigo = random.randint(4, 20)
            if defendendo:
                dano_inimigo //= 2
                mensagem_combate += " Voce defendeu!"
            hp_jogador = max(0, hp_jogador - dano_inimigo)
        defendendo = False

    elif botao_defender.collidepoint(pos):
        defendendo = True
        bonus_dano = True
        dano = random.randint(5, 8)
        mensagem_combate = "Voce defendeu e causou " + str(dano) + " de dano!"
        hp_jogador=hp_jogador+dano//2

        if hp_inimigo > 0:
            dano_inimigo = random.randint(15, 30) // 2
            hp_jogador = max(0, hp_jogador - dano_inimigo)
            mensagem_combate += " Dano recebido: " + str(dano_inimigo)
        defendendo = False

    elif botao_fugir.collidepoint(pos):
        mensagem_combate = "Voce fugiu do combate!"
        posicionar_inimigo_longe()
        tela_atual = "jogo"

    
    if hp_inimigo <= 0 and hp_jogador > 0:
        inimigo_ativo = False
        segunda_fase_liberada = True
        tela_atual = "segunda_fase_menu"


posicionar_inimigo_longe()


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


def tocar_musica_easter_egg():
    if not os.path.isfile(CAMINHO_MUSICA_EASTER_EGG):
        print("Musica nao encontrada:", CAMINHO_MUSICA_EASTER_EGG)
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(CAMINHO_MUSICA_EASTER_EGG)
        pygame.mixer.music.play()
    except pygame.error as erro:
        print("Erro ao tocar a musica:", erro)

def iniciar_musica_principal():
    if not os.path.isfile(CAMINHO_MUSICA_PRINCIPAL):
        print("Trilha sonora nao encontrada!")
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(CAMINHO_MUSICA_PRINCIPAL)
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)

    except pygame.error as erro:
        print("Erro ao tocar a trilha sonora:", erro)


def iniciar_musica_menu():
    if not os.path.isfile(CAMINHO_MUSICA_MENU):
        print("Musica do menu nao encontrada:", CAMINHO_MUSICA_MENU)
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(CAMINHO_MUSICA_MENU)
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)

    except pygame.error as erro:
        print("Erro ao tocar a musica do menu:", erro)


def encontrar_estatua_proxima():
    centro = hitbox_jogador().center
    estatua_mais_proxima = None
    menor_distancia = float("inf")

    for numero, estatua in ESTATUAS.items():
        dx = centro[0] - estatua["x"]
        dy = centro[1] - estatua["y"]
        distancia = math.sqrt(dx ** 2 + dy ** 2)

        if distancia <= estatua["raio"] and distancia < menor_distancia:
            menor_distancia = distancia
            estatua_mais_proxima = numero

    return estatua_mais_proxima


def interagir_estatua(numero):
    global proxima_estatua, mensagem_enigma, tempo_enigma
    global easter_egg_concluido, estatuas_ativadas
    global aura_protetora_ativa
    global mensagem_aura_pendente, tempo_mensagem_aura

    if easter_egg_concluido:
        mostrar_mensagem("O segredo das estatuas ja foi descoberto!")
        return

    if numero == proxima_estatua and numero == 4:
        easter_egg_concluido = True
        aura_protetora_ativa = True
        estatuas_ativadas.add(numero)
        mensagem_enigma = []
        tempo_enigma = 0
        tocar_musica_easter_egg()
        mostrar_mensagem("Voce descobriu o segredo das quatro estatuas!")
        mensagem_aura_pendente = True
        tempo_mensagem_aura = pygame.time.get_ticks() + 3500
        return

    if numero in ENIGMAS_ESTATUAS:
        mensagem_enigma = ENIGMAS_ESTATUAS[numero][:]
        tempo_enigma = pygame.time.get_ticks() + 10000
    else:
        mensagem_enigma = [
            "A pedra guarda um segredo antigo...",
            "Mas ainda nao chegou a hora de revela-lo."
        ]
        tempo_enigma = pygame.time.get_ticks() + 6000

    if numero == proxima_estatua:
        estatuas_ativadas.add(numero)
        proxima_estatua += 1


def desenhar_aura_protetora():
    if not aura_protetora_ativa:
        return

    pulso = int((math.sin(pygame.time.get_ticks() / 280) + 1) * 4)
    largura_aura = LARGURA_PERSONAGEM + 36 + pulso
    altura_aura = ALTURA_PERSONAGEM + 30 + pulso
    superficie_aura = pygame.Surface(
        (largura_aura, altura_aura), pygame.SRCALPHA
    )

    pygame.draw.ellipse(
        superficie_aura, (70, 160, 255, 30),
        (0, 0, largura_aura, altura_aura)
    )
    pygame.draw.ellipse(
        superficie_aura, (100, 190, 255, 55),
        (5, 5, largura_aura - 10, altura_aura - 10)
    )
    pygame.draw.ellipse(
        superficie_aura, (180, 225, 255, 180),
        (10, 10, largura_aura - 20, altura_aura - 20), 3
    )

    pos_x = int(player_x - camera_x - (largura_aura - LARGURA_PERSONAGEM) / 2)
    pos_y = int(player_y - camera_y - (altura_aura - ALTURA_PERSONAGEM) / 2)
    TELA.blit(superficie_aura, (pos_x, pos_y))


def desenhar_enigma():
    if not mensagem_enigma or tempo_enigma <= pygame.time.get_ticks():
        return

    altura_linha = 24
    altura_caixa = len(mensagem_enigma) * altura_linha + 24
    caixa = pygame.Rect(
        40, ALTURA - altura_caixa - 60, LARGURA - 80, altura_caixa
    )
    pygame.draw.rect(TELA, (25, 21, 27), caixa)
    pygame.draw.rect(TELA, (205, 165, 75), caixa, 2)

    for indice, linha in enumerate(mensagem_enigma):
        imagem = FONTE_PEQUENA.render(linha, True, (240, 235, 220))
        TELA.blit(imagem, (caixa.x + 15, caixa.y + 12 + indice * altura_linha))


def interagir():
    global bau_aberto, item_selecionado

    estatua = encontrar_estatua_proxima()
    if estatua is not None:
        interagir_estatua(estatua)
        return

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

musica_iniciada = False
musica_menu_iniciada = False
executando = True

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
            continue

        if tela_atual == "combate":
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                processar_clique_combate(evento.pos)
            continue

        if tela_atual == "segunda_fase_menu":
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if segunda_fase_liberada and botao_iniciar_fase2.collidepoint(evento.pos):
                    resultado = executar_fase2(TELA, RELOGIO, LARGURA, ALTURA)

                    if resultado is None:
                        executando = False
                    elif resultado:
                        # O video final so aparece depois da vitoria na fase 2.
                        pygame.mixer.music.stop()
                        if reproduzir_video(CAMINHO_VIDEO_FINAL):
                            tela_atual = "menu"
                            musica_menu_iniciada = False
                            musica_iniciada = False
                        else:
                            executando = False
                    else:
                        # Derrota ou saida antecipada: nao mostra o video final.
                        tela_atual = "menu"
                        musica_menu_iniciada = False
                        musica_iniciada = False
            continue

        if tela_atual == "menu":
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                mouse = evento.pos

                if botoes_menu["jogar"].collidepoint(mouse):
                    pygame.mixer.music.stop()
                    if reproduzir_video(
                        CAMINHO_VIDEO_INTRO,
                        CAMINHO_AUDIO_ABERTURA
                    ):
                        tela_atual = "jogo"
                        musica_iniciada = False
                    else:
                        executando = False

                elif botoes_menu["continuar"].collidepoint(mouse):
                    tela_atual = "jogo"

                elif botoes_menu["novo_jogo"].collidepoint(mouse):
                    player_x = min(1200, max(0, MAPA_LARGURA - LARGURA_PERSONAGEM))
                    player_y = min(900, max(0, MAPA_ALTURA - ALTURA_PERSONAGEM))
                    posicionar_inimigo_longe()
                    tela_atual = "jogo"

                elif botoes_menu["opcoes"].collidepoint(mouse):
                    tela_atual = "opcoes"

                elif botoes_menu["sair"].collidepoint(mouse):
                    executando = False

            continue

        if tela_atual == "opcoes":
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if botao_voltar.collidepoint(evento.pos):
                    tela_atual = "menu"

            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                tela_atual = "menu"

            continue
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
    if not executando:
        break

    if tela_atual == "menu":
        if not musica_menu_iniciada:
            iniciar_musica_menu()
            musica_menu_iniciada = True
            musica_iniciada = False

        TELA.blit(MENU, (0, 0))
        pygame.display.flip()
        continue

    if tela_atual == "opcoes":
        TELA.fill((15, 10, 20))

        titulo = FONTE.render(
            "CONFIGURACOES",
            True,
            (220, 220, 220)
        )
        TELA.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 180)))

        texto = FONTE.render(
            "Tela: 960 x 640",
            True,
            (200, 200, 200)
        )
        TELA.blit(texto, texto.get_rect(center=(LARGURA // 2, 280)))

        pygame.draw.rect(TELA, (100, 25, 35), botao_voltar)
        texto_voltar = FONTE.render("VOLTAR", True, (255, 255, 255))
        TELA.blit(texto_voltar, texto_voltar.get_rect(center=botao_voltar.center))

        pygame.display.flip()
        continue

    if tela_atual == "segunda_fase_menu":
        TELA.fill((15, 10, 20))

        titulo_fase2 = pygame.font.SysFont("arial", 54, bold=True).render(
            "Você venceu!", True, (235, 220, 220)
        )
        TELA.blit(
            titulo_fase2,
            titulo_fase2.get_rect(center=(LARGURA // 2, 210))
        )

        descricao_fase2 = FONTE.render(
            "Voce derrotou o inimigo agora ira para a segunda fase,prepare para desviar!",
            True, (220, 220, 220)
        )
        TELA.blit(
            descricao_fase2,
            descricao_fase2.get_rect(center=(LARGURA // 2, 300))
        )

        pygame.draw.rect(TELA, (100, 25, 35), botao_iniciar_fase2)
        pygame.draw.rect(TELA, (230, 220, 220), botao_iniciar_fase2, 2)
        texto_iniciar = FONTE.render("INICIAR", True, (255, 255, 255))
        TELA.blit(texto_iniciar, texto_iniciar.get_rect(center=botao_iniciar_fase2.center))

        pygame.display.flip()
        continue

    if tela_atual == "combate":
        desenhar_menu_combate()
        pygame.display.flip()
        continue

    if tela_atual == "jogo" and not musica_iniciada:
        iniciar_musica_principal()
        musica_iniciada = True
        musica_menu_iniciada = False

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

        shift_pressionado = (
            teclas[pygame.K_LSHIFT]
            or teclas[pygame.K_RSHIFT]
        )

        # So tenta correr se houver estamina e a corrida nao estiver bloqueada.
        quer_correr = (
            shift_pressionado
            and andando
            and estamina > 0
            and not corrida_bloqueada
        )

        # Consome estamina uma unica vez por quadro.
        if quer_correr:
            estamina -= DRENAGEM_ESTAMINA * dt
        else:
            estamina += RECUPERACAO_ESTAMINA * dt

        estamina = max(0, min(ESTAMINA_MAXIMA, estamina))

        # Ao chegar a zero, so libera a corrida depois de recuperar 25%.
        if estamina <= 0:
            corrida_bloqueada = True
        elif estamina >= ESTAMINA_MAXIMA * PERCENTUAL_RETORNO_CORRIDA:
            corrida_bloqueada = False

        correndo = (
            shift_pressionado
            and andando
            and estamina > 0
            and not corrida_bloqueada
        )

        velocidade = VELOCIDADE_CORRIDA if correndo else VELOCIDADE

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

    if tela_atual == "jogo" and not (
        inventario_aberto or bau_aberto is not None
        or editor_colisoes or editor_portas or editor_baus
    ):
        atualizar_inimigo(dt)

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

    if inimigo_ativo:
        inimigo_tela = goblin_sprite.get_rect(
            center=(
                inimigo.centerx - int(camera_x),
                inimigo.centery - int(camera_y)
            )
        )
        TELA.blit(goblin_sprite, inimigo_tela)

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

    desenhar_aura_protetora()

    TELA.blit(
        sprite,
        (
            int(player_x - camera_x),
            int(player_y - camera_y)
        )
    )

    estatua_proxima = encontrar_estatua_proxima()
    if estatua_proxima is not None and not easter_egg_concluido:
        estatua = ESTATUAS[estatua_proxima]
        texto_interacao = FONTE_PEQUENA.render("[E] Interagir", True, (240, 235, 220))
        pos_x = int(estatua["x"] - camera_x - texto_interacao.get_width() // 2)
        pos_y = int(estatua["y"] - camera_y - estatua["altura_texto"])
        TELA.blit(texto_interacao, (pos_x, pos_y))

    desenhar_barra_estamina()
    desenhar_editor()
    desenhar_enigma()

    tempo_atual = pygame.time.get_ticks()
    if mensagem_aura_pendente and tempo_atual >= tempo_mensagem_aura:
        mensagem_aura_pendente = False
        mostrar_mensagem("Voce ganhou uma aura de protecao!")

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

