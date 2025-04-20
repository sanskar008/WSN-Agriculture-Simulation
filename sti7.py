import pygame
import math
import random

# --- Configuration ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
UPDATE_INTERVAL = 3000  # update sensor readings every 3 seconds
COMM_RANGE = 300        # define maximum distance to draw connection lines

# --- Helper Function ---
def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

# --- Sensor Node Classes ---

class SensorNode:
    def __init__(self, id, pos, node_type):
        """
        node_type: string identifying the node type: 'Env', 'Soil', or 'Relay'
        """
        self.id = id
        self.pos = pos
        self.node_type = node_type
        self.last_update = pygame.time.get_ticks()
        self.readings = {}  # dictionary to store simulated sensor readings
        self.update_readings()
    
    def update_readings(self):
        now = pygame.time.get_ticks()
        if now - self.last_update >= UPDATE_INTERVAL:
            if self.node_type == 'Env':
                # Node 1: Environmental sensing
                self.readings['Luminosity'] = random.randint(200, 1000)   # in lux
                self.readings['UV'] = round(random.uniform(0.5, 5.0), 2)    # UV index or mW/cm²
                self.readings['Pressure'] = random.randint(72000, 73000)    # in Pa
            elif self.node_type == 'Soil':
                # Node 2: Soil and air conditions
                self.readings['Soil Humidity'] = random.randint(30, 70)     # percentage
                self.readings['Air Temp'] = random.randint(15, 35)          # degree Celsius
                self.readings['Air Humidity'] = random.randint(40, 80)      # percentage
            elif self.node_type == 'Relay':
                # Node 3: Relay / routing node; simulating connectivity (e.g., RSSI)
                self.readings['RSSI'] = random.randint(-90, -30)            # RSSI in dBm
            self.last_update = now

    def draw(self, surface, font):
        # Represent different nodes with different colors and icons
        if self.node_type == 'Env':
            color = (255, 0, 0)  # red for environmental node
            label = "Node 1 (Env)"
        elif self.node_type == 'Soil':
            color = (0, 200, 0)  # green for soil/node
            label = "Node 2 (Soil)"
        elif self.node_type == 'Relay':
            color = (255, 165, 0)  # orange for relay
            label = "Node 3 (Relay)"
        
        # Draw a circle for the node
        pygame.draw.circle(surface, color, self.pos, 20)
        # Draw the label above the node (now in white)
        text = font.render(label, True, (255, 255, 255))
        surface.blit(text, (self.pos[0] - text.get_width() // 2, self.pos[1] - 50))
        
        # Display sensor readings below the node (now in white)
        y_offset = self.pos[1] + 25
        for key, value in self.readings.items():
            reading_text = font.render(f"{key}: {value}", True, (255, 255, 255))
            surface.blit(reading_text, (self.pos[0] - reading_text.get_width() // 2, y_offset))
            y_offset += 20

class CoordinatorNode:
    def __init__(self, pos):
        self.pos = pos
        self.collected_data = {}  # store the latest data from each sensor node

    def update_data(self, sensor_nodes):
        # For simulation, just collect the current readings from all nodes
        for node in sensor_nodes:
            self.collected_data[f"Node {node.id}"] = node.readings.copy()

    def draw(self, surface, font):
        # Draw coordinator as a larger blue square
        rect = pygame.Rect(self.pos[0] - 25, self.pos[1] - 25, 50, 50)
        pygame.draw.rect(surface, (0, 0, 255), rect)
        # Coordinator label stays white
        label = font.render("Coordinator", True, (255, 255, 255))
        surface.blit(label, (self.pos[0] - label.get_width() // 2, self.pos[1] - 40))
        
        # Draw collected sensor data on the side (now in white)
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

    # Load background image for the field
    try:
        background = pygame.image.load("field2.jpg")
        background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception as e:
        print("Error loading image:", e)
        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background.fill((200, 255, 200))  # fallback plain green field

    # Create sensor nodes with fixed positions:
    sensor_nodes = [
        SensorNode(1, (150, 100), "Env"),
        SensorNode(2, (150, 500), "Soil"),
        SensorNode(3, (750, 100), "Relay")
    ]
    # Place the coordinator node at bottom-right
    coordinator = CoordinatorNode((750, 500))

    running = True
    while running:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update sensor node readings
        for node in sensor_nodes:
            node.update_readings()

        # Coordinator collects data from each node
        coordinator.update_data(sensor_nodes)

        # Draw everything:
        screen.blit(background, (0, 0))

        # Draw connection lines
        for node in sensor_nodes:
            if distance(node.pos, coordinator.pos) < COMM_RANGE:
                pygame.draw.line(screen, (0, 0, 0), node.pos, coordinator.pos, 2)

        # Draw sensor nodes
        for node in sensor_nodes:
            node.draw(screen, font)

        # Draw the coordinator node
        coordinator.draw(screen, font)

        # Refresh the display
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    run_simulation()
