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

    def connect(self, host):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, TCP_PORT))
        threading.Thread(target=self.recv_loop, daemon=True).start()
        self.connected = True

    def recv_loop(self):
        buf = b""
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    self.connected = False
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    msg = json.loads(line.decode())
                    if msg["type"] == "welcome":
                        self.id = msg["id"]
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
    font = pygame.font.Font(None, 56)
    small = pygame.font.Font(None, 32)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "join"
                if event.key == pygame.K_2:
                    return "create"

        screen.fill((20, 20, 20))

        title = font.render("Multiplayer Racing", True, (255, 255, 255))
        join = small.render("Press 1 : Join Room", True, (200, 200, 200))
        create = small.render("Press 2 : Create Room (Localhost)", True, (200, 200, 200))

        screen.blit(title, (350, 200))
        screen.blit(join, (380, 300))
        screen.blit(create, (340, 350))

        pygame.display.flip()
        clock.tick(60)

pygame.init()
screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Multiplayer Racing Game")
clock = pygame.time.Clock()

client = Client()

choice = main_menu(screen)

if choice == "join":
    rooms = discover_rooms()
    room_code = rooms[0]["room_code"]
    if rooms:
        print("Found rooms:", rooms)
        client.connect(rooms[0]["host"])
    else:
        print("No rooms found.")
        pygame.quit()
        exit()

elif choice == "create":
    client.connect("127.0.0.1")
    room_code = "ROOM123"


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

        pygame.draw.rect(screen, color, (p["x"], p["y"], 40, 40))
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))
        help_text = font.render("Use Arrow Keys to Move", True, (200,200,200))
        screen.blit(help_text, (10, 40))
        status = "Connected" if client.connected else "Disconnected"
        status_text = font.render(f"Status: {status}", True, (255,255,0))
        screen.blit(status_text, (10, 70))
        room_text = font.render(f"Room: {room_code}", True, (255,255,255))
        screen.blit(room_text, (850, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
client.running = False
