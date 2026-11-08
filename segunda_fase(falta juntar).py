import pygame
import os
import random

VELOCIDADE_OBSTACULO = 400
INTERVALO_SPAWN = 0.5
TAMANHO_OBSTACULO = 30

LARGURA_PERSONAGEM = 90
ALTURA_PERSONAGEM = 110

VELOCIDADE = 150
VELOCIDADE_CORRIDA = 250


def carregar_imagem(pasta_assets, nome, tamanho=None):
    caminho = os.path.join(pasta_assets, nome)

    try:
        imagem = pygame.image.load(caminho).convert_alpha()

        if tamanho:
            imagem = pygame.transform.scale(imagem, tamanho)

        return imagem

    except (pygame.error, FileNotFoundError):
        return None


def carregar_animacao(pasta_assets, direcao, acao):
    frames = []

    for numero in range(1, 7):
        nome = f"{direcao}_{acao}_{numero}.png"
        caminho = os.path.join(pasta_assets, nome)

        try:
            imagem = pygame.image.load(caminho).convert_alpha()
        except (pygame.error, FileNotFoundError):
            continue

        largura_original, altura_original = imagem.get_size()

        escala = min(
            LARGURA_PERSONAGEM / largura_original,
            ALTURA_PERSONAGEM / altura_original
        )

        nova_largura = max(1, round(largura_original * escala))
        nova_altura = max(1, round(altura_original * escala))

        imagem = pygame.transform.scale(
            imagem,
            (nova_largura, nova_altura)
        )

        quadro = pygame.Surface(
            (LARGURA_PERSONAGEM, ALTURA_PERSONAGEM),
            pygame.SRCALPHA
        )

        pos_x = (LARGURA_PERSONAGEM - nova_largura) // 2
        pos_y = ALTURA_PERSONAGEM - nova_altura

        quadro.blit(imagem, (pos_x, pos_y))
        frames.append(quadro)

    return frames


def executar_fase2(TELA, RELOGIO, LARGURA, ALTURA):

    pasta = os.path.dirname(os.path.abspath(__file__))
    pasta_assets = os.path.join(pasta, "assets")
    caminho_mapa = os.path.join(pasta, "mapa_2.jpeg")

    mapa = pygame.image.load(caminho_mapa).convert()
    mapa = pygame.transform.scale(mapa, (LARGURA, ALTURA))
    animacoes = {}

    for direcao in ("front", "back", "left", "right"):

        animacoes[(direcao, "walk")] = carregar_animacao(
            pasta_assets, direcao, "walk"
        )

        animacoes[(direcao, "run")] = carregar_animacao(
            pasta_assets, direcao, "run"
        )

    player_frente = carregar_imagem(
        pasta_assets,
        "player.png",
        (LARGURA_PERSONAGEM, ALTURA_PERSONAGEM)
    )

    player_costas = carregar_imagem(
        pasta_assets,
        "player_back.png",
        (LARGURA_PERSONAGEM, ALTURA_PERSONAGEM)
    )

    if player_frente is None:
        raise FileNotFoundError("Não encontrei assets/player.png")

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

    jogador_x = float((LARGURA - LARGURA_PERSONAGEM) // 2)
    jogador_y = float(250)

    jogador = pygame.Rect(
        int(jogador_x),
        int(jogador_y),
        LARGURA_PERSONAGEM,
        ALTURA_PERSONAGEM
    )

    direcao = "front"
    quadro = 0
    tempo_animacao = 0

    executando_fase = True

    #coisas pa disviar
    obstaculos = []
    tempo_spawn = 0
    morreu = False

    tempo_sobrevivencia = 0
    TEMPO_LIMITE = 60

    

    while executando_fase and not morreu:

        dt = min(RELOGIO.tick(60) / 1000, 0.05)
        tempo_sobrevivencia += dt
        if tempo_sobrevivencia >= TEMPO_LIMITE:
            executando_fase = False

        tempo_animacao += dt * 1000

        andando = False
        correndo = False

        
        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                return False

            if evento.type == pygame.KEYDOWN:

                if evento.key == pygame.K_ESCAPE:
                    executando_fase = False

        teclas = pygame.key.get_pressed()

        dx = 0
        dy = 0

        # movi
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            dx -= 1
            direcao = "left"

        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            dx += 1
            direcao = "right"

        andando = dx != 0 or dy != 0

        correndo = (
            teclas[pygame.K_LSHIFT]
            or teclas[pygame.K_RSHIFT]
        ) and andando

        velocidade = (
            VELOCIDADE_CORRIDA
            if correndo
            else VELOCIDADE
        )

        # pa n dar bug
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        jogador_x += dx * velocidade * dt
        jogador_y += dy * velocidade * dt

        jogador.x = round(jogador_x)
        jogador.y = round(jogador_y)

        
        jogador.clamp_ip(
            pygame.Rect(0, 0, LARGURA, ALTURA)
        )

        jogador_x = float(jogador.x)
        jogador_y = float(jogador.y)

        if andando:

            intervalo = 75 if correndo else 125

            if tempo_animacao >= intervalo:
                quadro += 1
                tempo_animacao = 0

        else:
            quadro = 0
            tempo_animacao = 0

        sprite = imagem_personagem(
            direcao,
            correndo,
            andando,
            quadro
        )


        tempo_spawn += dt

        if tempo_spawn >= INTERVALO_SPAWN:

            tempo_spawn = 0

            x = random.randint(
                0,
                LARGURA - TAMANHO_OBSTACULO
            )

            obstaculo = pygame.Rect(
                x,
                -TAMANHO_OBSTACULO,
                TAMANHO_OBSTACULO,
                TAMANHO_OBSTACULO
            )

            obstaculos.append(obstaculo)

        
        for obstaculo in obstaculos[:]:
            obstaculo.y += int(VELOCIDADE_OBSTACULO * dt)
            hitbox_obstaculo = obstaculo.inflate(-5, -5)
            if jogador.colliderect(hitbox_obstaculo):
                morreu = True
            if obstaculo.top > ALTURA:
                obstaculos.remove(obstaculo)

        TELA.blit(mapa, (0, 0))

        for obstaculo in obstaculos:
            pygame.draw.rect(
                TELA,
                (255, 0, 0),
                obstaculo
            )

        TELA.blit(sprite, jogador.topleft)

        pygame.display.flip()

    
    if morreu:

        fonte = pygame.font.Font(None, 70)

        texto = fonte.render(
            "VOCE MORREU!",
            True,
            (255, 0, 0)
        )

        TELA.fill((0, 0, 0))

        TELA.blit(
            texto,
            (
                LARGURA // 2 - texto.get_width() // 2,
                ALTURA // 2 - texto.get_height() // 2
            )
        )

        pygame.display.flip()
        pygame.time.delay(2000)

    elif tempo_sobrevivencia >= TEMPO_LIMITE:

        fonte = pygame.font.Font(None, 70)

        texto = fonte.render(
            "o jogo acabou obrigado por jogar!",
            True,
            (255, 255, 255)
        )

        TELA.fill((0, 0, 0))

        TELA.blit(
            texto,
            (
                LARGURA // 2 - texto.get_width() // 2,
                ALTURA // 2 - texto.get_height() // 2
            )
        )

        pygame.display.flip()
        pygame.time.delay(3000)

    
    return True



# Testar a fase 2 separadamente
if __name__ == "__main__":

    pygame.init()

    LARGURA = 960
    ALTURA = 640

    TELA = pygame.display.set_mode(
        (LARGURA, ALTURA)
    )

    pygame.display.set_caption(
        "Between Two Worlds - Fase 2"
    )

    RELOGIO = pygame.time.Clock()

    executar_fase2(
        TELA,
        RELOGIO,
        LARGURA,
        ALTURA
    )

    pygame.quit()
