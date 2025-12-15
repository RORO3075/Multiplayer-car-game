import socket
import threading
import json
import pygame
from pygame import mixer
import time
import random

DISCOVERY_PORT = 50001
TCP_PORT = 50000

# Discover rooms
def discover_rooms(timeout=1.5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(0.4)

    found = []
    start = time.time()

    while time.time() - start < timeout:
        sock.sendto(b"DISCOVER_ROOM", ("<broadcast>", DISCOVERY_PORT))
        try:
            data, addr = sock.recvfrom(1024)
            info = json.loads(data.decode())
            found.append(info)
        except:
            pass

    return found

# Car sprite generation - TOP DOWN VIEW
def generate_car_sprite(color):
    """Generate a top-down car sprite"""
    surf = pygame.Surface((40, 40), pygame.SRCALPHA)
    
    # Main body (rectangle, top-down view)
    pygame.draw.rect(surf, color, (10, 5, 20, 30))
    
    # Front bumper (darker)
    pygame.draw.rect(surf, (100, 100, 100), (8, 3, 24, 2))
    
    # Windows (light blue)
    pygame.draw.rect(surf, (100, 150, 255), (12, 8, 16, 6))
    pygame.draw.rect(surf, (100, 150, 255), (12, 18, 16, 6))
    
    # Left wheels
    pygame.draw.rect(surf, (30, 30, 30), (6, 10, 4, 6))
    pygame.draw.rect(surf, (30, 30, 30), (6, 24, 4, 6))
    
    # Right wheels
    pygame.draw.rect(surf, (30, 30, 30), (30, 10, 4, 6))
    pygame.draw.rect(surf, (30, 30, 30), (30, 24, 4, 6))
    
    # Headlights (small circles at front)
    pygame.draw.circle(surf, (255, 255, 0), (14, 4), 1)
    pygame.draw.circle(surf, (255, 255, 0), (26, 4), 1)
    
    return surf

# Pre-generate car sprites
car_sprites = {
    "green": generate_car_sprite((0, 255, 0)),
    "blue": generate_car_sprite((0, 0, 255))
}


class Obstacle:
    def __init__(self, x, y, width=60, height=40):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = 3 
    
    def update(self):
        self.y += self.speed
    
    def draw(self, screen):
        pygame.draw.rect(screen, (255, 50, 50), (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, (200, 0, 0), (self.x, self.y, self.width, self.height), 2)
    
    def is_offscreen(self):
        return self.y > 700


class SoundManager:
    def __init__(self):
        mixer.init()
        self.sounds = {}
        self.load_sounds()
    
    def load_sounds(self):
        try:
            self.sounds['connect'] = mixer.Sound('client/sounds/connect.mp3')
            self.sounds['move'] = mixer.Sound('client/sounds/movement.mp3')
            self.sounds['error'] = mixer.Sound('client/sounds/error.mp3')
        except FileNotFoundError:
            print("[SOUND] Sound files not found, using generated sounds")
    
    def play(self, sound_name):
        try:
            if sound_name in self.sounds and self.sounds[sound_name]:
                self.sounds[sound_name].play()
        except Exception as e:
            print(f"[SOUND] Error playing sound {sound_name}: {e}")

class Client:
    def __init__(self):
        self.sock = None
        self.players = []
        self.running = True
        self.error = None

    def connect(self, host, room_code):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, TCP_PORT))

        join_msg = json.dumps({
            "type": "join",
            "room_code": room_code
        }) + "\n"

        self.sock.sendall(join_msg.encode())
        threading.Thread(target=self.recv_loop, daemon=True).start()


    def recv_loop(self):
        buf = b""
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break

                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    msg = json.loads(line.decode())

                    if msg["type"] == "welcome":
                        self.id = msg["id"]

                    elif msg["type"] == "error":
                        self.error = msg.get("message", "Server not found")
                        self.running = False
                        self.sock.close()
                        return

                    elif msg["type"] == "state":
                        self.players = msg["players"]

            except:
                break
            


    def send_input(self, dx, dy):
        msg = json.dumps({"dx": dx, "dy": dy}) + "\n"
        try:
            self.sock.sendall(msg.encode())
        except:
            pass

sound_mgr = SoundManager()
# ---------------------- PYGAME LOOP ----------------------

def main_menu(screen):
    pygame.font.init()
    font = pygame.font.Font(None, 56)
    small = pygame.font.Font(None, 32)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_1]:
            return "random"
        if keys[pygame.K_2]:
            return "custom"
        if keys[pygame.K_3]:
            return "create"

        screen.fill((20, 20, 20))

        screen.blit(font.render("Multiplayer Racing", True, (255,255,255)), (300, 180))
        screen.blit(small.render("1 - Join Random Room", True, (200,200,200)), (360, 280))
        screen.blit(small.render("2 - Join Custom Room", True, (200,200,200)), (360, 320))
        screen.blit(small.render("3 - Create Room", True, (200,200,200)), (360, 360))

        pygame.display.flip()
        clock.tick(60)

def fade_transition(screen, duration=0.5, fade_out=True):
    clock = pygame.time.Clock()
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        progress = min(elapsed / duration, 1.0)
        
        if fade_out:
            alpha = int(255 * progress)
        else:
            alpha = int(255 * (1 - progress))
        
        fade_surface = pygame.Surface((1000, 700))
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)
        
        if progress >= 1.0:
            break

def join_room_menu(screen):
    pygame.font.init()
    font = pygame.font.Font(None, 48)
    small = pygame.font.Font(None, 32)
    clock = pygame.time.Clock()

    room_code = ""

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(room_code) > 0:
                    return room_code.upper()

                elif event.key == pygame.K_BACKSPACE:
                    room_code = room_code[:-1]

                elif len(room_code) < 4 and event.unicode.isalnum():
                    room_code += event.unicode.upper()

        screen.fill((25, 25, 25))

        title = font.render("Join Room", True, (255, 255, 255))
        code = font.render(room_code or "____", True, (0, 255, 0))
        hint = small.render("Type Room Code & Press ENTER", True, (180, 180, 180))

        screen.blit(title, (420, 200))
        screen.blit(code, (450, 300))
        screen.blit(hint, (330, 380))

        pygame.display.flip()
        clock.tick(60)

def error_screen(screen, message):
    font = pygame.font.Font(None, 48)
    small = pygame.font.Font(None, 28)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return  # go back to menu

        screen.fill((30, 0, 0))

        screen.blit(font.render("Connection Failed", True, (255, 80, 80)), (300, 260))
        screen.blit(small.render(message, True, (255, 255, 255)), (300, 320))
        screen.blit(small.render("Press ESC to return", True, (200, 200, 200)), (300, 360))

        pygame.display.flip()
        clock.tick(60)

def draw_player_list(screen, players):
    font = pygame.font.Font(None, 28)

    sidebar_x = 780

    pygame.draw.rect(
        screen,
        (35, 35, 35),
        (sidebar_x, 0, 220, 700)
    )

    title = font.render("Players", True, (255, 255, 255))
    screen.blit(title, (sidebar_x + 60, 20))

    y = 60
    for p in players:
        txt = font.render(p["id"], True, (0, 255, 0))
        screen.blit(txt, (sidebar_x + 40, y))
        y += 28

pygame.init()
screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Multiplayer Racing Game")
clock = pygame.time.Clock()

while True:
    client = Client()

    choice = main_menu(screen)

    if choice == "random":
        rooms = discover_rooms()
        room_code = rooms[0]["room_code"]
        if not rooms:
            error_screen(screen, "No rooms found")
            continue
        sound_mgr.play('connect')
        fade_transition(screen, duration=0.5, fade_out=True)
        fade_transition(screen, duration=0.5, fade_out=False)
        client.connect(rooms[0]["host"], rooms[0]["room_code"])

    elif choice == "custom":
        room_code = join_room_menu(screen)
        sound_mgr.play('connect')
        fade_transition(screen, duration=0.5, fade_out=True)
        fade_transition(screen, duration=0.5, fade_out=False)
        client.connect("127.0.0.1", room_code)
        
        time.sleep(0.5)

        if client.error:
            sound_mgr.play('error')
            fade_transition(screen, duration=0.5, fade_out=True)
            fade_transition(screen, duration=0.5, fade_out=False)
            error_screen(screen, client.error)
            continue

    elif choice == "create":
        sound_mgr.play('connect')
        rooms = discover_rooms()
        room_code = rooms[0]["room_code"]
        fade_transition(screen, duration=0.5, fade_out=True)
        fade_transition(screen, duration=0.5, fade_out=False)
        client.connect("127.0.0.1", room_code)

    break


running = True
font = pygame.font.SysFont(None, 24)
playing_sounds = {}
obstacles = []
spawn_counter = 0
spawn_rate = 30

while running:
    dx = dy = 0

    # Process events once per frame
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # LEFT key
    if keys[pygame.K_LEFT]:
        dx = -5
        if 'move_left' not in playing_sounds and 'move' in sound_mgr.sounds:
            sound = sound_mgr.sounds['move']
            sound.play(-1)
            playing_sounds['move_left'] = sound
    else:
        if 'move_left' in playing_sounds:
            playing_sounds['move_left'].stop()
            del playing_sounds['move_left']

    # RIGHT key
    if keys[pygame.K_RIGHT]:
        dx = 5
        if 'move_right' not in playing_sounds and 'move' in sound_mgr.sounds:
            sound = sound_mgr.sounds['move']
            sound.play(-1)
            playing_sounds['move_right'] = sound
    else:
        if 'move_right' in playing_sounds:
            playing_sounds['move_right'].stop()
            del playing_sounds['move_right']

    # UP key
    if keys[pygame.K_UP]:
        dy = -5
        if 'move_up' not in playing_sounds and 'move' in sound_mgr.sounds:
            sound = sound_mgr.sounds['move']
            sound.play(-1)
            playing_sounds['move_up'] = sound
    else:
        if 'move_up' in playing_sounds:
            playing_sounds['move_up'].stop()
            del playing_sounds['move_up']

    # DOWN key
    if keys[pygame.K_DOWN]:
        dy = 5
        if 'move_down' not in playing_sounds and 'move' in sound_mgr.sounds:
            sound = sound_mgr.sounds['move']
            sound.play(-1)
            playing_sounds['move_down'] = sound
    else:
        if 'move_down' in playing_sounds:
            playing_sounds['move_down'].stop()
            del playing_sounds['move_down']

    # Always send input and update world each frame
    client.send_input(dx, dy)

    spawn_counter += 1
    if spawn_counter >= spawn_rate:
        random_x = random.randint(0, 740)
        obstacles.append(Obstacle(random_x, -40))
        spawn_counter = 0

    for obs in obstacles:
        obs.update()

    obstacles = [obs for obs in obstacles if not obs.is_offscreen()]

    # Background gradient
    for yy in range(700):
        shade = 30 + int(40 * (yy / 700))
        pygame.draw.line(screen, (shade, shade, shade), (0, yy), (1000, yy))

    # Draw obstacles
    for obs in obstacles:
        obs.draw(screen)

    for p in client.players:
        if p["id"] == client.id:
            car_sprite = car_sprites["blue"]
        else:
            car_sprite = car_sprites["green"]
        p["x"] = max(0, min(p["x"], 740))
        p["y"] = max(0, min(p["y"], 660))
        screen.blit(car_sprite, (p["x"], p["y"]))
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))
        help_text = font.render("Use Arrow Keys to Move", True, (200,200,200))
        screen.blit(help_text, (10, 40))
        status = "Connected" if client.connect else "Disconnected"
        status_text = font.render(f"Status: {status}", True, (255,255,0))
        screen.blit(status_text, (10, 70))
        room_text = font.render(f"Room: {room_code}", True, (255,255,255))
        screen.blit(room_text, (10, 670))

        draw_player_list(screen, client.players)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
client.running = False
