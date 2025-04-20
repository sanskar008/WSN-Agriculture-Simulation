import pygame
import math
import random

# --- Configuration ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
UPDATE_INTERVAL = 3000  # update sensor readings every 3 seconds
COMM_RANGE = 300        # define maximum distance to draw connection lines
PACKET_SPEED = 100      # pixels per second for packet animation
PACKET_SIZE = 12        # packet size
PACKET_COLOR = (0, 0, 0)  # black for packets
PACKET_OUTLINE_COLOR = (255, 255, 255)  # white outline for contrast

# --- Helper Function ---
def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

# --- Packet Class ---
class Packet:
    def __init__(self, source_pos, dest_pos):
        self.source_pos = source_pos
        self.dest_pos = dest_pos
        self.progress = 0.0  # 0.0 = at source, 1.0 = at destination
        self.pos = list(source_pos)  # current position
        self.time = 0.0  # for pulsing effect

    def update(self, dt):
        # Update progress
        self.progress += (PACKET_SPEED * dt) / distance(self.source_pos, self.dest_pos)
        if self.progress >= 1.0:
            self.progress = 1.0
        # Interpolate position
        self.pos[0] = self.source_pos[0] + (self.dest_pos[0] - self.source_pos[0]) * self.progress
        self.pos[1] = self.source_pos[1] + (self.dest_pos[1] - self.source_pos[1]) * self.progress
        # Update time for pulsing
        self.time += dt

    def is_arrived(self):
        return self.progress >= 1.0

    def draw(self, surface):
        # Pulsing effect: size varies between 10 and 14
        pulse_size = PACKET_SIZE + 2 * math.sin(self.time * 5)
        # Draw white outline (slightly larger)
        pygame.draw.circle(surface, PACKET_OUTLINE_COLOR, (int(self.pos[0]), int(self.pos[1])), int(pulse_size + 2))
        # Draw main packet
        pygame.draw.circle(surface, PACKET_COLOR, (int(self.pos[0]), int(self.pos[1])), int(pulse_size))

# --- Sensor Node Classes ---
class SensorNode:
    def __init__(self, id, pos, node_type):
        self.id = id
        self.pos = pos
        self.node_type = node_type
        self.last_update = pygame.time.get_ticks()
        self.readings = {}
        self.update_readings()
        self.last_packet_time = self.last_update

    def update_readings(self):
        now = pygame.time.get_ticks()
        if now - self.last_update >= UPDATE_INTERVAL:
            if self.node_type == 'Env':
                self.readings['Luminosity'] = random.randint(200, 1000)
                self.readings['UV'] = round(random.uniform(0.5, 5.0), 2)
                self.readings['Pressure'] = random.randint(72000, 73000)
            elif self.node_type == 'Soil':
                self.readings['Soil Humidity'] = random.randint(30, 70)
                self.readings['Air Temp'] = random.randint(15, 35)
                self.readings['Air Humidity'] = random.randint(40, 80)
            elif self.node_type == 'Relay':
                self.readings['RSSI'] = random.randint(-90, -30)
            self.last_update = now

    def should_send_packet(self):
        now = pygame.time.get_ticks()
        if now - self.last_packet_time >= UPDATE_INTERVAL:
            self.last_packet_time = now
            return True
        return False

    def draw(self, surface, font):
        if self.node_type == 'Env':
            color = (255, 0, 0)
            label = "Node 1 (Env)"
        elif self.node_type == 'Soil':
            color = (0, 200, 0)
            label = "Node 2 (Soil)"
        elif self.node_type == 'Relay':
            color = (255, 165, 0)
            label = "Node 3 (Relay)"
        
        pygame.draw.circle(surface, color, self.pos, 20)
        text = font.render(label, True, (255, 255, 255))
        surface.blit(text, (self.pos[0] - text.get_width() // 2, self.pos[1] - 50))
        
        y_offset = self.pos[1] + 25
        for key, value in self.readings.items():
            reading_text = font.render(f"{key}: {value}", True, (255, 255, 255))
            surface.blit(reading_text, (self.pos[0] - reading_text.get_width() // 2, y_offset))
            y_offset += 20

class CoordinatorNode:
    def __init__(self, pos):
        self.pos = pos
        self.collected_data = {}

    def update_data(self, sensor_nodes):
        for node in sensor_nodes:
            self.collected_data[f"Node {node.id}"] = node.readings.copy()

    def draw(self, surface, font):
        rect = pygame.Rect(self.pos[0] - 25, self.pos[1] - 25, 50, 50)
        pygame.draw.rect(surface, (0, 0, 255), rect)
        label = font.render("Coordinator", True, (255, 255, 255))
        surface.blit(label, (self.pos[0] - label.get_width() // 2, self.pos[1] - 40))
        
        start_y = 20
        header = font.render("Coordinator Data:", True, (255, 255, 255))
        surface.blit(header, (SCREEN_WIDTH - 250, start_y))
        start_y += 25
        for node_id, readings in self.collected_data.items():
            node_label = font.render(node_id + ":", True, (255, 255, 255))
            surface.blit(node_label, (SCREEN_WIDTH - 250, start_y))
            start_y += 20
            for key, value in readings.items():
                data_text = font.render(f"{key}: {value}", True, (255, 255, 255))
                surface.blit(data_text, (SCREEN_WIDTH - 240, start_y))
                start_y += 20
            start_y += 10

# --- Main Simulation ---
def run_simulation():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("WSN Agricultural Field Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 16)

    # Load background image
    try:
        background = pygame.image.load("field2.jpg")
        background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception as e:
        print("Error loading image:", e)
        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background.fill((200, 255, 200))

    # Create nodes
    sensor_nodes = [
        SensorNode(1, (150, 100), "Env"),
        SensorNode(2, (150, 500), "Soil"),
        SensorNode(3, (750, 100), "Relay")
    ]
    coordinator = CoordinatorNode((750, 500))

    packets = []

    running = True
    while running:
        dt = clock.tick(30) / 1000.0

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update sensor nodes and generate packets
        for node in sensor_nodes:
            node.update_readings()
            if node.should_send_packet() and distance(node.pos, coordinator.pos) < COMM_RANGE:
                packets.append(Packet(node.pos, coordinator.pos))

        # Update packets
        for packet in packets[:]:
            packet.update(dt)
            if packet.is_arrived():
                packets.remove(packet)

        # Coordinator collects data
        coordinator.update_data(sensor_nodes)

        # Draw everything
        screen.blit(background, (0, 0))

        # Draw connection lines
        for node in sensor_nodes:
            if distance(node.pos, coordinator.pos) < COMM_RANGE:
                pygame.draw.line(screen, (0, 0, 0), node.pos, coordinator.pos, 2)

        # Draw nodes
        for node in sensor_nodes:
            node.draw(screen, font)
        coordinator.draw(screen, font)

        # Draw packets last for visibility
        for packet in packets:
            packet.draw(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run_simulation()