"""
Honour Among Thieves — Single-file submission build.

Merged from:
  - utils/drawing.py   (drawing helpers)
  - levels/tutorial.py (TutorialLevel class)
  - main.py            (WindowConfig, Camera, GameState, GLUT loop)

All geometry uses only OpenGL/GLUT primitives from the course template + glDepth.
Assigned to: Nafiz
"""

import sys
import os
import math
import time

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *


# ══════════════════════════════════════════════════════════════════════════════
# DRAWING HELPERS  (was utils/drawing.py)
# ══════════════════════════════════════════════════════════════════════════════

def set_material(color, emissive=None):
    """Apply a material color (r, g, b) to subsequent geometry.

    Args:
        color: Tuple of (r, g, b) floats in 0.0-1.0 range.
        emissive: Optional (r, g, b) emissive glow color.
    """
    r, g, b = color
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT,  [r * 0.3, g * 0.3, b * 0.3, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE,  [r, g, b, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.2, 0.2, 0.2, 1.0])
    glMaterialf (GL_FRONT_AND_BACK, GL_SHININESS, 20.0)
    if emissive:
        er, eg, eb = emissive
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [er, eg, eb, 1.0])
    else:
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])


def draw_cube(x, y, z, sx, sy, sz, color, emissive=None):
    """Draw a solid cube centered at (x, y, z) with full size (sx, sy, sz).

    Args:
        x, y, z:   World position (center of cube).
        sx, sy, sz: Full width/height/depth.
        color:     (r, g, b) tuple.
        emissive:  Optional (r, g, b) emissive glow.
    """
    set_material(color, emissive)
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glutSolidCube(1)
    glPopMatrix()


def draw_sphere(x, y, z, radius, color, emissive=None, slices=16, stacks=16):
    """Draw a solid sphere at (x, y, z).

    Args:
        x, y, z:  World position (center).
        radius:   Sphere radius.
        color:    (r, g, b) tuple.
        emissive: Optional (r, g, b) emissive glow.
        slices:   Longitudinal divisions.
        stacks:   Latitudinal divisions.
    """
    set_material(color, emissive)
    glPushMatrix()
    glTranslatef(x, y, z)
    glutSolidSphere(radius, slices, stacks)
    glPopMatrix()


def draw_floor_tile(x, z, size, color):
    """Draw a single floor quad on the XZ plane at y=0.

    Args:
        x, z:  World position of tile center.
        size:  Side length of the square tile.
        color: (r, g, b) tuple.
    """
    set_material(color)
    half = size / 2.0
    glBegin(GL_QUADS)
    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(x - half, 0.0, z - half)
    glVertex3f(x + half, 0.0, z - half)
    glVertex3f(x + half, 0.0, z + half)
    glVertex3f(x - half, 0.0, z + half)
    glEnd()


def draw_quad(x, y, z, width, height, normal, color):
    """Draw a single quad (wall segment, ceiling panel, etc.).

    Orientation is determined by the face normal:
      (0,1,0)  → horizontal (floor/ceiling)
      (0,0,±1) → vertical, facing along Z
      (±1,0,0) → vertical, facing along X

    Args:
        x, y, z: Center position.
        width:   Quad width.
        height:  Quad height.
        normal:  (nx, ny, nz) face normal.
        color:   (r, g, b) tuple.
    """
    set_material(color)
    hw = width  / 2.0
    hh = height / 2.0
    nx, ny, nz = normal

    glBegin(GL_QUADS)
    glNormal3f(nx, ny, nz)
    if abs(ny) > 0.5:
        glVertex3f(x - hw, y, z - hh)
        glVertex3f(x + hw, y, z - hh)
        glVertex3f(x + hw, y, z + hh)
        glVertex3f(x - hw, y, z + hh)
    elif abs(nz) > 0.5:
        glVertex3f(x - hw, y - hh, z)
        glVertex3f(x + hw, y - hh, z)
        glVertex3f(x + hw, y + hh, z)
        glVertex3f(x - hw, y + hh, z)
    else:
        glVertex3f(x, y - hh, z - hw)
        glVertex3f(x, y - hh, z + hw)
        glVertex3f(x, y + hh, z + hw)
        glVertex3f(x, y + hh, z - hw)
    glEnd()


def draw_text_2d(x, y, text, window_width=1200, window_height=800):
    """Render bitmap text on the 2D HUD overlay.

    Temporarily switches to orthographic projection, draws text, then restores.

    Args:
        x, y:          Screen pixel coordinates (origin at bottom-left).
        text:          String to render.
        window_width:  Current window width in pixels.
        window_height: Current window height in pixels.
    """
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)


def draw_text_3d(x, y, z, text):
    """Render bitmap text at a 3D world position.

    Args:
        x, y, z: World position for the text.
        text:    String to render.
    """
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos3f(x, y, z)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glEnable(GL_LIGHTING)


# ══════════════════════════════════════════════════════════════════════════════
# TUTORIAL LEVEL  (was levels/tutorial.py)
# Assigned to: Nafiz (Background/level design)
# ══════════════════════════════════════════════════════════════════════════════

class TutorialLevel:
    """
    Self-contained tutorial room.

    All tunable values are class attributes — change them here and they
    propagate everywhere inside the class automatically.
    """

    # ──────────────────────────────────────────────
    # Color Palette
    # ──────────────────────────────────────────────

    COLOR_WALL          = (0.23, 0.23, 0.20)
    COLOR_WALL_ACCENT   = (0.29, 0.25, 0.20)
    COLOR_FLOOR_DARK    = (0.18, 0.18, 0.18)
    COLOR_FLOOR_LIGHT   = (0.24, 0.24, 0.22)
    COLOR_CEILING       = (0.10, 0.10, 0.10)
    COLOR_WOOD_CRATE    = (0.55, 0.41, 0.08)
    COLOR_WOOD_TABLE    = (0.36, 0.25, 0.20)
    COLOR_BULB          = (1.0,  0.84, 0.0)
    COLOR_BULB_EMISSIVE = (1.0,  0.90, 0.4)
    COLOR_GOLD          = (1.0,  0.84, 0.0)
    COLOR_GOLD_EMISSIVE = (0.6,  0.5,  0.0)
    COLOR_DOOR_FRAME    = (0.42, 0.48, 0.55)
    COLOR_PILLAR        = (0.30, 0.30, 0.28)
    COLOR_ALCOVE        = (0.26, 0.24, 0.20)

    # ──────────────────────────────────────────────
    # Room Dimensions
    # ──────────────────────────────────────────────

    ROOM_WIDTH       = 20.0   # X axis
    ROOM_DEPTH       = 20.0   # Z axis
    ROOM_HEIGHT      = 5.0    # Y axis
    WALL_THICKNESS   = 0.5

    ALCOVE_WIDTH     = 4.0
    ALCOVE_DEPTH     = 3.0

    DOOR_WIDTH           = 3.0
    DOOR_HEIGHT          = 3.5
    DOOR_FRAME_THICKNESS = 0.3

    TILE_SIZE = 2.0

    # ──────────────────────────────────────────────
    # Lighting Parameters
    # ──────────────────────────────────────────────

    LIGHT0_AMBIENT  = [0.08, 0.08, 0.12, 1.0]
    LIGHT0_DIFFUSE  = [0.15, 0.15, 0.20, 1.0]
    LIGHT0_SPECULAR = [0.05, 0.05, 0.05, 1.0]

    LIGHT1_AMBIENT               = [0.05, 0.04, 0.02, 1.0]
    LIGHT1_DIFFUSE               = [0.90, 0.75, 0.40, 1.0]
    LIGHT1_SPECULAR              = [0.50, 0.40, 0.20, 1.0]
    LIGHT1_CONSTANT_ATTENUATION  = 1.0
    LIGHT1_LINEAR_ATTENUATION    = 0.05
    LIGHT1_QUADRATIC_ATTENUATION = 0.01

    # ──────────────────────────────────────────────
    # Prop Positions / Sizes
    # ──────────────────────────────────────────────

    BOX_POS  = (-4.0, -2.0)   # (x, z)
    BOX_SIZE = 1.5

    TABLE_POS           = (4.0, 2.0)   # (x, z)
    TABLE_TOP_Y         = 1.2
    TABLE_WIDTH         = 2.5
    TABLE_DEPTH         = 1.5
    TABLE_TOP_THICKNESS = 0.15
    TABLE_LEG_THICKNESS = 0.15

    COLLECTIBLE_BOB_SPEED     = 2.0    # radians / second
    COLLECTIBLE_BOB_AMPLITUDE = 0.15   # world units
    COLLECTIBLE_RADIUS        = 0.3

    PILLAR_POSITIONS = [
        (-6.0, -6.0),
        ( 6.0, -6.0),
        (-6.0,  6.0),
        ( 6.0,  6.0),
    ]

    STACK_POS        = (-7.0, 6.0)   # (x, z)
    STACK_CRATE_SIZE = 1.0

    # ──────────────────────────────────────────────
    # Derived helpers
    # ──────────────────────────────────────────────

    @classmethod
    def spawn_pos(cls):
        """Return the (x, y, z) player spawn position inside the alcove."""
        return (
            0.0,
            1.0,
            -(cls.ROOM_DEPTH / 2.0) - (cls.ALCOVE_DEPTH / 2.0),
        )

    # ──────────────────────────────────────────────
    # Lighting
    # ──────────────────────────────────────────────

    @classmethod
    def setup_level_lighting(cls):
        """Configure lights for the tutorial area.

        GL_LIGHT0: Dim ambient moonlight.
        GL_LIGHT1: Warm overhead point light.
        """
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT,  cls.LIGHT0_AMBIENT)
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  cls.LIGHT0_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_SPECULAR, cls.LIGHT0_SPECULAR)
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, cls.ROOM_HEIGHT + 5.0, 0.0, 0.0])

        glEnable(GL_LIGHT1)
        bulb_pos = [0.0, cls.ROOM_HEIGHT - 0.5, 0.0, 1.0]
        glLightfv(GL_LIGHT1, GL_AMBIENT,  cls.LIGHT1_AMBIENT)
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  cls.LIGHT1_DIFFUSE)
        glLightfv(GL_LIGHT1, GL_SPECULAR, cls.LIGHT1_SPECULAR)
        glLightfv(GL_LIGHT1, GL_POSITION, bulb_pos)
        glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION,  cls.LIGHT1_CONSTANT_ATTENUATION)
        glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION,    cls.LIGHT1_LINEAR_ATTENUATION)
        glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, cls.LIGHT1_QUADRATIC_ATTENUATION)

    # ──────────────────────────────────────────────
    # Geometry
    # ──────────────────────────────────────────────

    @classmethod
    def draw_floor(cls):
        """Draw a checkerboard-pattern tiled floor."""
        half_w = cls.ROOM_WIDTH  / 2.0
        half_d = cls.ROOM_DEPTH  / 2.0

        x = -half_w + cls.TILE_SIZE / 2.0
        ix = 0
        while x < half_w:
            z = -half_d + cls.TILE_SIZE / 2.0
            iz = 0
            while z < half_d:
                color = cls.COLOR_FLOOR_DARK if (ix + iz) % 2 == 0 else cls.COLOR_FLOOR_LIGHT
                draw_floor_tile(x, z, cls.TILE_SIZE, color)
                z += cls.TILE_SIZE
                iz += 1
            x += cls.TILE_SIZE
            ix += 1

        # Alcove floor
        ax = -cls.ALCOVE_WIDTH / 2.0 + cls.TILE_SIZE / 2.0
        az = -half_d - cls.ALCOVE_DEPTH + cls.TILE_SIZE / 2.0
        x = ax
        ix = 0
        while x < cls.ALCOVE_WIDTH / 2.0:
            z = az
            iz = 0
            while z < -half_d:
                color = cls.COLOR_FLOOR_DARK if (ix + iz) % 2 == 0 else cls.COLOR_FLOOR_LIGHT
                draw_floor_tile(x, z, cls.TILE_SIZE, color)
                z += cls.TILE_SIZE
                iz += 1
            x += cls.TILE_SIZE
            ix += 1

    @classmethod
    def draw_ceiling(cls):
        """Draw the ceiling over the main room and alcove."""
        half_w = cls.ROOM_WIDTH / 2.0
        half_d = cls.ROOM_DEPTH / 2.0

        set_material(cls.COLOR_CEILING)
        glBegin(GL_QUADS)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-half_w, cls.ROOM_HEIGHT, -half_d)
        glVertex3f( half_w, cls.ROOM_HEIGHT, -half_d)
        glVertex3f( half_w, cls.ROOM_HEIGHT,  half_d)
        glVertex3f(-half_w, cls.ROOM_HEIGHT,  half_d)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-cls.ALCOVE_WIDTH / 2.0, cls.ROOM_HEIGHT, -half_d - cls.ALCOVE_DEPTH)
        glVertex3f( cls.ALCOVE_WIDTH / 2.0, cls.ROOM_HEIGHT, -half_d - cls.ALCOVE_DEPTH)
        glVertex3f( cls.ALCOVE_WIDTH / 2.0, cls.ROOM_HEIGHT, -half_d)
        glVertex3f(-cls.ALCOVE_WIDTH / 2.0, cls.ROOM_HEIGHT, -half_d)
        glEnd()

    @classmethod
    def draw_walls(cls):
        """Draw perimeter walls with alcove gap (-Z) and door gap (+Z)."""
        half_w = cls.ROOM_WIDTH  / 2.0
        half_d = cls.ROOM_DEPTH  / 2.0
        wall_y = cls.ROOM_HEIGHT / 2.0

        # Left wall
        draw_cube(-half_w, wall_y, 0.0,
                  cls.WALL_THICKNESS, cls.ROOM_HEIGHT, cls.ROOM_DEPTH, cls.COLOR_WALL)
        # Right wall
        draw_cube( half_w, wall_y, 0.0,
                  cls.WALL_THICKNESS, cls.ROOM_HEIGHT, cls.ROOM_DEPTH, cls.COLOR_WALL)

        # Back wall (-Z) — gap for alcove
        seg_w = (cls.ROOM_WIDTH - cls.ALCOVE_WIDTH) / 2.0
        draw_cube(-half_w + seg_w / 2.0, wall_y, -half_d,
                  seg_w, cls.ROOM_HEIGHT, cls.WALL_THICKNESS, cls.COLOR_WALL)
        draw_cube( half_w - seg_w / 2.0, wall_y, -half_d,
                  seg_w, cls.ROOM_HEIGHT, cls.WALL_THICKNESS, cls.COLOR_WALL)

        # Front wall (+Z) — gap for door
        fseg_w = (cls.ROOM_WIDTH - cls.DOOR_WIDTH) / 2.0
        draw_cube(-half_w + fseg_w / 2.0, wall_y, half_d,
                  fseg_w, cls.ROOM_HEIGHT, cls.WALL_THICKNESS, cls.COLOR_WALL)
        draw_cube( half_w - fseg_w / 2.0, wall_y, half_d,
                  fseg_w, cls.ROOM_HEIGHT, cls.WALL_THICKNESS, cls.COLOR_WALL)
        # Top above door
        draw_cube(0.0,
                  cls.DOOR_HEIGHT + (cls.ROOM_HEIGHT - cls.DOOR_HEIGHT) / 2.0, half_d,
                  cls.DOOR_WIDTH, cls.ROOM_HEIGHT - cls.DOOR_HEIGHT, cls.WALL_THICKNESS,
                  cls.COLOR_WALL)

        # Door frame
        ft = cls.DOOR_FRAME_THICKNESS
        draw_cube(-cls.DOOR_WIDTH / 2.0, cls.DOOR_HEIGHT / 2.0, half_d,
                  ft, cls.DOOR_HEIGHT, ft + 0.2, cls.COLOR_DOOR_FRAME)
        draw_cube( cls.DOOR_WIDTH / 2.0, cls.DOOR_HEIGHT / 2.0, half_d,
                  ft, cls.DOOR_HEIGHT, ft + 0.2, cls.COLOR_DOOR_FRAME)
        draw_cube(0.0, cls.DOOR_HEIGHT, half_d,
                  cls.DOOR_WIDTH + ft * 2, ft, ft + 0.2, cls.COLOR_DOOR_FRAME)

    @classmethod
    def draw_alcove(cls):
        """Draw the spawn alcove walls."""
        half_d        = cls.ROOM_DEPTH  / 2.0
        wall_y        = cls.ROOM_HEIGHT / 2.0
        alcove_half_w = cls.ALCOVE_WIDTH / 2.0

        draw_cube(0.0, wall_y, -half_d - cls.ALCOVE_DEPTH,
                  cls.ALCOVE_WIDTH + cls.WALL_THICKNESS, cls.ROOM_HEIGHT, cls.WALL_THICKNESS,
                  cls.COLOR_ALCOVE)
        draw_cube(-alcove_half_w, wall_y, -half_d - cls.ALCOVE_DEPTH / 2.0,
                  cls.WALL_THICKNESS, cls.ROOM_HEIGHT, cls.ALCOVE_DEPTH, cls.COLOR_ALCOVE)
        draw_cube( alcove_half_w, wall_y, -half_d - cls.ALCOVE_DEPTH / 2.0,
                  cls.WALL_THICKNESS, cls.ROOM_HEIGHT, cls.ALCOVE_DEPTH, cls.COLOR_ALCOVE)

    @classmethod
    def draw_overhead_light(cls):
        """Draw the visible light bulb hanging from the ceiling."""
        bulb_y = cls.ROOM_HEIGHT - 0.5
        draw_cube(0.0, cls.ROOM_HEIGHT - 0.2, 0.0, 0.05, 0.6, 0.05, (0.15, 0.15, 0.15))
        draw_sphere(0.0, bulb_y, 0.0, 0.25, cls.COLOR_BULB, emissive=cls.COLOR_BULB_EMISSIVE)
        draw_cube(0.0, cls.ROOM_HEIGHT - 0.05, 0.0, 0.3, 0.1, 0.3, (0.2, 0.2, 0.2))

    @classmethod
    def draw_wooden_box(cls):
        """Draw a wooden crate — placeholder for Ahona's obstacle system."""
        box_x, box_z = cls.BOX_POS
        s  = cls.BOX_SIZE
        by = s / 2.0
        dark_wood = (0.45, 0.33, 0.06)
        draw_cube(box_x, by, box_z, s, s, s, cls.COLOR_WOOD_CRATE)
        plank_off = s / 2.0 + 0.01
        draw_cube(box_x, by, box_z + plank_off, s * 0.9, 0.1,    0.05, dark_wood)
        draw_cube(box_x, by, box_z + plank_off, 0.1,    s * 0.9, 0.05, dark_wood)

    @classmethod
    def draw_table(cls):
        """Draw a table with 4 legs."""
        tx, tz = cls.TABLE_POS
        ty  = cls.TABLE_TOP_Y
        tw  = cls.TABLE_WIDTH
        td  = cls.TABLE_DEPTH
        tt  = cls.TABLE_TOP_THICKNESS
        lt  = cls.TABLE_LEG_THICKNESS
        lh  = ty - tt / 2.0
        ly  = lh / 2.0
        lxo = tw / 2.0 - lt
        lzo = td / 2.0 - lt

        draw_cube(tx, ty, tz, tw, tt, td, cls.COLOR_WOOD_TABLE)
        for dx in (-1, 1):
            for dz in (-1, 1):
                draw_cube(tx + dx * lxo, ly, tz + dz * lzo,
                          lt, lh, lt, cls.COLOR_WOOD_TABLE)

    @classmethod
    def draw_collectible(cls, time_elapsed):
        """Draw a bobbing gold sphere on the table.

        Args:
            time_elapsed: Elapsed time in seconds.
        """
        tx, tz = cls.TABLE_POS
        base_y = cls.TABLE_TOP_Y + 0.4
        bob_y  = base_y + math.sin(time_elapsed * cls.COLLECTIBLE_BOB_SPEED) * cls.COLLECTIBLE_BOB_AMPLITUDE
        draw_sphere(tx, bob_y, tz, cls.COLLECTIBLE_RADIUS, cls.COLOR_GOLD, emissive=cls.COLOR_GOLD_EMISSIVE)

    @classmethod
    def draw_pillars(cls):
        """Draw decorative pillars for visual depth and cover practice."""
        for px, pz in cls.PILLAR_POSITIONS:
            shaft_h = cls.ROOM_HEIGHT - 0.6
            draw_cube(px, 0.15,                  pz, 1.0, 0.3,     1.0, cls.COLOR_PILLAR)
            draw_cube(px, shaft_h / 2.0 + 0.3,   pz, 0.6, shaft_h, 0.6, cls.COLOR_PILLAR)
            draw_cube(px, cls.ROOM_HEIGHT - 0.15, pz, 1.0, 0.3,     1.0, cls.COLOR_PILLAR)

    @classmethod
    def draw_stacked_crates(cls):
        """Draw a corner stack of crates for environmental detail."""
        bx, bz = cls.STACK_POS
        s      = cls.STACK_CRATE_SIZE
        draw_cube(bx,       s / 2.0, bz, s, s, s, cls.COLOR_WOOD_CRATE)
        draw_cube(bx + 1.1, s / 2.0, bz, s, s, s, cls.COLOR_WOOD_CRATE)
        draw_cube(bx + 0.2, s * 1.5, bz, s, s, s, (0.50, 0.37, 0.07))

    @classmethod
    def draw_tutorial_hints(cls):
        """Draw HUD tutorial text."""
        draw_text_2d(20, 760, "TUTORIAL AREA")
        draw_text_2d(20, 730, "WASD - Move   |   Mouse - Look Around")
        draw_text_2d(20, 700, "Find the golden item on the table and walk to it")
        draw_text_2d(20, 40,  "Head to the exit doorway when ready...")

    @classmethod
    def draw_alcove_marker(cls):
        """Draw an in-world START marker in the spawn alcove."""
        draw_text_3d(
            0.0, 2.5,
            -(cls.ROOM_DEPTH / 2.0) - cls.ALCOVE_DEPTH + 1.0,
            "START"
        )

    @classmethod
    def draw(cls, time_elapsed):
        """Main draw entry point — called every frame by the game loop.

        Args:
            time_elapsed: Total elapsed time in seconds (drives animations).
        """
        cls.setup_level_lighting()
        cls.draw_floor()
        cls.draw_ceiling()
        cls.draw_walls()
        cls.draw_alcove()
        cls.draw_overhead_light()
        cls.draw_wooden_box()
        cls.draw_table()
        cls.draw_collectible(time_elapsed)
        cls.draw_pillars()
        cls.draw_stacked_crates()
        cls.draw_tutorial_hints()
        cls.draw_alcove_marker()


# ══════════════════════════════════════════════════════════════════════════════
# WINDOW CONFIGURATION  (was main.py → WindowConfig)
# ══════════════════════════════════════════════════════════════════════════════

class WindowConfig:
    """Tunable window / display settings."""
    WIDTH  = 1200
    HEIGHT = 800
    TITLE  = b"Honour Among Thieves"
    FOV    = 60.0    # Perspective field-of-view in degrees
    Z_NEAR = 0.1
    Z_FAR  = 200.0


# ══════════════════════════════════════════════════════════════════════════════
# CAMERA  (was main.py → Camera)
# Temporary free-look — Mehrab will replace this with his camera system.
# ══════════════════════════════════════════════════════════════════════════════

class Camera:
    """
    Temporary free-look camera.

    All tunable values live here as class attributes.
    Mehrab will replace this class with his own camera system.
    """

    START_YAW   = 90.0   # Start facing +Z into the room
    START_PITCH = 0.0

    MOVE_SPEED        = 0.15
    MOUSE_SENSITIVITY = 0.15
    PITCH_LIMIT       = 89.0
    MOUSE_WARP_THRESHOLD = 100

    def __init__(self, x, y, z):
        self.x     = x
        self.y     = y
        self.z     = z
        self.yaw   = Camera.START_YAW
        self.pitch = Camera.START_PITCH

        self.keys_pressed = {b'w': False, b's': False, b'a': False, b'd': False}

        self.mouse_last_x = WindowConfig.WIDTH  // 2
        self.mouse_last_y = WindowConfig.HEIGHT // 2
        self.captured     = True
        self.first_move   = True

    def _look_direction(self):
        rad_yaw   = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        lx = math.cos(rad_pitch) * math.cos(rad_yaw)
        ly = math.sin(rad_pitch)
        lz = math.cos(rad_pitch) * math.sin(rad_yaw)
        return lx, ly, lz

    def process_movement(self):
        """Update position based on currently pressed keys."""
        rad_yaw   = math.radians(self.yaw)
        forward_x = math.cos(rad_yaw)
        forward_z = math.sin(rad_yaw)
        right_x   = math.cos(rad_yaw - math.pi / 2.0)
        right_z   = math.sin(rad_yaw - math.pi / 2.0)
        spd = Camera.MOVE_SPEED

        if self.keys_pressed.get(b'w'): self.x += forward_x * spd; self.z += forward_z * spd
        if self.keys_pressed.get(b's'): self.x -= forward_x * spd; self.z -= forward_z * spd
        if self.keys_pressed.get(b'a'): self.x += right_x   * spd; self.z += right_z   * spd
        if self.keys_pressed.get(b'd'): self.x -= right_x   * spd; self.z -= right_z   * spd

    def apply(self):
        """Apply camera transform to the OpenGL modelview matrix."""
        lx, ly, lz = self._look_direction()
        glLoadIdentity()
        gluLookAt(self.x, self.y, self.z,
                  self.x + lx, self.y + ly, self.z + lz,
                  0.0, 1.0, 0.0)

    def on_key_down(self, key):
        if key in self.keys_pressed:
            self.keys_pressed[key] = True

    def on_key_up(self, key):
        if key in self.keys_pressed:
            self.keys_pressed[key] = False

    def on_mouse_move(self, x, y):
        if not self.captured:
            return
        if self.first_move:
            self.mouse_last_x = x
            self.mouse_last_y = y
            self.first_move = False
            return

        dx = x - self.mouse_last_x
        dy = self.mouse_last_y - y   # Inverted Y
        self.mouse_last_x = x
        self.mouse_last_y = y

        self.yaw   += dx * Camera.MOUSE_SENSITIVITY
        self.pitch += dy * Camera.MOUSE_SENSITIVITY
        limit = Camera.PITCH_LIMIT
        self.pitch = max(-limit, min(limit, self.pitch))

        cx = WindowConfig.WIDTH  // 2
        cy = WindowConfig.HEIGHT // 2
        if abs(x - cx) > Camera.MOUSE_WARP_THRESHOLD or abs(y - cy) > Camera.MOUSE_WARP_THRESHOLD:
            glutWarpPointer(cx, cy)
            self.mouse_last_x = cx
            self.mouse_last_y = cy

    def toggle_capture(self):
        self.captured = not self.captured
        glutSetCursor(GLUT_CURSOR_NONE if self.captured else GLUT_CURSOR_INHERIT)


# ══════════════════════════════════════════════════════════════════════════════
# GAME STATE  (was main.py → GameState)
# ══════════════════════════════════════════════════════════════════════════════

class GameState:
    """Tracks which level/phase is currently active."""
    TUTORIAL       = "tutorial"
    STEALING_AREA  = "stealing_area"
    POLICE_STATION = "police_station"
    CUTSCENE       = "cutscene"
    WIN            = "win"
    LOSE           = "lose"

    def __init__(self):
        self.current = GameState.TUTORIAL


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCES & GLUT LOOP
# ══════════════════════════════════════════════════════════════════════════════

_spawn     = TutorialLevel.spawn_pos()
camera     = Camera(_spawn[0], _spawn[1], _spawn[2])
game_state = GameState()
start_time = 0.0


def init():
    """Initialize OpenGL settings."""
    glClearColor(0.02, 0.02, 0.05, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_NORMALIZE)
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.05, 0.05, 0.07, 1.0])
    glShadeModel(GL_SMOOTH)
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)


def setup_projection():
    """Set up the perspective projection matrix."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(
        WindowConfig.FOV,
        WindowConfig.WIDTH / WindowConfig.HEIGHT,
        WindowConfig.Z_NEAR,
        WindowConfig.Z_FAR,
    )
    glMatrixMode(GL_MODELVIEW)


def display():
    """Main render callback."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    setup_projection()
    camera.process_movement()
    camera.apply()

    time_elapsed = time.time() - start_time

    if game_state.current == GameState.TUTORIAL:
        TutorialLevel.draw(time_elapsed)

    glutSwapBuffers()


def idle():
    """Keep the render loop alive."""
    glutPostRedisplay()


def reshape(width, height):
    """Handle window resize."""
    if height == 0:
        height = 1
    WindowConfig.WIDTH  = width
    WindowConfig.HEIGHT = height
    glViewport(0, 0, width, height)
    setup_projection()


def keyboard_down(key, x, y):
    if key == b'\x1b':
        camera.toggle_capture()
        return
    camera.on_key_down(key)


def keyboard_up(key, x, y):
    camera.on_key_up(key)


def mouse_motion(x, y):
    camera.on_mouse_move(x, y)


def main():
    """Initialize GLUT, create window, register callbacks, start main loop."""
    global start_time

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WindowConfig.WIDTH, WindowConfig.HEIGHT)
    glutInitWindowPosition(100, 50)
    glutCreateWindow(WindowConfig.TITLE)

    init()
    start_time = time.time()

    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutPassiveMotionFunc(mouse_motion)
    glutMotionFunc(mouse_motion)

    glutSetCursor(GLUT_CURSOR_NONE)

    print("=== Honour Among Thieves ===")
    print("Tutorial Area loaded.")
    print("Controls: WASD to move, Mouse to look, ESC to release cursor")
    print()

    glutMainLoop()


if __name__ == "__main__":
    main()
