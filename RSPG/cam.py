import pygame
import math
import random
import time

WORLD_WIDTH = 20000
WORLD_HIGHT = 20000
CHUNK_SIZE = 1000
CHUNKS_ON_X = WORLD_WIDTH // CHUNK_SIZE
CHUNKS_ON_Y = WORLD_HIGHT // CHUNK_SIZE

# temporary test image
img = pygame.image.load("tarane/watter.png")
img = pygame.transform.scale(img, (CHUNK_SIZE, CHUNK_SIZE))

# dictionary for lazy-loaded chunks
tiles = {}  # key = (cx, cy), value = Chunk object

seed_obj = {
    "x": [
        1000, 500, 1200, 800, 1600, 2500, 3200, 4000, 4700, 5200,
        6000, 6800, 7500, 8200, 8900, 9500, 10200, 11000, 11800, 12500,
        13200, 14000, 14800, 15500, 16200, 17000, 17600, 18200, 18800, 19500,
        2000, 3400, 5600, 7200, 9100, 10400, 11600, 12800, 13900, 15000,
        16100, 17200, 18300, 19400, 2050, 4100, 6050, 8150, 10200, 12100
    ],
    "y": [
        1500, 750, 1800, 200, 1100, 2600, 3400, 4200, 5100, 5900,
        6600, 7400, 8100, 8900, 9600, 10300, 11100, 11900, 12600, 13400,
        14100, 14900, 15700, 16400, 17100, 17900, 18600, 19200, 19800, 20200,
        2800, 4600, 6300, 7700, 9400, 10800, 12100, 13300, 14400, 15500,
        16600, 17700, 18800, 19900, 2350, 4750, 6900, 9050, 11250, 13750
    ],
    "size": [
        300, 150, 450, 200, 350, 500, 400, 600, 250, 300,
        550, 200, 400, 300, 500, 450, 350, 600, 200, 500,
        250, 300, 550, 400, 600, 450, 500, 350, 250, 300,
        500, 600, 450, 200, 300, 350, 400, 500, 250, 600,
        300, 450, 500, 550, 200, 350, 600, 400, 450, 500
    ],
    "temp": [
        3, 7, 1, 9, 5, 2, 6, 8, 4, 10,
        1, 5, 7, 2, 9, 3, 6, 8, 4, 10,
        2, 7, 5, 3, 9, 1, 6, 8, 4, 10,
        5, 2, 8, 7, 1, 9, 6, 4, 3, 10,
        7, 2, 6, 9, 5, 1, 4, 8, 3, 10
    ]
}


def temp_to_color(temp):
    """
    Approximate mk48.io color palette
    """
    if temp <= 1:   # Deep water
        return (25, 60, 150)
    elif temp == 2: # Shallow water
        return (40, 100, 190)
    elif temp == 3: # Beach / sand
        return (210, 200, 120)
    elif temp == 4: # Light grass
        return (130, 190, 90)
    elif temp == 5: # Normal grass
        return (100, 160, 70)
    elif temp == 6: # Darker grass
        return (70, 130, 50)
    elif temp == 7: # Light forest
        return (50, 110, 40)
    elif temp == 8: # Dense forest
        return (30, 90, 30)
    elif temp == 9: # Rocky / mountain
        return (110, 110, 110)
    else:           # Snow / ice cap
        return (230, 230, 230)


class Chunk:
    def __init__(self, cx, cy, chunk_size):
        self.cx = cx
        self.cy = cy
        self.size = chunk_size
        self.surf = pygame.Surface((chunk_size, chunk_size), flags=pygame.SRCALPHA)
        #self.surf.fill((40 + (cx*5) % 200, 80 + (cy*5) % 150, 40, 255))
        self.surf.blit(img, (0,0))
        self._scaled = None
        self._last_zoom = None
        self.generate_terrain()

    def scaled_surface(self, zoom):
        if self._last_zoom != zoom or self._scaled is None:
            w = max(1, int(self.size * zoom))
            h = max(1, int(self.size * zoom))
            self._scaled = pygame.transform.scale(self.surf, (w, h))
            self._last_zoom = zoom
        return self._scaled

    def generate_terrain(self):
        pass

def get_chunk(cx, cy):
    if (cx, cy) not in tiles:
        tiles[(cx, cy)] = Chunk(cx, cy, CHUNK_SIZE)
        print(f"Created chunk {cx},{cy}")
    return tiles[(cx, cy)]

class GameCamera:
    def __init__(self, display_surface, chunk_size):
        self.display_surface = display_surface
        self.chunk_size = chunk_size
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = 1.0

    def set_zoom(self, level):
        self.zoom = max(0.1, level)

    def camera_render(self, target_x, target_y, zoom=1.0):
        self.set_zoom(zoom)
        W, H = self.display_surface.get_size()
        z = self.zoom

        self.offset_x = -target_x * z + W // 2
        self.offset_y = -target_y * z + H // 2

        world_left   = -self.offset_x / z
        world_top    = -self.offset_y / z
        world_right  = world_left + W / z
        world_bottom = world_top + H / z

        min_cx = max(0, int(math.floor(world_left / CHUNK_SIZE)))
        max_cx = min(CHUNKS_ON_X - 1, int(math.floor(world_right / CHUNK_SIZE)))
        min_cy = max(0, int(math.floor(world_top / CHUNK_SIZE)))
        max_cy = min(CHUNKS_ON_Y - 1, int(math.floor(world_bottom / CHUNK_SIZE)))

        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                chunk = get_chunk(cx, cy)
                surf = chunk.scaled_surface(z)
                screen_x = cx * CHUNK_SIZE * z + self.offset_x
                screen_y = cy * CHUNK_SIZE * z + self.offset_y
                self.display_surface.blit(surf, (screen_x, screen_y))

