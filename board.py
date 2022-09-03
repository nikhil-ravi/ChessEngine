from __future__ import annotations
import pygame as pg
import numpy as np
from const import HEIGHT, ROWS, COLS, SQSIZE, WIDTH, pieceImages, MOVELOG_HEIGHT, MOVELOG_WIDTH


class BoardState:
    def __init__(self):
        self.board = np.array(
            [
                ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
                ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
                ["--", "--", "--", "--", "--", "--", "--", "--"],
                ["--", "--", "--", "--", "--", "--", "--", "--"],
                ["--", "--", "--", "--", "--", "--", "--", "--"],
                ["--", "--", "--", "--", "--", "--", "--", "--"],
                ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
                ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
            ]
        )
        self.IMAGES = pieceImages()
        self.whiteMove = True
        self.moveLog = []
        self.pieceMoveDict = {
            "p": self._pawnMoves,
            "R": self._RookMoves,
            "B": self._BishopMoves,
            "N": self._KnightMoves,
            "Q": self._QueenMoves,
            "K": self._KingMoves,
        }

        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)

        self.inCheck = False
        self.pins = []
        self.checks = []

        self.checkmate = False
        self.stalemate = False
        self.enpassantPossible = ()
        self.enpassantPossibleLogs = [self.enpassantPossible]
        self.currentCastlingRights = CastleRights(True, True, True, True)
        self.castleRightsLog = [
            CastleRights(
                self.currentCastlingRights.wks,
                self.currentCastlingRights.bks,
                self.currentCastlingRights.wqs,
                self.currentCastlingRights.bqs,
            )
        ]

    def makeMove(self, move: Move):
        """Make the given move.

        Args:
            move (Move): The move to make.
        """
        self.board[move.startSqRow, move.startSqCol] = "--"
        self.board[move.endSqRow, move.endSqCol] = move.movedPiece
        self.moveLog.append(move)
        self.whiteMove = not self.whiteMove
        if move.movedPiece == "wK":
            self.whiteKingLocation = (move.endSqRow, move.endSqCol)
        elif move.movedPiece == "bK":
            self.blackKingLocation = (move.endSqRow, move.endSqCol)

        if move.isPawnPromotion:
            promotedPiece = input("Promote to Q, R, B or N: ")
            self.board[move.endSqRow, move.endSqCol] = (
                move.movedPiece[0] + promotedPiece
            )

        if move.isEnpassantMove:
            self.board[move.startSqRow, move.endSqCol] = "--"

        if move.movedPiece[1] == "p" and abs(move.startSqRow - move.endSqRow) == 2:
            self.enpassantPossible = (
                (move.startSqRow + move.endSqRow) // 2,
                move.startSqCol,
            )
        else:
            self.enpassantPossible = ()

        if move.isCastleMove:
            if move.endSqCol - move.startSqCol == 2:
                self.board[move.endSqRow, move.endSqCol - 1] = self.board[
                    move.endSqRow, move.endSqCol + 1
                ]
                self.board[move.endSqRow, move.endSqCol + 1] = "--"
            else:
                self.board[move.endSqRow, move.endSqCol + 1] = self.board[
                    move.endSqRow, move.endSqCol - 2
                ]
                self.board[move.endSqRow, move.endSqCol - 2] = "--"

        self.enpassantPossibleLogs.append(self.enpassantPossible)

        self.updateCastleRights(move)
        self.castleRightsLog.append(
            CastleRights(
                self.currentCastlingRights.wks,
                self.currentCastlingRights.bks,
                self.currentCastlingRights.wqs,
                self.currentCastlingRights.bqs,
            )
        )

    def undoMove(self):
        """Undo the last move made."""
        if self.moveLog:
            lastMove = self.moveLog.pop()
            self.board[lastMove.startSqRow, lastMove.startSqCol] = lastMove.movedPiece
            self.board[lastMove.endSqRow, lastMove.endSqCol] = lastMove.capturedPiece
            self.whiteMove = not self.whiteMove
            if lastMove.movedPiece == "wK":
                self.whiteKingLocation = (lastMove.startSqRow, lastMove.startSqCol)
            elif lastMove.movedPiece == "bK":
                self.blackKingLocation = (lastMove.startSqRow, lastMove.startSqCol)
            # undo enpassant
            if lastMove.isEnpassantMove:
                self.board[lastMove.endSqRow, lastMove.endSqCol] = "--"
                self.board[
                    lastMove.startSqRow, lastMove.endSqCol
                ] = lastMove.capturedPiece

            self.enpassantPossibleLogs.pop()
            self.enpassantPossible = self.enpassantPossibleLogs[-1]

        # undo castling rights
        self.castleRightsLog.pop()
        self.currentCastlingRights = self.castleRightsLog[-1]

        if lastMove.isCastleMove:
            if lastMove.endSqCol - lastMove.startSqCol == 2:
                self.board[lastMove.endSqRow, lastMove.endSqCol + 1] = self.board[
                    lastMove.endSqRow, lastMove.endSqCol - 1
                ]
                self.board[lastMove.endSqRow, lastMove.endSqCol - 1] = "--"
            else:
                self.board[lastMove.endSqRow, lastMove.endSqCol - 2] = self.board[
                    lastMove.endSqRow, lastMove.endSqCol + 1
                ]
                self.board[lastMove.endSqRow, lastMove.endSqCol + 1] = "--"

        self.checkmate = False
        self.stalemate = False

    # Update castle rights - whenever a rook or a king moves
    def updateCastleRights(self, move):
        if move.capturedPiece == "wR":
            if move.endSqCol == 0:
                self.currentCastlingRights.wqs = False
            elif move.endSqCol == 7:
                self.currentCastlingRights.wks = False
        elif move.capturedPiece == "bR":
            if move.endSqCol == 0:
                self.currentCastlingRights.bqs = False
            elif move.endSqCol == 7:
                self.currentCastlingRights.bks = False

        if move.movedPiece == "wK":
            self.currentCastlingRights.wqs = False
            self.currentCastlingRights.wks = False
        elif move.movedPiece == "bK":
            self.currentCastlingRights.bqs = False
            self.currentCastlingRights.bks = False
        elif move.movedPiece == "wR":
            if move.startSqRow == 7:
                if move.startSqCol == 0:
                    self.currentCastlingRights.wqs = False
                elif move.startSqCol == 7:
                    self.currentCastlingRights.wks = False
        elif move.movedPiece == "bR":
            if move.startSqRow == 0:
                if move.startSqCol == 0:
                    self.currentCastlingRights.bqs = False
                elif move.startSqCol == 7:
                    self.currentCastlingRights.bks = False

    def getValidMoves(self):
        tempCastleRights = CastleRights(
            self.currentCastlingRights.wks,
            self.currentCastlingRights.bks,
            self.currentCastlingRights.wqs,
            self.currentCastlingRights.bqs,
        )
        moves = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        kingRow, kingCol = (
            self.whiteKingLocation if self.whiteMove else self.blackKingLocation
        )
        if self.inCheck:
            if len(self.checks) == 1:
                moves = self.getAllPossibleMoves()
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow, checkCol]
                validSquares = []
                if pieceChecking[1] == "N":
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSquare = (
                            kingRow + i * check[2],
                            kingCol + i * check[3],
                        )
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:
                            break
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].movedPiece[1] != "K":
                        if not (moves[i].endSqRow, moves[i].endSqCol) in validSquares:
                            moves.remove(moves[i])
            else:
                self._KingMoves(kingRow, kingCol, moves)
        else:
            moves = self.getAllPossibleMoves()
            if self.whiteMove:
                self._getCastleMoves(
                    self.whiteKingLocation[0], self.whiteKingLocation[1], moves
                )
            else:
                self._getCastleMoves(
                    self.blackKingLocation[0], self.blackKingLocation[1], moves
                )

        if len(moves) == 0:
            if self._inCheck():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.currentCastlingRights = tempCastleRights
        return moves

    def _inCheck(self):
        if self.whiteMove:
            return self._isUnderAttack(
                self.whiteKingLocation[0], self.whiteKingLocation[1]
            )
        else:
            return self._isUnderAttack(
                self.blackKingLocation[0], self.blackKingLocation[1]
            )

    def _isUnderAttack(self, row, col):
        self.whiteMove = not self.whiteMove
        opponentMoves = self.getAllPossibleMoves()
        self.whiteMove = not self.whiteMove
        for move in opponentMoves:
            if move.endSqRow == row and move.endSqCol == col:
                return True
        return False

    def getAllPossibleMoves(self):
        moves = []
        for row in range(self.board.shape[0]):
            for col in range(self.board.shape[1]):
                turn = self.board[row, col][0]
                if (turn == "w" and self.whiteMove) or (
                    turn == "b" and not self.whiteMove
                ):
                    piece = self.board[row, col][1]
                    self.pieceMoveDict[piece](row, col, moves)
        return moves

    def checkForPinsAndChecks(self):
        pins = []
        checks = []
        inCheck = False

        allyColor, opponentColor, startRow, startCol = (
            ("w", "b", self.whiteKingLocation[0], self.whiteKingLocation[1])
            if self.whiteMove
            else ("b", "w", self.blackKingLocation[0], self.blackKingLocation[1])
        )
        directions = [
            (-1, 0),
            (0, -1),
            (1, 0),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]
        for j, direction in enumerate(directions):
            possiblePin = ()
            for i in range(1, 8):
                endRow = startRow + direction[0] * i
                endCol = startCol + direction[1] * i
                if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                    endPiece = self.board[endRow, endCol]
                    if endPiece[0] == allyColor and endPiece[1] != "K":
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, direction[0], direction[1])
                        else:
                            break
                    elif endPiece[0] == opponentColor:
                        pieceType = endPiece[1]
                        if (
                            (0 <= j <= 3 and pieceType == "R")
                            or (4 <= j <= 7 and pieceType == "B")
                            or (
                                i == 1
                                and pieceType == "p"
                                and (
                                    (opponentColor == "w" and 6 <= j <= 7)
                                    or (opponentColor == "b" and 4 <= j <= 5)
                                )
                            )
                            or (pieceType == "Q")
                            or (i == 1 and pieceType == "K")
                        ):
                            if possiblePin == ():  # No piece blocking, so check.
                                inCheck = True
                                checks.append(
                                    (endRow, endCol, direction[0], direction[1])
                                )
                                break
                            else:  # Piece blocking, so pin.
                                pins.append(possiblePin)
                                break
                        else:
                            break
                else:
                    break
        knightMoves = [
            (-2, -1),
            (-2, 1),
            (-1, 2),
            (1, 2),
            (2, -1),
            (2, 1),
            (-1, -2),
            (1, -2),
        ]
        for move in knightMoves:
            endRow = startRow + move[0]
            endCol = startCol + move[1]
            if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                endPiece = self.board[endRow, endCol]
                if endPiece[0] == opponentColor and endPiece[1] == "N":
                    inCheck = True
                    checks.append((endRow, endCol, move[0], move[1]))
        return inCheck, pins, checks

    def _pawnMoves(self, row: int, col: int, moves: list[Move]):
        """Generate the list of possible moves for a pawn at position row, col.

        Args:
            row (int): The row in which the pawn resides.
            col (int): The col in which the pawn resides.
            moves (list[Move]): The list of possible pawn moves.
        """

        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        opponentColor, direction, pawnRow = (
            ("b", -1, 6) if self.whiteMove else ("w", 1, 1)
        )
        # Go up one square:
        if self.board[row + direction, col] == "--":
            if not piecePinned or pinDirection == (direction, 0):
                moves.append(Move((row, col), (row + direction, col), self.board))
                # Go up two squares
                if row == pawnRow and self.board[row + direction * 2, col] == "--":
                    moves.append(
                        Move((row, col), (row + direction * 2, col), self.board)
                    )
        # Capture
        for colDirection in [-1, 1]:
            if 0 <= (col + colDirection) <= 7:
                if not piecePinned or pinDirection == (direction, colDirection):
                    if (
                        self.board[row + direction, col + colDirection][0]
                        == opponentColor
                    ):
                        moves.append(
                            Move(
                                (row, col),
                                (row + direction, col + colDirection),
                                self.board,
                            )
                        )
                    elif (
                        row + direction,
                        col + colDirection,
                    ) == self.enpassantPossible:
                        moves.append(
                            Move(
                                (row, col),
                                (row + direction, col + colDirection),
                                self.board,
                                isEnpassantMove=True,
                            )
                        )

    def _RookMoves(self, row: int, col: int, moves: list[Move]):
        """Generate the list of possible moves for a rook at position row, col.

        Args:
            row (int): The row in which the rook resides.
            col (int): The col in which the rook resides.
            moves (list[Move]): The list of possible rook moves.
        """
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[row, col][1] != "Q":
                    self.pins.remove(self.pins[i])
                break

        directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
        self.__RookBishopMoves(row, col, moves, directions, piecePinned, pinDirection)

    def _BishopMoves(self, row: int, col: int, moves: list[Move]):
        """Generate the list of possible moves for a bishop at position row, col.

        Args:
            row (int): The row in which the bishop resides.
            col (int): The col in which the bishop resides.
            moves (list[Move]): The list of possible bishop moves.
        """
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
        self.__RookBishopMoves(row, col, moves, directions, piecePinned, pinDirection)

    def __RookBishopMoves(self, row, col, moves, directions, piecePinned, pinDirection):
        opponentColor = "b" if self.whiteMove else "w"
        for direction in directions:
            for i in range(1, 8):
                endRow = row + i * direction[0]
                endCol = col + i * direction[1]
                if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                    if (
                        not piecePinned
                        or pinDirection == direction
                        or pinDirection == (-direction[0], -direction[1])
                    ):
                        endPiece = self.board[endRow, endCol]
                        if endPiece == "--":
                            moves.append(Move((row, col), (endRow, endCol), self.board))
                        elif endPiece[0] == opponentColor:
                            moves.append(Move((row, col), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:
                    break

    def _KnightMoves(self, row: int, col: int, moves: list[Move]):
        """Generate the list of possible moves for a knight at position row, col.

        Args:
            row (int): The row in which the knight resides.
            col (int): The col in which the knight resides.
            moves (list[Move]): The list of possible knight moves.
        """
        piecePinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        allyColor = "w" if self.whiteMove else "b"
        knightMoves = [
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
            (-1, 2),
            (-1, -2),
            (-2, 1),
            (-2, -1),
        ]
        for move in knightMoves:
            endRow = row + move[0]
            endCol = col + move[1]
            if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                if not piecePinned:
                    endPiece = self.board[endRow, endCol]
                    if endPiece[0] != allyColor:
                        moves.append(Move((row, col), (endRow, endCol), self.board))

    def _QueenMoves(self, row: int, col: int, moves: list[Move]):
        """Generate the list of possible moves for a queen at position row, col.

        Args:
            row (int): The row in which the queen resides.
            col (int): The col in which the queen resides.
            moves (list[Move]): The list of possible queen moves.
        """
        self._BishopMoves(row, col, moves)
        self._RookMoves(row, col, moves)

    def _KingMoves(self, row: int, col: int, moves: list[Move]):
        """Generate the list of possible moves for a king at position row, col.

        Args:
            row (int): The row in which the king resides.
            col (int): The col in which the king resides.
            moves (list[Move]): The list of possible king moves.
        """
        allyColor = "w" if self.whiteMove else "b"
        kingMoves = [
            (1, 0),
            (1, -1),
            (0, -1),
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ]
        for move in kingMoves:
            endRow = row + move[0]
            endCol = col + move[1]
            if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                endPiece = self.board[endRow, endCol]
                if endPiece[0] != allyColor:
                    if allyColor == "w":
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((row, col), (endRow, endCol), self.board))
                    if allyColor == "w":
                        self.whiteKingLocation = (row, col)
                    else:
                        self.blackKingLocation = (row, col)

        # self._getCastleMoves(row, col, moves)

    def _getCastleMoves(self, row, col, moves):
        if self._isUnderAttack(row, col):
            return
        if (self.whiteMove and self.currentCastlingRights.wks) or (
            not self.whiteMove and self.currentCastlingRights.bks
        ):
            self._getKingSideCastleMoves(row, col, moves)
        if (self.whiteMove and self.currentCastlingRights.wqs) or (
            not self.whiteMove and self.currentCastlingRights.bqs
        ):
            self._getQueenSideCastleMoves(row, col, moves)

    def _getKingSideCastleMoves(self, row, col, moves):
        if self.board[row, col + 1] == "--" and self.board[row, col + 2] == "--":
            if not self._isUnderAttack(row, col + 1) and not self._isUnderAttack(
                row, col + 2
            ):
                moves.append(
                    Move((row, col), (row, col + 2), self.board, isCastleMove=True)
                )

    def _getQueenSideCastleMoves(self, row, col, moves):
        if (
            self.board[row, col - 1] == "--"
            and self.board[row, col - 2] == "--"
            and self.board[row, col - 3] == "--"
        ):
            if not self._isUnderAttack(row, col - 1) and not self._isUnderAttack(
                row, col - 2
            ):
                moves.append(
                    Move((row, col), (row, col - 2), self.board, isCastleMove=True)
                )

    def drawBoardState(
        self,
        screen: pg.Surface,
        validMoves: list[Move],
        sqSelected: tuple[int, int],
        lightColor: str = "white",
        darkColor: str = "gray",
    ):
        """Draw the game board at the current state.

        Args:
            screen (pg.Surface): The board surface.
            lightColor (str, optional): The color of the light squares. Defaults to "white".
            darkColor (str, optional): The color of the dark squares. Defaults to "gray".

        """
        self._drawBoard(screen, lightColor, darkColor)
        self.highlightSquare(screen, validMoves, sqSelected)
        self._drawPieces(screen)

    def _drawBoard(
        self, screen: pg.Surface, lightColor: str = "white", darkColor: str = "gray"
    ):
        """Draw the game board base.

        Args:
            screen (pg.Surface): The game board surface.
            lightColor (str, optional): The color of the light squares. Defaults to "white".
            darkColor (str, optional): The color of the dark squares. Defaults to "gray".

        """
        colors = [pg.Color(lightColor), pg.Color(darkColor)]
        for r in range(ROWS):
            for c in range(COLS):
                pg.draw.rect(
                    screen,
                    colors[(r + c) % 2],
                    pg.Rect(c * SQSIZE, r * SQSIZE, SQSIZE, SQSIZE),
                )

    def _drawPieces(self, screen: pg.Surface):
        """Draw the pieces in their current state.

        Args:
            screen (pg.Surface): The board surface.

        """
        for r in range(ROWS):
            for c in range(COLS):
                if self.board[r, c] != "--":
                    screen.blit(
                        self.IMAGES[self.board[r, c]],
                        pg.Rect(c * SQSIZE, r * SQSIZE, SQSIZE, SQSIZE),
                    )

    def highlightSquare(
        self, screen: pg.Surface, validMoves: list[Move], sqSelected: tuple[int, int]
    ):
        if self.moveLog:
            lastMove = self.moveLog[-1]
            s = pg.Surface((SQSIZE, SQSIZE))
            s.set_alpha(100)
            s.fill(pg.Color("green"))
            screen.blit(s, (lastMove.endSqCol * SQSIZE, lastMove.endSqRow * SQSIZE))
        if sqSelected:
            row, col = sqSelected
            if self.board[row, col][0] == ("w" if self.whiteMove else "b"):
                s = pg.Surface((SQSIZE, SQSIZE))
                s.set_alpha(100)
                s.fill(pg.Color("blue"))
                screen.blit(s, (col * SQSIZE, row * SQSIZE))
                s.fill(pg.Color("yellow"))
                for move in validMoves:
                    if move.startSqRow == row and move.startSqCol == col:
                        screen.blit(s, (move.endSqCol * SQSIZE, move.endSqRow * SQSIZE))

    def drawMoveLog(self, screen, font):
        moveLogRect = pg.Rect(WIDTH, 0, MOVELOG_WIDTH, MOVELOG_HEIGHT)
        pg.draw.rect(screen, pg.Color("black"), moveLogRect)
        move_texts = []
        for i in range(0,len(self.moveLog), 2):
            move_string = str(i // 2 + 1) + ". " + str(self.moveLog[i]) + " "
            if i + 1 < len(self.moveLog):
                move_string += str(self.moveLog[i+1]) + " "
            move_texts.append(move_string)
        
        moves_per_row = 3
        padding = 5
        line_spacing = 2
        text_y = padding
        for i in range(0, len(move_texts), moves_per_row):
            text = ""
            for j in range(moves_per_row):
                if i + j < len(move_texts):
                    text += move_texts[i+j]
            
            text_object = font.render(text, True, pg.Color("white"))
            textLocation = moveLogRect.move(padding, text_y)
            screen.blit(text_object, textLocation)
            text_y += text_object.get_height() + line_spacing

    def drawEndGameText(self, screen: pg.Surface, txt: str):
        font = pg.font.SysFont("Helvetica", 32, True, False)
        text = font.render(txt, False, pg.color("gray"))
        textLocation = pg.Rect(0, 0, WIDTH, HEIGHT).move(
            WIDTH / 2 - text.get_width() / 2, HEIGHT / 2 - text.get_height() / 2
        )
        screen.blit(text, textLocation)
        text = font.render(text, False, pg.Color("black"))
        screen.blit(text, textLocation.move(2, 2))

    def animateMove(self, screen, clock):
        """
        Animating a move
        """
        move = self.moveLog[-1] 
        board = self.board
        colors = [pg.Color("white"), pg.Color("gray")]
        d_row = move.endSqRow - move.startSqRow
        d_col = move.endSqCol - move.startSqCol
        frames_per_square = 10  # frames to move one square
        frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
        for frame in range(frame_count + 1):
            row, col = (move.startSqRow + d_row * frame / frame_count, move.startSqCol + d_col * frame / frame_count)
            self._drawBoard(screen)
            self._drawPieces(screen)
            # erase the piece moved from its ending square
            color = colors[(move.endSqRow + move.endSqCol) % 2]
            end_square = pg.Rect(move.endSqCol * SQSIZE, move.endSqRow * SQSIZE, SQSIZE, SQSIZE)
            pg.draw.rect(screen, color, end_square)
            # draw captured piece onto rectangle
            if move.capturedPiece != '--':
                if move.isEnpassantMove:
                    enpassant_row = move.endSqRow + 1 if move.capturedPiece[0] == 'b' else move.endSqRow - 1
                    end_square = pg.Rect(move.endSqCol * SQSIZE, enpassant_row * SQSIZE, SQSIZE, SQSIZE)
                screen.blit(self.IMAGES[move.capturedPiece], end_square)
            # draw moving piece
            screen.blit(self.IMAGES[move.movedPiece], pg.Rect(col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE))
            pg.display.flip()
            clock.tick(60)

class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    ranksToRows = {f"{8-rank}": rank for rank in range(8)}
    RowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {chr(97 + file): file for file in range(8)}
    ColsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(
        self, startSq, endSq, board, isEnpassantMove=False, isCastleMove=False
    ):
        self.startSqRow = startSq[0]
        self.startSqCol = startSq[1]
        self.endSqRow = endSq[0]
        self.endSqCol = endSq[1]
        self.movedPiece = board[self.startSqRow, self.startSqCol]
        self.capturedPiece = board[self.endSqRow, self.endSqCol]

        self.isPawnPromotion = (self.movedPiece == "wp" and self.endSqRow == 0) or (
            self.movedPiece == "bp" and self.endSqRow == 7
        )

        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.capturedPiece = "wp" if self.movedPiece == "bp" else "bp"

        self.isCastleMove = isCastleMove

        self.is_capture = self.capturedPiece != "--"
        
        self.MoveID = (
            1000 * self.startSqRow
            + 100 * self.startSqCol
            + 10 * self.endSqRow
            + self.endSqCol
        )

    def getRankFile(self, row, col):
        return self.ColsToFiles[col] + self.RowsToRanks[row]

    def getChessNotation(self) -> str:
        """Generate the chess notation for the move.

        Returns:
            str: The chess notation of the move.
        """
        if self.isPawnPromotion:
            return self.getRankFile(self.endSqRow, self.endSqCol) + "Q"
        if self.isCastleMove:
            if self.endSqCol == 2:
                return "0-0-0"
            else:
                return "0-0"
        if self.isEnpassantMove:
            return (
                self.getRankFile(self.startSqRow, self.startSqCol)[0]
                + "x"
                + self.getRankFile(self.endSqRow, self.endSqCol)
                + "e.p."
            )

        if self.capturedPiece != "--":
            if self.movedPiece[1] == "p":
                return (
                    self.getRankFile(self.startSqRow, self.startSqCol)[0]
                    + "x"
                    + self.getRankFile(self.endSqRow, self.endSqCol)
                )
            else:
                return self.movedPiece[1] + "x" + self.getRankFile(self.endSqRow, self.endSqCol)
        else:
            if self.movedPiece[1] == "p":
                return self.getRankFile(self.endSqRow, self.endSqCol)
            else:
                return self.movedPiece[1] + self.getRankFile(self.endSqRow, self.endSqCol)

    def __eq__(self, other: Move) -> bool:
        """Override the equals method to compare two moves.

        Args:
            other (Move): The other move to compare with.

        Returns:
            bool: Whether the other move is equal to the given move.
        """
        if isinstance(other, Move):
            return self.MoveID == other.MoveID
        return False

    def __repr__(self) -> str:
        return f"Move({self.ColsToFiles[self.startSqCol] + self.RowsToRanks[self.startSqRow] + self.ColsToFiles[self.endSqCol] + self.RowsToRanks[self.endSqRow]})"

    def __str__(self) -> str:
        if self.isCastleMove:
            return "0-0" if self.endcol == 6 else "0-0-0"
        
        endSq = self.getRankFile(self.endSqRow, self.endSqCol)
        
        if self.movedPiece[1] == "p":
            if self.is_capture:
                return self.ColsToFiles[self.startSqCol] + "x" + endSq
            else:
                return endSq + "Q" if self.isPawnPromotion else endSq
        
        move_string = self.movedPiece[1]
        if self.is_capture:
            move_string += "x"
        return move_string + endSq