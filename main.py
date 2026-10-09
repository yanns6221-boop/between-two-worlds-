
import pygame
import os
import sys
import json

pygame.init()

LARGURA = 960
ALTURA = 640
FPS = 60
VELOCIDADE = 1.8
VELOCIDADE_CORRIDA = 4.5
ESCALA_MAPA = 1.80
TAMANHO_CELULA = 12
LARGURA_PERSONAGEM = 48
ALTURA_PERSONAGEM = 72
HITBOX_LARGURA = 24
HITBOX_ALTURA = 27
INTERVALO_ANIMACAO = 120

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Between Two Worlds")
RELOGIO = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ARQUIVO_COLISAO = os.path.join(BASE_DIR, "collision_map.json")
ARQUIVO_PORTAS = os.path.join(BASE_DIR, "doors.json")

BRANCO = (240, 240, 240)
VERMELHO = (255, 70, 70)
VERDE = (90, 230, 120)
AMARELO = (255, 220, 70)
MARROM = (115, 65, 35)
PRETO = (0, 0, 0)

def sair_com_erro(mensagem):
    print(mensagem)
    pygame.quit()
    sys.exit()

def carregar_imagem(caminho, alpha=True):
    try:
        imagem = pygame.image.load(caminho)

        if alpha:
            return imagem.convert_alpha()

        return imagem.convert()

    except Exception as erro:
        print("Erro ao carregar imagem:", caminho)
        print(erro)
        return None

def encontrar_mapa():
    if not os.path.isdir(ASSETS_DIR):
        return None

    candidatos = []
    extensoes = [".png", ".jpg", ".jpeg", ".bmp", ".webp"]
    ignorar = [
        "player.png",
        "player_back.png",
        "player_sheet.png"
    ]

    for nome in os.listdir(ASSETS_DIR):
        caminho = os.path.join(ASSETS_DIR, nome)

        if not os.path.isfile(caminho):
            continue

        if os.path.splitext(nome)[1].lower() not in extensoes:
            continue

        if nome.lower() in ignorar:
            continue

        try:
            imagem = pygame.image.load(caminho)
            area = imagem.get_width() * imagem.get_height()

            if area > 200000:
                candidatos.append((area, caminho))

        except Exception:
            pass

    if not candidatos:
        return None

    candidatos.sort(reverse=True)
    return candidatos[0][1]

CAMINHO_MAPA = encontrar_mapa()

if CAMINHO_MAPA is None:
    sair_com_erro(
        "ERRO: não encontrei uma imagem de mapa dentro da pasta assets."
    )

MAPA_ORIGINAL = carregar_imagem(CAMINHO_MAPA, False)

if MAPA_ORIGINAL is None:
    sair_com_erro("ERRO: não consegui abrir a imagem do mapa.")

MAPA_LARGURA_ORIGINAL = MAPA_ORIGINAL.get_width()
MAPA_ALTURA_ORIGINAL = MAPA_ORIGINAL.get_height()

MAPA_LARGURA = int(MAPA_LARGURA_ORIGINAL * ESCALA_MAPA)
MAPA_ALTURA = int(MAPA_ALTURA_ORIGINAL * ESCALA_MAPA)

MAPA = pygame.transform.scale(
    MAPA_ORIGINAL,
    (MAPA_LARGURA, MAPA_ALTURA)
)

print("Mapa utilizado:", CAMINHO_MAPA)
print("Tamanho do mapa:", MAPA_LARGURA, "x", MAPA_ALTURA)

def carregar_sheet(nome):
    caminho = os.path.join(ASSETS_DIR, nome)
    imagem = carregar_imagem(caminho, True)

    if imagem is None:
        sair_com_erro(
            "ERRO: não encontrei " + nome + " dentro da pasta assets."
        )

    return imagem

PLAYER_SHEET = carregar_sheet("player.png")
PLAYER_BACK_SHEET = carregar_sheet("player_back.png")

def cortar_frames_horizontais(
    sheet,
    quantidade,
    largura_final=48,
    altura_final=72
):
    frames = []
    largura = sheet.get_width()
    altura = sheet.get_height()
    largura_frame = largura // quantidade

    for i in range(quantidade):
        recorte = pygame.Surface(
            (largura_frame, altura),
            pygame.SRCALPHA
        )

        recorte.blit(
            sheet,
            (0, 0),
            (i * largura_frame, 0, largura_frame, altura)
        )

        frames.append(
            pygame.transform.scale(
                recorte,
                (largura_final, altura_final)
            )
        )

    return frames

def separar_costas(sheet):
    largura = sheet.get_width()
    altura = sheet.get_height()
    colunas = []

    for x in range(largura):
        tem_pixel = False

        for y in range(altura):
            if sheet.get_at((x, y)).a > 10:
                tem_pixel = True
                break

        colunas.append(tem_pixel)

    grupos = []
    inicio = None

    for x in range(largura):
        if colunas[x]:
            if inicio is None:
                inicio = x

        elif inicio is not None:
            fim = x - 1

            if fim - inicio >= 3:
                grupos.append((inicio, fim))

            inicio = None

    if inicio is not None:
        grupos.append((inicio, largura - 1))

    if len(grupos) < 4:
        print("Aviso: não identifiquei quatro sprites de costas.")
        print("Usando os sprites da frente como alternativa.")

        frente = cortar_frames_horizontais(PLAYER_SHEET, 2)
        return [frente[0], frente[1], frente[0], frente[1]]

    frames = []

    for inicio, fim in grupos[:4]:
        topo = altura
        fundo = 0

        for x in range(inicio, fim + 1):
            for y in range(altura):
                if sheet.get_at((x, y)).a > 10:
                    topo = min(topo, y)
                    fundo = max(fundo, y)

        largura_recorte = fim - inicio + 1
        altura_recorte = max(1, fundo - topo + 1)

        recorte = pygame.Surface(
            (largura_recorte, altura_recorte),
            pygame.SRCALPHA
        )

        recorte.blit(
            sheet,
            (0, 0),
            (inicio, topo, largura_recorte, altura_recorte)
        )

        escala = min(
            44 / largura_recorte,
            68 / altura_recorte
        )

        nova_largura = max(1, int(largura_recorte * escala))
        nova_altura = max(1, int(altura_recorte * escala))

        recorte = pygame.transform.scale(
            recorte,
            (nova_largura, nova_altura)
        )

        frame = pygame.Surface((48, 72), pygame.SRCALPHA)

        frame.blit(
            recorte,
            (
                (48 - nova_largura) // 2,
                72 - nova_altura
            )
        )

        frames.append(frame)

    print("Sprites de costas identificados:", len(frames))
    return frames

FRAMES_FRENTE = cortar_frames_horizontais(PLAYER_SHEET, 2)
FRAMES_COSTAS = separar_costas(PLAYER_BACK_SHEET)

FRENTE = 0
COSTAS = 1
ESQUERDA = 2
DIREITA = 3

celulas_colisao = set()
portas = []

def tamanho_celula_mundo():
    return TAMANHO_CELULA * ESCALA_MAPA

def celula_valida(cx, cy):
    tamanho = tamanho_celula_mundo()

    return (
        cx >= 0
        and cy >= 0
        and cx * tamanho < MAPA_LARGURA
        and cy * tamanho < MAPA_ALTURA
    )

def celula_para_rect(cx, cy):
    tamanho = tamanho_celula_mundo()

    return pygame.Rect(
        int(cx * tamanho),
        int(cy * tamanho),
        int(tamanho) + 1,
        int(tamanho) + 1
    )

def mouse_para_celula(mx, my, camera_x, camera_y):
    mundo_x = mx + camera_x
    mundo_y = my + camera_y
    tamanho = tamanho_celula_mundo()

    return (
        int(mundo_x // tamanho),
        int(mundo_y // tamanho)
    )

def carregar_colisoes():
    global celulas_colisao
    celulas_colisao = set()

    if not os.path.exists(ARQUIVO_COLISAO):
        print("Nenhum mapa de colisão encontrado.")
        return

    try:
        with open(ARQUIVO_COLISAO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            if isinstance(item, list) and len(item) == 2:
                celulas_colisao.add((int(item[0]), int(item[1])))

        print("Colisões carregadas:", len(celulas_colisao))

    except Exception as erro:
        print("Erro ao carregar colisões:", erro)

def salvar_colisoes():
    dados = [[x, y] for x, y in sorted(celulas_colisao)]

    try:
        with open(ARQUIVO_COLISAO, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=4)

        print("Colisões salvas:", len(dados))

    except Exception as erro:
        print("Erro ao salvar colisões:", erro)

def carregar_portas():
    global portas
    portas = []

    if not os.path.exists(ARQUIVO_PORTAS):
        print("Nenhum arquivo de portas encontrado.")
        return

    try:
        with open(ARQUIVO_PORTAS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            if not isinstance(item, dict):
                continue

            if "x" not in item or "y" not in item:
                continue

            cx = int(item["x"])
            cy = int(item["y"])

            if not celula_valida(cx, cy):
                continue

            portas.append({
                "x": cx,
                "y": cy,
                "aberta": bool(item.get("aberta", False))
            })

        print("Portas carregadas:", len(portas))

    except Exception as erro:
        print("Erro ao carregar portas:", erro)

def salvar_portas():
    dados = []

    for porta in portas:
        dados.append({
            "x": porta["x"],
            "y": porta["y"],
            "aberta": porta["aberta"]
        })

    try:
        with open(ARQUIVO_PORTAS, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=4)

        print("Portas salvas:", len(portas))

    except Exception as erro:
        print("Erro ao salvar portas:", erro)

def porta_na_celula(cx, cy):
    for porta in portas:
        if porta["x"] == cx and porta["y"] == cy:
            return porta

    return None

def hitbox_porta(porta):
    return celula_para_rect(porta["x"], porta["y"])

def hitbox_player(x=None, y=None):
    if x is None:
        x = player_x

    if y is None:
        y = player_y

    return pygame.Rect(
        int(x),
        int(y),
        HITBOX_LARGURA,
        HITBOX_ALTURA
    )

def dentro_do_mapa(rect):
    return (
        rect.left >= 0
        and rect.top >= 0
        and rect.right <= MAPA_LARGURA
        and rect.bottom <= MAPA_ALTURA
    )

def colide_com_mapa(rect):
    if not dentro_do_mapa(rect):
        return True

    tamanho = tamanho_celula_mundo()

    cx_inicio = max(0, int(rect.left // tamanho))
    cy_inicio = max(0, int(rect.top // tamanho))
    cx_fim = int(rect.right // tamanho)
    cy_fim = int(rect.bottom // tamanho)

    for cx in range(cx_inicio, cx_fim + 1):
        for cy in range(cy_inicio, cy_fim + 1):
            if (cx, cy) not in celulas_colisao:
                continue

            obstaculo = celula_para_rect(cx, cy)

            if rect.colliderect(obstaculo):
                return True

    for porta in portas:
        if porta["aberta"]:
            continue

        if rect.colliderect(hitbox_porta(porta)):
            return True

    return False

def encontrar_posicao_inicial():
    passo = max(8, int(tamanho_celula_mundo()))

    centro_x = max(
        0,
        min(
            MAPA_LARGURA - HITBOX_LARGURA,
            MAPA_LARGURA // 2 - HITBOX_LARGURA // 2
        )
    )

    centro_y = max(
        0,
        min(
            MAPA_ALTURA - HITBOX_ALTURA,
            MAPA_ALTURA // 2 - HITBOX_ALTURA // 2
        )
    )

    max_raio = max(MAPA_LARGURA, MAPA_ALTURA) // passo + 2

    for raio in range(max_raio):
        candidatos = []

        if raio == 0:
            candidatos.append((centro_x, centro_y))
        else:
            deslocamento = raio * passo

            for offset in range(-deslocamento, deslocamento + 1, passo):
                candidatos.append(
                    (centro_x + offset, centro_y - deslocamento)
                )
                candidatos.append(
                    (centro_x + offset, centro_y + deslocamento)
                )
                candidatos.append(
                    (centro_x - deslocamento, centro_y + offset)
                )
                candidatos.append(
                    (centro_x + deslocamento, centro_y + offset)
                )

        for x, y in candidatos:
            x = max(0, min(MAPA_LARGURA - HITBOX_LARGURA, x))
            y = max(0, min(MAPA_ALTURA - HITBOX_ALTURA, y))

            teste = pygame.Rect(
                int(x),
                int(y),
                HITBOX_LARGURA,
                HITBOX_ALTURA
            )

            if not colide_com_mapa(teste):
                return x, y

    return 0, 0

carregar_colisoes()
carregar_portas()

player_x, player_y = encontrar_posicao_inicial()

print("Posição inicial:", int(player_x), int(player_y))

direcao = FRENTE
frame_atual = 0
tempo_animacao = 0
andando = False

modo_editor = False
modo_editor_portas = False

mensagem = ""
tempo_mensagem = 0

def mover_e_testar(dx, dy):
    global player_x, player_y

    if dx:
        teste = hitbox_player(player_x + dx, player_y)

        if not colide_com_mapa(teste):
            player_x += dx

    if dy:
        teste = hitbox_player(player_x, player_y + dy)

        if not colide_com_mapa(teste):
            player_y += dy

def atualizar_camera():
    camera_x = (
        player_x
        + HITBOX_LARGURA // 2
        - LARGURA // 2
    )

    camera_y = (
        player_y
        + HITBOX_ALTURA // 2
        - ALTURA // 2
    )

    camera_x = max(0, min(camera_x, MAPA_LARGURA - LARGURA))
    camera_y = max(0, min(camera_y, MAPA_ALTURA - ALTURA))

    return int(camera_x), int(camera_y)

def obter_porta_proxima():
    centro_x = player_x + HITBOX_LARGURA // 2
    centro_y = player_y + HITBOX_ALTURA // 2
    alcance = tamanho_celula_mundo() * 1.8

    melhor_porta = None
    menor_distancia = alcance * alcance

    for porta in portas:
        if porta["aberta"]:
            continue

        rect = hitbox_porta(porta)

        ponto_x = max(rect.left, min(centro_x, rect.right))
        ponto_y = max(rect.top, min(centro_y, rect.bottom))

        distancia_x = centro_x - ponto_x
        distancia_y = centro_y - ponto_y

        distancia = (
            distancia_x * distancia_x
            + distancia_y * distancia_y
        )

        if distancia <= menor_distancia:
            menor_distancia = distancia
            melhor_porta = porta

    return melhor_porta

def mostrar_mensagem(texto):
    global mensagem, tempo_mensagem

    mensagem = texto
    tempo_mensagem = 180
    print(texto)

def interagir():
    porta = obter_porta_proxima()

    if porta is not None:
        porta["aberta"] = True
        salvar_portas()
        mostrar_mensagem("Você abriu a porta.")
    else:
        mostrar_mensagem(
            "Você observa os arredores, mas não há nada para interagir aqui."
        )

def desenhar_portas(camera_x, camera_y):
    for porta in portas:
        rect = hitbox_porta(porta).move(-camera_x, -camera_y)

        if porta["aberta"]:
            pygame.draw.rect(TELA, VERDE, rect, 2)
        else:
            pygame.draw.rect(TELA, MARROM, rect)
            pygame.draw.rect(TELA, AMARELO, rect, 2)

            pygame.draw.circle(
                TELA,
                AMARELO,
                rect.center,
                2
            )

def desenhar_editor(camera_x, camera_y):
    for cx, cy in celulas_colisao:
        rect = celula_para_rect(cx, cy).move(-camera_x, -camera_y)

        if (
            rect.right >= 0
            and rect.left <= LARGURA
            and rect.bottom >= 0
            and rect.top <= ALTURA
        ):
            superficie = pygame.Surface(
                (rect.width, rect.height),
                pygame.SRCALPHA
            )

            superficie.fill((255, 45, 45, 100))
            TELA.blit(superficie, rect.topleft)
            pygame.draw.rect(TELA, VERMELHO, rect, 1)

    fonte = pygame.font.SysFont(None, 24)

    texto = fonte.render(
        "COLISOES: esquerdo marca | direito apaga | P/F2 salva",
        True,
        BRANCO
    )

    TELA.blit(texto, (12, 12))

def desenhar_editor_portas(camera_x, camera_y):
    fonte = pygame.font.SysFont(None, 24)

    texto = fonte.render(
        "PORTAS: esquerdo coloca | direito remove | F4/F6 salva",
        True,
        BRANCO
    )

    TELA.blit(texto, (12, 12))

    for porta in portas:
        rect = hitbox_porta(porta).move(-camera_x, -camera_y)
        cor = VERDE if porta["aberta"] else AMARELO
        pygame.draw.rect(TELA, cor, rect, 2)

def desenhar_mensagem():
    if tempo_mensagem <= 0 or not mensagem:
        return

    caixa = pygame.Rect(30, ALTURA - 65, LARGURA - 60, 42)

    pygame.draw.rect(TELA, (15, 15, 20), caixa)
    pygame.draw.rect(TELA, (180, 180, 180), caixa, 1)

    texto = fonte_mensagem.render(mensagem, True, BRANCO)
    TELA.blit(texto, (caixa.x + 12, caixa.y + 12))

fonte_mensagem = pygame.font.SysFont(None, 25)

executando = True

while executando:
    dt = RELOGIO.tick(FPS)

    if tempo_mensagem > 0:
        tempo_mensagem -= 1

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                if modo_editor:
                    salvar_colisoes()
                    modo_editor = False
                elif modo_editor_portas:
                    salvar_portas()
                    modo_editor_portas = False
                else:
                    executando = False

            elif evento.key in (pygame.K_p, pygame.K_F2):
                if modo_editor:
                    salvar_colisoes()
                    modo_editor = False
                    print("Editor de colisões fechado.")
                elif not modo_editor_portas:
                    modo_editor = True
                    print("Editor de colisões aberto.")

            elif evento.key in (pygame.K_F4, pygame.K_F6):
                if modo_editor_portas:
                    salvar_portas()
                    modo_editor_portas = False
                    print("Editor de portas fechado.")
                elif not modo_editor:
                    modo_editor_portas = True
                    print("Editor de portas aberto.")

            elif evento.key == pygame.K_e:
                if not modo_editor and not modo_editor_portas:
                    interagir()

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if modo_editor or modo_editor_portas:
                mx, my = pygame.mouse.get_pos()
                camera_x, camera_y = atualizar_camera()

                cx, cy = mouse_para_celula(
                    mx,
                    my,
                    camera_x,
                    camera_y
                )

                if not celula_valida(cx, cy):
                    continue

                if modo_editor:
                    if evento.button == 1:
                        celulas_colisao.add((cx, cy))
                    elif evento.button == 3:
                        celulas_colisao.discard((cx, cy))

                elif modo_editor_portas:
                    if evento.button == 1:
                        if porta_na_celula(cx, cy) is None:
                            portas.append({
                                "x": cx,
                                "y": cy,
                                "aberta": False
                            })

                    elif evento.button == 3:
                        porta = porta_na_celula(cx, cy)

                        if porta is not None:
                            portas.remove(porta)

    teclas = pygame.key.get_pressed()

    dx = 0
    dy = 0
    andando = False

    if not modo_editor and not modo_editor_portas:
        velocidade_atual = VELOCIDADE

        if teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]:
            velocidade_atual = VELOCIDADE_CORRIDA

        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            dx -= velocidade_atual
            direcao = ESQUERDA

        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            dx += velocidade_atual
            direcao = DIREITA

        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            dy -= velocidade_atual
            direcao = COSTAS

        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            dy += velocidade_atual
            direcao = FRENTE

        andando = dx != 0 or dy != 0

        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071

        mover_e_testar(dx, dy)

    if andando:
        tempo_animacao += dt

        while tempo_animacao >= INTERVALO_ANIMACAO:
            frame_atual += 1
            tempo_animacao -= INTERVALO_ANIMACAO

    else:
        tempo_animacao = 0

    camera_x, camera_y = atualizar_camera()

    TELA.fill(PRETO)
    TELA.blit(MAPA, (-camera_x, -camera_y))

    desenhar_portas(camera_x, camera_y)

    if direcao == COSTAS:
        frames = FRAMES_COSTAS
    else:
        frames = FRAMES_FRENTE

    indice = frame_atual % len(frames) if andando else 0
    imagem_player = frames[indice]

    if direcao == ESQUERDA:
        imagem_player = pygame.transform.flip(
            imagem_player,
            True,
            False
        )

    desenho_x = int(
        player_x
        - camera_x
        - (LARGURA_PERSONAGEM - HITBOX_LARGURA) // 2
    )

    desenho_y = int(
        player_y
        - camera_y
        - (ALTURA_PERSONAGEM - HITBOX_ALTURA)
    )

    TELA.blit(imagem_player, (desenho_x, desenho_y))

    if modo_editor:
        desenhar_editor(camera_x, camera_y)

    if modo_editor_portas:
        desenhar_editor_portas(camera_x, camera_y)

    desenhar_mensagem()

    pygame.display.flip()

salvar_colisoes()
salvar_portas()

pygame.quit()
sys.exit()