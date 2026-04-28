# Info Marketplace Visualization System

## Overview

The Info Marketplace Visualization System transforms trial JSON files into MP4 videos showing the multi-agent simulation. The system uses PyGame for rendering and FFmpeg for video compilation.

### Key Technologies
- **PyGame** - 2D graphics rendering and sprite management
- **FFmpeg** - Video compilation from PNG frames
- **Python** - JSON parsing and orchestration

### Output Format
- **Images**: PNG files (1920x1080 pixels)
- **Videos**: MP4 files (H.264 codec, 2 FPS default)

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Trial JSON File                           │
│      (game_log with rounds, messages, actions, etc.)        │
└────────────────────┬────────────────────────────────────────┘
                     │ Load and parse
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Visualizer Script                        │
│         (Orchestrates rendering for each round)             │
└────────────────────┬────────────────────────────────────────┘
                     │ Round data
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               MarketplaceRenderer                           │
│         (PyGame-based rendering engine)                     │
└────────────────────┬────────────────────────────────────────┘
                     │ pygame.Surface
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Frame Rendering Pipeline                       │
│  Background → Regions → Agents → Events → Resources →       │
│  Settlement → Messages → Overlays                           │
└────────────────────┬────────────────────────────────────────┘
                     │ PNG frames
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          FFmpeg Video Compilation                           │
│              Output: trial_XXX.mp4                          │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
info_marketplace/
├── __init__.py
├── renderer.py                    # MarketplaceRenderer class
├── visualizer.py                  # Main script (JSON → Video)
├── VISUALIZATION_ARCHITECTURE.md  # This file
└── ... (existing simulation files)

sprites/                           # Sprite assets
├── player_down.png               # Scout agents (4 directional)
├── player_up.png
├── player_left.png
├── player_right.png
├── gold_coin.png                 # Resource icons
├── magic_gem.png                 # Can represent food/water
├── grass.png                     # Region backgrounds
├── tree.png                      # Forest region
├── town_hall.png                 # Settlement building
└── ... (other sprites)

output/                            # Generated videos
└── trial_XXX_visualization/
    ├── frame_0000.png
    ├── frame_0001.png
    └── ...
```

---

## Visual Layout Design

### Screen Layout (1920x1080)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                Info Marketplace - Round 3/10 - Mixed Condition             │
├──────────────────────────────┬────────────────────────────────────────────┤
│                              │                                            │
│         FOREST               │              RIVER                         │
│    ┌──────────────┐          │         ┌──────────────┐                   │
│    │  [Forest BG] │          │         │  [Water BG]  │                   │
│    │              │          │         │              │                   │
│    │  Agent_0 👤  │          │         │  Agent_1 👤  │                   │
│    │  0f, 0w, 0g  │          │         │  1f, 0w, 0g  │                   │
│    │              │          │         │              │                   │
│    │  📦 1 food   │          │         │  📦 4 water  │                   │
│    └──────────────┘          │         │  📦 1 food   │                   │
│                              │         └──────────────┘                   │
├──────────────────────────────┼────────────────────────────────────────────┤
│          SETTLEMENT          │                                            │
│      ┌──────────────┐        │                                            │
│      │   🏛️ Town    │        │                                            │
│      │     Hall     │        │                                            │
│      │              │        │                                            │
│      │  Food: 9     │        │                                            │
│      │  Water: 7    │        │                                            │
│      │  [ALIVE]     │        │                                            │
│      └──────────────┘        │                                            │
├──────────────────────────────┼────────────────────────────────────────────┤
│                              │                                            │
│         PLAINS               │              MINES                         │
│    ┌──────────────┐          │         ┌──────────────┐                   │
│    │  [Plains BG] │          │         │  [Cave BG]   │                   │
│    │              │          │         │              │                   │
│    │  Agent_2 👤  │          │         │  Agent_3 👤  │                   │
│    │  0f, 1w, 0g  │          │         │  0f, 0w, 1g  │                   │
│    │              │          │         │              │                   │
│    │  📦 2 water  │          │         │  📦 5 food   │                   │
│    │  ⚡ Event:   │          │         │  📦 2 gold   │                   │
│    │  3w found    │          │         │  ⚡ Event:   │                   │
│    └──────────────┘          │         │  5f found    │                   │
│                              │         └──────────────┘                   │
└──────────────────────────────┴────────────────────────────────────────────┘
│ 💬 Messages this round:                                                   │
│ ├─ Agent_0 [PUBLIC]: REPORT Forest: "I found 1 food here."               │
│ ├─ Agent_1 [PUBLIC]: REPORT River: "I found 4 water and 1 food here."    │
│ ├─ Agent_2 [PUBLIC]: REPORT Plains: "I found 3 water here."              │
│ └─ Agent_3 [PRIVATE→self]: PROMISE: "I'll monitor the gold here..."      │
├───────────────────────────────────────────────────────────────────────────┤
│ ⚙️ Actions this round:                                                    │
│ ├─ Agent_0: Gather food [SUCCESS]                                        │
│ ├─ Agent_1: Gather food [SUCCESS]                                        │
│ ├─ Agent_2: Gather water [SUCCESS]                                       │
│ └─ Agent_3: Gather gold [SUCCESS]                                        │
└───────────────────────────────────────────────────────────────────────────┘
```

### Layout Dimensions

- **Screen size**: 1920 x 1080 pixels
- **Region panels**: 4 quadrants (960 x 540 each for main regions)
  - Top-left: Forest
  - Top-right: River
  - Bottom-left: Plains + Settlement overlay
  - Bottom-right: Mines
- **Settlement overlay**: 400 x 300 pixels (overlaid on bottom-left)
- **Message panel**: Bottom 200 pixels (full width)
- **Header**: Top 60 pixels (round counter, condition)

---

## Rendering Pipeline

### Phase 1: Initialization

```python
class MarketplaceRenderer:
    def __init__(self, trial_data, sprites_dir, output_dir):
        """Initialize renderer with trial data and output settings."""

        # PyGame setup
        pygame.init()
        pygame.font.init()

        # Screen dimensions
        self.screen_width = 1920
        self.screen_height = 1080
        self.surface = pygame.Surface((self.screen_width, self.screen_height))

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.header_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

        # Sprite cache
        self.sprite_cache = {}
        self.sprites_dir = Path(sprites_dir)

        # Trial data
        self.trial_data = trial_data
        self.condition = trial_data['condition']
        self.goals = trial_data['goals']

        # Colors
        self.BG_COLOR = (30, 30, 40)           # Dark blue-gray
        self.FOREST_COLOR = (34, 139, 34)      # Forest green
        self.RIVER_COLOR = (65, 105, 225)      # Royal blue
        self.PLAINS_COLOR = (210, 180, 140)    # Tan
        self.MINES_COLOR = (105, 105, 105)     # Dim gray
        self.SETTLEMENT_COLOR = (169, 169, 169) # Gray
        self.PANEL_COLOR = (50, 50, 60)        # Dark panel
        self.TEXT_COLOR = (255, 255, 255)      # White

        # Frame counter
        self.frame_count = 0
```

### Phase 2: Sprite Loading

```python
def _load_sprite(self, name: str, size: tuple = None) -> pygame.Surface:
    """Load and cache a sprite with optional resizing."""

    cache_key = f"{name}_{size}" if size else name

    if cache_key in self.sprite_cache:
        return self.sprite_cache[cache_key]

    sprite_path = self.sprites_dir / f"{name}.png"

    if not sprite_path.exists():
        return None

    sprite = pygame.image.load(str(sprite_path))

    if size:
        sprite = pygame.transform.scale(sprite, size)

    self.sprite_cache[cache_key] = sprite
    return sprite
```

### Phase 3: Frame Rendering (9 Layers)

#### Layer 1: Background
```python
def _render_background(self):
    """Fill screen with background color."""
    self.surface.fill(self.BG_COLOR)
```

#### Layer 2: Header
```python
def _render_header(self, round_num, max_rounds):
    """Render title bar with round counter and condition."""

    # Dark header background
    header_rect = pygame.Rect(0, 0, self.screen_width, 60)
    pygame.draw.rect(self.surface, self.PANEL_COLOR, header_rect)

    # Title text
    title = f"Info Marketplace - Round {round_num}/{max_rounds} - {self.condition.title()} Condition"
    title_surf = self.header_font.render(title, True, self.TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(self.screen_width // 2, 30))
    self.surface.blit(title_surf, title_rect)
```

#### Layer 3: Region Panels
```python
def _render_region_panel(self, region_name, position, round_data):
    """Render a single region panel with background, resources, events, agents."""

    x, y, width, height = position  # e.g., (0, 60, 960, 540)

    # Region background color
    bg_color = self._get_region_color(region_name)
    panel_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(self.surface, bg_color, panel_rect)

    # Region name label
    name_surf = self.header_font.render(region_name.upper(), True, self.TEXT_COLOR)
    self.surface.blit(name_surf, (x + 20, y + 20))

    # Border
    pygame.draw.rect(self.surface, (200, 200, 200), panel_rect, 3)
```

#### Layer 4: Resources Display
```python
def _render_resources(self, region_name, resources, position):
    """Display resource icons and counts in a region."""

    x, y = position
    offset_y = 0

    for resource, amount in resources.items():
        if amount > 0:
            # Resource icon
            icon = self._get_resource_icon(resource)
            if icon:
                self.surface.blit(icon, (x, y + offset_y))

            # Resource count text
            text = f"{amount} {resource}"
            text_surf = self.text_font.render(text, True, self.TEXT_COLOR)
            self.surface.blit(text_surf, (x + 40, y + offset_y))

            offset_y += 35

def _get_resource_icon(self, resource_type):
    """Map resource type to sprite."""
    icons = {
        'food': self._load_sprite('magic_gem', (32, 32)),      # Red gem
        'water': self._load_sprite('magic_potion', (32, 32)),  # Blue potion
        'gold': self._load_sprite('gold_coin', (32, 32))       # Gold coin
    }
    return icons.get(resource_type)
```

#### Layer 5: Event Display
```python
def _render_events(self, events, position):
    """Display active events in a region."""

    x, y = position

    for i, event in enumerate(events):
        # Event icon (⚡ for events)
        icon_text = "⚡"
        icon_surf = self.header_font.render(icon_text, True, (255, 215, 0))
        self.surface.blit(icon_surf, (x, y + i * 40))

        # Event description
        desc = event['description']
        desc_surf = self.small_font.render(f"Event: {desc}", True, self.TEXT_COLOR)
        self.surface.blit(desc_surf, (x + 40, y + i * 40 + 5))
```

#### Layer 6: Agent Display
```python
def _render_agents(self, region_name, agents_data, position):
    """Render agents in a region with sprites and inventory."""

    x, y = position

    for i, agent_data in enumerate(agents_data):
        agent_name = agent_data['name']
        inventory = agent_data['inventory']

        # Agent sprite
        sprite = self._load_sprite('player_down', (64, 64))
        self.surface.blit(sprite, (x + i * 80, y))

        # Agent name
        name_surf = self.small_font.render(agent_name, True, self.TEXT_COLOR)
        self.surface.blit(name_surf, (x + i * 80, y + 70))

        # Agent inventory (compact)
        inv_text = f"{inventory['food']}f, {inventory['water']}w, {inventory['gold']}g"
        inv_surf = self.small_font.render(inv_text, True, (200, 200, 200))
        self.surface.blit(inv_surf, (x + i * 80, y + 90))

        # Agent goal indicator (colored border)
        goal_tier = self._get_agent_goal_tier(agent_name)
        goal_color = self._get_tier_color(goal_tier)
        pygame.draw.rect(self.surface, goal_color,
                        (x + i * 80 - 2, y - 2, 68, 68), 3)
```

#### Layer 7: Settlement Panel
```python
def _render_settlement(self, settlement_status, position):
    """Render settlement overlay panel."""

    x, y, width, height = position

    # Semi-transparent background
    panel = pygame.Surface((width, height), pygame.SRCALPHA)
    panel.fill((50, 50, 60, 220))  # Dark with alpha
    self.surface.blit(panel, (x, y))

    # Settlement icon
    icon = self._load_sprite('town_hall', (100, 100))
    if icon:
        self.surface.blit(icon, (x + width // 2 - 50, y + 20))

    # Status text
    food = settlement_status['food']
    water = settlement_status['water']
    alive = settlement_status['alive']

    status_text = f"Food: {food}  |  Water: {water}"
    status_surf = self.text_font.render(status_text, True, self.TEXT_COLOR)
    self.surface.blit(status_surf, (x + 20, y + 140))

    # Alive indicator
    status_label = "[ALIVE]" if alive else "[DEAD]"
    status_color = (0, 255, 0) if alive else (255, 0, 0)
    label_surf = self.header_font.render(status_label, True, status_color)
    self.surface.blit(label_surf, (x + 20, y + 180))

    # Border
    pygame.draw.rect(self.surface, (200, 200, 200), (x, y, width, height), 3)
```

#### Layer 8: Message Panel
```python
def _render_messages(self, messages):
    """Render message log at bottom of screen."""

    panel_y = 880
    panel_height = 200

    # Background
    panel_rect = pygame.Rect(0, panel_y, self.screen_width, panel_height)
    pygame.draw.rect(self.surface, self.PANEL_COLOR, panel_rect)

    # Title
    title_surf = self.text_font.render("💬 Messages this round:", True, self.TEXT_COLOR)
    self.surface.blit(title_surf, (20, panel_y + 10))

    # Message list (up to 4 messages)
    y_offset = panel_y + 45
    for i, msg in enumerate(messages[:4]):
        # Format message
        sender = msg['sender']
        is_public = msg.get('is_public', True)
        msg_type = msg.get('type', 'report')

        if msg_type == 'report':
            region = msg.get('region_claimed', '')
            claim = msg.get('claim', '')
            prefix = "[PUBLIC]" if is_public else "[PRIVATE]"
            text = f"├─ {sender} {prefix}: REPORT {region}: \"{claim[:60]}...\""
        elif msg_type == 'promise':
            target = msg.get('target', '')
            commitment = msg.get('commitment', '')
            text = f"├─ {sender}: PROMISE {target}: \"{commitment[:60]}...\""

        # Render
        color = self.TEXT_COLOR if is_public else (200, 150, 255)
        text_surf = self.small_font.render(text, True, color)
        self.surface.blit(text_surf, (20, y_offset + i * 30))

    # Border
    pygame.draw.rect(self.surface, (100, 100, 110), panel_rect, 2)
```

#### Layer 9: Action Panel
```python
def _render_actions(self, actions, action_results):
    """Render action log below messages."""

    panel_y = 1010

    # Title
    title_surf = self.text_font.render("⚙️ Actions this round:", True, self.TEXT_COLOR)
    self.surface.blit(title_surf, (self.screen_width // 2 + 20, panel_y + 10))

    # Action list (up to 4 actions)
    y_offset = panel_y + 45
    for i, (agent, action) in enumerate(list(actions.items())[:4]):
        action_desc = action['description']
        success = action_results[agent]['success']

        status = "[✓]" if success else "[✗]"
        color = (0, 255, 0) if success else (255, 100, 100)

        text = f"├─ {agent}: {action_desc} {status}"
        text_surf = self.small_font.render(text, True, self.TEXT_COLOR)

        # Status indicator
        status_surf = self.small_font.render(status, True, color)
        self.surface.blit(text_surf, (self.screen_width // 2 + 20, y_offset + i * 30))
```

### Phase 4: Main Render Method

```python
def render_frame(self, round_num: int, round_data: dict) -> pygame.Surface:
    """Render a complete frame for a given round."""

    # Layer 1: Background
    self._render_background()

    # Layer 2: Header
    max_rounds = self.trial_data['game_log']['config']['num_rounds']
    self._render_header(round_num, max_rounds)

    # Layer 3-6: Region panels (4 quadrants)
    regions_layout = {
        'Forest': (0, 60, 960, 410),
        'River': (960, 60, 960, 410),
        'Plains': (0, 470, 960, 410),
        'Mines': (960, 470, 960, 410)
    }

    for region_name, position in regions_layout.items():
        self._render_region_panel(region_name, position, round_data)

        # Get region-specific data
        resources = self._extract_resources(region_name, round_data)
        events = self._extract_events(region_name, round_data)
        agents = self._extract_agents_in_region(region_name, round_data)

        # Render components
        self._render_resources(region_name, resources,
                              (position[0] + 20, position[1] + 80))
        self._render_events(events,
                           (position[0] + 20, position[1] + 250))
        self._render_agents(region_name, agents,
                           (position[0] + 20, position[1] + 350))

    # Layer 7: Settlement (overlaid on Plains region)
    settlement_status = round_data['settlement_status']
    self._render_settlement(settlement_status, (50, 520, 400, 280))

    # Layer 8: Messages
    messages = round_data.get('messages', [])
    self._render_messages(messages)

    # Layer 9: Actions
    actions = round_data.get('actions', {})
    action_results = round_data.get('action_results', {})
    self._render_actions(actions, action_results)

    self.frame_count += 1
    return self.surface
```

---

## Visualizer Script

### Main Entry Point

```python
# info_marketplace/visualizer.py

import json
import pygame
from pathlib import Path
from info_marketplace.renderer import MarketplaceRenderer

def load_trial(trial_path: str) -> dict:
    """Load trial JSON file."""
    with open(trial_path, 'r') as f:
        return json.load(f)

def visualize_trial(trial_path: str, output_dir: str = None, fps: int = 2):
    """
    Convert a trial JSON file to a video.

    Args:
        trial_path: Path to trial JSON file
        output_dir: Output directory (default: auto-generated)
        fps: Frames per second (default: 2)

    Returns:
        Path to generated video file
    """

    # Load trial data
    print(f"📂 Loading trial: {trial_path}")
    trial_data = load_trial(trial_path)

    trial_id = trial_data['trial_id']
    condition = trial_data['condition']

    # Setup output directory
    if output_dir is None:
        trial_name = Path(trial_path).stem
        output_dir = Path("output") / f"{trial_name}_visualization"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")

    # Initialize renderer
    sprites_dir = Path(__file__).parent.parent / "sprites"
    renderer = MarketplaceRenderer(trial_data, sprites_dir, output_dir)

    # Render initial frame (round -1, setup)
    print("\n🎨 Rendering frames...")
    frame_paths = []

    # Initial state frame
    initial_frame = renderer.render_initial_frame()
    initial_path = output_dir / "frame_0000.png"
    pygame.image.save(initial_frame, str(initial_path))
    frame_paths.append(initial_path)
    print(f"  ✓ Frame 0000 (initial state)")

    # Render each round
    rounds = trial_data['game_log']['rounds']
    for i, round_data in enumerate(rounds):
        frame = renderer.render_frame(round_data['round'], round_data)

        frame_num = i + 1
        frame_path = output_dir / f"frame_{frame_num:04d}.png"
        pygame.image.save(frame, str(frame_path))
        frame_paths.append(frame_path)

        if frame_num % 5 == 0:
            print(f"  ✓ Frame {frame_num:04d}")

    print(f"\n✓ Rendered {len(frame_paths)} frames")

    # Generate video
    print("\n🎬 Generating video...")
    video_path = output_dir.parent / f"{output_dir.name}.mp4"

    success = frames_to_video(
        frame_dir=str(output_dir),
        output_video=str(video_path),
        fps=fps
    )

    if success:
        print(f"✅ Video created: {video_path}")
        duration = len(frame_paths) / fps
        print(f"   Duration: {duration:.1f} seconds")
        return video_path
    else:
        print("❌ Video generation failed")
        return None

def frames_to_video(frame_dir: str, output_video: str, fps: int = 2):
    """Convert PNG frames to MP4 using FFmpeg."""
    import subprocess
    import os

    frame_pattern = os.path.join(frame_dir, "frame_%04d.png")

    cmd = [
        'ffmpeg',
        '-framerate', str(fps),
        '-i', frame_pattern,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-y',
        output_video
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except FileNotFoundError:
        print("❌ FFmpeg not found. Install: brew install ffmpeg")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e.stderr}")
        return False

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python visualizer.py <trial_json_path> [fps]")
        print("Example: python visualizer.py results/mixed_gpt-5.4-mini_20260415/trial_006.json 2")
        sys.exit(1)

    trial_path = sys.argv[1]
    fps = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    visualize_trial(trial_path, fps=fps)
```

---

## Usage Examples

### Command Line

```bash
# Visualize a single trial
python info_marketplace/visualizer.py results/mixed_gpt-5.4-mini_20260415/trial_006.json

# Visualize with custom FPS
python info_marketplace/visualizer.py results/mixed_gpt-5.4-mini_20260415/trial_006.json 4

# Batch process all trials in a directory
for trial in results/mixed_*/trial_*.json; do
    python info_marketplace/visualizer.py "$trial"
done
```

### Python API

```python
from info_marketplace.visualizer import visualize_trial

# Single trial
video_path = visualize_trial(
    "results/mixed_gpt-5.4-mini_20260415/trial_006.json",
    fps=2
)

# Custom output directory
video_path = visualize_trial(
    "results/mixed_gpt-5.4-mini_20260415/trial_006.json",
    output_dir="my_videos/trial_006",
    fps=3
)
```

---

## Sprite Requirements

### Required Sprites (Minimum)

| Sprite | Purpose | File |
|--------|---------|------|
| **Agents** | Scout characters | `player_down.png` (or directional) |
| **Resources** | Food icon | `magic_gem.png` (red) |
| | Water icon | `magic_potion.png` (blue) |
| | Gold icon | `gold_coin.png` |
| **Settlement** | Settlement building | `town_hall.png` |

### Optional Sprites (Enhanced)

| Sprite | Purpose | File |
|--------|---------|------|
| **Backgrounds** | Forest region | `tree.png` (tiled) |
| | River region | `grass.png` (blue-tinted) |
| | Plains region | `grass.png` |
| | Mines region | Custom cave sprite |
| **Events** | Threat indicators | Custom icons |

---

## Color Coding System

### Agent Goal Tiers
- **ALIGNED**: Green border (0, 255, 0)
- **ORTHOGONAL**: Yellow border (255, 215, 0)
- **COMPETITIVE**: Red border (255, 0, 0)

### Message Types
- **PUBLIC**: White text (255, 255, 255)
- **PRIVATE**: Purple text (200, 150, 255)

### Settlement Status
- **ALIVE**: Green text (0, 255, 0)
- **DEAD**: Red text (255, 0, 0)

### Regions
- **Forest**: Forest green (34, 139, 34)
- **River**: Royal blue (65, 105, 225)
- **Plains**: Tan (210, 180, 140)
- **Mines**: Dim gray (105, 105, 105)

---

## Implementation Checklist

- [ ] Create `info_marketplace/renderer.py`
  - [ ] `MarketplaceRenderer` class
  - [ ] Sprite loading and caching
  - [ ] Region rendering
  - [ ] Agent rendering
  - [ ] Resource rendering
  - [ ] Event rendering
  - [ ] Settlement rendering
  - [ ] Message panel rendering
  - [ ] Action panel rendering

- [ ] Create `info_marketplace/visualizer.py`
  - [ ] JSON loading
  - [ ] Frame generation loop
  - [ ] FFmpeg integration
  - [ ] CLI interface

- [ ] Test with sample trial
  - [ ] Verify frame generation
  - [ ] Verify video compilation
  - [ ] Check visual quality

- [ ] Documentation
  - [ ] Usage examples
  - [ ] Sprite requirements
  - [ ] Troubleshooting guide

---

## Future Enhancements

### Phase 2 Features
- [ ] Deception highlighting (red glow for fabricated messages)
- [ ] Animated agent movement between regions
- [ ] Event icons (storm, bandits, drought)
- [ ] Promise tracking (show fulfilled vs broken)
- [ ] Interactive HTML viewer (click to see agent plans)

### Phase 3 Features
- [ ] Comparison videos (side-by-side conditions)
- [ ] Statistical overlays (deception rate graph)
- [ ] Agent "thinking" visualization (show LLM reasoning)
- [ ] Time-lapse mode (skip unchanged rounds)

---

## Performance Targets

- **Rendering**: ~100ms per frame (10 FPS capable)
- **Video compilation**: ~2-5 seconds for 10-round trial
- **Memory usage**: <500 MB for typical trial

---

## Troubleshooting

### FFmpeg Not Found
```bash
# Install FFmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Linux
```

### Missing Sprites
- Falls back to colored rectangles with text labels
- Check `sprites/` directory exists
- Verify sprite filenames match expected names

### Blank Video
- Check trial JSON is valid
- Verify rounds data is populated
- Enable debug output in renderer

---

This architecture provides a complete, scalable system for visualizing Info Marketplace simulations with rich, informative output suitable for research analysis and presentation.
