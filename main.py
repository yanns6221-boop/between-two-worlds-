import pygame
import sys

pygame.init()

LARGURA = 800
ALTURA = 600

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Between Two Worlds")

relogio = pygame.time.Clock()

# Carregar personagem
player = pygame.image.load("assets/player.png").convert_alpha()

largura = player.get_width() // 2
player = player.subsurface((0, 0, largura, player.get_height()))

player = pygame.transform.scale(player, (64, 96))
# Posição inicial
x = 370
y = 250

velocidade = 4

rodando = True

while rodando:

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    teclas = pygame.key.get_pressed()

    if teclas[pygame.K_a]:
        x -= velocidade

    if teclas[pygame.K_d]:
        x += velocidade

    if teclas[pygame.K_w]:
        y -= velocidade

    if teclas[pygame.K_s]:
        y += velocidade

    tela.fill((20, 20, 25))

    tela.blit(player, (x, y))

    pygame.display.flip()

    relogio.tick(60)

pygame.quit()
sys.exit()