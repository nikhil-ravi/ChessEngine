import os
from typing import Dict
import pygame as pg

WIDTH = 512
HEIGHT = 512
MOVELOG_WIDTH = 256
MOVELOG_HEIGHT = HEIGHT

ROWS, COLS = 8, 8
SQSIZE = WIDTH // COLS

MAX_FPS = 15


def pieceImages(style: str = "classic") -> Dict[str, pg.Surface]:
    """Load chess piece images of a given style.

    Args:
        style (str, optional): The piece style. Defaults to "classic".

    Returns:
        Dict[str, pg.Surface]: A dictionary of piece images.
    """
    IMAGES = {
        f[:-4]: pg.transform.scale(
            pg.image.load(os.path.join(f"./images/{style}/", f)), (SQSIZE, SQSIZE)
        )
        for f in os.listdir(f"./images/{style}/")
    }

    return IMAGES
