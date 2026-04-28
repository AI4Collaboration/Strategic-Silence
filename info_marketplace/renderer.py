"""PyGame-based renderer for Info Marketplace visualization."""

import pygame
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class MarketplaceRenderer:
    """Renders Info Marketplace trial data to PNG frames using PyGame."""

from __future__ import annotations

    def __init__(self, trial_data: dict, sprites_dir: Path, output_dir: Path):
        """Initialize renderer with trial data and output settings.

        Args:
            trial_data: Complete trial JSON data
            sprites_dir: Path to sprites directory
            output_dir: Path to output directory for frames
        """
        # PyGame setup
        pygame.init()
        pygame.font.init()

        # Screen dimensions (16:9 aspect ratio)
        self.screen_width = 1920
        self.screen_height = 1080
        self.surface = pygame.Surface((self.screen_width, self.screen_height))

        # Fonts
        self.title_font = pygame.font.Font(None, 56)
        self.header_font = pygame.font.Font(None, 42)
        self.text_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 26)
        self.tiny_font = pygame.font.Font(None, 20)

        # Sprite cache
        self.sprite_cache = {}
        self.sprites_dir = Path(sprites_dir)

        # Trial data
        self.trial_data = trial_data
        self.condition = trial_data.get('condition', 'unknown')
        self.goals = trial_data.get('goals', [])

        # Map layout - positions for each region (centered coordinates)
        # Ring topology: Forest-River-Mines-Plains in a circle
        self.map_offset_x = 200
        self.map_offset_y = 150
        self.region_size = 380  # Size of each region area

        self.region_positions = {
            'Forest': (self.map_offset_x + 200, self.map_offset_y + 150),      # Top-left
            'River': (self.map_offset_x + 700, self.map_offset_y + 150),       # Top-right
            'Mines': (self.map_offset_x + 700, self.map_offset_y + 550),       # Bottom-right
            'Plains': (self.map_offset_x + 200, self.map_offset_y + 550)       # Bottom-left
        }

        # Settlement in the center
        self.settlement_pos = (self.map_offset_x + 450, self.map_offset_y + 350)

        # Colors
        self.BG_COLOR = (20, 25, 35)           # Dark background
        self.FOREST_COLOR = (34, 139, 34)      # Forest green
        self.RIVER_COLOR = (65, 105, 225)      # Royal blue
        self.PLAINS_COLOR = (210, 180, 140)    # Tan
        self.MINES_COLOR = (70, 70, 80)        # Dark gray
        self.TEXT_COLOR = (255, 255, 255)      # White
        self.PANEL_BG = (40, 45, 55)           # Panel background

        # Frame counter
        self.frame_count = 0

    def _load_sprite(self, name: str, size: Tuple[int, int] = None) -> Optional[pygame.Surface]:
        """Load and cache a sprite with optional resizing."""
        cache_key = f"{name}_{size}" if size else name

        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]

        sprite_path = self.sprites_dir / f"{name}.png"

        if not sprite_path.exists():
            return None

        try:
            sprite = pygame.image.load(str(sprite_path))

            if size:
                sprite = pygame.transform.scale(sprite, size)

            self.sprite_cache[cache_key] = sprite
            return sprite
        except Exception as e:
            print(f"Warning: Failed to load sprite {name}: {e}")
            return None

    def _get_region_color(self, region_name: str) -> Tuple[int, int, int]:
        """Get background color for a region."""
        colors = {
            'Forest': self.FOREST_COLOR,
            'River': self.RIVER_COLOR,
            'Plains': self.PLAINS_COLOR,
            'Mines': self.MINES_COLOR
        }
        return colors.get(region_name, self.BG_COLOR)

    def _get_tier_color(self, tier: str) -> Tuple[int, int, int]:
        """Get color for agent goal tier."""
        colors = {
            'ALIGNED': (0, 255, 0),      # Green
            'ORTHOGONAL': (255, 215, 0), # Gold
            'COMPETITIVE': (255, 0, 0)   # Red
        }
        return colors.get(tier, (255, 255, 255))

    def _get_agent_goal_tier(self, agent_name: str) -> str:
        """Get goal tier for an agent."""
        for goal in self.goals:
            if goal['agent'] == agent_name:
                return goal['tier']
        return 'UNKNOWN'

    def _get_resource_icon(self, resource_type: str) -> Optional[pygame.Surface]:
        """Map resource type to sprite icon."""
        icons = {
            'food': self._load_sprite('magic_gem', (28, 28)),      # Red gem
            'water': self._load_sprite('magic_potion', (28, 28)),  # Blue potion
            'gold': self._load_sprite('gold_coin', (28, 28))       # Gold coin
        }
        return icons.get(resource_type)

    def _extract_resources(self, region_name: str, round_data: dict) -> Dict[str, int]:
        """Extract resource counts for a region from observations."""
        resources = {'food': 0, 'water': 0, 'gold': 0}

        for agent_name, obs_text in round_data.get('observations', {}).items():
            if f"You are in: {region_name}" in obs_text:
                if "Resources here:" in obs_text:
                    resource_line = obs_text.split("Resources here:")[1].split("\n")[0]

                    for res_type in ['food', 'water', 'gold']:
                        parts = resource_line.split(res_type)
                        if len(parts) > 1:
                            before = parts[0].strip().split()
                            if before and before[-1].isdigit():
                                resources[res_type] = int(before[-1])
                break

        return resources

    def _extract_events(self, region_name: str, round_data: dict) -> List[dict]:
        """Extract active events for a region from observations."""
        events = []

        for agent_name, obs_text in round_data.get('observations', {}).items():
            if f"You are in: {region_name}" in obs_text:
                if "Events here:" in obs_text:
                    events_section = obs_text.split("Events here:")[1].split("Your inventory:")[0]

                    for line in events_section.split("\n"):
                        line = line.strip()
                        if line and line != "No notable events." and line.startswith("-"):
                            event_desc = line[2:].strip()
                            events.append({'description': event_desc})
                break

        return events

    def _extract_agents_in_region(self, region_name: str, round_data: dict) -> List[dict]:
        """Extract agents present in a region with their inventories."""
        agents = []

        for agent_name, obs_text in round_data.get('observations', {}).items():
            if f"You are in: {region_name}" in obs_text:
                inventory = {'food': 0, 'water': 0, 'gold': 0}

                if "Your inventory:" in obs_text:
                    inv_line = obs_text.split("Your inventory:")[1].split("\n")[0]

                    for res_type in ['food', 'water', 'gold']:
                        parts = inv_line.split(res_type)
                        if len(parts) > 1:
                            before = parts[0].strip().split()
                            if before and before[-1].isdigit():
                                inventory[res_type] = int(before[-1])

                agents.append({
                    'name': agent_name,
                    'inventory': inventory
                })

        return agents

    def _word_wrap(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max_width pixels."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            text_surf = self.small_font.render(test_line, True, (0, 0, 0))

            if text_surf.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else ['']

    def _draw_thought_bubble(self, agent_pos: Tuple[int, int], thought: str):
        """Draw a thought bubble (cloudy style) above an agent for planning phase.

        Args:
            agent_pos: (x, y) position of agent on screen
            thought: Thought text to display
        """
        # Truncate long thoughts
        if len(thought) > 100:
            thought = thought[:97] + "..."

        # Word wrap
        max_width = 280
        lines = self._word_wrap(thought, max_width)

        # Calculate bubble dimensions
        padding = 12
        line_height = 22
        bubble_width = max_width + padding * 2
        bubble_height = padding * 2 + line_height * len(lines) + 10

        # Position above agent
        bubble_x = agent_pos[0] - bubble_width // 2
        bubble_y = agent_pos[1] - bubble_height - 100

        # Clamp to screen bounds
        bubble_x = max(10, min(bubble_x, self.screen_width - bubble_width - 10))
        bubble_y = max(80, bubble_y)

        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)

        # Cloudy thought bubble style
        bg_color = (240, 248, 255)      # Light blue (Alice blue)
        border_color = (100, 149, 237)   # Cornflower blue
        text_color = (25, 25, 112)       # Midnight blue

        # Draw bubble background with cloud effect
        pygame.draw.rect(self.surface, bg_color, bubble_rect, border_radius=20)
        pygame.draw.rect(self.surface, border_color, bubble_rect, width=3, border_radius=20)

        # Draw thought indicator (brain emoji)
        type_text = "🧠"
        type_surf = self.text_font.render(type_text, True, text_color)
        self.surface.blit(type_surf, (bubble_x + 10, bubble_y + 8))

        # Draw text lines
        y_offset = bubble_y + padding + 10
        for line in lines:
            text_surf = self.small_font.render(line, True, text_color)
            self.surface.blit(text_surf, (bubble_x + 40, y_offset))
            y_offset += line_height

        # Draw thought bubble "clouds" (small circles) instead of pointer
        cloud_y = bubble_y + bubble_height
        clouds = [
            (agent_pos[0] - 10, cloud_y + 10, 12),
            (agent_pos[0] + 5, cloud_y + 25, 8),
            (agent_pos[0] - 5, cloud_y + 35, 5)
        ]
        for cx, cy, radius in clouds:
            pygame.draw.circle(self.surface, bg_color, (cx, cy), radius)
            pygame.draw.circle(self.surface, border_color, (cx, cy), radius, 2)

    def _draw_speech_bubble(self, agent_pos: Tuple[int, int], message: str,
                           is_public: bool = True, msg_type: str = 'report'):
        """Draw a speech bubble above an agent.

        Args:
            agent_pos: (x, y) position of agent on screen
            message: Message text to display
            is_public: Whether message is public or private
            msg_type: Type of message ('report' or 'promise')
        """
        # Truncate long messages
        if len(message) > 80:
            message = message[:77] + "..."

        # Word wrap
        max_width = 280
        lines = self._word_wrap(message, max_width)

        # Calculate bubble dimensions
        padding = 12
        line_height = 22
        bubble_width = max_width + padding * 2
        bubble_height = padding * 2 + line_height * len(lines) + 10

        # Position above agent
        bubble_x = agent_pos[0] - bubble_width // 2
        bubble_y = agent_pos[1] - bubble_height - 80

        # Clamp to screen bounds
        bubble_x = max(10, min(bubble_x, self.screen_width - bubble_width - 10))
        bubble_y = max(80, bubble_y)

        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)

        # Style based on message type
        if is_public:
            bg_color = (255, 255, 255)      # White for public
            border_color = (100, 100, 100)   # Gray border
            text_color = (0, 0, 0)           # Black text
        else:
            bg_color = (230, 210, 250)       # Light purple for private
            border_color = (150, 100, 200)   # Purple border
            text_color = (50, 0, 100)        # Dark purple text

        # Draw bubble background
        pygame.draw.rect(self.surface, bg_color, bubble_rect, border_radius=15)
        pygame.draw.rect(self.surface, border_color, bubble_rect, width=3, border_radius=15)

        # Draw type indicator
        type_text = "💬" if msg_type == 'report' else "🤝"
        type_surf = self.text_font.render(type_text, True, text_color)
        self.surface.blit(type_surf, (bubble_x + 10, bubble_y + 8))

        # Draw text lines
        y_offset = bubble_y + padding + 10
        for line in lines:
            text_surf = self.small_font.render(line, True, text_color)
            self.surface.blit(text_surf, (bubble_x + 40, y_offset))
            y_offset += line_height

        # Draw pointer (triangle pointing to agent)
        pointer_size = 15
        pointer_points = [
            (agent_pos[0], agent_pos[1] - 60),
            (agent_pos[0] - pointer_size, bubble_y + bubble_height),
            (agent_pos[0] + pointer_size, bubble_y + bubble_height)
        ]
        pygame.draw.polygon(self.surface, bg_color, pointer_points)
        pygame.draw.lines(self.surface, border_color, False,
                         [pointer_points[1], pointer_points[0], pointer_points[2]], 3)

    def _render_background(self):
        """Render background with grass tiles."""
        self.surface.fill(self.BG_COLOR)

        # Draw grass background for map area
        grass = self._load_sprite('grass', (64, 64))
        if grass:
            for y in range(0, self.screen_height, 64):
                for x in range(0, 1200, 64):
                    self.surface.blit(grass, (x, y))

    def _render_region_area(self, region_name: str, position: Tuple[int, int],
                           resources: Dict[str, int], events: List[dict]):
        """Render a region area with background, resources, and events.

        Args:
            region_name: Name of the region
            position: (center_x, center_y) for the region
            resources: Resource counts
            events: Active events list
        """
        cx, cy = position
        size = self.region_size

        # Draw region background area
        region_color = self._get_region_color(region_name)
        region_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        region_surface.fill((*region_color, 100))  # Semi-transparent

        region_rect = region_surface.get_rect(center=(cx, cy))
        self.surface.blit(region_surface, region_rect)

        # Draw region decorations based on type
        if region_name == 'Forest':
            # Draw trees
            tree = self._load_sprite('tree', (60, 60))
            if tree:
                tree_positions = [(cx - 120, cy - 100), (cx + 80, cy - 80),
                                (cx - 80, cy + 90), (cx + 100, cy + 70)]
                for tree_pos in tree_positions:
                    self.surface.blit(tree, tree_pos)

        elif region_name == 'River':
            # Draw water effect (darker blue overlay)
            water_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            water_surface.fill((30, 60, 180, 120))
            self.surface.blit(water_surface, region_rect)

        elif region_name == 'Mines':
            # Draw cave/mine entrance
            cave_color = (40, 40, 45)
            pygame.draw.ellipse(self.surface, cave_color,
                              (cx - 50, cy - 30, 100, 80))
            pygame.draw.ellipse(self.surface, (20, 20, 25),
                              (cx - 50, cy - 30, 100, 80), 5)

        # Draw region name label
        label_surf = self.header_font.render(region_name.upper(), True, self.TEXT_COLOR)
        label_rect = label_surf.get_rect(center=(cx, cy - size // 2 + 30))

        # Background for label
        label_bg = pygame.Rect(label_rect.x - 10, label_rect.y - 5,
                              label_rect.width + 20, label_rect.height + 10)
        pygame.draw.rect(self.surface, self.PANEL_BG, label_bg, border_radius=8)
        pygame.draw.rect(self.surface, region_color, label_bg, 3, border_radius=8)

        self.surface.blit(label_surf, label_rect)

        # Draw resources in corner
        res_x = cx - size // 2 + 20
        res_y = cy - size // 2 + 70
        offset_y = 0

        for resource, amount in resources.items():
            if amount > 0:
                icon = self._get_resource_icon(resource)
                if icon:
                    self.surface.blit(icon, (res_x, res_y + offset_y))

                text = f"×{amount}"
                text_surf = self.text_font.render(text, True, self.TEXT_COLOR)

                # Background for text
                text_bg = pygame.Rect(res_x + 32, res_y + offset_y - 2, 60, 32)
                pygame.draw.rect(self.surface, self.PANEL_BG, text_bg, border_radius=5)

                self.surface.blit(text_surf, (res_x + 35, res_y + offset_y))
                offset_y += 35

        # Draw events (bigger and more visible!)
        event_y = cy + size // 2 - 100
        for i, event in enumerate(events[:2]):  # Max 2 events
            event_desc = event['description']

            # Determine icon and color based on type (infer from description)
            if "threat" in event_desc.lower() or "storm" in event_desc.lower() or "bandit" in event_desc.lower():
                icon = "⚠️"
                text_color = (255, 50, 50)  # Red for threats
                bg_color = (100, 0, 0, 220)
            elif "deplet" in event_desc.lower():
                icon = "📉"
                text_color = (255, 140, 0)  # Orange for depletion
                bg_color = (100, 50, 0, 220)
            elif "gold" in event_desc.lower():
                icon = "🪙"
                text_color = (255, 215, 0)  # Gold
                bg_color = (80, 80, 0, 220)
            else:
                icon = "📦"
                text_color = (100, 255, 100)  # Green for resources
                bg_color = (0, 80, 0, 220)

            event_text = f"{icon} {event_desc}"
            if len(event_text) > 32:
                event_text = event_text[:29] + "..."

            event_surf = self.text_font.render(event_text, True, text_color)
            event_rect = event_surf.get_rect(center=(cx, event_y + i * 35))

            # Background with glow effect
            event_bg = pygame.Rect(event_rect.x - 10, event_rect.y - 6,
                                  event_rect.width + 20, event_rect.height + 12)
            pygame.draw.rect(self.surface, bg_color, event_bg, border_radius=10)
            pygame.draw.rect(self.surface, text_color, event_bg, 2, border_radius=10)

            self.surface.blit(event_surf, event_rect)

    def _render_agent(self, agent_name: str, region_name: str, inventory: Dict[str, int],
                     agent_index: int, total_agents: int):
        """Render an agent sprite with inventory in a region.

        Args:
            agent_name: Agent name
            region_name: Region the agent is in
            inventory: Agent's inventory
            agent_index: Index of agent in region (for positioning)
            total_agents: Total agents in region
        """
        # Get region center position
        region_cx, region_cy = self.region_positions[region_name]

        # Position agents in a circle around region center
        angle_offset = (2 * 3.14159 / max(total_agents, 1)) * agent_index
        radius = 80
        agent_x = region_cx + int(radius * (agent_index - total_agents / 2) * 0.8)
        agent_y = region_cy + 20

        # Load agent sprite
        sprite = self._load_sprite('player_down', (64, 64))
        if sprite:
            self.surface.blit(sprite, (agent_x - 32, agent_y - 32))
        else:
            # Fallback: colored circle
            pygame.draw.circle(self.surface, (100, 150, 255), (agent_x, agent_y), 32)

        # Goal tier border
        goal_tier = self._get_agent_goal_tier(agent_name)
        goal_color = self._get_tier_color(goal_tier)
        pygame.draw.circle(self.surface, goal_color, (agent_x, agent_y), 34, 4)

        # Agent name below
        name_surf = self.small_font.render(agent_name, True, self.TEXT_COLOR)
        name_rect = name_surf.get_rect(center=(agent_x, agent_y + 45))

        # Background
        name_bg = pygame.Rect(name_rect.x - 5, name_rect.y - 2,
                             name_rect.width + 10, name_rect.height + 4)
        pygame.draw.rect(self.surface, self.PANEL_BG, name_bg, border_radius=5)

        self.surface.blit(name_surf, name_rect)

        # Inventory below name (if has items)
        total_items = sum(inventory.values())
        if total_items > 0:
            inv_parts = []
            if inventory['food'] > 0:
                inv_parts.append(f"{inventory['food']}🍎")
            if inventory['water'] > 0:
                inv_parts.append(f"{inventory['water']}💧")
            if inventory['gold'] > 0:
                inv_parts.append(f"{inventory['gold']}🪙")

            inv_text = " ".join(inv_parts)
            inv_surf = self.tiny_font.render(inv_text, True, (200, 200, 200))
            inv_rect = inv_surf.get_rect(center=(agent_x, agent_y + 65))
            self.surface.blit(inv_surf, inv_rect)

        return (agent_x, agent_y)  # Return position for speech bubbles

    def _render_settlement(self, settlement_status: dict):
        """Render settlement building in center."""
        cx, cy = self.settlement_pos

        # Settlement building sprite
        building = self._load_sprite('town_hall', (150, 150))
        if building:
            self.surface.blit(building, (cx - 75, cy - 75))
        else:
            # Fallback
            pygame.draw.rect(self.surface, (150, 150, 150), (cx - 60, cy - 60, 120, 120))

        # Settlement label
        label_surf = self.text_font.render("SETTLEMENT", True, self.TEXT_COLOR)
        label_rect = label_surf.get_rect(center=(cx, cy - 100))

        label_bg = pygame.Rect(label_rect.x - 8, label_rect.y - 4,
                              label_rect.width + 16, label_rect.height + 8)
        pygame.draw.rect(self.surface, self.PANEL_BG, label_bg, border_radius=8)

        self.surface.blit(label_surf, label_rect)

        # Status
        food = settlement_status['food']
        water = settlement_status['water']
        alive = settlement_status['alive']

        status_text = f"🍎 {food}  💧 {water}"
        status_surf = self.text_font.render(status_text, True, self.TEXT_COLOR)
        status_rect = status_surf.get_rect(center=(cx, cy + 90))

        status_bg = pygame.Rect(status_rect.x - 8, status_rect.y - 4,
                               status_rect.width + 16, status_rect.height + 8)
        pygame.draw.rect(self.surface, self.PANEL_BG, status_bg, border_radius=8)

        self.surface.blit(status_surf, status_rect)

        # Alive/Dead indicator
        status_color = (0, 255, 0) if alive else (255, 0, 0)
        status_label = "✓ ALIVE" if alive else "✗ DEAD"
        label_surf = self.text_font.render(status_label, True, status_color)
        label_rect = label_surf.get_rect(center=(cx, cy + 115))
        self.surface.blit(label_surf, label_rect)

    def _render_info_panel(self, round_num: int, max_rounds: int, messages: List[dict],
                          actions: Dict[str, dict], phase: str = "Action",
                          current_event: dict = None):
        """Render info panel on the right side.

        Args:
            round_num: Current round number
            max_rounds: Total rounds
            messages: Messages list
            actions: Actions dict
            phase: Phase name ("Planning" or "Action")
            current_event: Current round's event data
        """
        panel_x = 1200
        panel_width = 720

        # Panel background
        panel_rect = pygame.Rect(panel_x, 0, panel_width, self.screen_height)
        pygame.draw.rect(self.surface, self.PANEL_BG, panel_rect)
        pygame.draw.line(self.surface, (100, 100, 110), (panel_x, 0),
                        (panel_x, self.screen_height), 3)

        # Header
        header_text = f"Round {round_num}/{max_rounds}"
        header_surf = self.title_font.render(header_text, True, self.TEXT_COLOR)
        self.surface.blit(header_surf, (panel_x + 30, 30))

        # Phase indicator
        phase_color = (100, 200, 255) if phase == "Planning" else (255, 200, 100)
        phase_text = f"Phase: {phase}"
        phase_surf = self.header_font.render(phase_text, True, phase_color)
        self.surface.blit(phase_surf, (panel_x + 30, 90))

        # Condition
        cond_text = f"Condition: {self.condition.title()}"
        cond_surf = self.text_font.render(cond_text, True, (150, 150, 150))
        self.surface.blit(cond_surf, (panel_x + 30, 140))

        # Current event notification (prominent!)
        if current_event:
            event_y = 180
            event_type = current_event.get('type', '')
            event_region = current_event.get('region', '')
            event_desc = current_event.get('description', '')

            # Different styling based on event type
            if event_type == 'THREAT':
                bg_color = (139, 0, 0)  # Dark red
                border_color = (255, 0, 0)  # Bright red
                icon = "⚠️"
                label = "THREAT DETECTED"
            elif event_type == 'DEPLETION':
                bg_color = (139, 69, 0)  # Dark orange
                border_color = (255, 140, 0)  # Orange
                icon = "📉"
                label = "DEPLETION WARNING"
            elif event_type == 'GOLD_FOUND':
                bg_color = (85, 85, 0)  # Dark yellow
                border_color = (255, 215, 0)  # Gold
                icon = "🪙"
                label = "GOLD DISCOVERED"
            else:  # RESOURCE_FOUND
                bg_color = (0, 100, 0)  # Dark green
                border_color = (0, 255, 0)  # Bright green
                icon = "📦"
                label = "RESOURCES FOUND"

            # Event banner
            banner_rect = pygame.Rect(panel_x + 10, event_y, panel_width - 20, 100)
            pygame.draw.rect(self.surface, bg_color, banner_rect, border_radius=10)
            pygame.draw.rect(self.surface, border_color, banner_rect, 3, border_radius=10)

            # Icon
            icon_surf = self.title_font.render(icon, True, self.TEXT_COLOR)
            self.surface.blit(icon_surf, (panel_x + 25, event_y + 10))

            # Label
            label_surf = self.header_font.render(label, True, self.TEXT_COLOR)
            self.surface.blit(label_surf, (panel_x + 80, event_y + 15))

            # Region
            region_text = f"Location: {event_region}"
            region_surf = self.small_font.render(region_text, True, (220, 220, 220))
            self.surface.blit(region_surf, (panel_x + 80, event_y + 50))

            # Description
            if len(event_desc) > 35:
                event_desc = event_desc[:32] + "..."
            desc_surf = self.small_font.render(event_desc, True, (200, 200, 200))
            self.surface.blit(desc_surf, (panel_x + 80, event_y + 70))

        # Messages section (adjust position if event shown)
        msg_y = 300 if current_event else 200
        msg_title = self.header_font.render("💬 Communications", True, self.TEXT_COLOR)
        self.surface.blit(msg_title, (panel_x + 30, msg_y))

        y_offset = msg_y + 60
        for i, msg in enumerate(messages[:8]):  # Show up to 8 messages
            sender = msg.get('sender', 'Unknown')
            is_public = msg.get('is_public', True)
            msg_type = msg.get('type', 'report')

            # Determine color
            if is_public:
                color = (200, 200, 200)
                prefix = "📢"
            else:
                color = (200, 150, 255)
                prefix = "🔒"

            # Format message
            if msg_type == 'report':
                region = msg.get('region_claimed', '')
                claim = msg.get('claim', '')[:40]
                text = f"{prefix} {sender}: {claim}"
            else:
                commitment = msg.get('commitment', '')[:40]
                text = f"🤝 {sender}: {commitment}"

            text_surf = self.small_font.render(text, True, color)
            self.surface.blit(text_surf, (panel_x + 40, y_offset))
            y_offset += 30

            if y_offset > (800 if current_event else 700):  # Don't overflow
                break

        # Actions section (adjust position if event shown)
        action_y = 850 if current_event else 750
        action_title = self.header_font.render("⚙️ Actions", True, self.TEXT_COLOR)
        self.surface.blit(action_title, (panel_x + 30, action_y))

        y_offset = action_y + 60
        for agent, action in list(actions.items())[:10]:
            action_desc = action.get('description', 'Unknown')

            text = f"• {agent}: {action_desc}"
            text_surf = self.small_font.render(text, True, (180, 180, 180))
            self.surface.blit(text_surf, (panel_x + 40, y_offset))
            y_offset += 30

    def render_initial_frame(self) -> pygame.Surface:
        """Render initial frame showing trial setup."""
        self._render_background()

        # Title
        title = "Info Marketplace Simulation"
        title_surf = self.title_font.render(title, True, self.TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 200))
        self.surface.blit(title_surf, title_rect)

        # Condition
        cond_text = f"Condition: {self.condition.upper()}"
        cond_surf = self.header_font.render(cond_text, True, (200, 200, 200))
        cond_rect = cond_surf.get_rect(center=(self.screen_width // 2, 280))
        self.surface.blit(cond_surf, cond_rect)

        # Goals
        goals_y = 380
        goals_title = "Agent Goals:"
        goals_surf = self.header_font.render(goals_title, True, self.TEXT_COLOR)
        goals_rect = goals_surf.get_rect(center=(self.screen_width // 2, goals_y))
        self.surface.blit(goals_surf, goals_rect)

        for i, goal in enumerate(self.goals):
            agent = goal['agent']
            tier = goal['tier']
            desc = goal['description']

            tier_color = self._get_tier_color(tier)

            y = goals_y + 80 + i * 100

            # Agent name with tier
            agent_text = f"{agent} [{tier}]"
            agent_surf = self.text_font.render(agent_text, True, tier_color)
            agent_rect = agent_surf.get_rect(center=(self.screen_width // 2, y))
            self.surface.blit(agent_surf, agent_rect)

            # Description
            desc_surf = self.small_font.render(desc, True, (180, 180, 180))
            desc_rect = desc_surf.get_rect(center=(self.screen_width // 2, y + 35))
            self.surface.blit(desc_surf, desc_rect)

        self.frame_count += 1
        return self.surface

    def render_planning_frame(self, round_num: int, round_data: dict) -> pygame.Surface:
        """Render planning phase frame with thought bubbles showing agent plans.

        Args:
            round_num: Current round number
            round_data: Round data dictionary from game_log

        Returns:
            pygame.Surface ready to save
        """
        # Layer 1: Background
        self._render_background()

        # Layer 2: Region areas with resources and events
        for region_name, position in self.region_positions.items():
            resources = self._extract_resources(region_name, round_data)
            events = self._extract_events(region_name, round_data)
            self._render_region_area(region_name, position, resources, events)

        # Layer 3: Settlement
        settlement_status = round_data.get('settlement_status', {})
        self._render_settlement(settlement_status)

        # Layer 4: Agents (and collect positions)
        agent_positions = {}

        for region_name in self.region_positions.keys():
            agents = self._extract_agents_in_region(region_name, round_data)
            for i, agent_data in enumerate(agents):
                agent_name = agent_data['name']
                inventory = agent_data['inventory']
                pos = self._render_agent(agent_name, region_name, inventory,
                                        i, len(agents))
                agent_positions[agent_name] = pos

        # Layer 5: Thought bubbles for plans
        plans = round_data.get('plans', {})
        for agent_name, plan_text in plans.items():
            if agent_name in agent_positions:
                self._draw_thought_bubble(agent_positions[agent_name], plan_text)

        # Layer 6: Info panel (planning phase)
        max_rounds = self.trial_data['game_log']['config']['num_rounds']
        messages = round_data.get('messages', [])
        actions = {}  # No actions yet in planning phase
        current_event = round_data.get('event')
        self._render_info_panel(round_num, max_rounds, messages, actions,
                               phase="Planning", current_event=current_event)

        self.frame_count += 1
        return self.surface

    def render_action_frame(self, round_num: int, round_data: dict) -> pygame.Surface:
        """Render action phase frame with speech bubbles and actions.

        Args:
            round_num: Current round number
            round_data: Round data dictionary from game_log

        Returns:
            pygame.Surface ready to save
        """
        # Layer 1: Background
        self._render_background()

        # Layer 2: Region areas with resources and events
        for region_name, position in self.region_positions.items():
            resources = self._extract_resources(region_name, round_data)
            events = self._extract_events(region_name, round_data)
            self._render_region_area(region_name, position, resources, events)

        # Layer 3: Settlement
        settlement_status = round_data.get('settlement_status', {})
        self._render_settlement(settlement_status)

        # Layer 4: Agents (and collect positions for speech bubbles)
        agent_positions = {}

        for region_name in self.region_positions.keys():
            agents = self._extract_agents_in_region(region_name, round_data)
            for i, agent_data in enumerate(agents):
                agent_name = agent_data['name']
                inventory = agent_data['inventory']
                pos = self._render_agent(agent_name, region_name, inventory,
                                        i, len(agents))
                agent_positions[agent_name] = pos

        # Layer 5: Speech bubbles for messages
        messages = round_data.get('messages', [])
        for msg in messages:
            sender = msg.get('sender')
            if sender in agent_positions:
                is_public = msg.get('is_public', True)
                msg_type = msg.get('type', 'report')

                # Get message text
                if msg_type == 'report':
                    claim = msg.get('claim', '')
                    message_text = claim
                else:
                    commitment = msg.get('commitment', '')
                    message_text = commitment

                # Draw speech bubble
                self._draw_speech_bubble(
                    agent_positions[sender],
                    message_text,
                    is_public,
                    msg_type
                )

        # Layer 6: Info panel (action phase)
        max_rounds = self.trial_data['game_log']['config']['num_rounds']
        actions = round_data.get('actions', {})
        current_event = round_data.get('event')
        self._render_info_panel(round_num, max_rounds, messages, actions,
                               phase="Action", current_event=current_event)

        self.frame_count += 1
        return self.surface
