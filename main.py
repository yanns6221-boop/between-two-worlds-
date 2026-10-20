import pygame
import os
import sys
import json
import math

pygame.init()

LARGURA = 960
ALTURA = 640
FPS = 60

VELOCIDADE = 2.8
VELOCIDADE_CORRIDA = 4.5

ESCALA_MAPA = 3.0
TAMANHO_CELULA = 12
CELULA_MUNDO = int(TAMANHO_CELULA * ESCALA_MAPA)

LARGURA_PERSONAGEM = 90
ALTURA_PERSONAGEM = 110
HITBOX_LARGURA = 22
HITBOX_ALTURA = 25
INTERVALO_ANIMACAO = 110

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_ASSETS = os.path.join(PASTA, "assets")

ARQUIVO_COLISOES = os.path.join(PASTA, "collision_map.json")
ARQUIVO_PORTAS = os.path.join(PASTA, "doors.json")
ARQUIVO_BAUS = os.path.join(PASTA, "chests.json")
ARQUIVO_INVENTARIO = os.path.join(PASTA, "inventory.json")

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Between Two Worlds")
relogio = pygame.time.Clock()

fonte = pygame.font.SysFont("arial", 20)
fonte_pequena = pygame.font.SysFont("arial", 15)
fonte_titulo = pygame.font.SysFont("arial", 28, bold=True)

BRANCO = (240, 235, 220)
PRETO = (15, 13, 17)
CINZA = (65, 59, 65)
CINZA_CLARO = (120, 110, 112)
DOURADO = (205, 165, 75)
MARROM = (91, 52, 29)
MARROM_CLARO = (135, 83, 43)
VERDE = (105, 170, 105)
VERMELHO = (190, 70, 70)


def carregar_json(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError, TypeError):
        print("Não foi possível ler:", caminho)
        return padrao


def salvar_json(caminho, dados):
    try:
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=4, ensure_ascii=False)
    except OSError as erro:
        print("Erro ao salvar:", erro)



def encontrar_mapa():
    if not os.path.isdir(PASTA_ASSETS):
        return None

    extensoes = (".png", ".jpg", ".jpeg", ".bmp")
    candidatos = []

    for nome in os.listdir(PASTA_ASSETS):
        caminho = os.path.join(PASTA_ASSETS, nome)

        if not os.path.isfile(caminho):
            continue

        if nome.lower() in (
            "player.png",
            "player_back.png",
            "player_sheet.png"
        ):
            continue

        if nome.lower().startswith((
            "front_", "back_", "left_", "right_"
        )):
            continue

        if not nome.lower().endswith(extensoes):
            continue

        try:
            imagem = pygame.image.load(caminho)
            largura, altura = imagem.get_size()

            if largura * altura > 200000:
                candidatos.append((largura * altura, caminho))
        except pygame.error:
            pass

    if not candidatos:
        return None

    candidatos.sort(reverse=True)
    return candidatos[0][1]


caminho_mapa = encontrar_mapa()

if caminho_mapa is None:
    print("ERRO: não encontrei o mapa dentro da pasta assets.")
    print("Coloque o arquivo do mapa dentro de assets e tente novamente.")
    pygame.quit()
    sys.exit()

mapa_original = pygame.image.load(caminho_mapa).convert()
mapa = pygame.transform.scale(
    mapa_original,
    (
        int(mapa_original.get_width() * ESCALA_MAPA),
        int(mapa_original.get_height() * ESCALA_MAPA)
    )
)

MAPA_LARGURA = mapa.get_width()
MAPA_ALTURA = mapa.get_height()

print("Mapa carregado:", caminho_mapa)
print("Tamanho do mapa:", MAPA_LARGURA, "x", MAPA_ALTURA)



def carregar_imagem(caminho):
    if not os.path.exists(caminho):
        return None

    try:
        imagem = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.scale(
            imagem,
            (LARGURA_PERSONAGEM, ALTURA_PERSONAGEM)
        )
    except pygame.error:
        return None


def carregar_frames(prefixo, quantidade=6):
    frames = []

    for numero in range(1, quantidade + 1):
        nome = "{}_{}.png".format(prefixo, numero)
        caminho = os.path.join(PASTA_ASSETS, nome)
        imagem = carregar_imagem(caminho)

        if imagem is not None:
            frames.append(imagem)

    return frames


frames = {
    "frente": carregar_frames("front_walk"),
    "costas": carregar_frames("back_walk"),
    "esquerda": carregar_frames("left_walk"),
    "direita": carregar_frames("right_walk")
}

frames_corrida = {
    "frente": carregar_frames("front_run"),
    "costas": carregar_frames("back_run"),
    "esquerda": carregar_frames("left_run"),
    "direita": carregar_frames("right_run")
}

sprite_frente = carregar_imagem(
    os.path.join(PASTA_ASSETS, "player.png")
)
sprite_costas = carregar_imagem(
    os.path.join(PASTA_ASSETS, "player_back.png")
)

if not frames["frente"] and sprite_frente is not None:
    frames["frente"] = [sprite_frente]

if not frames["costas"] and sprite_costas is not None:
    frames["costas"] = [sprite_costas]

for direcao in ("esquerda", "direita", "frente", "costas"):
    if not frames[direcao]:
        if sprite_frente is not None:
            frames[direcao] = [sprite_frente]
        else:
            imagem_temporaria = pygame.Surface(
                (LARGURA_PERSONAGEM, ALTURA_PERSONAGEM),
                pygame.SRCALPHA
            )
            pygame.draw.rect(
                imagem_temporaria,
                (130, 35, 35),
                (25, 10, 40, 90)
            )
            frames[direcao] = [imagem_temporaria]

    if not frames_corrida[direcao]:
        frames_corrida[direcao] = frames[direcao][:]

print("Sprites de caminhada carregados.")
print("Sprites de corrida carregados.")




def carregar_colisoes():
    dados = carregar_json(ARQUIVO_COLISOES, [])
    resultado = set()

    if isinstance(dados, dict):
        dados = dados.get("colisoes", dados.get("cells", []))

    if not isinstance(dados, list):
        return resultado

    for item in dados:
        try:
            if isinstance(item, dict):
                if "cx" in item and "cy" in item:
                    cx = int(item["cx"])
                    cy = int(item["cy"])
                else:
                    cx = int(item["x"])
                    cy = int(item["y"])

            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                cx = int(item[0])
                cy = int(item[1])

            elif isinstance(item, str) and "," in item:
                partes = item.split(",")
                cx = int(partes[0])
                cy = int(partes[1])

            else:
                continue

            resultado.add((cx, cy))
        except (ValueError, TypeError, KeyError):
            continue

    return resultado


colisoes = carregar_colisoes()
print("Colisões carregadas:", len(colisoes))


def salvar_colisoes():
    dados = []

    for cx, cy in sorted(colisoes):
        dados.append([cx, cy])

    salvar_json(ARQUIVO_COLISOES, dados)
    print("Colisões salvas:", len(colisoes))




def carregar_portas():
    dados = carregar_json(ARQUIVO_PORTAS, [])

    if isinstance(dados, dict):
        dados = dados.get("portas", [])

    if not isinstance(dados, list):
        return []

    resultado = []

    for item in dados:
        if not isinstance(item, dict):
            continue

        try:
            porta = {
                "x": int(item["x"]),
                "y": int(item["y"]),
                "aberta": bool(item.get("aberta", False))
            }
            resultado.append(porta)
        except (ValueError, TypeError, KeyError):
            continue

    return resultado


portas = carregar_portas()


def salvar_portas():
    salvar_json(ARQUIVO_PORTAS, portas)
    print("Portas salvas:", len(portas))


def retangulo_porta(porta):
    return pygame.Rect(
        porta["x"] * CELULA_MUNDO,
        porta["y"] * CELULA_MUNDO,
        CELULA_MUNDO * 2,
        CELULA_MUNDO * 2
    )




ITENS_INICIAIS_BAU = [
    "Poção antiga",
    "Chave enferrujada",
    "Moeda de prata"
]


def carregar_baus():
    dados = carregar_json(ARQUIVO_BAUS, [])

    if isinstance(dados, dict):
        dados = dados.get("baus", [])

    if not isinstance(dados, list):
        return []

    resultado = []

    for item in dados:
        if not isinstance(item, dict):
            continue

        try:
            itens = item.get("itens", [])

            if not isinstance(itens, list):
                itens = []

            bau = {
                "x": int(item["x"]),
                "y": int(item["y"]),
                "aberto": bool(item.get("aberto", False)),
                "itens": itens
            }

            resultado.append(bau)

        except (ValueError, TypeError, KeyError):
            continue

    return resultado


baus = carregar_baus()


def salvar_baus():
    salvar_json(ARQUIVO_BAUS, baus)
    print("Baús salvos:", len(baus))


def retangulo_bau(bau):
    return pygame.Rect(
        bau["x"] * CELULA_MUNDO,
        bau["y"] * CELULA_MUNDO,
        CELULA_MUNDO,
        CELULA_MUNDO
    )



def carregar_inventario():
    dados = carregar_json(ARQUIVO_INVENTARIO, [])

    if not isinstance(dados, list):
        return []

    inventario = []

    for item in dados:
        if isinstance(item, str):
            inventario.append({
                "nome": item,
                "quantidade": 1
            })

        elif isinstance(item, dict):
            nome = item.get("nome", "")
            quantidade = item.get("quantidade", 1)

            if nome:
                try:
                    quantidade = max(1, int(quantidade))
                except (ValueError, TypeError):
                    quantidade = 1

                inventario.append({
                    "nome": str(nome),
                    "quantidade": quantidade
                })

    return inventario


inventario = carregar_inventario()


def salvar_inventario():
    salvar_json(ARQUIVO_INVENTARIO, inventario)


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


def retirar_item_bau(bau, indice):
    if indice < 0 or indice >= len(bau["itens"]):
        return

    item = bau["itens"].pop(indice)

    if isinstance(item, dict):
        nome = item.get("nome", "Item desconhecido")
        quantidade = max(1, int(item.get("quantidade", 1)))
    else:
        nome = str(item)
        quantidade = 1

    for numero in range(quantidade):
        adicionar_item(nome)

    salvar_baus()
    print("Item obtido:", nome)



player_x = 1200
player_y = 900

direcao = "frente"
indice_frame = 0
tempo_animacao = 0
personagem_movendo = False
personagem_correndo = False

camera_x = 0
camera_y = 0


def retangulo_personagem(x=None, y=None):
    if x is None:
        x = player_x

    if y is None:
        y = player_y

    return pygame.Rect(
        int(x + (LARGURA_PERSONAGEM - HITBOX_LARGURA) / 2),
        int(y + ALTURA_PERSONAGEM - HITBOX_ALTURA - 8),
        HITBOX_LARGURA,
        HITBOX_ALTURA
    )


def retangulo_no_mundo(retangulo):
    return retangulo.move(camera_x, camera_y)


def ha_colisao(retangulo):
    if retangulo.left < 0 or retangulo.top < 0:
        return True

    if retangulo.right > MAPA_LARGURA:
        return True

    if retangulo.bottom > MAPA_ALTURA:
        return True

    cx_inicio = retangulo.left // CELULA_MUNDO
    cy_inicio = retangulo.top // CELULA_MUNDO
    cx_fim = (retangulo.right - 1) // CELULA_MUNDO
    cy_fim = (retangulo.bottom - 1) // CELULA_MUNDO

    for cx in range(cx_inicio, cx_fim + 1):
        for cy in range(cy_inicio, cy_fim + 1):
            if (cx, cy) in colisoes:
                celula = pygame.Rect(
                    cx * CELULA_MUNDO,
                    cy * CELULA_MUNDO,
                    CELULA_MUNDO,
                    CELULA_MUNDO
                )

                if retangulo.colliderect(celula):
                    return True

    for porta in portas:
        if not porta["aberta"]:
            if retangulo.colliderect(retangulo_porta(porta)):
                return True

    for bau in baus:
        if retangulo.colliderect(retangulo_bau(bau)):
            return True

    return False


def atualizar_camera():
    global camera_x, camera_y

    centro_x = player_x + LARGURA_PERSONAGEM / 2
    centro_y = player_y + ALTURA_PERSONAGEM / 2

    camera_x = int(centro_x - LARGURA / 2)
    camera_y = int(centro_y - ALTURA / 2)

    camera_x = max(0, min(camera_x, MAPA_LARGURA - LARGURA))
    camera_y = max(0, min(camera_y, MAPA_ALTURA - ALTURA))




bau_atual = None
indice_item_bau = 0
mensagem = ""
tempo_mensagem = 0


def mostrar_mensagem(texto, duracao=1800):
    global mensagem, tempo_mensagem

    mensagem = texto
    tempo_mensagem = pygame.time.get_ticks() + duracao


def distancia_ate(retangulo):
    px = player_x + LARGURA_PERSONAGEM / 2
    py = player_y + ALTURA_PERSONAGEM - 15

    ox = retangulo.centerx
    oy = retangulo.centery

    return math.sqrt((px - ox) ** 2 + (py - oy) ** 2)


def encontrar_bau_proximo():
    melhor = None
    menor_distancia = 75

    for bau in baus:
        distancia = distancia_ate(retangulo_bau(bau))

        if distancia < menor_distancia:
            melhor = bau
            menor_distancia = distancia

    return melhor


def encontrar_porta_proxima():
    melhor = None
    menor_distancia = 85

    for porta in portas:
        distancia = distancia_ate(retangulo_porta(porta))

        if distancia < menor_distancia:
            melhor = porta
            menor_distancia = distancia

    return melhor


def interagir():
    global bau_atual, indice_item_bau

    if bau_atual is not None:
        bau_atual = None
        mostrar_mensagem("Baú fechado.")
        return

    bau = encontrar_bau_proximo()

    if bau is not None:
        bau["aberto"] = True
        bau_atual = bau
        indice_item_bau = 0
        salvar_baus()
        mostrar_mensagem("Baú aberto. Clique em um item para pegá-lo.")
        return

    porta = encontrar_porta_proxima()

    if porta is not None:
        porta["aberta"] = not porta["aberta"]
        salvar_portas()

        if porta["aberta"]:
            mostrar_mensagem("Você abriu a porta.")
        else:
            mostrar_mensagem("Você fechou a porta.")

        return

    mostrar_mensagem("Nenhum baú ou porta por perto.")



modo_editor_colisoes = False
modo_editor_portas = False
modo_editor_baus = False
inventario_aberto = False


def fechar_editores():
    global modo_editor_colisoes, modo_editor_portas, modo_editor_baus

    modo_editor_colisoes = False
    modo_editor_portas = False
    modo_editor_baus = False


def alternar_editor_colisoes():
    global modo_editor_colisoes

    fechar_editores()
    modo_editor_colisoes = True
    mostrar_mensagem("Editor de colisões: clique esquerdo adiciona; direito remove.")


def alternar_editor_portas():
    global modo_editor_portas

    fechar_editores()
    modo_editor_portas = True
    mostrar_mensagem("Editor de portas: clique esquerdo adiciona; direito remove.")


def alternar_editor_baus():
    global modo_editor_baus

    fechar_editores()
    modo_editor_baus = True
    mostrar_mensagem("Editor de baús: clique esquerdo adiciona; direito remove.")


def salvar_editores():
    salvar_colisoes()
    salvar_portas()
    salvar_baus()


def posicao_celula_mouse(posicao):
    mx, my = posicao
    mundo_x = mx + camera_x
    mundo_y = my + camera_y

    cx = int(mundo_x // CELULA_MUNDO)
    cy = int(mundo_y // CELULA_MUNDO)

    return cx, cy


def editar_colisao(posicao, botao):
    cx, cy = posicao_celula_mouse(posicao)

    if botao == 1:
        colisoes.add((cx, cy))
        salvar_colisoes()

    elif botao == 3:
        colisoes.discard((cx, cy))
        salvar_colisoes()


def editar_porta(posicao, botao):
    cx, cy = posicao_celula_mouse(posicao)

    if botao == 1:
        for porta in portas:
            if porta["x"] == cx and porta["y"] == cy:
                mostrar_mensagem("Já existe uma porta nessa posição.")
                return

        portas.append({
            "x": cx,
            "y": cy,
            "aberta": False
        })
        salvar_portas()

    elif botao == 3:
        for porta in portas:
            if porta["x"] == cx and porta["y"] == cy:
                portas.remove(porta)
                salvar_portas()
                return


def editar_bau(posicao, botao):
    cx, cy = posicao_celula_mouse(posicao)

    if botao == 1:
        for bau in baus:
            if bau["x"] == cx and bau["y"] == cy:
                mostrar_mensagem("Já existe um baú nessa posição.")
                return

        baus.append({
            "x": cx,
            "y": cy,
            "aberto": False,
            "itens": ITENS_INICIAIS_BAU[:]
        })

        salvar_baus()
        mostrar_mensagem("Baú criado com três itens de teste.")

    elif botao == 3:
        for bau in baus:
            if bau["x"] == cx and bau["y"] == cy:
                baus.remove(bau)

                if bau_atual is bau:
                    fechar_bau()

                salvar_baus()
                mostrar_mensagem("Baú removido.")
                return


def fechar_bau():
    global bau_atual, indice_item_bau

    bau_atual = None
    indice_item_bau = 0




def desenhar_bau(superficie, retangulo, aberto):
    x = retangulo.x
    y = retangulo.y
    tamanho = retangulo.width

    cor_madeira = MARROM_CLARO if aberto else MARROM

    pygame.draw.rect(
        superficie,
        (35, 24, 20),
        (x + 3, y + 7, tamanho - 6, tamanho - 10)
    )

    pygame.draw.rect(
        superficie,
        cor_madeira,
        (x + 2, y + 3, tamanho - 4, tamanho - 8)
    )

    pygame.draw.rect(
        superficie,
        DOURADO,
        (x + tamanho // 2 - 3, y + tamanho // 2, 6, 9)
    )

    pygame.draw.rect(
        superficie,
        (65, 39, 23),
        (x + 5, y + 7, tamanho - 10, 4)
    )

    pygame.draw.rect(
        superficie,
        DOURADO,
        (x + 2, y + 3, tamanho - 4, 2)
    )




def desenhar_inventario():
    largura_painel = 560
    altura_painel = 420

    x = (LARGURA - largura_painel) // 2
    y = (ALTURA - altura_painel) // 2

    pygame.draw.rect(
        tela, (25, 21, 27),
        (x, y, largura_painel, altura_painel)
    )
    pygame.draw.rect(
        tela, DOURADO,
        (x, y, largura_painel, altura_painel), 3
    )

    titulo = fonte_titulo.render("INVENTÁRIO", True, DOURADO)
    tela.blit(titulo, (x + 22, y + 16))

    instrucoes = fonte_pequena.render(
        "I ou ESC: fechar",
        True,
        BRANCO
    )
    tela.blit(instrucoes, (x + 22, y + 55))

    colunas = 5
    linhas = 4
    tamanho_slot = 76
    espacamento = 10

    inicio_x = x + 22
    inicio_y = y + 95

    for linha in range(linhas):
        for coluna in range(colunas):
            indice = linha * colunas + coluna

            slot_x = inicio_x + coluna * (tamanho_slot + espacamento)
            slot_y = inicio_y + linha * (tamanho_slot + espacamento)

            pygame.draw.rect(
                tela,
                (53, 45, 51),
                (slot_x, slot_y, tamanho_slot, tamanho_slot)
            )

            pygame.draw.rect(
                tela,
                DOURADO if indice < len(inventario) else CINZA,
                (slot_x, slot_y, tamanho_slot, tamanho_slot),
                2
            )

            if indice < len(inventario):
                item = inventario[indice]
                nome = item["nome"]
                quantidade = item["quantidade"]

                palavras = nome.split()
                linhas_nome = []
                linha_texto = ""

                for palavra in palavras:
                    teste = (linha_texto + " " + palavra).strip()

                    if fonte_pequena.size(teste)[0] > tamanho_slot - 8:
                        linhas_nome.append(linha_texto)
                        linha_texto = palavra
                    else:
                        linha_texto = teste

                if linha_texto:
                    linhas_nome.append(linha_texto)

                for n, texto in enumerate(linhas_nome[:3]):
                    imagem_texto = fonte_pequena.render(
                        texto, True, BRANCO
                    )
                    tela.blit(
                        imagem_texto,
                        (
                            slot_x + 4,
                            slot_y + 8 + n * 16
                        )
                    )

                if quantidade > 1:
                    texto_qtd = fonte_pequena.render(
                        "x" + str(quantidade),
                        True,
                        DOURADO
                    )
                    tela.blit(
                        texto_qtd,
                        (
                            slot_x + tamanho_slot - texto_qtd.get_width() - 5,
                            slot_y + tamanho_slot - 22
                        )
                    )

    rodape = fonte_pequena.render(
        "Itens guardados: " + str(len(inventario)),
        True,
        BRANCO
    )
    tela.blit(rodape, (x + 22, y + altura_painel - 28))




def desenhar_janela_bau():
    if bau_atual is None:
        return

    largura_painel = 480
    altura_painel = 340

    x = (LARGURA - largura_painel) // 2
    y = (ALTURA - altura_painel) // 2

    pygame.draw.rect(
        tela, (25, 21, 27),
        (x, y, largura_painel, altura_painel)
    )
    pygame.draw.rect(
        tela, DOURADO,
        (x, y, largura_painel, altura_painel), 3
    )

    titulo = fonte_titulo.render("BAÚ", True, DOURADO)
    tela.blit(titulo, (x + 20, y + 15))

    texto_ajuda = fonte_pequena.render(
        "Clique em um item para pegá-lo. E ou ESC fecha.",
        True,
        BRANCO
    )
    tela.blit(texto_ajuda, (x + 20, y + 52))

    if not bau_atual["itens"]:
        texto_vazio = fonte.render(
            "Este baú está vazio.",
            True,
            BRANCO
        )
        tela.blit(texto_vazio, (x + 25, y + 110))
        return

    for indice, item in enumerate(bau_atual["itens"][:8]):
        item_y = y + 95 + indice * 27

        if isinstance(item, dict):
            nome = str(item.get("nome", "Item desconhecido"))
            quantidade = item.get("quantidade", 1)
            texto_item = nome + " x" + str(quantidade)
        else:
            texto_item = str(item)

        cor = DOURADO if indice == indice_item_bau else BRANCO

        pygame.draw.rect(
            tela,
            (57, 45, 42) if indice == indice_item_bau else (35, 30, 34),
            (x + 20, item_y, largura_painel - 40, 24)
        )

        imagem_item = fonte_pequena.render(
            texto_item, True, cor
        )
        tela.blit(imagem_item, (x + 30, item_y + 4))





def desenhar_editor():
    if not (
        modo_editor_colisoes
        or modo_editor_portas
        or modo_editor_baus
    ):
        return

    for cx, cy in colisoes:
        retangulo = pygame.Rect(
            cx * CELULA_MUNDO - camera_x,
            cy * CELULA_MUNDO - camera_y,
            CELULA_MUNDO,
            CELULA_MUNDO
        )

        pygame.draw.rect(
            tela,
            (220, 40, 40, 110),
            retangulo,
            2
        )

    for porta in portas:
        retangulo = retangulo_porta(porta).move(
            -camera_x, -camera_y
        )

        cor = VERDE if porta["aberta"] else DOURADO
        pygame.draw.rect(tela, cor, retangulo, 3)

    for bau in baus:
        retangulo = retangulo_bau(bau).move(
            -camera_x, -camera_y
        )
        pygame.draw.rect(tela, (70, 170, 230), retangulo, 3)

    if modo_editor_colisoes:
        texto = "EDITOR DE COLISOES - clique esquerdo adiciona, direito remove, ESC salva"
    elif modo_editor_portas:
        texto = "EDITOR DE PORTAS - clique esquerdo adiciona, direito remove, ESC salva"
    else:
        texto = "EDITOR DE BAUS - clique esquerdo adiciona, direito remove, ESC salva"

    faixa = pygame.Surface((LARGURA, 35))
    faixa.set_alpha(220)
    faixa.fill((15, 13, 17))
    tela.blit(faixa, (0, 0))

    imagem_texto = fonte_pequena.render(texto, True, BRANCO)
    tela.blit(imagem_texto, (12, 9))




def desenhar_hud():
    pygame.draw.rect(
        tela,
        (20, 18, 22),
        (10, ALTURA - 42, 390, 32)
    )

    texto = fonte_pequena.render(
        "WASD/setas: mover | Shift: correr | E: interagir | I: inventário",
        True,
        BRANCO
    )
    tela.blit(texto, (18, ALTURA - 34))

    if tempo_mensagem > pygame.time.get_ticks():
        caixa = pygame.Rect(0, 12, LARGURA, 34)
        pygame.draw.rect(tela, (25, 21, 27), caixa)

        imagem_mensagem = fonte.render(mensagem, True, DOURADO)
        tela.blit(
            imagem_mensagem,
            (
                (LARGURA - imagem_mensagem.get_width()) // 2,
                17
            )
        )




executando = True

while executando:
    delta = relogio.tick(FPS)
    tempo_atual = pygame.time.get_ticks()

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            salvar_editores()
            salvar_inventario()
            executando = False

        elif evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_ESCAPE:
                if bau_atual is not None:
                    fechar_bau()

                elif inventario_aberto:
                    inventario_aberto = False

                elif (
                    modo_editor_colisoes
                    or modo_editor_portas
                    or modo_editor_baus
                ):
                    salvar_editores()
                    fechar_editores()
                    mostrar_mensagem("Editor fechado e dados salvos.")

            elif evento.key == pygame.K_i:
                if bau_atual is not None:
                    fechar_bau()

                inventario_aberto = not inventario_aberto

            elif evento.key == pygame.K_e:
                if inventario_aberto:
                    inventario_aberto = False
                else:
                    interagir()

            elif evento.key in (pygame.K_p, pygame.K_F2):
                if not inventario_aberto and bau_atual is None:
                    if modo_editor_colisoes:
                        salvar_colisoes()
                        fechar_editores()
                    else:
                        alternar_editor_colisoes()

            elif evento.key in (pygame.K_F4, pygame.K_F6):
                if not inventario_aberto and bau_atual is None:
                    if modo_editor_portas:
                        salvar_portas()
                        fechar_editores()
                    else:
                        alternar_editor_portas()

            elif evento.key in (pygame.K_F5, pygame.K_b):
                if not inventario_aberto and bau_atual is None:
                    print("A tecla F5/B foi detectada!")

                    if modo_editor_baus:
                        salvar_baus()
                        fechar_editores()
                    else:
                        alternar_editor_baus()

            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if bau_atual is not None and bau_atual["itens"]:
                    retirar_item_bau(bau_atual, indice_item_bau)

                    if bau_atual["itens"]:
                        indice_item_bau = min(
                            indice_item_bau,
                            len(bau_atual["itens"]) - 1
                        )
                    else:
                        indice_item_bau = 0

            elif evento.key == pygame.K_UP:
                if bau_atual is not None and bau_atual["itens"]:
                    indice_item_bau = (
                        indice_item_bau - 1
                    ) % len(bau_atual["itens"])

            elif evento.key == pygame.K_DOWN:
                if bau_atual is not None and bau_atual["itens"]:
                    indice_item_bau = (
                        indice_item_bau + 1
                    ) % len(bau_atual["itens"])

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button in (1, 3):
                if modo_editor_colisoes:
                    editar_colisao(evento.pos, evento.button)

                elif modo_editor_portas:
                    editar_porta(evento.pos, evento.button)

                elif modo_editor_baus:
                    editar_bau(evento.pos, evento.button)

                elif bau_atual is not None and evento.button == 1:
                    x = (LARGURA - 480) // 2
                    y = (ALTURA - 340) // 2

                    inicio_itens = y + 95
                    indice = (evento.pos[1] - inicio_itens) // 27

                    dentro_painel = (
                        x + 20 <= evento.pos[0] <= x + 460
                        and inicio_itens <= evento.pos[1] <= y + 95 + 8 * 27
                    )

                    if (
                        dentro_painel
                        and 0 <= indice < len(bau_atual["itens"])
                    ):
                        indice_item_bau = indice
                        retirar_item_bau(bau_atual, indice)

                        if bau_atual["itens"]:
                            indice_item_bau = min(
                                indice_item_bau,
                                len(bau_atual["itens"]) - 1
                            )
                        else:
                            indice_item_bau = 0

                elif inventario_aberto:
                    pass

    
    teclas = pygame.key.get_pressed()

    pode_mover = (
        not inventario_aberto
        and bau_atual is None
        and not modo_editor_colisoes
        and not modo_editor_portas
        and not modo_editor_baus
    )

    dx = 0
    dy = 0

    if pode_mover:
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            dx -= 1

        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            dx += 1

        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            dy -= 1

        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            dy += 1

    personagem_movendo = dx != 0 or dy != 0
    personagem_correndo = (
        personagem_movendo
        and (teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT])
    )

    if dx != 0 and dy != 0:
        dx *= 0.7071
        dy *= 0.7071

    velocidade = (
        VELOCIDADE_CORRIDA
        if personagem_correndo
        else VELOCIDADE
    )

    deslocamento_x = dx * velocidade
    deslocamento_y = dy * velocidade

    if dx < 0:
        direcao = "esquerda"
    elif dx > 0:
        direcao = "direita"
    elif dy < 0:
        direcao = "costas"
    elif dy > 0:
        direcao = "frente"

    
    if deslocamento_x != 0:
        novo_x = player_x + deslocamento_x
        retangulo = retangulo_personagem(novo_x, player_y)

        if not ha_colisao(retangulo):
            player_x = novo_x

   
    if deslocamento_y != 0:
        novo_y = player_y + deslocamento_y
        retangulo = retangulo_personagem(player_x, novo_y)

        if not ha_colisao(retangulo):
            player_y = novo_y

    player_x = max(
        0,
        min(player_x, MAPA_LARGURA - LARGURA_PERSONAGEM)
    )
    player_y = max(
        0,
        min(player_y, MAPA_ALTURA - ALTURA_PERSONAGEM)
    )

    if personagem_movendo:
        tempo_animacao += delta

        if tempo_animacao >= INTERVALO_ANIMACAO:
            tempo_animacao = 0

            if personagem_correndo:
                lista_frames = frames_corrida[direcao]
            else:
                lista_frames = frames[direcao]

            if len(lista_frames) > 1:
                indice_frame = (
                    indice_frame + 1
                ) % len(lista_frames)
            else:
                indice_frame = 0
    else:
        indice_frame = 0
        tempo_animacao = 0

    atualizar_camera()

    
    tela.blit(mapa, (-camera_x, -camera_y))

    # Desenhar baús
    for bau in baus:
        retangulo = retangulo_bau(bau).move(
            -camera_x, -camera_y
        )
        desenhar_bau(tela, retangulo, bau["aberto"])

    
    for porta in portas:
        retangulo = retangulo_porta(porta).move(
            -camera_x, -camera_y
        )

        if porta["aberta"]:
            pygame.draw.rect(
                tela, (80, 125, 75), retangulo, 2
            )
        else:
            pygame.draw.rect(
                tela, (95, 49, 32), retangulo
            )
            pygame.draw.rect(
                tela, DOURADO, retangulo, 2
            )

    
    if personagem_correndo:
        lista_frames = frames_corrida[direcao]
    else:
        lista_frames = frames[direcao]

    if lista_frames:
        imagem_personagem = lista_frames[
            indice_frame % len(lista_frames)
        ]
    else:
        imagem_personagem = frames["frente"][0]

    tela.blit(
        imagem_personagem,
        (int(player_x - camera_x), int(player_y - camera_y))
    )

    desenhar_editor()
    desenhar_hud()

    if inventario_aberto:
        desenhar_inventario()

    if bau_atual is not None:
        desenhar_janela_bau()

    pygame.display.flip()




salvar_editores()
salvar_inventario()

pygame.quit()
sys.exit()