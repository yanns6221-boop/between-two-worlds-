
import pygame
import random
import os

pygame.init()
PASTA = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(PASTA, "assets")

tela = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Sistema de Combate")

fundo = pygame.image.load(os.path.join(ASSETS, "combate.jpeg")).convert()
fundo = pygame.transform.scale(fundo, (800, 600))

personagem = pygame.image.load(os.path.join(ASSETS, "personagem.jpeg")).convert_alpha()
personagem.set_colorkey((255, 255, 255))
personagem = pygame.transform.scale(personagem, (180, 280))

fonte = pygame.font.Font(None, 32)
fonte_grande = pygame.font.Font(None, 65)

hp_jogador = 100
hp_inimigo = 100

bonus_dano = False
defendendo = False
mensagem = ""

botao_atacar = pygame.Rect(100, 520, 180, 50)
botao_defender = pygame.Rect(310, 520, 180, 50)
botao_fugir = pygame.Rect(520, 520, 180, 50)


def cor_vida(vida):
    if vida > 60:
        return (0, 255, 0)
    elif vida > 30:
        return (255, 255, 0)
    else:
        return (255, 0, 0)


def barra_vida(tela, x, y, vida, nome):
    pygame.draw.rect(tela, (50, 50, 50), (x, y, 300, 25))

    largura = int(300 * vida / 100)

    pygame.draw.rect(
        tela,
        cor_vida(vida),
        (x, y, largura, 25)
    )

    texto = fonte.render(
        nome + ": " + str(vida) + "/100",
        True,
        (255, 255, 255)
    )

    tela.blit(texto, (x, y - 30))


rodando = True

while rodando:

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            rodando = False

        if evento.type == pygame.MOUSEBUTTONDOWN and hp_jogador > 0 and hp_inimigo > 0:

            mouse = pygame.mouse.get_pos()

            if botao_atacar.collidepoint(mouse):

                dano = random.randint(10, 20)

                if bonus_dano:
                    dano += 15
                    bonus_dano = False
                    mensagem = "Ataque fortalecido! Dano: " + str(dano)
                else:
                    mensagem = "Voce atacou! Dano: " + str(dano)

                hp_inimigo -= dano

                if hp_inimigo < 0:
                    hp_inimigo = 0

                if hp_inimigo > 0:
                    dano_inimigo = random.randint(15, 30)

                    if defendendo:
                        dano_inimigo //= 2
                        mensagem += " Voce defendeu!"

                    hp_jogador -= dano_inimigo

                    if hp_jogador < 0:
                        hp_jogador = 0

                defendendo = False

            elif botao_defender.collidepoint(mouse):

                defendendo = True
                bonus_dano = True

                dano = random.randint(5, 10)
                hp_inimigo -= dano

                if hp_inimigo < 0:
                    hp_inimigo = 0

                mensagem = "Voce defendeu e atacou! Dano: " + str(dano)

                if hp_inimigo > 0:
                    dano_inimigo = random.randint(15, 30)
                    dano_inimigo //= 2

                    hp_jogador -= dano_inimigo

                    if hp_jogador < 0:
                        hp_jogador = 0

                defendendo = False

            elif botao_fugir.collidepoint(mouse):

                mensagem = "Voce fugiu do combate!"
                rodando = False

    tela.blit(fundo, (0, 0))
    tela.blit(personagem, (100, 300))

    barra_vida(tela, 50, 50, hp_jogador, "PRINCESA")
    barra_vida(tela, 450, 50, hp_inimigo, "INIMIGO")

    pygame.draw.rect(tela, (80, 80, 80), botao_atacar)
    pygame.draw.rect(tela, (80, 80, 80), botao_defender)
    pygame.draw.rect(tela, (80, 80, 80), botao_fugir)

    texto_atacar = fonte.render("ATACAR", True, (255, 255, 255))
    texto_defender = fonte.render("DEFENDER", True, (255, 255, 255))
    texto_fugir = fonte.render("FUGIR", True, (255, 255, 255))

    tela.blit(texto_atacar, (botao_atacar.x + 45, botao_atacar.y + 12))
    tela.blit(texto_defender, (botao_defender.x + 35, botao_defender.y + 12))
    tela.blit(texto_fugir, (botao_fugir.x + 55, botao_fugir.y + 12))

    if mensagem != "":
        texto_mensagem = fonte.render(
            mensagem,
            True,
            (255, 255, 255)
        )

        tela.blit(texto_mensagem, (100, 470))

    if hp_inimigo <= 0:
        texto_vitoria = fonte_grande.render(
            "YOU WIN!",
            True,
            (255, 255, 255)
        )

        tela.blit(texto_vitoria, (300, 200))

    elif hp_jogador <= 0:
        texto_derrota = fonte_grande.render(
            "YOU LOSE!",
            True,
            (255, 255, 255)
        )

        tela.blit(texto_derrota, (300, 200))

    pygame.display.flip()

pygame.quit()
