
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

