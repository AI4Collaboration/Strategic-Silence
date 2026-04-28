"""Main script to convert Info Marketplace trial JSON files to GIFs."""

import json
import pygame
import subprocess
import os
from pathlib import Path
from typing import Optional, List

from info_marketplace.renderer import MarketplaceRenderer


def load_trial(trial_path: str) -> dict:
    """Load trial JSON file.

from __future__ import annotations

    Args:
        trial_path: Path to trial JSON file

    Returns:
        Parsed trial data dictionary
    """
    with open(trial_path, 'r') as f:
        return json.load(f)


def frames_to_gif(frame_dir: str, output_gif: str, fps: int = 2) -> bool:
    """Convert PNG frames to GIF using FFmpeg.

    Args:
        frame_dir: Directory containing frame_XXXX.png files
        output_gif: Output GIF file path (e.g., "output.gif")
        fps: Frames per second (default: 2)

    Returns:
        True if successful, False otherwise

    Requires:
        FFmpeg installed (brew install ffmpeg on macOS)
    """
    frame_pattern = os.path.join(frame_dir, "frame_%04d.png")

    # FFmpeg command for high-quality GIF
    cmd = [
        'ffmpeg',
        '-framerate', str(fps),        # Input framerate
        '-i', frame_pattern,            # Input files
        '-vf', f'fps={fps},scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',  # Generate optimal palette for quality
        '-y',                            # Overwrite output file if exists
        output_gif
    ]

    try:
        # Run FFmpeg (suppress output)
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except FileNotFoundError:
        print("❌ FFmpeg not found. Install it with: brew install ffmpeg")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e.stderr}")
        return False


def visualize_trial(
    trial_path: str,
    output_dir: Optional[str] = None,
    fps: int = 2,
    keep_frames: bool = True
) -> Optional[Path]:
    """Convert a trial JSON file to a GIF.

    Args:
        trial_path: Path to trial JSON file
        output_dir: Output directory (default: auto-generated)
        fps: Frames per second (default: 2)
        keep_frames: Keep PNG frames after GIF generation (default: True)

    Returns:
        Path to generated GIF file, or None if failed
    """
    # Load trial data
    print(f"\n📂 Loading trial: {trial_path}")
    trial_data = load_trial(trial_path)

    trial_id = trial_data.get('trial_id', 0)
    condition = trial_data.get('condition', 'unknown')

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
    if not sprites_dir.exists():
        print(f"⚠️  Warning: Sprites directory not found at {sprites_dir}")
        print("   Using fallback rendering (colored shapes)")

    renderer = MarketplaceRenderer(trial_data, sprites_dir, output_dir)

    # Render frames
    print("\n🎨 Rendering frames...")
    frame_paths = []

    # Render each round (2 phases per round)
    rounds = trial_data['game_log']['rounds']
    total_rounds = len(rounds)

    for i, round_data in enumerate(rounds):
        round_num = round_data['round']

        # Phase 1: Planning frame (with thought bubbles)
        planning_frame = renderer.render_planning_frame(round_num, round_data)
        planning_frame_num = i * 2
        planning_path = output_dir / f"frame_{planning_frame_num:04d}.png"
        pygame.image.save(planning_frame, str(planning_path))
        frame_paths.append(planning_path)

        # Phase 2: Action frame (with speech bubbles)
        action_frame = renderer.render_action_frame(round_num, round_data)
        action_frame_num = (i * 2) + 1
        action_path = output_dir / f"frame_{action_frame_num:04d}.png"
        pygame.image.save(action_frame, str(action_path))
        frame_paths.append(action_path)

        # Progress indicator
        if i == 0 or (i + 1) % 3 == 0 or (i + 1) == total_rounds:
            print(f"   ✓ Round {round_num + 1}/{total_rounds} (frames {planning_frame_num:04d}-{action_frame_num:04d})")

    print(f"\n✅ Rendered {len(frame_paths)} frames")

    # Generate GIF
    print("\n🎬 Generating GIF with FFmpeg...")
    gif_path = output_dir.parent / f"{output_dir.name}.gif"

    success = frames_to_gif(
        frame_dir=str(output_dir),
        output_gif=str(gif_path),
        fps=fps
    )

    if success:
        print(f"\n✅ GIF created: {gif_path}")
        duration = len(frame_paths) / fps
        print(f"   Duration: {duration:.1f} seconds ({len(frame_paths)} frames @ {fps} FPS)")
        print(f"   Condition: {condition}")
        print(f"   Trial ID: {trial_id}")

        # Clean up frames if requested
        if not keep_frames:
            print("\n🧹 Cleaning up frames...")
            for frame_path in frame_paths:
                frame_path.unlink()
            output_dir.rmdir()
            print("   ✓ Frames deleted")

        return gif_path
    else:
        print("\n❌ GIF generation failed")
        print(f"   Frames are still available at: {output_dir}")
        return None


def batch_visualize(
    results_dir: str,
    pattern: str = "trial_*.json",
    fps: int = 2,
    max_trials: Optional[int] = None
) -> List[Path]:
    """Batch process multiple trial files.

    Args:
        results_dir: Directory containing trial JSON files
        pattern: Glob pattern for trial files (default: "trial_*.json")
        fps: Frames per second (default: 2)
        max_trials: Maximum number of trials to process (default: all)

    Returns:
        List of paths to generated GIF files
    """
    results_path = Path(results_dir)
    trial_files = sorted(results_path.glob(f"**/{pattern}"))

    if max_trials:
        trial_files = trial_files[:max_trials]

    print(f"\n🎯 Found {len(trial_files)} trial files to process")

    gif_paths = []
    for i, trial_file in enumerate(trial_files, 1):
        print(f"\n{'='*60}")
        print(f"Processing trial {i}/{len(trial_files)}")
        print(f"{'='*60}")

        gif_path = visualize_trial(str(trial_file), fps=fps)
        if gif_path:
            gif_paths.append(gif_path)

    print(f"\n{'='*60}")
    print(f"✅ Batch processing complete!")
    print(f"   Successfully generated {len(gif_paths)}/{len(trial_files)} GIFs")
    print(f"{'='*60}\n")

    return gif_paths


def main():
    """Main CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("=" * 60)
        print("Info Marketplace Trial Visualizer (GIF)")
        print("=" * 60)
        print("\nUsage:")
        print("  Single trial:")
        print("    python visualizer.py <trial_json_path> [fps]")
        print("\n  Batch processing:")
        print("    python visualizer.py --batch <results_dir> [fps] [max_trials]")
        print("\nExamples:")
        print("  python visualizer.py results/mixed_gpt-5.4-mini_20260415/trial_006.json")
        print("  python visualizer.py results/mixed_gpt-5.4-mini_20260415/trial_006.json 4")
        print("  python visualizer.py --batch results/mixed_gpt-5.4-mini_20260415 2")
        print("  python visualizer.py --batch results/ 2 5")
        print("\nOptions:")
        print("  fps: Frames per second (default: 2)")
        print("       - 1: Slow, detailed analysis")
        print("       - 2: Default, balanced")
        print("       - 4: Faster playback")
        print("\nOutput:")
        print("  - GIFs saved to: output/trial_XXX_visualization.gif")
        print("  - Individual frames: output/trial_XXX_visualization/frame_XXXX.png")
        print("\nRequirements:")
        print("  - FFmpeg must be installed (brew install ffmpeg)")
        print("=" * 60)
        sys.exit(1)

    # Parse arguments
    if sys.argv[1] == "--batch":
        # Batch mode
        if len(sys.argv) < 3:
            print("❌ Error: --batch requires a results directory")
            sys.exit(1)

        results_dir = sys.argv[2]
        fps = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        max_trials = int(sys.argv[4]) if len(sys.argv) > 4 else None

        batch_visualize(results_dir, fps=fps, max_trials=max_trials)
    else:
        # Single trial mode
        trial_path = sys.argv[1]
        fps = int(sys.argv[2]) if len(sys.argv) > 2 else 2

        if not Path(trial_path).exists():
            print(f"❌ Error: File not found: {trial_path}")
            sys.exit(1)

        visualize_trial(trial_path, fps=fps)


if __name__ == "__main__":
    main()
