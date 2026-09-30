import pygame
import os
import sys
import math
import json

pygame.init()

# ============================================================
# CONFIGURAÇÕES
# ============================================================

LARGURA = 960
ALTURA = 640
FPS = 60

VELOCIDADE = 2.8

ESCALA_MAPA = 1.35

# Tamanho de cada bloco usado no editor.
# Menor = colisões mais precisas.
TAMANHO_CELULA = 12


# ============================================================
# JANELA
# ============================================================

TELA = pygame.display.set_mode(
    (LARGURA, ALTURA)
)

pygame.display.set_caption(
    "Between Two Worlds"
)

RELOGIO = pygame.time.Clock()


# ============================================================
# PASTAS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ASSETS_DIR = os.path.join(
    BASE_DIR,
    "assets"
)

ARQUIVO_COLISAO = os.path.join(
    BASE_DIR,
    "collision_map.json"
)


# ============================================================
# CARREGAR IMAGEM
# ============================================================

def carregar_imagem(caminho, alpha=True):

    try:

        imagem = pygame.image.load(caminho)

        if alpha:

            imagem = imagem.convert_alpha()

        else:

            imagem = imagem.convert()

        return imagem

    except Exception as erro:

        print()
        print("Erro ao carregar imagem:")
        print(caminho)
        print(erro)

        return None


# ============================================================
# ENCONTRAR MAPA
# ============================================================

def encontrar_mapa():

    if not os.path.exists(ASSETS_DIR):

        return None


    arquivos = os.listdir(
        ASSETS_DIR
    )

    candidatos = []


    for arquivo in arquivos:

        caminho = os.path.join(
            ASSETS_DIR,
            arquivo
        )


        if not os.path.isfile(caminho):

            continue


        extensao = os.path.splitext(
            arquivo
        )[1].lower()


        if extensao not in [
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".webp"
        ]:

            continue


        nome = arquivo.lower()


        if nome in [
            "player.png",
            "player_sheet.png"
        ]:

            continue


        try:

            imagem = pygame.image.load(
                caminho
            )

            largura = imagem.get_width()
            altura = imagem.get_height()

            area = largura * altura


            if area > 200000:

                candidatos.append(
                    (
                        area,
                        caminho
                    )
                )


        except:

            pass


    if not candidatos:

        return None


    candidatos.sort(
        reverse=True
    )


    return candidatos[0][1]


# ============================================================
# MAPA
# ============================================================

CAMINHO_MAPA = encontrar_mapa()


if CAMINHO_MAPA is None:

    print()
    print("ERRO: não encontrei o mapa dentro de assets.")
    print()

    pygame.quit()
    sys.exit()


print()
print("Mapa utilizado:")
print(CAMINHO_MAPA)
print()


MAPA_ORIGINAL = carregar_imagem(
    CAMINHO_MAPA,
    False
)


if MAPA_ORIGINAL is None:

    pygame.quit()
    sys.exit()


MAPA_ORIGINAL_LARGURA = (
    MAPA_ORIGINAL.get_width()
)

MAPA_ORIGINAL_ALTURA = (
    MAPA_ORIGINAL.get_height()
)


MAPA_LARGURA = int(
    MAPA_ORIGINAL_LARGURA *
    ESCALA_MAPA
)

MAPA_ALTURA = int(
    MAPA_ORIGINAL_ALTURA *
    ESCALA_MAPA
)


MAPA = pygame.transform.smoothscale(
    MAPA_ORIGINAL,
    (
        MAPA_LARGURA,
        MAPA_ALTURA
    )
)


# ============================================================
# PLAYER
# ============================================================

CAMINHO_PLAYER = os.path.join(
    ASSETS_DIR,
    "player.png"
)


PLAYER_SHEET = carregar_imagem(
    CAMINHO_PLAYER,
    True
)


if PLAYER_SHEET is None:

    print(
        "ERRO: player.png não encontrado."
    )

    pygame.quit()
    sys.exit()


SHEET_LARGURA = (
    PLAYER_SHEET.get_width()
)

SHEET_ALTURA = (
    PLAYER_SHEET.get_height()
)


NUM_FRAMES = 2

FRAME_LARGURA = (
    SHEET_LARGURA //
    NUM_FRAMES
)

FRAME_ALTURA = SHEET_ALTURA


def criar_frame(numero):

    frame = pygame.Surface(
        (
            FRAME_LARGURA,
            FRAME_ALTURA
        ),
        pygame.SRCALPHA
    )


    frame.blit(
        PLAYER_SHEET,
        (0, 0),
        (
            numero * FRAME_LARGURA,
            0,
            FRAME_LARGURA,
            FRAME_ALTURA
        )
    )


    frame = pygame.transform.scale(
        frame,
        (52, 78)
    )


    return frame


FRAME_0 = criar_frame(0)
FRAME_1 = criar_frame(1)


# ============================================================
# DIREÇÕES
# ============================================================

FRENTE = 0
COSTAS = 1
ESQUERDA = 2
DIREITA = 3


# ============================================================
# COLISÕES
# ============================================================

# As colisões agora são armazenadas como células.
#
# Exemplo:
#
# "10,15"
#
# significa que existe uma célula bloqueada
# na posição X=10, Y=15 do mapa original.


celulas_colisao = set()


# ============================================================
# CARREGAR COLISÕES
# ============================================================

def carregar_colisoes():

    global celulas_colisao


    if not os.path.exists(
        ARQUIVO_COLISAO
    ):

        print(
            "Nenhum mapa de colisão encontrado."
        )

        celulas_colisao = set()

        return


    try:

        with open(
            ARQUIVO_COLISAO,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(
                arquivo
            )


        celulas_colisao = set()


        for item in dados:

            if (
                isinstance(item, list)
                and len(item) == 2
            ):

                x = int(item[0])
                y = int(item[1])

                celulas_colisao.add(
                    (x, y)
                )


        print(
            "Colisões carregadas:",
            len(celulas_colisao)
        )


    except Exception as erro:

        print(
            "Erro ao carregar colisões:",
            erro
        )

        celulas_colisao = set()


# ============================================================
# SALVAR COLISÕES
# ============================================================

def salvar_colisoes():

    dados = []


    for x, y in sorted(
        celulas_colisao
    ):

        dados.append(
            [x, y]
        )


    try:

        with open(
            ARQUIVO_COLISAO,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                dados,
                arquivo,
                indent=4
            )


        print()
        print(
            "Mapa de colisão salvo!"
        )

        print(
            "Total de células:",
            len(dados)
        )

        print()


    except Exception as erro:

        print(
            "Erro ao salvar colisões:",
            erro
        )


# ============================================================
# CONVERTER CÉLULA PARA RETÂNGULO
# ============================================================

def celula_para_rect(cx, cy):

    x = int(
        cx *
        TAMANHO_CELULA *
        ESCALA_MAPA
    )

    y = int(
        cy *
        TAMANHO_CELULA *
        ESCALA_MAPA
    )

    largura = int(
        TAMANHO_CELULA *
        ESCALA_MAPA
    ) + 1

    altura = int(
        TAMANHO_CELULA *
        ESCALA_MAPA
    ) + 1


    return pygame.Rect(
        x,
        y,
        largura,
        altura
    )


# ============================================================
# CONVERTER MOUSE PARA CÉLULA
# ============================================================

def mouse_para_celula(
    mouse_x,
    mouse_y,
    camera_x,
    camera_y
):

    # posição do mouse no mundo
    mundo_x = (
        mouse_x +
        camera_x
    )

    mundo_y = (
        mouse_y +
        camera_y
    )


    # volta para escala original
    original_x = (
        mundo_x /
        ESCALA_MAPA
    )

    original_y = (
        mundo_y /
        ESCALA_MAPA
    )


    cx = int(
        original_x //
        TAMANHO_CELULA
    )

    cy = int(
        original_y //
        TAMANHO_CELULA
    )


    return cx, cy


# ============================================================
# RETÂNGULOS DE COLISÃO DO JOGO
# ============================================================

def obter_colisoes():

    resultado = []


    for cx, cy in celulas_colisao:

        resultado.append(
            celula_para_rect(
                cx,
                cy
            )
        )


    return resultado


# ============================================================
# PLAYER
# ============================================================

class Player:

    def __init__(self):

        self.x = (
            450 *
            ESCALA_MAPA
        )

        self.y = (
            280 *
            ESCALA_MAPA
        )


        # Hitbox apenas dos pés
        self.largura = 26
        self.altura = 30


        self.rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.largura,
            self.altura
        )


        self.vel_x = 0
        self.vel_y = 0


        self.direcao = FRENTE


        self.frame = 0

        self.tempo_animacao = 0

        self.andando = False


    # --------------------------------------------------------
    # RECT
    # --------------------------------------------------------

    def atualizar_rect(self):

        self.rect.x = int(
            self.x
        )

        self.rect.y = int(
            self.y
        )


    # --------------------------------------------------------
    # ANIMAÇÃO
    # --------------------------------------------------------

    def atualizar_animacao(
        self,
        dt
    ):

        if not self.andando:

            self.frame = 0

            self.tempo_animacao = 0

            return


        self.tempo_animacao += dt


        if self.tempo_animacao >= 130:

            self.tempo_animacao = 0

            self.frame += 1


            if self.frame >= 2:

                self.frame = 0


    # --------------------------------------------------------
    # IMAGEM
    # --------------------------------------------------------

    def obter_imagem(self):

        if self.direcao == COSTAS:

            imagem = FRAME_0

        else:

            if self.frame == 1:

                imagem = FRAME_1

            else:

                imagem = FRAME_0


        if self.direcao == ESQUERDA:

            imagem = pygame.transform.flip(
                imagem,
                True,
                False
            )


        return imagem


    # --------------------------------------------------------
    # MOVIMENTO HORIZONTAL
    # --------------------------------------------------------

    def mover_horizontal(
        self,
        quantidade,
        colisoes
    ):

        self.x += quantidade

        self.atualizar_rect()


        for obstaculo in colisoes:

            if self.rect.colliderect(
                obstaculo
            ):

                if quantidade > 0:

                    self.rect.right = (
                        obstaculo.left
                    )

                elif quantidade < 0:

                    self.rect.left = (
                        obstaculo.right
                    )


                self.x = self.rect.x


    # --------------------------------------------------------
    # MOVIMENTO VERTICAL
    # --------------------------------------------------------

    def mover_vertical(
        self,
        quantidade,
        colisoes
    ):

        self.y += quantidade

        self.atualizar_rect()


        for obstaculo in colisoes:

            if self.rect.colliderect(
                obstaculo
            ):

                if quantidade > 0:

                    self.rect.bottom = (
                        obstaculo.top
                    )

                elif quantidade < 0:

                    self.rect.top = (
                        obstaculo.bottom
                    )


                self.y = self.rect.y


    # --------------------------------------------------------
    # MOVIMENTO COM COLISÃO
    # --------------------------------------------------------

    def mover_com_colisao(
        self,
        dx,
        dy,
        colisoes
    ):

        distancia = math.sqrt(
            dx * dx +
            dy * dy
        )


        passos = max(
            1,
            math.ceil(
                distancia / 1.5
            )
        )


        passo_x = (
            dx /
            passos
        )

        passo_y = (
            dy /
            passos
        )


        for _ in range(passos):

            if passo_x != 0:

                self.mover_horizontal(
                    passo_x,
                    colisoes
                )


            if passo_y != 0:

                self.mover_vertical(
                    passo_y,
                    colisoes
                )


    # --------------------------------------------------------
    # LIMITAR AO MAPA
    # --------------------------------------------------------

    def limitar_ao_mapa(self):

        if self.rect.left < 0:

            self.rect.left = 0

            self.x = self.rect.x


        if self.rect.top < 0:

            self.rect.top = 0

            self.y = self.rect.y


        if self.rect.right > MAPA_LARGURA:

            self.rect.right = (
                MAPA_LARGURA
            )

            self.x = self.rect.x


        if self.rect.bottom > MAPA_ALTURA:

            self.rect.bottom = (
                MAPA_ALTURA
            )

            self.y = self.rect.y


    # --------------------------------------------------------
    # ATUALIZAR
    # --------------------------------------------------------

    def atualizar(
        self,
        teclas,
        dt,
        colisoes
    ):

        self.vel_x = 0
        self.vel_y = 0


        # A
        if teclas[pygame.K_a]:

            self.vel_x = -VELOCIDADE

            self.direcao = ESQUERDA


        # D
        if teclas[pygame.K_d]:

            self.vel_x = VELOCIDADE

            self.direcao = DIREITA


        # W
        if teclas[pygame.K_w]:

            self.vel_y = -VELOCIDADE

            self.direcao = COSTAS


        # S
        if teclas[pygame.K_s]:

            self.vel_y = VELOCIDADE

            self.direcao = FRENTE


        # Diagonal
        if (
            self.vel_x != 0
            and
            self.vel_y != 0
        ):

            fator = 0.7071

            self.vel_x *= fator

            self.vel_y *= fator


        self.andando = (
            self.vel_x != 0
            or
            self.vel_y != 0
        )


        if self.andando:

            self.mover_com_colisao(
                self.vel_x,
                self.vel_y,
                colisoes
            )


        self.atualizar_rect()

        self.limitar_ao_mapa()

        self.atualizar_animacao(
            dt
        )


    # --------------------------------------------------------
    # DESENHAR
    # --------------------------------------------------------

    def desenhar(
        self,
        tela,
        camera_x,
        camera_y
    ):

        imagem = self.obter_imagem()


        pos_x = (
            self.rect.centerx
            -
            camera_x
            -
            imagem.get_width() // 2
        )


        pos_y = (
            self.rect.bottom
            -
            camera_y
            -
            imagem.get_height()
        )


        tela.blit(
            imagem,
            (
                pos_x,
                pos_y
            )
        )


# ============================================================
# PLAYER
# ============================================================

player = Player()


# ============================================================
# CÂMERA
# ============================================================

camera_x = 0
camera_y = 0

MARGEM_CAMERA_X = 220
MARGEM_CAMERA_Y = 150


def atualizar_camera():

    global camera_x
    global camera_y


    limite_esquerdo = (
        camera_x +
        MARGEM_CAMERA_X
    )

    limite_direito = (
        camera_x +
        LARGURA -
        MARGEM_CAMERA_X
    )

    limite_superior = (
        camera_y +
        MARGEM_CAMERA_Y
    )

    limite_inferior = (
        camera_y +
        ALTURA -
        MARGEM_CAMERA_Y
    )


    if player.rect.centerx < limite_esquerdo:

        camera_x = (
            player.rect.centerx -
            MARGEM_CAMERA_X
        )


    elif player.rect.centerx > limite_direito:

        camera_x = (
            player.rect.centerx -
            (
                LARGURA -
                MARGEM_CAMERA_X
            )
        )


    if player.rect.centery < limite_superior:

        camera_y = (
            player.rect.centery -
            MARGEM_CAMERA_Y
        )


    elif player.rect.centery > limite_inferior:

        camera_y = (
            player.rect.centery -
            (
                ALTURA -
                MARGEM_CAMERA_Y
            )
        )


    if camera_x < 0:

        camera_x = 0


    if camera_y < 0:

        camera_y = 0


    max_camera_x = max(
        0,
        MAPA_LARGURA -
        LARGURA
    )

    max_camera_y = max(
        0,
        MAPA_ALTURA -
        ALTURA
    )


    if camera_x > max_camera_x:

        camera_x = max_camera_x


    if camera_y > max_camera_y:

        camera_y = max_camera_y


# ============================================================
# EDITOR DE COLISÃO
# ============================================================

editor = False

pintando = False

apagando = False


# Câmera própria do editor
editor_camera_x = 0
editor_camera_y = 0


def desenhar_editor():

    global editor_camera_x
    global editor_camera_y


    # --------------------------------------------------------
    # FUNDO
    # --------------------------------------------------------

    TELA.fill(
        (10, 10, 12)
    )


    # --------------------------------------------------------
    # MAPA
    # --------------------------------------------------------

    TELA.blit(
        MAPA,
        (
            -editor_camera_x,
            -editor_camera_y
        )
    )


    # --------------------------------------------------------
    # COLISÕES
    # --------------------------------------------------------

    camada = pygame.Surface(
        (
            LARGURA,
            ALTURA
        ),
        pygame.SRCALPHA
    )


    tamanho_tela = int(
        TAMANHO_CELULA *
        ESCALA_MAPA
    )


    for cx, cy in celulas_colisao:

        rect = celula_para_rect(
            cx,
            cy
        )


        rect.x -= editor_camera_x
        rect.y -= editor_camera_y


        pygame.draw.rect(
            camada,
            (255, 40, 40, 100),
            rect
        )


        pygame.draw.rect(
            camada,
            (255, 80, 80, 180),
            rect,
            1
        )


    TELA.blit(
        camada,
        (0, 0)
    )


    # --------------------------------------------------------
    # GRADE LEVE
    # --------------------------------------------------------

    # Mostra apenas quando o mouse está sobre o mapa

    mouse_x, mouse_y = pygame.mouse.get_pos()


    if (
        0 <= mouse_x < LARGURA
        and
        0 <= mouse_y < ALTURA
    ):

        cx, cy = mouse_para_celula(
            mouse_x,
            mouse_y,
            editor_camera_x,
            editor_camera_y
        )


        if (
            cx >= 0
            and
            cy >= 0
        ):

            destaque = celula_para_rect(
                cx,
                cy
            )


            destaque.x -= editor_camera_x
            destaque.y -= editor_camera_y


            pygame.draw.rect(
                TELA,
                (255, 255, 255),
                destaque,
                2
            )


    # --------------------------------------------------------
    # PAINEL DE INSTRUÇÕES
    # --------------------------------------------------------

    fonte = pygame.font.Font(
        None,
        24
    )

    fonte_pequena = pygame.font.Font(
        None,
        20
    )


    painel = pygame.Surface(
        (
            LARGURA,
            90
        ),
        pygame.SRCALPHA
    )


    painel.fill(
        (0, 0, 0, 210)
    )


    TELA.blit(
        painel,
        (0, 0)
    )


    texto1 = fonte.render(
        "EDITOR DE COLISÃO",
        True,
        (255, 255, 255)
    )


    texto2 = fonte_pequena.render(
        "Mouse esquerdo: criar parede   |   Mouse direito: apagar",
        True,
        (255, 255, 255)
    )


    texto3 = fonte_pequena.render(
        "ENTER: salvar   |   ESC: sair   |   Setas: mover mapa",
        True,
        (255, 255, 255)
    )


    TELA.blit(
        texto1,
        (20, 12)
    )


    TELA.blit(
        texto2,
        (20, 42)
    )


    TELA.blit(
        texto3,
        (20, 65)
    )


    pygame.display.flip()


# ============================================================
# PINTAR COLISÃO
# ============================================================

def pintar_celula(
    mouse_x,
    mouse_y
):

    cx, cy = mouse_para_celula(
        mouse_x,
        mouse_y,
        editor_camera_x,
        editor_camera_y
    )


    # Não deixa pintar fora do mapa

    limite_x = (
        MAPA_ORIGINAL_LARGURA //
        TAMANHO_CELULA
    )

    limite_y = (
        MAPA_ORIGINAL_ALTURA //
        TAMANHO_CELULA
    )


    if (
        cx < 0
        or
        cy < 0
        or
        cx > limite_x
        or
        cy > limite_y
    ):

        return


    if pintando:

        celulas_colisao.add(
            (cx, cy)
        )


    if apagando:

        celulas_colisao.discard(
            (cx, cy)
        )


# ============================================================
# CARREGAR COLISÕES
# ============================================================

carregar_colisoes()


# ============================================================
# ESTADO
# ============================================================

rodando = True


# ============================================================
# LOOP PRINCIPAL
# ============================================================

while rodando:

    dt = RELOGIO.tick(FPS)


    # ========================================================
    # EDITOR
    # ========================================================

    if editor:

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:

                rodando = False


            # ------------------------------------------------
            # TECLAS
            # ------------------------------------------------

            if evento.type == pygame.KEYDOWN:

                # Sair do editor

                if evento.key == pygame.K_ESCAPE:

                    editor = False

                    pintar = False
                    apagando = False


                # Salvar

                elif evento.key == pygame.K_RETURN:

                    salvar_colisoes()


                # Setas movem o mapa

                elif evento.key == pygame.K_LEFT:

                    editor_camera_x -= 100


                elif evento.key == pygame.K_RIGHT:

                    editor_camera_x += 100


                elif evento.key == pygame.K_UP:

                    editor_camera_y -= 100


                elif evento.key == pygame.K_DOWN:

                    editor_camera_y += 100


            # ------------------------------------------------
            # MOUSE
            # ------------------------------------------------

            if evento.type == pygame.MOUSEBUTTONDOWN:

                if evento.button == 1:

                    pintando = True

                    apagando = False


                elif evento.button == 3:

                    apagando = True

                    pintando = False


            if evento.type == pygame.MOUSEBUTTONUP:

                if evento.button == 1:

                    pintando = False


                elif evento.button == 3:

                    apagando = False


            if evento.type == pygame.MOUSEMOTION:

                if pintando or apagando:

                    mouse_x, mouse_y = (
                        pygame.mouse.get_pos()
                    )


                    pintar_celula(
                        mouse_x,
                        mouse_y
                    )


        # ----------------------------------------------------
        # LIMITES DA CÂMERA DO EDITOR
        # ----------------------------------------------------

        max_editor_x = max(
            0,
            MAPA_LARGURA -
            LARGURA
        )


        max_editor_y = max(
            0,
            MAPA_ALTURA -
            ALTURA
        )


        editor_camera_x = max(
            0,
            min(
                editor_camera_x,
                max_editor_x
            )
        )


        editor_camera_y = max(
            0,
            min(
                editor_camera_y,
                max_editor_y
            )
        )


        desenhar_editor()


        continue


    # ========================================================
    # JOGO NORMAL
    # ========================================================

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:

            rodando = False


        if evento.type == pygame.KEYDOWN:

            # P abre o editor

            if evento.key == pygame.K_p:

                editor = True

                editor_camera_x = camera_x
                editor_camera_y = camera_y


    # ========================================================
    # TECLAS
    # ========================================================

    teclas = pygame.key.get_pressed()


    # ========================================================
    # COLISÕES
    # ========================================================

    colisoes = obter_colisoes()


    # ========================================================
    # PLAYER
    # ========================================================

    player.atualizar(
        teclas,
        dt,
        colisoes
    )


    # ========================================================
    # CÂMERA
    # ========================================================

    atualizar_camera()


    # ========================================================
    # DESENHAR JOGO
    # ========================================================

    TELA.fill(
        (15, 15, 18)
    )


    TELA.blit(
        MAPA,
        (
            -camera_x,
            -camera_y
        )
    )


    player.desenhar(
        TELA,
        camera_x,
        camera_y
    )


    pygame.display.flip()


# ============================================================
# FINALIZAR
# ============================================================

pygame.quit()

sys.exit()