
#from cam import Chunk, get_chunk, GameCamera
import math
import pygame
import random
import time
import json
import numpy as np
import os



with open("planes/levels.json","r") as file:
    levels = json.load(file)
level1 = levels["level1"]
level2 = levels['level2']
with open("data/settings.json","r") as file:
    settings_data = json.load(file)
with open("data/death_msgs.json","r") as file:
    death_msgs = json.load(file)
with open("data/game_data.json","r") as file:
    game_data = json.load(file)



pygame.init()
runing = True

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

def color_swap(surface: pygame.Surface, old_color: tuple, new_color: tuple) -> pygame.Surface:
    arr_rgb = pygame.surfarray.array3d(surface)
    arr_alpha = pygame.surfarray.array_alpha(surface)
    mask = np.all(arr_rgb == old_color, axis=-1)
    arr_rgb[mask] = new_color
    new_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA, 32)
    new_surface = new_surface.convert_alpha()
    pygame.surfarray.blit_array(new_surface, arr_rgb)
    pygame.surfarray.pixels_alpha(new_surface)[:] = arr_alpha
    return new_surface


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

        if len(seed_obj['x']) == len(seed_obj['y']):
            chunk_rect = pygame.Rect(self.cx * self.size, self.cy * self.size, self.size, self.size)
            for land in seed_obj['x']:
                land_rect = pygame.Rect(land, seed_obj['y'][seed_obj['x'].index(land)], seed_obj['size'][seed_obj['x'].index(land)], seed_obj['size'][seed_obj['x'].index(land)])
                if chunk_rect.colliderect(land_rect):
                    land_color = temp_to_color(seed_obj['temp'][seed_obj['x'].index(land)])
                    pygame.draw.ellipse(self.surf, land_color, land_rect.move(-chunk_rect.x, -chunk_rect.y))

def get_chunk(cx, cy):
    #Return chunk at (cx, cy), create if it doesn’t exist yet.
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


loops = 0
window = pygame.display.set_mode((1500,750))
if not pygame.display.is_fullscreen():
    pygame.display.toggle_fullscreen()

display = pygame.Surface((1500,750))
display_rect = display.get_rect(center=(window.get_width() // 2, window.get_height() // 2))
window_width = window.get_width()
window_height = window.get_height()
scale = min(window_width / display.get_width(), window_height / display.get_height())
new_size = (int(display.get_width() * scale), int(display.get_height() * scale))
W_pos = ((window_width - new_size[0]) // 2, (window_height - new_size[1]) // 2)

disp_ico = pygame.image.load("planes/pt-17.png")
pygame.display.set_icon(disp_ico)
display.fill((49, 104, 158))
center_x = display.get_width() / 2
center_y = display.get_height() / 2
camra = GameCamera(display,CHUNK_SIZE)
clock = pygame.Clock()

text_font = pygame.font.SysFont("Arial", 20)
text_font_big = pygame.font.SysFont("Arial", 50)

def disp_text(text, font, color, x, y):
    img = font.render(text, True, color)
    rect = img.get_rect(center=(x, y))
    display.blit(img, rect)
    return rect

def play_sound(file_path, volume=0.5):
    pygame.mixer_music.load(file_path)
    pygame.mixer_music.set_volume(vol + 0.5)
    pygame.mixer_music.play(-1)

# init game_data
menue_buttone_data = game_data['buttons']
for button in menue_buttone_data:
    bimg = pygame.image.load(button['image_path']).convert_alpha()
    bimg = pygame.transform.scale(bimg, (button['sizex'], button['sizey']))
    button['image'] = bimg

class PacketBuilder:
    @staticmethod
    def build(tick, planes, bullets, particles, ais):
        return {
            "T": "tick",
            "tick": tick % 32767,
            "P": [p.to_dict() for p in planes],
            "B": [b.to_dict() for b in bullets],
            "p": [px.to_dict() for px in particles],
            "AI": [ai.to_dict() for ai in ais]
        }

    @staticmethod
    def to_json(packet_dict):
        return json.dumps(packet_dict)

    @staticmethod
    def from_json(packet_str):
        return json.loads(packet_str)


class Parical():
    def __init__(self,WT,x,y,direction,user_name=None,NW_OW="server"):
        self.NW_OW = NW_OW
        self.WT = WT
        self.x = x
        self.y = y
        with open(f"images/{WT}.json") as file:
            data = json.load(file)
        self.data = data
        self.amount = data['amount']
        self.sizex = data['sizex']
        self.sizey = data['sizey']
        self.life_time = data['life_time']
        self.original_image = pygame.image.load(f"images/{WT}.png")
        self.image = pygame.transform.scale(self.original_image,(self.sizex,self.sizey))
        self.original_image = pygame.transform.scale(self.original_image,(self.sizex,self.sizey))
        self.rect = self.image.get_rect(center=(500, 350))
        self.current_scaled_image = self.image
        self.owner = user_name
        self.screen_rect = self.rect
        self.player_dist = 0
        self.update(display,camra)

    def to_dict(self):
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "ang": 0, 
            "LT": int(self.life_time),
            "PT": self.WT,
            "o": self.NW_OW
        }

    def load_frome_paket(self, data):
        self.x = data['x']
        self.y = data['y']
        self.life_time = data['LT']
        self.WT = data['PT']
        self.owner = data['O']
        self.NW_OW = data['o']
        with open(f"images/{self.WT}.json") as file:
            data = json.load(file)
        self.data = data
        self.amount = data['amount']
        self.sizex = data['sizex']
        self.sizey = data['sizey']
        self.life_time = data['life_time']
        self.original_image = pygame.image.load(f"images/{self.WT}.png")
        self.image = pygame.transform.scale(self.original_image,(self.sizex,self.sizey))
        self.original_image = pygame.transform.scale(self.original_image,(self.sizex,self.sizey))
        self.rect = self.image.get_rect(center=(500, 350))
        self.current_scaled_image = self.image
        self.owner = user_name
        self.screen_rect = self.rect
        self.player_dist = 0

    def update_player_dist(self):
        global player1
        dx = self.x - player1.x
        dy = self.y - player1.y
        self.player_dist = math.hypot(dx, dy)
        

    def update(self, display_surface, camera_obj):
        self.life_time -= 1
        if loops % 8 == 2:
            self.update_player_dist()
        self.screen_rect = self.current_scaled_image.get_rect(center=((self.x+ camra.offset_x), (self.y+ camra.offset_y)))
        display_surface.blit(self.current_scaled_image, self.screen_rect)
        return self.screen_rect

    def blit(self,display_surface):
        display_surface.blit(self.current_scaled_image,self.screen_rect)

class AI():
    def __init__(self,all_planes,all_bullets,all_xp,NW_OW="server"):
        global player1
        self.NW_OW = NW_OW
        with open("data/ai_names.json","r") as file:
            plane_names = json.load(file)
        self.all_xp = all_xp
        self.all_planes = all_planes
        self.plane = Plane(random.choice(plane_names['names']),random.choice(level1),NW_OW=NW_OW)
        self.fired = self.plane.fired
        #self.health = self.plane.health
        self.target = None
        all_planes.append(self.plane)
        self.all_planes.remove(self.plane)
        self.target = self.find_target(self.all_planes,800)
        self.confidance = 0
        self.rand1 = random.randint(-2,30)
        self.rand2 = random.randint(-32,32)
        self.un_loaded_ticks = 0
        self.player_dist = 0

    def to_dict(self):
        return {
            "PD": int(self.player_dist),
            "ULT": int(self.un_loaded_ticks),
            "r1": self.rand1,
            "r2": self.rand2,
            "o": self.NW_OW
        }

    def update_player_dist(self):
        global player1
        dx = self.plane.x - player1.x
        dy = self.plane.y - player1.y
        self.player_dist = math.hypot(dx, dy)

    def find_target(self, all_objects, distance):
        # Only consider planes within a certain distance
        nearby = [obj for obj in all_objects if math.hypot(obj.x - self.plane.x, obj.y - self.plane.y) <= distance and obj.PT != "pNone"]
        if not nearby:
            return None
        # Find the closest
        return min(nearby, key=lambda obj: math.hypot(obj.x - self.plane.x, obj.y - self.plane.y))

    def whay_ops(self):
        if self.target != None:
            C_health = self.plane.health - self.target.health
            C_top_speed = self.plane.top_speed - self.target.top_speed
            C_turn_speed = self.plane.turn_speed - self.target.turn_speed
            C_fire_speed = self.plane.fire_speed - self.target.fire_speed
            C_armor = self.plane.armor - self.target.armor
            C_acceleration = self.plane.acceleration - self.target.acceleration
            B_health = 1 if C_health >= 0 else 0
            B_top_speed = 1 if C_top_speed >= 0 else 0
            B_turn_speed = 1 if C_turn_speed >= 0 else 0
            B_fire_speed = 1 if C_fire_speed >= 0 else 0
            B_armor = 1 if C_armor >= 0 else 0
            B_acceleration = 1 if C_acceleration >= 0 else 0
            average_score = (B_health + B_top_speed + B_turn_speed +
                             B_fire_speed + B_armor + B_acceleration) / 6
            return average_score
        else:
            return 0

    def whay_xp(self,dist=300):
        #auglobal all_xp,xp_cluster,all_planes
        #conf = len(xp_cluster) / len(all_xp)
        return 0
  
    def find_xp(self):
        global all_xp,xp_cluster
        for obj in xp_cluster:
            dx = obj[0] - self.plane.x
            dy = obj[1] - self.plane.y
            dist = math.hypot(dx, dy)
            try:
                if dist < closest_dist and dist <= dist:
                    target,closest = obj,obj
                    closest_dist = dist
            except Exception:
                closest_dist = dist
                target = obj
                # Calculate relative position
        dx = (target[0]) - self.plane.x
        dy = (target[1]) - self.plane.y
        distance = math.hypot(dx, dy)

        # Angle to the target (in degrees)
        angle_to_target = (math.degrees(math.atan2(-dx, -dy)) + 360) % 360
        angle_diff = (angle_to_target - self.plane.angle + 360) % 360
        if angle_diff > 180:
            angle_diff -= 360  # Convert to range -180 to 180

        # Speed difference
        speed_diff = self.plane.speed - 0

        # Turning decision
        if angle_diff > 10:
            leftRite = 1  # turn right
        elif angle_diff < -10:
            leftRite = 2  # turn left
        else:
            leftRite = 0  # aligned enough

        # Forward/back decision
        if distance > 250 and speed_diff < 0:
            frontBack = 1  # go faster to catch up
        elif distance < 150 and speed_diff > 0:
            frontBack = 2  # slow down
        else:
            frontBack = 0  # maintain speed

        # Fire if roughly aligned and within shooting range
        if abs(angle_diff) < 5 and distance < 300:
            spaceShif = 1
        else:
            spaceShif = 0

        # num_k can be used to indicate level of confidence, or tactic mode
        num_k = 1 if spaceShif == 1 else 0

        return frontBack, leftRite, spaceShif, num_k

    def attack(self, target):
        
        amount = self.target.speed * self.rand1
        direction = self.target.angle
        rad = math.radians(direction)
        delta_x = -amount * math.sin(rad)
        delta_y = -amount * math.cos(rad)

        # Calculate relative position
        dx = (target.x+delta_x) - self.plane.x
        dy = (target.y+delta_y) - self.plane.y
        distance = math.hypot(dx, dy)

        # Angle to the target (in degrees)
        angle_to_target = (math.degrees(math.atan2(-dx, -dy)) + 360) % 360
        angle_diff = (angle_to_target - self.plane.angle + 360) % 360
        if angle_diff > 180:
            angle_diff -= 360  # Convert to range -180 to 180

        # Speed difference
        speed_diff = self.plane.speed - target.speed

        # Turning decision
        if angle_diff > 10:
            leftRite = 1  # turn right
        elif angle_diff < -10:
            leftRite = 2  # turn left
        else:
            leftRite = 0  # aligned enough

        # Forward/back decision
        if distance > 250 and speed_diff < 0:
            frontBack = 1  # go faster to catch up
        elif distance < 150 and speed_diff > 0:
            frontBack = 2  # slow down
        else:
            frontBack = 0  # maintain speed

        # Fire if roughly aligned and within shooting range
        if abs(angle_diff) < 5 and distance < 300:
            spaceShif = 1
        else:
            spaceShif = 0

        # num_k can be used to indicate level of confidence, or tactic mode
        num_k = 1 if spaceShif == 1 else 0

        return frontBack, leftRite, spaceShif, num_k

    def run(self, target_plane):
        leftRite = 0

        amount = self.target.speed * self.rand2
        direction = self.target.angle
        rad = math.radians(direction)
        delta_x = -amount * math.sin(rad)
        delta_y = -amount * math.cos(rad)

        angle = self.plane.angle % 360
        dx = (target_plane.x+delta_x) - self.plane.x
        dy = (target_plane.y+delta_y) - self.plane.y
        distance = math.hypot(dx, dy)
        angle = (math.degrees(math.atan2(-dx, -dy)) + 360) % 360

        angle_to_target = (math.degrees(math.atan2(-dx, -dy)) + 360) % 360
        angle_diff = (angle_to_target - self.plane.angle + 360) % 360
        if angle_diff > 180:
            angle_diff -= 360 

        # Turning decision
        if angle_diff > 10:
            leftRite = 2  
        elif angle_diff < -10:
            leftRite = 1  
        else:
            leftRite = 0 

        return leftRite
      
    def choose_op(self):
        choice = 0
        frontBack, leftRite, spaceShif, num_k = 0,0,0,0
        if loops % 2 == 0:
            self.confidance = self.whay_ops()
        if loops % 8 == 4:
            self.update_player_dist()
            self.target = self.find_target(self.all_planes,800)
        xp_conf = self.whay_xp()
        if self.target != None:

            if self.confidance >= 0.6 and xp_conf <= self.confidance:
                print(f"{self.plane.PT} is atacking PT>{self.target.PT}")
                frontBack, leftRite, spaceShif, num_k = self.attack(self.target)
                self.plane.ai_event(loops,frontBack, leftRite, spaceShif, 0)
            elif xp_conf >= 0.6:
                print("colecting xp")
                self.plane.ai_event(loops,frontBack, leftRite, spaceShif, 0)
            else:
                print("runing")
                leftRite = self.run(self.target)
                frontBack = 1
                self.plane.ai_event(loops,frontBack, leftRite, spaceShif, 0)
        else:
            if xp_conf >= 0.5:
                print("gathering xp")
                frontBack, leftRite, spaceShif, num_k = self.find_xp()
                self.plane.ai_event(loops,frontBack, leftRite, spaceShif, 0)
            else:
                print("wandering")
                self.plane.ai_event(loops,frontBack, leftRite, spaceShif, 0)

class Wepons():
    def __init__(self,WT,x,y,direction,user_name,NW_OW="server"):
        self.NW_OW = NW_OW
        self.WT = WT
        self.x = x
        self.y = y
        self.angle = direction
        with open(f"wepons/wepon_stats/{WT}.json") as file:
            data = json.load(file)
        self.data = data
        self.speed = data['speed']
        self.damage = data['damage']
        self.sizex = data['sizex']
        self.sizey = data['sizey']
        self.life_time = data['life_time']
        self.fire_sound = data['fire_sound']
        self.hit_sound = data['hit_sound']
        if self.data['extra_BC'] >= 1:
            self.life_time += random.randint(0,self.data['extra_BLT']*self.data['extra_BC'])
        rad = math.radians(direction)
        delta_x = -self.speed * math.sin(rad)
        delta_y = -self.speed * math.cos(rad)
        self.x += delta_x
        self.y += delta_y
        self.dx = delta_x
        self.dy = delta_y
        self.Roriginal_image = pygame.image.load(f"wepons/{WT}.png")
        self.image = pygame.transform.scale(self.Roriginal_image,(self.sizex,self.sizey))
        self.original_image = pygame.transform.scale(self.Roriginal_image,(self.sizex,self.sizey))
        self.original_image = pygame.transform.rotate(self.original_image, direction)
        self.rect = self.image.get_rect(center=(500, 350))
        self.owner = user_name
        self.screen_rect = self.rect
        self.dist = 0
        self.scaled_width = int(self.original_image.get_width() * camra.zoom)
        self.scaled_height = int(self.original_image.get_height() * camra.zoom)

        self.has_ai = False
        self.turn_speed = 0
        self.target = None
        self.rect.center = (self.x, self.y)
        if WT in settings_data['wepons_with_ai']:
            self.turn_speed = data['turn_speed']
            self.has_ai = True
            self.target = self.find_closest_target(simulation_dist)

    def to_dict(self):
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "ang": round(self.angle, 2),
            "LT": int(self.life_time),
            "BT": self.WT,
            "O": self.owner,
            "o": self.NW_OW
        }

    def update_player_dist(self):
        global player1
        dx = self.x - player1.x
        dy = self.y - player1.y
        self.dist = math.hypot(dx, dy)

    def update(self, display_surface, camera_obj):
        self.x += self.dx
        self.y += self.dy
        self.life_time -= 1
        if loops % 5 == 1:
            self.update_player_dist()
        #screen_rect = self.original_image.get_rect(center=(self.x + camera_obj.offset_x, self.y + camera_obj.offset_y))
        display_surface.blit(self.original_image, self.original_image.get_rect(center=(self.x + camera_obj.offset_x, self.y + camera_obj.offset_y)))
        return 0 #screen_rect

    def scater(self):
        global all_bullets,display,camra
        BT = self.data["extra_BT"]
        BC = self.data["extra_BC"]
        for B in range((BC)):
            bullet = Wepons(BT,self.x,self.y,random.randint(0,360),self.owner)
            bullet.life_time = self.data['extra_BLT']
            all_bullets.append(bullet)
          
    def fire(self):
        #global vol
        max_vol = vol + 1
        max_dist = 2000
        clamped_dist = min(self.dist, max_dist)
        volume_factor = 1.0 - (clamped_dist / max_dist)
        calculated_volume = max_vol * volume_factor
        final_volume = max(0.0, min(max_vol, calculated_volume))
        sound = pygame.mixer.Sound((f"sounds/{self.fire_sound}.mp3"))
        sound.set_volume(final_volume)
        sound.play()

    def hit(self):
        dx = self.x - player1.x
        dy = self.y - player1.y
        self.dist = math.hypot(dx, dy)
        max_vol = vol + 0.3
        max_dist = 1000
        clamped_dist = min(self.dist, max_dist)
        volume_factor = 1.0 - (clamped_dist / max_dist)
        calculated_volume = max_vol * volume_factor
        final_volume = max(0.0, min(max_vol, calculated_volume))
        sound = pygame.mixer.Sound((f"sounds/{self.hit_sound}.mp3"))
        sound.set_volume(final_volume)
        sound.play()

class Plane():

    def __init__(self,user_name,PT,NW_OW="server"):
        global all_bullets,player1,WORLD_HIGHT,WORLD_WIDTH
        self.NW_OW = NW_OW
        self.user_name = user_name
        self.angle = 0
        self.speed = 1
        self.x = random.randint(100,WORLD_WIDTH-100)
        self.y = random.randint(100,WORLD_HIGHT-100)
        self.PT = PT
        try:
            with open(f"planes/stats/{PT}.json") as file:
                data = json.load(file)
        except Exception:
            with open(f"planes/stats/{PT}.json") as file:
                data = json.load(file)
        self.data = data
        self.acceleration = data['acceleration']
        self.armor = data['armor']
        self.fire_speed = data['fire_speed']
        self.max_health = data['health']
        self.health = self.max_health
        self.reload_speed = data['reload_speed']
        self.sizex = data['sizex']
        self.sizey = data['sizey']
        self.top_speed = data['top_speed']
        self.min_speed = data['min_speed']
        self.turn_speed = data['turn_speed']
        self.wepons = data['wepons']
        self.wepon = self.wepons[0]
        self.wepon_amounts = data['wepon_amounts']
        self.xp_value = data['xp_value']
        self.curent_leval = data['leval']
        self.C_amo = self.wepon_amounts[0]
        self.original_image = pygame.image.load(f"planes/{PT}.png")
        self.image = pygame.transform.scale(self.original_image,(self.sizex,self.sizey))
        self.original_image = pygame.transform.scale(self.original_image,(self.sizex,self.sizey))
        self.Rect = self.image.get_rect(center=(center_x, center_y))
        self.screen_rect = self.Rect
        self.num = 0
        self.xp = 0
        self.fired = 0
        self.death_cause = ["None",""]

    def respawn(self,PT,op_data=None):
        self.PT = PT
        if op_data == None:
            with open(f"planes/stats/{PT}.json") as file:
                data = json.load(file)
        else:
            data = op_data
        self.acceleration = data['acceleration']
        self.armor = data['armor']
        self.fire_speed = data['fire_speed']
        self.max_health = data['health']
        self.health = self.max_health
        self.reload_speed = data['reload_speed']
        self.sizex = data['sizex']
        self.sizey = data['sizey']
        self.top_speed = data['top_speed']
        self.min_speed = data['min_speed']
        self.turn_speed = data['turn_speed']
        self.wepons = data['wepons']
        if self.wepons != []:
            self.wepon = self.wepons[0]
        self.wepon_amounts = data['wepon_amounts']
        self.xp_value = data['xp_value']
        self.curent_leval = data['leval']
        if self.wepon_amounts != []:
            self.C_amo = self.wepon_amounts[0]
        self.original_image = pygame.image.load(f"planes/{PT}.png")
        self.image = pygame.transform.scale(self.original_image,(self.sizex,self.sizey))
        self.original_image = pygame.transform.scale(self.original_image,(self.sizex,self.sizey))
        self.Rect = self.image.get_rect(center=(center_x, center_y))
        self.data = data
        self.death_cause = ["None",""]

    def pacager(self,mods):
        # this is for packaging data to send over the network
        pass

    def to_dict(self):
        return {
            "id": self.user_name,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "ang": round(self.angle, 2),
            "H": int(self.health),
            "PT": self.PT,
            "o": self.NW_OW
        }

    def rotate(self):
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.Rect = self.image.get_rect(center=(center_x, center_y))

    def blit(self):
        global camra_zoom
        if not self.health <= 0:
            camra.camera_render(self.x, self.y)
            display.blit(self.image, self.Rect.topleft)
            print(f"{self.user_name}s health is {self.health}")
        else:
            camra.camera_render(self.x, self.y,camra_zoom)
            return True
        rec = disp_text(self.user_name,text_font,(0,10,0),self.Rect.centerx,self.Rect.y -30)
        pygame.draw.rect(display,(0,100,0),(center_x-self.health/2,rec.y+30,self.health,10),border_radius=3)

    def drop_xp(self):
        global all_xp
        for i in range(int((self.xp_value/settings_data['death_xp_amount']) + (self.xp/settings_data['death_xp_amount'])/8 )):
            XP = Parical("death_xp",self.x+random.randint(0,self.sizex),self.y+random.randint(0,self.sizey),0,self.user_name)
            XP.update(display,camra)
            all_xp.append(XP)

    def move(self):
        amount = self.speed
        direction = self.angle
        rad = math.radians(direction)
        delta_x = -amount * math.sin(rad)
        delta_y = -amount * math.cos(rad)
        self.x += delta_x
        self.y += delta_y
        
    def wep(self,num):
        if num != None:
            num -= 1
            WL = len(self.wepons)
            num = (num % WL)
            self.wepon = self.wepons[num]
            self.C_amo = self.wepon_amounts[num]
            self.num = num

    def fire(self):
        global all_bullets,display,camra
        if (self.fired) <= self.C_amo:
            B1 = Wepons(self.wepon,self.x,self.y,self.angle,self.user_name)
            B1.fire()
            all_bullets.append(B1)
            self.fired += 1

    def update_bullets(self,all_bullets,owners_bullets=False):
        self.screen_rect = self.image.get_rect(center=(self.x, self.y))
        for bullet in all_bullets:
                bullet.screen_rect = bullet.image.get_rect(center=(bullet.x, bullet.y))
                if bullet.owner != self.user_name:
                    if bullet.screen_rect.colliderect(self.screen_rect):#(self.x,self.y,self.sizex,self.sizey)
                        self.health -= bullet.damage / self.armor
                        bullet.hit()
                        bullet.life_time = 0
                        if self.health <= 0:
                            self.death_cause = ["shot_down",bullet.owner]
                elif bullet.owner == self.user_name:
                    if bullet.life_time <= 0:
                        if bullet.data["extra_BC"] >= 1:
                            bullet.scater()
                            self.fired += 1
                        self.fired -= 1
                        all_bullets.remove(bullet)
                        del bullet
            
    def collect_xp(self):
        global all_xp
        for Xp in all_xp:
            Xp.blit(display)
            if self.Rect.colliderect(Xp.screen_rect):
                self.xp += Xp.amount
                pygame.draw.rect(display,(255,0,0),Xp.screen_rect)
                Xp.life_time = 0

    def display_death_msg(self):
        global death_msgs,display
        try:
            msg = death_msgs[self.death_cause[0]]
            msg = msg.format(player=self.death_cause[1])
        except Exception:
            msg = f"you died = {self.death_cause[0]}"
        disp_text(msg, text_font_big, (255, 0, 0), center_x, center_y-100)
                         
    def event(self,loops):
        global all_planes,R_menue_G,button_rects,respawn_lev,heal_amount,settings_data,vol
        presed = False
        num = None
        button = pygame.key.get_pressed()
        if button[pygame.K_w]:
            if self.speed <= self.top_speed:
                self.speed += self.acceleration
            presed = True
        elif button[pygame.K_s]:
            if self.speed > self.min_speed:
                self.speed -= self.acceleration
            elif self.speed < self.min_speed:
                self.speed = self.min_speed
            presed = True
        if button[pygame.K_a]:
            self.angle += self.turn_speed
            self.rotate()
            presed = True
        elif button[pygame.K_d]:
            self.angle -= self.turn_speed
            self.rotate()
            presed = True
        if button[pygame.K_SPACE]:
            if loops % self.fire_speed == 0:
                self.fire()

        if self.speed > self.top_speed:
            self.speed -= self.acceleration

        if button[pygame.K_1]:
            num = 1
        elif button[pygame.K_2]:
            num = 2
        elif button[pygame.K_3]:
            num = 3
        elif button[pygame.K_4]:
            num = 4
        elif button[pygame.K_5]:
            num = 5
        elif button[pygame.K_6]:
            num = 6
        elif button[pygame.K_7]:
            num = 7
        elif button[pygame.K_8]:
            num = 8
        elif button[pygame.K_9]:
            num = 9
        elif button[pygame.K_0]:
            num = 10

        self.wep(num)
        self.move()
        if loops % 4 == 0:
            #self.clean()
            #  HARD BORDER ENFORCEMENT
            out_of_bounds = False
            if self.x < 0:
                out_of_bounds = True
            elif self.x > WORLD_WIDTH:
                out_of_bounds = True
            if self.y < 0:
                out_of_bounds = True
            elif self.y > WORLD_HIGHT:
                out_of_bounds = True
            if out_of_bounds:
                self.health = 0
                if self.health <= 0 and self.PT != "pNone":
                    self.death_cause = ["out_of_bounds",""]
                    disp_text("you died ", text_font_big, (255, 0, 0), center_x, center_y-100)
            # ----------------------
        if self.xp >= self.xp_value and self.health < self.data["health"] and heal_amount == 10:
            self.xp -= heal_amount/5
            self.xp = int(self.xp)
            self.health += heal_amount/5
          
        if self.health <= 0 and self.PT != "pNone":
            self.respawn("pNone")
            obj = all_planes.index(self)
            all_planes[obj].PT = "pNone"
            pygame.mixer_music.load(f"sounds/{random.choice(settings_data['death_songs'])}")
            pygame.mixer_music.set_volume(vol + 1)
            pygame.mixer_music.play()
            respawn_lev = None
            button_rects = []
            R_menue_G = None
            

            self.drop_xp()

        print(f"user >{self.user_name} is at x>{self.x} y>{self.y}")
        print(f"the speed is {self.speed}")
        self.blit()
        return presed

    def ai_move(self):
        amount = self.speed
        rad = math.radians(self.angle)
        delta_x = -amount * math.sin(rad)
        delta_y = -amount * math.cos(rad)
        self.x += delta_x
        self.y += delta_y

    def ai_blit(self, display_surface, camera_obj):
        if self.health <= 0:
            return

        scaled_width = int(self.original_image.get_width() * camera_obj.zoom)
        scaled_height = int(self.original_image.get_height() * camera_obj.zoom)

        if scaled_width > 0 and scaled_height > 0:
            scaled_image = pygame.transform.scale(self.original_image, (scaled_width, scaled_height))
        else:
            scaled_image = pygame.Surface((1,1))

        rotated_image = pygame.transform.rotate(scaled_image, self.angle)
        rect = rotated_image.get_rect()
    
        screen_x = (self.x * camera_obj.zoom) + camera_obj.offset_x
        screen_y = (self.y * camera_obj.zoom) + camera_obj.offset_y
        rect.center = (screen_x, screen_y)

        display_surface.blit(rotated_image, rect)

        # Optional: Draw name above AI plane
        rec = disp_text(self.user_name, text_font, (0, 0, 0), rect.centerx, rect.top - 15)
        pygame.draw.rect(display,(0,100,0),(rect.centerx-self.health/2,rec.y+30,self.health,10),border_radius=3)

    def ai_event(self,loops,frontBack,leftRite,spaceShif,num_k):
        global all_planes
        presed = False
        num = None
        if frontBack == 1:
            if self.speed <= self.top_speed:
                self.speed += self.acceleration
            presed = True
        elif frontBack == 2:
            if self.speed > self.min_speed:
                self.speed -= self.acceleration
            elif self.speed < self.min_speed:
                self.speed = self.min_speed
            presed = True
        if leftRite == 1:
            self.angle += self.turn_speed
            self.rotate()
            presed = True
        elif leftRite == 2:
            self.angle -= self.turn_speed
            self.rotate()
            presed = True
        if spaceShif == 1:
            if loops % self.fire_speed == 0:
                self.fire()
        elif spaceShif == 2:
            print("shift is not bound")

        if num_k == 1:
            num = 1
        elif num_k == 2:
            num = 2
        elif num_k == 3:
            num = 3
        elif num_k == 4:
            num = 4
        elif num_k == 5:
            num = 5
        elif num_k == 6:
            num = 6
        elif num_k == 7:
            num = 7
        elif num_k == 8:
            num = 8
        elif num_k == 9:
            num = 9
        elif num_k == 10:
            num = 10

        self.wep(num)
        self.ai_move()   
        if loops % 4 == 0:
            #self.clean()
            #  HARD BORDER ENFORCEMENT
            out_of_bounds = False
            if self.x < 0:
                out_of_bounds = True
            elif self.x > WORLD_WIDTH:
                out_of_bounds = True
            if self.y < 0:
                out_of_bounds = True
            elif self.y > WORLD_HIGHT:
                out_of_bounds = True
            if out_of_bounds:
                self.health -= 1
            # ----------------------
        self.ai_blit(display,camra)
        if self.health <= 0 and self.PT != "pNone":
            self.respawn("pNone")
            obj = all_planes.index(self)
            all_planes[obj].PT = "pNone"
            self.xp = self.xp / 2
            self.drop_xp()

        if self.xp >= self.xp_value and self.health < self.data["health"] and heal_amount == 10:
            self.xp -= heal_amount/1.5
            self.xp = int(self.xp)
            self.health += heal_amount/5

        print(f"AI>{self.user_name} is at x>{self.x} y>{self.y} at speed {self.speed}")
        print(f"AI>{self.user_name}s health is {self.health}")
        return presed

def event():
    global runing,g,text,Menue,camra_zoom,all_xp,R_menue_G,player1,button_rects,respawn_lev,vol,settings_data,all_planes,all_ais,levels,vol,mouse_pos,UI
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runing = False
        if event.type == pygame.KEYDOWN:
            if settings_data["dev_ops"] == 1:
                if event.key == pygame.K_r:
                    player1.health += 20
                if event.key == pygame.K_f:
                    player1.speed += 50
                if event.key == pygame.K_k:
                    Xp = Parical("xp",player1.x+100,player1.y+100,0)
                    Xp.update(display,camra)
                    all_xp.append(Xp)
                if event.key == pygame.K_p:
                    ai = AI(all_planes,all_bullets,all_xp)
                    all_ais.append(ai)
                    ai.plane.x = player1.x + random.randint(-200,200)
                    ai.plane.y = player1.y + random.randint(-200,200)
                    all_planes.append(ai.plane)
                elif event.key == pygame.K_x:
                    for ai in all_ais:
                        ai.plane.health = 0
                if event.key == pygame.K_LSHIFT:
                    lev = random.choice(levels["levels"])
                    PT = random.choice(levels[lev])
                    player1.respawn(PT)

            if event.key == pygame.K_ESCAPE:
                Menue = 0
                pygame.mixer_music.stop()
                pygame.mixer.music.stop()
                main_channel.stop()
                pygame.mixer.music.load(random.choice(menue_songs))
                pygame.mixer.music.set_volume(vol + 1)
                pygame.mixer_music.play(-1)
            if event.key == pygame.K_F3:
                if UI == 0:
                    UI = 1
                elif UI == 1:
                    UI = 0
                else:
                    UI = 0

            if event.key == pygame.K_v:
                vol += 0.1
            elif event.key == pygame.K_b:
                vol -= 0.1

        if event.type == pygame.MOUSEBUTTONDOWN:
          if R_menue_G != None and respawn_lev != None:
            for p in button_rects:
                    pos = mouse_pos #pygame.mouse.get_pos()
                    rec = p[1]
                    plane = p[0]
                    rec_pos = p[2]
                    rec.x = rec_pos[0] + (center_x-R_menue_G.get_width()/2)
                    rec.y = rec_pos[1] + 20
                    if rec.collidepoint(pos[0],pos[1]):
                        print(f"player ->{player1.user_name} is leveling up to {plane}")
                        player1.respawn(plane)
                        player1.xp -= player1.curent_leval * lev_data["level_amount"]
                        respawn_lev = None
                        button_rects = []
                        R_menue_G = None
                        sound = pygame.mixer.Sound("sounds/f79c30ab-003b-48ea-af96-b131c00ecddb.mp3")
                        sound.set_volume(vol + 0.7)
                        sound.play()
                        break

def Game():
    global runing,g,text,Menue,camra_zoom,all_xp,R_menue_G,player1,button_rects,respawn_lev,vol,settings_data,all_planes,all_ais,levels,vol,mouse_pos,UI,heal_amount,loops
    heal_amount = random.randint(0,20)
    player1.event(loops)
    manage_xp()
    manage_ais()
    update_B(all_bullets)
    player1.update_bullets(all_bullets)
    player1.collect_xp()

    if loops % 8:
        respawn_check(player1,False)
        all_planes = get_ranked_planes()
        """
        packet = PacketBuilder.build(loops, all_planes, all_bullets, all_xp, all_ais)
        with open(f"logs/sent_packets/_P-{loops}.json", "w") as f:
            f.write(PacketBuilder.to_json(packet))
            print(f"logs/sent_packets/_P-{loops}.json   was sucsesfuly saved")
        """
    if respawn_lev != None and R_menue_G != None:
        display.blit(R_menue_G,(center_x-R_menue_G.get_width()/2,20))
    event()
    if settings_data["dev_ops"] == 1:
        disp_text(f"FPS -> {int(clock.get_fps())}",text_font,(0,0,0),100,10)
    if UI == 1:
        wW ,hH = text_font.size("1 th ashjkjhgfdsdfghjhgfdfhjkg has 19093 xp: ") 
        pygame.draw.rect(display,(100,100,100),(display.get_width()-wW,25,display.get_width(),230),border_radius=10)
        pygame.draw.rect(display,(50,50,50),(display.get_width()-wW,25,display.get_width(),230),width= 4,border_radius=10)
        for plane_ind in range(10):
            wW,hH = text_font.size(f"{plane_ind+1}th : {((all_planes[plane_ind % len(all_planes)].user_name))} has {(all_planes[plane_ind % len(all_planes)].xp)} xp")
            disp_text(f"{plane_ind+1}th : {((all_planes[plane_ind % len(all_planes)].user_name))} has {(all_planes[plane_ind % len(all_planes)].xp)} xp     ",text_font,(0,0,0),display.get_width()-(wW/2),50+(plane_ind*20))

    disp_text(f"XP -> {int(player1.xp)}",text_font,(0,0,0),100,50)
    disp_text(f"x: {int(player1.x)} y: {int(player1.y)}",text_font,(0,0,0),100,70)
    wepons_menue()

    packet = PacketBuilder.build(loops, all_planes, all_bullets, all_xp, all_ais)

def main_menue():
    global runing,g,text,typing,user_name,Menue,player1,all_planes,R_menue_G,player1,button_rects,respawn_lev,vol,mouse_pos
    DT = "enter username"
    if text != "":
        DT = text

    # text box
    pygame.draw.rect(display,(100,100,100,100),(center_x-200,center_y-50,400,50),border_radius=20)
    pygame.draw.rect(display,(50,50,50,0),(center_x-200,center_y-50,400,50),width= 4,border_radius=15)
    disp_text(DT,pygame.font.SysFont("Arial", 25),(80,80,80),center_x,center_y-25)
    img = pygame.image.load("pt-17.png")
    img = pygame.transform.scale(img,(40,40))
    img = pygame.transform.rotate(img, -45)
    display.blit(img,(center_x-220,center_y-80))
    # play button
    play_rect = pygame.rect.Rect(center_x-100,center_y+10,200,60)
    display.blit(menue_buttone_data[0]["image"].convert_alpha(),(menue_buttone_data[0]['x'],menue_buttone_data[0]['y']))
    # setings button
    settintg_rect = pygame.draw.rect(display,(100,150,100),(display.get_width()-200,display.get_height()-50,150,30),border_radius=3)
    pygame.draw.rect(display,(50,100,50),(display.get_width()-200,display.get_height()-50,150,30),width= 2,border_radius=3)
    disp_text("settings ",text_font,(7,0,0),display.get_width()-150,display.get_height()-36)
    # qit button
    quit_rect = pygame.draw.rect(display,(150,50,50),(10,display.get_height()-50,150,30),border_radius=6)
    display.blit(menue_buttone_data[2]["image"].convert_alpha(),(menue_buttone_data[2]['x'],menue_buttone_data[2]['y']))
    # how to play button
    how_to_play_rect = pygame.draw.rect(display,(100,100,100),(display.get_width()-200,display.get_height()-100,150,30),border_radius=3)
    display.blit(menue_buttone_data[1]["image"].convert_alpha(),(menue_buttone_data[1]['x'],menue_buttone_data[1]['y']))
    
    disp_text("your plane will be randomly selected from level 1",text_font,(100,0,0),center_x,10)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runing = False
        if typing:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                elif event.key == pygame.K_RETURN:
                    if text != "" and text != " ":
                        Menue = 1
                        user_name = text
                        display.fill([49, 104, 158])
                        player1 = Plane(text,random.choice(level1))

                        all_planes.append(player1)
                        pygame.mixer_music.stop()
                        try:
                            pygame.mixer_music.stop()
                            pygame.mixer_music.load("sounds/game_song1.mp3")
                            pygame.mixer_music.set_volume(vol + 0.5)
                            pygame.mixer_music.play(-1)
                        except Exception:
                            print("error starting sound thread")
                else:
                    if len(text) <= 24 and event.key != pygame.K_ESCAPE:
                        text += event.unicode
                if event.key == pygame.K_ESCAPE:
                    pygame.display.toggle_fullscreen()
                    camra.camera_render(random.randint(0, int(float(WORLD_WIDTH) / 1.1)),random.randint(0,int(float(WORLD_HIGHT) / 1.1)))
                if event.key == pygame.K_v:
                    vol += 0.1
                elif event.key == pygame.K_b:
                    vol -= 0.1
        if event.type == pygame.MOUSEBUTTONDOWN:
            #mouse_pos = event.pos
            mouse_button = event.button
            if play_rect.collidepoint(mouse_pos[0],mouse_pos[1]) and mouse_button == 1 and text != "" and text != " ":
                Menue = 1
                user_name = text
                display.fill([49, 104, 158])
                if player1 != None:
                    xp = player1.xp
                else:
                    xp = 0
                player1 = Plane(user_name,random.choice(level1))
                player1.xp = xp
                all_planes.append(player1)
                pygame.mixer_music.stop()

            if settintg_rect.collidepoint(mouse_pos[0],mouse_pos[1]) and mouse_button == 1:
                #  settings_menue()
                Menue = 2
                camra.camera_render(random.randint(0, int(float(WORLD_WIDTH) / 1.1)),random.randint(0,int(float(WORLD_HIGHT) / 1.1)))
                print("settings was presed")
            if quit_rect.collidepoint(mouse_pos[0],mouse_pos[1]) and mouse_button == 1:
                runing = False
                print("quiting game")
            if how_to_play_rect.collidepoint(mouse_pos[0],mouse_pos[1]) and mouse_button == 1:
                Menue = 3
                camra.camera_render(random.randint(0, int(float(WORLD_WIDTH) / 1.1)),random.randint(0,int(float(WORLD_HIGHT) / 1.1)))
                print("how to play was presed")

def settings_menue():
    global runing,g,text,typing,user_name,Menue,settings_data,typing,text,mouse_pos
    #display.fill([49, 104, 158])

    with open("data/settings.json","r") as file:
        data = json.load(file)

    back_rect = pygame.draw.rect(display,(150,100,100),(display.get_width()-200,display.get_height()-50,150,30),border_radius=3)
    pygame.draw.rect(display,(50,50,50),(display.get_width()-200,display.get_height()-50,150,30),width= 2,border_radius=3)
    disp_text("back",text_font,(7,0,0),display.get_width()-150,display.get_height()-36)

    dev_ops_rect = pygame.draw.rect(display,(100,100,100),(display.get_width()-200,display.get_height()-100,150,30),border_radius=3)
    pygame.draw.rect(display,(50,50,50),(display.get_width()-200,display.get_height()-100,150,30),width= 2,border_radius=3)
    D_I = data["dev_ops"]
    disp_text(f"dev ops {D_I}",text_font,(7,0,0),display.get_width()-150,display.get_height()-86)

    ai_count_rect = pygame.draw.rect(display,(100,150,100),(display.get_width()-200,display.get_height()-150,150,30),border_radius=3)
    pygame.draw.rect(display,(50,100,50),(display.get_width()-200,display.get_height()-150,150,30),width= 2,border_radius=3)
    disp_text(f"max ai {data['max_ais']}",text_font,(7,0,0),display.get_width()-150,display.get_height()-136)

    more_ai_rect = pygame.draw.rect(display,(100,100,100),(display.get_width()-200,display.get_height()-200,150,30),border_radius=3)
    pygame.draw.rect(display,(50,50,50),(display.get_width()-200,display.get_height()-200,150,30),width= 2,border_radius=3)
    disp_text("more ai",text_font,(7,0,0),display.get_width()-150,display.get_height()-186)

    less_ai_rect = pygame.draw.rect(display,(100,100,100),(display.get_width()-200,display.get_height()-250,150,30),border_radius=3)
    pygame.draw.rect(display,(50,50,50),(display.get_width()-200,display.get_height()-250,150,30),width= 2,border_radius=3)
    disp_text("less ai",text_font,(7,0,0),display.get_width()-150,display.get_height()-236)

    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runing = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                Menue = 0
                camra.camera_render(random.randint(0, int(float(WORLD_WIDTH) / 1.1)),random.randint(0,int(float(WORLD_HIGHT) / 1.1)))

        if event.type == pygame.MOUSEBUTTONDOWN:
            #mouse_pos = event.pos
            mouse_button = event.button
            if mouse_button == 1 and back_rect.collidepoint(mouse_pos[0],mouse_pos[1]):
                Menue = 0
                camra.camera_render(random.randint(0, int(float(WORLD_WIDTH) / 1.1)),random.randint(0,int(float(WORLD_HIGHT) / 1.1)))
            elif mouse_button == 1 and dev_ops_rect.collidepoint(mouse_pos[0],mouse_pos[1]):
                with open("data/settings.json","r") as file:
                    data = json.load(file)
                if data['dev_ops'] == 0:
                    data['dev_ops'] = 1
                else:
                    data['dev_ops'] = 0

                with open("data/settings.json","w") as file:
                    json.dump(data,file,indent=4)
                settings_data = data
            elif mouse_button == 1 and more_ai_rect.collidepoint(mouse_pos[0],mouse_pos[1]):
                with open("data/settings.json","r") as file:
                    data = json.load(file)
                    data['max_ais'] += 1
                with open("data/settings.json","w") as file:
                    json.dump(data,file,indent=4)
            elif mouse_button == 1 and less_ai_rect.collidepoint(mouse_pos[0],mouse_pos[1]):
                with open("data/settings.json","r") as file:
                    data = json.load(file)
                    if data['max_ais'] > 0:
                        data['max_ais'] -= 1
                with open("data/settings.json","w") as file:
                    json.dump(data,file,indent=4)

def how_to_play_menue():
    global runing,g,text,typing,user_name,Menue,settings_data,typing,text,mouse_pos
    display.fill([49, 104, 158])
    back_rect = pygame.draw.rect(display,(150,100,100),(display.get_width()-200,display.get_height()-50,150,30),border_radius=3)
    pygame.draw.rect(display,(50,50,50),(display.get_width()-200,display.get_height()-50,150,30),width= 2,border_radius=3)
    disp_text("back",text_font,(7,0,0),display.get_width()-150,display.get_height()-36)
    disp_text("how to play",text_font_big,(0,0,0),center_x,10)
    disp_text("W - move forward",text_font,(0,0,0),center_x-200,50)
    disp_text("S - move backward",text_font,(0,0,0),center_x-200,70)
    disp_text("A - turn left",text_font,(0,0,0),center_x-200,90)
    disp_text("D - turn right",text_font,(0,0,0),center_x-200,110)
    disp_text("SPACE - fire weapon",text_font,(0,0,0),center_x-200,130)
    disp_text("1-9 - change weapon",text_font,(0,0,0),center_x-200,150)
    disp_text("ESC - open menue",text_font,(0,0,0),center_x-200,170)
    disp_text("F3 - toggle UI",text_font,(0,0,0),center_x-200,190)
    if settings_data["dev_ops"] == 1:
        disp_text("R - heal",text_font,(0,0,0),center_x-200,210)
        disp_text("F - increase speed",text_font,(0,0,0),center_x-200,230)
        disp_text("K - give XP",text_font,(0,0,0),center_x-200,250)
        disp_text("P - spawn AI",text_font,(0,0,0),center_x-200,270)
        disp_text("X - kill all AI",text_font,(0,0,0),center_x-200,290)
        disp_text("shift for swaping your plane",text_font,(0,0,0),center_x-200,315)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runing = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                Menue = 0
                camra.camera_render(random.randint(0, int(float(WORLD_WIDTH) / 1.1)),random.randint(0,int(float(WORLD_HIGHT) / 1.1)))
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_button = event.button
            if mouse_button == 1 and back_rect.collidepoint(mouse_pos[0],mouse_pos[1]):
                Menue = 0
                camra.camera_render(random.randint(0, int(float(WORLD_WIDTH) / 1.1)),random.randint(0,int(float(WORLD_HIGHT) / 1.1)))

def respawn_menue(level,create_surf=True, p_size_x=100, p_size_y=100, y_pos=20):
    if create_surf:
        rects = []
        plane_count = len(level)
        total_sizeX = p_size_x * plane_count
        total_sizeY = p_size_y
        menu_surface = pygame.Surface((total_sizeX, total_sizeY), pygame.SRCALPHA)
        menu_surface.fill((0, 0, 0, 0)) 
        background_rect = pygame.Rect(0, 0, total_sizeX, total_sizeY)
        pygame.draw.rect(menu_surface, (100, 100, 100), background_rect, border_radius=10)
        for ind, plane in enumerate(level):
            img = pygame.image.load(f"planes/{plane}.png").convert_alpha()
            img = pygame.transform.scale(img, (p_size_x, p_size_y))
            menu_surface.blit(img, (p_size_x * ind, 0))
            rects.append([plane,img.get_rect(),(p_size_x * ind, 0)])
        print(f"planes in level >{plane_count}")
        pygame.draw.rect(menu_surface, (50, 50, 50), background_rect, width=4, border_radius=10)
        return menu_surface,rects

def wepons_menue():
    player = player1
    wep_list = player.data['wepons']
    num = player.num
    curent_wep = player.wepon
    box_width = len(wep_list) * 80
    pygame.draw.rect(display,(100,100,100),(center_x-(box_width/2),display.get_height()-85,box_width,80),border_radius=10)
    pygame.draw.rect(display,(50,50,50),(center_x-(box_width/2),display.get_height()-85,box_width,80),width= 4,border_radius=10)
    for ind,wep in enumerate(wep_list):
        img = pygame.image.load(f"wepons/{wep}.png").convert_alpha()
        img = pygame.transform.scale(img, (60, 60))
        x_pos = center_x - (box_width/2) + (ind * 80) + 10
        y_pos = display.get_height() - 75
        display.blit(img, (x_pos, y_pos))
        if wep == curent_wep:
            pygame.draw.rect(display,(0,255,0),(x_pos-5,y_pos-5,70,70),width= 4,border_radius=10)
        if ind + 1 == num:
            pygame.draw.rect(display,(255,255,0),(x_pos-5,y_pos-5,70,70),width= 4,border_radius=10)
        disp_text(f"{ind+1}",text_font,(0,0,0),x_pos+30,y_pos+65)


def respawn_check(plane,is_ai):
    global lev_data,Menue,R_menue_G,button_rects,respawn_lev,powers
    ind = -1
    plane_lev = plane.curent_leval
    next_lev = plane_lev + 1
    next_lev_amount = next_lev * lev_data['level_amount']
    plane_xp = plane.xp
    if plane.PT == "pNone":
        plane.x = random.randint(0,WORLD_WIDTH)
        plane.y = random.randint(0,WORLD_HIGHT)
        Menue = 0
        plane.xp = plane.xp/2
    if plane_xp >= next_lev_amount:
        if is_ai:
            if next_lev <= lev_data['last_level']:
                choice = random.choice(lev_data[f"level{next_lev}"])
                plane.respawn(choice)
                plane.xp -= next_lev_amount
        else:
            if next_lev <= lev_data['last_level'] and button_rects == []:
                #powers = lev_data["pow_levs"]
                
                respawn_lev = lev_data[f"level{next_lev}"]
                R_menue_G,button_rects = respawn_menue(lev_data[f"level{next_lev}"],True)
    else:
        respawn_lev = None
        button_rects = []
        R_menue_G = None

def update_ai(ai):
    global all_ais,all_bullets,all_planes,loops,all_xp
    ai.all_planes = [p for p in all_planes if p is not ai.plane]
    ai.choose_op()
    ai.plane.ai_blit(display,camra)
    ai.plane.update_bullets(all_bullets)
    ai.plane.collect_xp()
    if loops % 40 == 0 and ai.plane.xp >= 50 :
        respawn_check(ai.plane,True)
    if ai.plane.health <= 0:
        all_planes.remove(ai.plane)
        ai.plane.drop_xp()
        del ai.plane
        all_ais.remove(ai)
        del ai

def update_B(all_B):
    global simulation_dist
    for bullet in all_B:
        if bullet.dist <= simulation_dist:
            bullet.update(display,camra)
        else:
            bullet.life_time -= 3

def manage_ais():
    global all_ais,all_bullets,all_planes,loops,all_xp,settings_data,simulation_dist,player1
    if len(all_ais) <= settings_data['max_ais']:
        ai = AI(all_planes,all_bullets,all_xp)
        ai.plane.x,ai.plane.y = rand_cords(player1)
        all_ais.append(ai)
        all_planes.append(ai.plane)
    if all_ais != []:
        for ai in all_ais:
            if ai.player_dist <= simulation_dist:
                update_ai(ai)
            else:
                ai.un_loaded_ticks += 1
                if ai.un_loaded_ticks >= 150:
                    del ai.plane
                    all_ais.remove(ai)
                    del ai

def manage_xp():
    global all_xp,all_planes,settings_data,player1,simulation_dist
    if len(all_xp) <= len(all_planes)*settings_data["xpp"]:
        rx,ry = rand_cords(player1)
        Xp = Parical("xp",rx,ry,0)
        Xp.update(display,camra)
        all_xp.append(Xp)
    for xp in all_xp:
        #if xp.NW_OW == "client":
            if xp.player_dist <= simulation_dist:
                xp.update(display,camra)
                if xp.life_time <= 0:
                    all_xp.remove(xp)
                    del xp
            else:
                all_xp.remove(xp)
                del xp
                """
        else:
            if loops % 4 == 0:
                pupdate = packet['p'][all_xp.index(xp)]
                xp.load_frome_paket()
            if xp.player_dist <= simulation_dist:
                xp.update(display,camra)
                if xp.life_time <= 0:
                    all_xp.remove(xp)
                    del xp
            else:
                all_xp.remove(xp)
                del xp
        """

def get_xp_clusters(cluster_radius=50):
    """
    Returns a list of (x, y) tuples representing the center of each XP cluster.
    """
    clusters = []
    visited = set()

    def distance(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    for i, xp in enumerate(all_xp):
        if i in visited:
            continue
        cluster = [xp]
        visited.add(i)
        for j, other_xp in enumerate(all_xp):
            if j not in visited and distance(xp, other_xp) <= cluster_radius:
                cluster.append(other_xp)
                visited.add(j)

        # Calculate cluster center
        avg_x = sum(item.x for item in cluster) / len(cluster)
        avg_y = sum(item.y for item in cluster) / len(cluster)
        clusters.append((avg_x, avg_y))

    return clusters

def get_ranked_planes():
    global all_planes
    return sorted(all_planes, key=lambda plane: plane.xp, reverse=True)

def rand_cords(obj):
    global WORLD_HIGHT,WORLD_WIDTH,simulation_dist
    rand_x = random.randint(int(max(0, obj.x - simulation_dist)),int(min(WORLD_WIDTH, obj.x + simulation_dist)))
    rand_y = random.randint(int(max(0, obj.y - simulation_dist)),int(min(WORLD_HIGHT, obj.y + simulation_dist)))
    return rand_x,rand_y

with open("planes/levels.json","r") as file1:
    lev_data = json.load(file1)
              
planeT = random.choice(level1)
player1 = None
Menue = 0
text = ""
typing = True
user_name = text
all_ais,all_planes,all_bullets,all_xp,powers,xp_cluster,button_rects = [],[],[],[],[],[],[]
ai_count = 0
camra_zoom = 1
respawn_lev = None
R_menue_G = None
vol = 0
UI = 1
packet = PacketBuilder.build(loops, all_planes, all_bullets, all_xp, all_ais)
simulation_dist = 2000
menue_songs = settings_data["menue_songs"]
pygame.mixer.init()
main_channel = pygame.mixer.Channel(0)
pygame.mixer.set_num_channels(32)

mx, my = pygame.mouse.get_pos()
mouse_pos = (((mx - W_pos[0]) / scale),((my - W_pos[1]) / scale))

camra.camera_render(random.randint(0, int(float(WORLD_WIDTH) / 1.1)),random.randint(0,int(float(WORLD_HIGHT) / 1.1)))
pygame.mixer.music.load(random.choice(menue_songs))
pygame.mixer.music.set_volume(vol + 1)
pygame.mixer_music.play(-1)
main_menue()


while runing:
    mx, my = pygame.mouse.get_pos()
    mouse_pos = (((mx - W_pos[0]) / scale),((my - W_pos[1]) / scale))

    if Menue == 0:
        main_menue()
    elif Menue == 1:
        Game()
    elif Menue == 2:
        settings_menue()
    elif Menue == 3:
        how_to_play_menue()

    loops += 1
    s_display = pygame.transform.smoothscale(display, new_size)
    window.blit(s_display,W_pos)
    print(f"loops are at {loops}")
    pygame.display.flip()

    clock.tick(20.5)


