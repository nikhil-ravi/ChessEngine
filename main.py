from const import *
import pygame as pg
from board import BoardState, Move
from const import HEIGHT, WIDTH, MOVELOG_WIDTH
import sys


def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH + MOVELOG_WIDTH, HEIGHT))
    clock = pg.time.Clock()
    screen.fill(pg.Color("white"))
    gameState = BoardState()
    validMoves = gameState.getValidMoves()
    moveMade = False
    animate = False
    running = True
    sqSelected = ()
    playerClicks = []
    gameOver = False
    moveUndone = False
    moveLogFont = pg.font.SysFont("Arial", 14, False, False)
    
    while running:
        for e in pg.event.get():
            if e.type == pg.QUIT:
                pg.quit()
                sys.exit()
            elif e.type == pg.MOUSEBUTTONDOWN:
                if not gameOver:
                    location = pg.mouse.get_pos()
                    col = location[0] // SQSIZE
                    row = location[1] // SQSIZE
                    if sqSelected == (row, col) or col >= 8:
                        sqSelected = ()
                        playerClicks = []
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)
                    if len(playerClicks) == 2:
                        move = Move(*playerClicks, gameState.board)
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gameState.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]

            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_z:
                    gameState.undoMove()
                    moveMade = True
                    animate = False
                    gameOver = False
                    moveUndone = True

                if e.key == pg.K_r:
                    gameState = BoardState()
                    validMoves = gameState.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
                    moveUndone = True

        if moveMade:
            if animate:
                gameState.animateMove(screen, clock)
            validMoves = gameState.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        gameState.drawBoardState(screen, validMoves, sqSelected)
        
        if not gameOver:
            gameState.drawMoveLog(screen, moveLogFont)
            
        if gameState.checkmate:
            gameOver = True
            gameState.drawEndGameText(
                screen,
                "{} wins by checkmate".format(
                    "Black" if gameState.whiteMove else "White"
                ),
            )
        elif gameState.stalemate:
            gameState.drawEndGameText(screen, "Stalemate")
            
        clock.tick(MAX_FPS)
        pg.display.flip()


if __name__ == "__main__":
    main()
