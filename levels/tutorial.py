"""
tutorial.py — Tutorial area level for Honour Among Thieves.

Layout: A small enclosed room where the player learns basic mechanics.
- Spawn alcove at one end
- Main courtyard with practice obstacles and a collectible
- Exit doorway leading to the stealing area

All geometry uses GLUT primitives only. No external assets.

Assigned to: Nafiz (Background/level design)
"""

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from utils.drawing import (
    draw_cube,
    draw_sphere,
    draw_floor_tile,
    draw_quad,
    draw_text_2d,
    draw_text_3d,
    set_material,
)

# ──────────────────────────────────────────────
# Color Palette
# ──────────────────────────────────────────────

# Walls — dark stone grey-brown
COLOR_WALL = (0.23, 0.23, 0.20)
COLOR_WALL_ACCENT = (0.29, 0.25, 0.20)

# Floor tiles — alternating dark stone
COLOR_FLOOR_DARK = (0.18, 0.18, 0.18)
COLOR_FLOOR_LIGHT = (0.24, 0.24, 0.22)

# Ceiling — very dark
COLOR_CEILING = (0.10, 0.10, 0.10)

# Wooden props
COLOR_WOOD_CRATE = (0.55, 0.41, 0.08)
COLOR_WOOD_TABLE = (0.36, 0.25, 0.20)

# Light bulb
COLOR_BULB = (1.0, 0.84, 0.0)
COLOR_BULB_EMISSIVE = (1.0, 0.90, 0.4)

# Collectible — gold
COLOR_GOLD = (1.0, 0.84, 0.0)
COLOR_GOLD_EMISSIVE = (0.6, 0.5, 0.0)

# Exit door frame — blue-grey metal
COLOR_DOOR_FRAME = (0.42, 0.48, 0.55)

# Pillar — slightly lighter stone
COLOR_PILLAR = (0.30, 0.30, 0.28)

# Spawn alcove — slightly warmer wall
COLOR_ALCOVE = (0.26, 0.24, 0.20)

# ──────────────────────────────────────────────
# Room Dimensions
# ──────────────────────────────────────────────

# Main room — centered at origin, extends in X and Z
ROOM_WIDTH = 20.0       # X axis
ROOM_DEPTH = 20.0       # Z axis
ROOM_HEIGHT = 5.0       # Y axis
WALL_THICKNESS = 0.5

# Spawn alcove (attached to -Z wall, centered on X)
ALCOVE_WIDTH = 4.0
ALCOVE_DEPTH = 3.0

# Exit doorway (in +Z wall, centered on X)
DOOR_WIDTH = 3.0
DOOR_HEIGHT = 3.5
DOOR_FRAME_THICKNESS = 0.3

# Floor tile size
TILE_SIZE = 2.0

# Player spawn position (inside the alcove)
SPAWN_POS = (0.0, 1.0, -(ROOM_DEPTH / 2.0) - (ALCOVE_DEPTH / 2.0))


def setup_level_lighting():
    """Configure lights specific to the tutorial area.

    GL_LIGHT0: Dim ambient moonlight (cool blue-grey fill).
    GL_LIGHT1: Warm point light at the overhead bulb position.
    """
    # Light 0 — dim ambient fill (moonlight)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.08, 0.08, 0.12, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.15, 0.15, 0.20, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.05, 0.05, 0.05, 1.0])
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, ROOM_HEIGHT + 5.0, 0.0, 0.0])  # Directional from above

    # Light 1 — warm overhead point light (the visible bulb)
    glEnable(GL_LIGHT1)
    bulb_pos = [0.0, ROOM_HEIGHT - 0.5, 0.0, 1.0]  # Point light
    glLightfv(GL_LIGHT1, GL_AMBIENT, [0.05, 0.04, 0.02, 1.0])
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.9, 0.75, 0.4, 1.0])
    glLightfv(GL_LIGHT1, GL_SPECULAR, [0.5, 0.4, 0.2, 1.0])
    glLightfv(GL_LIGHT1, GL_POSITION, bulb_pos)
    # Attenuation for point light falloff
    glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 1.0)
    glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.05)
    glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.01)


def draw_floor():
    """Draw a checkerboard-pattern tiled floor."""
    half_w = ROOM_WIDTH / 2.0
    half_d = ROOM_DEPTH / 2.0

    # Main room floor tiles
    x = -half_w + TILE_SIZE / 2.0
    ix = 0
    while x < half_w:
        z = -half_d + TILE_SIZE / 2.0
        iz = 0
        while z < half_d:
            color = COLOR_FLOOR_DARK if (ix + iz) % 2 == 0 else COLOR_FLOOR_LIGHT
            draw_floor_tile(x, z, TILE_SIZE, color)
            z += TILE_SIZE
            iz += 1
        x += TILE_SIZE
        ix += 1

    # Alcove floor tiles
    alcove_start_x = -ALCOVE_WIDTH / 2.0 + TILE_SIZE / 2.0
    alcove_start_z = -half_d - ALCOVE_DEPTH + TILE_SIZE / 2.0
    x = alcove_start_x
    ix = 0
    while x < ALCOVE_WIDTH / 2.0:
        z = alcove_start_z
        iz = 0
        while z < -half_d:
            color = COLOR_FLOOR_DARK if (ix + iz) % 2 == 0 else COLOR_FLOOR_LIGHT
            draw_floor_tile(x, z, TILE_SIZE, color)
            z += TILE_SIZE
            iz += 1
        x += TILE_SIZE
        ix += 1


def draw_ceiling():
    """Draw the ceiling quad covering the main room."""
    half_w = ROOM_WIDTH / 2.0
    half_d = ROOM_DEPTH / 2.0

    set_material(COLOR_CEILING)
    glBegin(GL_QUADS)
    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-half_w, ROOM_HEIGHT, -half_d)
    glVertex3f(half_w, ROOM_HEIGHT, -half_d)
    glVertex3f(half_w, ROOM_HEIGHT, half_d)
    glVertex3f(-half_w, ROOM_HEIGHT, half_d)
    glEnd()

    # Alcove ceiling
    glBegin(GL_QUADS)
    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-ALCOVE_WIDTH / 2.0, ROOM_HEIGHT, -half_d - ALCOVE_DEPTH)
    glVertex3f(ALCOVE_WIDTH / 2.0, ROOM_HEIGHT, -half_d - ALCOVE_DEPTH)
    glVertex3f(ALCOVE_WIDTH / 2.0, ROOM_HEIGHT, -half_d)
    glVertex3f(-ALCOVE_WIDTH / 2.0, ROOM_HEIGHT, -half_d)
    glEnd()


def draw_walls():
    """Draw the perimeter walls of the main room and spawn alcove.

    Walls are solid cubes scaled as thin slabs. The -Z wall has a gap for
    the alcove entrance, and the +Z wall has a gap for the exit doorway.
    """
    half_w = ROOM_WIDTH / 2.0
    half_d = ROOM_DEPTH / 2.0
    wall_y = ROOM_HEIGHT / 2.0

    # ── Left wall (-X side) ──
    draw_cube(
        -half_w, wall_y, 0.0,
        WALL_THICKNESS, ROOM_HEIGHT, ROOM_DEPTH,
        COLOR_WALL
    )

    # ── Right wall (+X side) ──
    draw_cube(
        half_w, wall_y, 0.0,
        WALL_THICKNESS, ROOM_HEIGHT, ROOM_DEPTH,
        COLOR_WALL
    )

    # ── Back wall (-Z side) — with gap for alcove entrance ──
    # Left segment of back wall
    left_seg_width = (ROOM_WIDTH - ALCOVE_WIDTH) / 2.0
    draw_cube(
        -half_w + left_seg_width / 2.0, wall_y, -half_d,
        left_seg_width, ROOM_HEIGHT, WALL_THICKNESS,
        COLOR_WALL
    )
    # Right segment of back wall
    draw_cube(
        half_w - left_seg_width / 2.0, wall_y, -half_d,
        left_seg_width, ROOM_HEIGHT, WALL_THICKNESS,
        COLOR_WALL
    )

    # ── Front wall (+Z side) — with gap for exit doorway ──
    # Left segment of front wall
    front_left_width = (ROOM_WIDTH - DOOR_WIDTH) / 2.0
    draw_cube(
        -half_w + front_left_width / 2.0, wall_y, half_d,
        front_left_width, ROOM_HEIGHT, WALL_THICKNESS,
        COLOR_WALL
    )
    # Right segment of front wall
    draw_cube(
        half_w - front_left_width / 2.0, wall_y, half_d,
        front_left_width, ROOM_HEIGHT, WALL_THICKNESS,
        COLOR_WALL
    )
    # Top segment above door
    draw_cube(
        0.0, DOOR_HEIGHT + (ROOM_HEIGHT - DOOR_HEIGHT) / 2.0, half_d,
        DOOR_WIDTH, ROOM_HEIGHT - DOOR_HEIGHT, WALL_THICKNESS,
        COLOR_WALL
    )

    # ── Door frame (decorative trim) ──
    # Left frame
    draw_cube(
        -DOOR_WIDTH / 2.0, DOOR_HEIGHT / 2.0, half_d,
        DOOR_FRAME_THICKNESS, DOOR_HEIGHT, DOOR_FRAME_THICKNESS + 0.2,
        COLOR_DOOR_FRAME
    )
    # Right frame
    draw_cube(
        DOOR_WIDTH / 2.0, DOOR_HEIGHT / 2.0, half_d,
        DOOR_FRAME_THICKNESS, DOOR_HEIGHT, DOOR_FRAME_THICKNESS + 0.2,
        COLOR_DOOR_FRAME
    )
    # Top frame (lintel)
    draw_cube(
        0.0, DOOR_HEIGHT, half_d,
        DOOR_WIDTH + DOOR_FRAME_THICKNESS * 2, DOOR_FRAME_THICKNESS, DOOR_FRAME_THICKNESS + 0.2,
        COLOR_DOOR_FRAME
    )


def draw_alcove():
    """Draw the spawn alcove walls (attached to the -Z side of the main room)."""
    half_d = ROOM_DEPTH / 2.0
    wall_y = ROOM_HEIGHT / 2.0
    alcove_half_w = ALCOVE_WIDTH / 2.0

    # Alcove back wall (furthest from main room)
    draw_cube(
        0.0, wall_y, -half_d - ALCOVE_DEPTH,
        ALCOVE_WIDTH + WALL_THICKNESS, ROOM_HEIGHT, WALL_THICKNESS,
        COLOR_ALCOVE
    )

    # Alcove left wall
    draw_cube(
        -alcove_half_w, wall_y, -half_d - ALCOVE_DEPTH / 2.0,
        WALL_THICKNESS, ROOM_HEIGHT, ALCOVE_DEPTH,
        COLOR_ALCOVE
    )

    # Alcove right wall
    draw_cube(
        alcove_half_w, wall_y, -half_d - ALCOVE_DEPTH / 2.0,
        WALL_THICKNESS, ROOM_HEIGHT, ALCOVE_DEPTH,
        COLOR_ALCOVE
    )


def draw_overhead_light():
    """Draw the visible light bulb hanging from the ceiling.

    The actual GL_LIGHT1 is positioned in setup_level_lighting().
    This draws the visible bulb geometry with emissive glow.
    """
    bulb_y = ROOM_HEIGHT - 0.5

    # Wire/cord from ceiling to bulb
    draw_cube(0.0, ROOM_HEIGHT - 0.2, 0.0, 0.05, 0.6, 0.05, (0.15, 0.15, 0.15))

    # Light bulb (sphere with emissive glow)
    draw_sphere(0.0, bulb_y, 0.0, 0.25, COLOR_BULB, emissive=COLOR_BULB_EMISSIVE)

    # Small fixture base
    draw_cube(0.0, ROOM_HEIGHT - 0.05, 0.0, 0.3, 0.1, 0.3, (0.2, 0.2, 0.2))


def draw_wooden_box():
    """Draw a wooden crate/box — placeholder for Ahona's obstacle interaction.

    Positioned in the left area of the courtyard.
    """
    box_x, box_z = -4.0, -2.0
    box_size = 1.5
    box_y = box_size / 2.0

    # Main box body
    draw_cube(box_x, box_y, box_z, box_size, box_size, box_size, COLOR_WOOD_CRATE)

    # Cross-planks (decorative detail using thin cubes)
    plank_offset = box_size / 2.0 + 0.01
    # Front face X plank
    draw_cube(box_x, box_y, box_z + plank_offset, box_size * 0.9, 0.1, 0.05, (0.45, 0.33, 0.06))
    # Front face vertical plank
    draw_cube(box_x, box_y, box_z + plank_offset, 0.1, box_size * 0.9, 0.05, (0.45, 0.33, 0.06))


def draw_table():
    """Draw a table with 4 legs.

    Positioned in the right area of the courtyard, holding a collectible.
    """
    table_x, table_z = 4.0, 2.0
    table_top_y = 1.2
    table_w, table_d = 2.5, 1.5
    top_thickness = 0.15
    leg_thickness = 0.15
    leg_height = table_top_y - top_thickness / 2.0

    # Tabletop
    draw_cube(
        table_x, table_top_y, table_z,
        table_w, top_thickness, table_d,
        COLOR_WOOD_TABLE
    )

    # 4 Legs
    leg_x_offset = (table_w / 2.0) - leg_thickness
    leg_z_offset = (table_d / 2.0) - leg_thickness
    leg_y = leg_height / 2.0

    for dx in [-1, 1]:
        for dz in [-1, 1]:
            lx = table_x + dx * leg_x_offset
            lz = table_z + dz * leg_z_offset
            draw_cube(lx, leg_y, lz, leg_thickness, leg_height, leg_thickness, COLOR_WOOD_TABLE)


def draw_collectible(time_elapsed):
    """Draw a collectible item (gold sphere) on the table.

    Has a gentle bobbing animation and emissive glow.

    Args:
        time_elapsed: Elapsed time in seconds for animation.
    """
    import math
    table_x, table_z = 4.0, 2.0
    base_y = 1.6
    bob_y = base_y + math.sin(time_elapsed * 2.0) * 0.15

    draw_sphere(table_x, bob_y, table_z, 0.3, COLOR_GOLD, emissive=COLOR_GOLD_EMISSIVE)


def draw_pillars():
    """Draw decorative pillars in the main room for visual depth and cover practice."""
    pillar_radius_approx = 0.4
    pillar_positions = [
        (-6.0, -6.0),
        (6.0, -6.0),
        (-6.0, 6.0),
        (6.0, 6.0),
    ]

    for px, pz in pillar_positions:
        # Base
        draw_cube(px, 0.15, pz, 1.0, 0.3, 1.0, COLOR_PILLAR)
        # Shaft (stack of cubes to approximate a column)
        shaft_height = ROOM_HEIGHT - 0.6
        draw_cube(px, shaft_height / 2.0 + 0.3, pz, 0.6, shaft_height, 0.6, COLOR_PILLAR)
        # Capital (top)
        draw_cube(px, ROOM_HEIGHT - 0.15, pz, 1.0, 0.3, 1.0, COLOR_PILLAR)


def draw_stacked_crates():
    """Draw a small stack of crates in a corner for environmental detail."""
    base_x, base_z = -7.0, 6.0
    crate_size = 1.0

    # Bottom crate
    draw_cube(base_x, crate_size / 2.0, base_z, crate_size, crate_size, crate_size, COLOR_WOOD_CRATE)
    # Second crate (offset slightly)
    draw_cube(base_x + 1.1, crate_size / 2.0, base_z, crate_size, crate_size, crate_size, COLOR_WOOD_CRATE)
    # Top crate (on first)
    draw_cube(base_x + 0.2, crate_size * 1.5, base_z, crate_size, crate_size, crate_size,
              (0.50, 0.37, 0.07))


def draw_tutorial_hints():
    """Draw HUD text with tutorial instructions."""
    draw_text_2d(20, 760, "TUTORIAL AREA")
    draw_text_2d(20, 730, "WASD - Move   |   Mouse - Look Around")
    draw_text_2d(20, 700, "Find the golden item on the table and walk to it")
    draw_text_2d(20, 40, "Head to the exit doorway when ready...")


def draw_alcove_marker():
    """Draw an in-world text marker in the spawn alcove."""
    draw_text_3d(0.0, 2.5, -(ROOM_DEPTH / 2.0) - ALCOVE_DEPTH + 1.0, "START")


def draw(time_elapsed):
    """Main draw function for the tutorial level.

    Called every frame by the game loop.

    Args:
        time_elapsed: Total elapsed time in seconds (for animations).
    """
    setup_level_lighting()
    draw_floor()
    draw_ceiling()
    draw_walls()
    draw_alcove()
    draw_overhead_light()
    draw_wooden_box()
    draw_table()
    draw_collectible(time_elapsed)
    draw_pillars()
    draw_stacked_crates()
    draw_tutorial_hints()
    draw_alcove_marker()
