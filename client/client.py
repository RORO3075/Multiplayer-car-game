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
        self.connected = False

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
pygame.init()
screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Multiplayer Racing Game")
clock = pygame.time.Clock()

client = Client()

rooms = discover_rooms()
if rooms:
    print("Found rooms:", rooms)
    client.connect(rooms[0]["host"])   # auto-join first found
else:
    print("No rooms found.")

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
    screen.fill((30, 30, 30))
    for p in client.players:
        x = max(0, min(960, p["x"]))
        y = max(0, min(660, p["y"]))
        pygame.draw.rect(screen, (0,255,0), (x, y, 40, 40))
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))
        help_text = font.render("Use Arrow Keys to Move", True, (200,200,200))
        screen.blit(help_text, (10, 40))
        status = "Connected" if client.connected else "Disconnected"
        status_text = font.render(f"Status: {status}", True, (255,255,0))
        screen.blit(status_text, (10, 70))




    pygame.display.flip()
    clock.tick(60)

pygame.quit()
client.running = False
