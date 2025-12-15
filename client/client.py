import socket
import threading
import json
import pygame
import time

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
        client.connect(rooms[0]["host"], rooms[0]["room_code"])

    elif choice == "custom":
        room_code = join_room_menu(screen)
        client.connect("127.0.0.1", room_code)

    elif choice == "create":
        rooms = discover_rooms()
        room_code = rooms[0]["room_code"]
        client.connect("127.0.0.1", room_code)

    
    time.sleep(0.5)

    if client.error:
        error_screen(screen, client.error)
        continue

    break


running = True
font = pygame.font.SysFont(None, 24)
while running:
    dx = dy = 0
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: dx = -5
    if keys[pygame.K_RIGHT]: dx = 5
    if keys[pygame.K_UP]: dy = -5
    if keys[pygame.K_DOWN]: dy = 5

    client.send_input(dx, dy)

    # draw
    for y in range(700):
        shade = 30 + int(40 * (y / 700))
        pygame.draw.line(screen, (shade, shade, shade), (0, y), (1000, y))

    for p in client.players:
        color = (0,255,0)
        if p["id"] == client.id:
            color = (0,0,255)  # local player blue
        p["x"] = max(0, min(p["x"], 740))
        p["y"] = max(0, min(p["y"], 660))
        pygame.draw.rect(screen, color, (p["x"], p["y"], 40, 40))
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
