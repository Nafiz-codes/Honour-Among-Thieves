"""
levels/level2.py  —  HeistLevel: The Grand Mansion Heist Arena.

Level 2 is the main playing field for Honour Among Thieves.
It is an 80×60 unit multi-room mansion with:
  - 8 interconnected rooms
  - 8 breakable point lights (shoot / press L to cycle off)
  - Overhead hangable bars in the corridor and kitchen
  - Floor and wall vents with grating details
  - Upper cabinets and hidden areas for loot
  - 5 collectible items with bobbing animation
  - Cupboards, glass display cases, lockers, bunk beds, and more

Assigned to: Nafiz (Level Design / Background)
"""

import math
from OpenGL.GL   import *
from OpenGL.GLUT import *
from OpenGL.GLU  import *

# ──────────────────────────────────────────────────────────────────────────────
# Re-use drawing helpers from the shared utility module
# ──────────────────────────────────────────────────────────────────────────────
from utils.drawing import (
    set_material, draw_cube, draw_sphere,
    draw_floor_tile, draw_quad,
    draw_text_2d, draw_text_3d,
)


# ══════════════════════════════════════════════════════════════════════════════
class HeistLevel:
    """
    Grand Mansion — Level 2.

    All tunable layout values are class-level constants.
    All mutable state (light flags, collectible timers) are class-level lists
    so they persist across frames without needing an instance.

    Coordinate system
    ─────────────────
    Origin (0, 0, 0) = centre of Grand Foyer floor.
    +X  = East   |  –X = West
    +Z  = South  |  –Z = North
    +Y  = Up
    """

    # ──────────────────────────────────────────────────────
    # ROOM DIMENSIONS  (all units are OpenGL world units)
    # ──────────────────────────────────────────────────────

    # Grand Foyer — central hub
    FOYER_W       = 24.0
    FOYER_D       = 20.0
    FOYER_H       = 10.0   # Tall double-height ceiling
    FOYER_X       = 0.0
    FOYER_Z       = 0.0

    # Main Corridor — east spine connecting north rooms
    CORR_W        = 8.0
    CORR_D        = 36.0
    CORR_H        = 6.0
    CORR_X        = 16.0   # East of foyer
    CORR_Z        = -8.0   # North-centre

    # Security Office — north-west
    SEC_W         = 14.0
    SEC_D         = 12.0
    SEC_H         = 5.0
    SEC_X         = -25.0
    SEC_Z         = -16.0

    # Trophy Vault — north-east
    VAULT_W       = 14.0
    VAULT_D       = 14.0
    VAULT_H       = 6.0
    VAULT_X       = 27.0
    VAULT_Z       = -20.0

    # Library — east side
    LIB_W         = 12.0
    LIB_D         = 16.0
    LIB_H         = 8.0    # Tall for upper walkway
    LIB_X         = 27.0
    LIB_Z         = 8.0

    # Utility Room — west side
    UTIL_W        = 10.0
    UTIL_D        = 14.0
    UTIL_H        = 6.0
    UTIL_X        = -25.0
    UTIL_Z        = 8.0

    # Kitchen — south-west
    KITCH_W       = 18.0
    KITCH_D       = 14.0
    KITCH_H       = 5.0
    KITCH_X       = -8.0
    KITCH_Z       = 22.0

    # Guard Barracks — south-east
    BUNK_W        = 12.0
    BUNK_D        = 14.0
    BUNK_H        = 5.0
    BUNK_X        = 14.0
    BUNK_Z        = 22.0

    WALL_T        = 0.5    # Universal wall thickness
    MEZZANINE_Y   = 3.5    # Height of upper walkways / balconies
    MEZZANINE_T   = 0.3    # Floor slab thickness

    DOOR_W        = 2.8
    DOOR_H        = 3.2
    DOOR_FT       = 0.25   # Door frame thickness

    # ──────────────────────────────────────────────────────
    # COLOR PALETTE
    # ──────────────────────────────────────────────────────

    # Walls & structure
    C_WALL_STONE    = (0.28, 0.27, 0.24)
    C_WALL_PLASTER  = (0.32, 0.30, 0.26)
    C_WALL_DARK     = (0.15, 0.14, 0.12)
    C_CEILING       = (0.10, 0.10, 0.09)
    C_CEILING_DARK  = (0.08, 0.07, 0.06)
    C_SKIRTING      = (0.20, 0.18, 0.14)

    # Floors
    C_TILE_A        = (0.18, 0.17, 0.15)   # Dark tile
    C_TILE_B        = (0.28, 0.26, 0.20)   # Light tile
    C_TILE_GOLD     = (0.45, 0.38, 0.12)   # Gold accent tile (foyer)
    C_CONCRETE      = (0.22, 0.22, 0.22)
    C_WOOD_FLOOR    = (0.35, 0.24, 0.12)

    # Wood tones
    C_WOOD_DARK     = (0.25, 0.15, 0.07)
    C_WOOD_MED      = (0.40, 0.28, 0.12)
    C_WOOD_LIGHT    = (0.55, 0.40, 0.20)
    C_MAHOGANY      = (0.35, 0.10, 0.05)

    # Metal tones
    C_METAL_DARK    = (0.18, 0.18, 0.20)
    C_METAL_MED     = (0.35, 0.35, 0.38)
    C_METAL_LIGHT   = (0.55, 0.55, 0.60)
    C_BRASS         = (0.72, 0.58, 0.15)
    C_COPPER        = (0.55, 0.30, 0.10)

    # Glass / surfaces
    C_GLASS         = (0.40, 0.55, 0.65)
    C_MONITOR_OFF   = (0.05, 0.05, 0.08)
    C_MONITOR_ON    = (0.05, 0.15, 0.35)
    C_MONITOR_EM    = (0.02, 0.08, 0.30)

    # Lights — bulb mesh colours
    C_BULB_WARM     = (1.00, 0.88, 0.55)
    C_BULB_WARM_EM  = (0.90, 0.70, 0.30)
    C_BULB_COLD     = (0.75, 0.85, 1.00)
    C_BULB_COLD_EM  = (0.40, 0.55, 0.90)
    C_BULB_RED      = (1.00, 0.18, 0.08)
    C_BULB_RED_EM   = (0.70, 0.08, 0.02)
    C_BULB_DEAD     = (0.12, 0.12, 0.12)
    C_LASER         = (0.90, 0.05, 0.05)
    C_LASER_EM      = (0.70, 0.02, 0.02)

    # Collectibles
    C_IDOL          = (1.00, 0.84, 0.00)
    C_IDOL_EM       = (0.60, 0.45, 0.00)
    C_KEYCARD       = (0.10, 0.90, 0.30)
    C_KEYCARD_EM    = (0.03, 0.50, 0.10)
    C_CASH          = (0.20, 0.80, 0.55)
    C_CASH_EM       = (0.05, 0.40, 0.20)
    C_GEM           = (0.60, 0.10, 0.90)
    C_GEM_EM        = (0.30, 0.02, 0.55)
    C_STASH         = (0.85, 0.85, 0.90)
    C_STASH_EM      = (0.40, 0.40, 0.50)

    # Foyer accent
    C_MARBLE_WHITE  = (0.88, 0.87, 0.84)
    C_MARBLE_DARK   = (0.30, 0.28, 0.24)
    C_PILLAR        = (0.75, 0.73, 0.68)
    C_GOLD_TRIM     = (0.70, 0.56, 0.12)

    # Door frames
    C_DOOR_FRAME    = (0.38, 0.33, 0.24)
    C_DOOR_PANEL    = (0.30, 0.22, 0.12)
    C_KEYPAD_OFF    = (0.60, 0.05, 0.05)
    C_KEYPAD_ON     = (0.05, 0.60, 0.10)

    # Misc props
    C_LOCKER        = (0.22, 0.30, 0.25)
    C_LOCKER_ACCENT = (0.14, 0.20, 0.16)
    C_SHELF         = (0.30, 0.20, 0.10)
    C_BOOK_A        = (0.60, 0.12, 0.08)
    C_BOOK_B        = (0.08, 0.25, 0.55)
    C_BOOK_C        = (0.10, 0.40, 0.15)
    C_VENT_GRATE    = (0.20, 0.20, 0.22)
    C_PIPE          = (0.28, 0.28, 0.32)
    C_HANG_BAR      = (0.45, 0.43, 0.48)

    TILE_SZ = 2.0

    # ──────────────────────────────────────────────────────
    # BREAKABLE LIGHT STATE
    # Index → GL light number (GL_LIGHT0 = global ambient only)
    #   0 → GL_LIGHT1  Foyer chandelier      (warm)
    #   1 → GL_LIGHT2  Corridor sconce A     (warm)
    #   2 → GL_LIGHT3  Corridor sconce B     (warm)
    #   3 → GL_LIGHT4  Vault spotlight        (cold)
    #   4 → GL_LIGHT5  Security office light  (cold)
    #   5 → GL_LIGHT6  Kitchen fluorescent    (cold)
    #   6 → GL_LIGHT7  Emergency red ambient  (activates when others break)
    # ──────────────────────────────────────────────────────

    lights_on = [True, True, True, True, True, True, False]

    # GL enum list indexed to match lights_on
    GL_LIGHTS = [GL_LIGHT1, GL_LIGHT2, GL_LIGHT3,
                 GL_LIGHT4, GL_LIGHT5, GL_LIGHT6, GL_LIGHT7]

    # World positions of each breakable bulb (x, y, z)
    LIGHT_POSITIONS = [
        (  0.0,  9.5,   0.0),   # 0: Foyer chandelier
        ( 16.0,  5.5,  -2.0),   # 1: Corridor sconce A
        ( 16.0,  5.5, -18.0),   # 2: Corridor sconce B
        ( 27.0,  5.5, -20.0),   # 3: Vault spotlight
        (-25.0,  4.5, -16.0),   # 4: Security office
        ( -8.0,  4.5,  22.0),   # 5: Kitchen fluorescent
        (  0.0,  1.5,   0.0),   # 6: Emergency red (floor-level glow, off by default)
    ]

    # ──────────────────────────────────────────────────────
    # HANGABLE BAR POSITIONS (x, y, z, length_x)
    # ──────────────────────────────────────────────────────
    HANGABLE_BARS = [
        # Corridor overhead pipe bars
        (16.0,  4.8, -2.0,  6.0),
        (16.0,  4.8, -8.0,  6.0),
        (16.0,  4.8,-14.0,  6.0),
        (16.0,  4.8,-20.0,  6.0),
        (16.0,  4.8,-26.0,  6.0),
        # Kitchen hanging utensil rack
        (-8.0,  3.8,  18.0, 10.0),
        (-8.0,  3.8,  22.0, 10.0),
        # Library upper walkway grabs
        (27.0,  5.5,   8.0,  8.0),
    ]

    # ──────────────────────────────────────────────────────
    # VENT OPENINGS (x, y, z, width, height, facing: 'x'|'z'|'y')
    # ──────────────────────────────────────────────────────
    VENT_OPENINGS = [
        # Utility room — wall vent (west wall)
        (-30.0, 1.5, 8.0, 1.8, 1.2, 'x'),
        # Utility room — floor vent
        (-25.0, 0.02, 5.0, 1.8, 1.8, 'y'),
        # Corridor — wall vent into security office
        (12.0, 1.5, -14.0, 1.8, 1.2, 'x'),
        # Library — floor vent to hidden passage
        (27.0, 0.02, 14.5, 1.4, 1.4, 'y'),
    ]

    # ──────────────────────────────────────────────────────
    # COLLECTIBLE DATA  (x, y, z, color, emissive, label)
    # ──────────────────────────────────────────────────────
    COLLECTIBLES = [
        (27.0, 1.4, -20.0, C_IDOL,    C_IDOL_EM,    "Golden Idol"),
        (-25.0, 1.2, -14.0, C_KEYCARD, C_KEYCARD_EM, "Keycard"),
        (14.0, 0.6,  24.0, C_CASH,   C_CASH_EM,    "Cash Bag"),
        (31.0, 0.6,  15.0, C_GEM,    C_GEM_EM,     "Antique Gem"),
        (-12.0, 2.5,  20.0, C_STASH,  C_STASH_EM,   "Kitchen Stash"),
    ]

    BOB_SPEED     = 2.0
    BOB_AMPLITUDE = 0.15
    COLLECT_R     = 0.25

    # ──────────────────────────────────────────────────────
    # PUBLIC API — for game logic hooks
    # ──────────────────────────────────────────────────────

    @classmethod
    def spawn_pos(cls):
        """Return (x, y, z) player spawn — south end of Grand Foyer."""
        return (0.0, 1.0, cls.FOYER_D / 2.0 - 2.0)

    @classmethod
    def get_hangable_bars(cls):
        """Return list of (x, y, z, length_x) tuples for grab detection."""
        return cls.HANGABLE_BARS

    @classmethod
    def get_vent_openings(cls):
        """Return list of (x, y, z, w, h, facing) tuples for crawl detection."""
        return cls.VENT_OPENINGS

    @classmethod
    def toggle_light(cls, index):
        """Toggle a breakable light on or off (0-indexed into lights_on).

        Args:
            index: 0-based index (0 = chandelier … 5 = kitchen).
        """
        if 0 <= index < len(cls.lights_on) - 1:  # don't toggle emergency light directly
            cls.lights_on[index] = not cls.lights_on[index]
            # Activate emergency light when ANY normal light is broken
            any_off = any(not v for v in cls.lights_on[:-1])
            cls.lights_on[6] = any_off

    # ══════════════════════════════════════════════════════
    # LIGHTING SETUP
    # ══════════════════════════════════════════════════════

    @classmethod
    def setup_lighting(cls):
        """Configure all 7 dynamic light sources for this level."""

        # GL_LIGHT0 — near-black global ambient (stealth mood)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.04, 0.04, 0.06, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.06, 0.06, 0.08, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.02, 0.02, 0.02, 1.0])
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 50.0, 0.0, 0.0])  # Directional

        # GL_LIGHT1 — Foyer chandelier (warm amber)
        lp = cls.LIGHT_POSITIONS[0]
        if cls.lights_on[0]:
            glEnable(GL_LIGHT1)
            glLightfv(GL_LIGHT1, GL_AMBIENT,  [0.06, 0.05, 0.02, 1.0])
            glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.95, 0.80, 0.45, 1.0])
            glLightfv(GL_LIGHT1, GL_SPECULAR, [0.50, 0.40, 0.20, 1.0])
            glLightfv(GL_LIGHT1, GL_POSITION, [lp[0], lp[1], lp[2], 1.0])
            glLightf(GL_LIGHT1,  GL_CONSTANT_ATTENUATION,  1.0)
            glLightf(GL_LIGHT1,  GL_LINEAR_ATTENUATION,    0.018)
            glLightf(GL_LIGHT1,  GL_QUADRATIC_ATTENUATION, 0.004)
        else:
            glDisable(GL_LIGHT1)

        # GL_LIGHT2 — Corridor sconce A
        lp = cls.LIGHT_POSITIONS[1]
        if cls.lights_on[1]:
            glEnable(GL_LIGHT2)
            glLightfv(GL_LIGHT2, GL_AMBIENT,  [0.03, 0.02, 0.01, 1.0])
            glLightfv(GL_LIGHT2, GL_DIFFUSE,  [0.85, 0.65, 0.35, 1.0])
            glLightfv(GL_LIGHT2, GL_SPECULAR, [0.30, 0.25, 0.10, 1.0])
            glLightfv(GL_LIGHT2, GL_POSITION, [lp[0], lp[1], lp[2], 1.0])
            glLightf(GL_LIGHT2,  GL_CONSTANT_ATTENUATION,  1.0)
            glLightf(GL_LIGHT2,  GL_LINEAR_ATTENUATION,    0.040)
            glLightf(GL_LIGHT2,  GL_QUADRATIC_ATTENUATION, 0.010)
        else:
            glDisable(GL_LIGHT2)

        # GL_LIGHT3 — Corridor sconce B
        lp = cls.LIGHT_POSITIONS[2]
        if cls.lights_on[2]:
            glEnable(GL_LIGHT3)
            glLightfv(GL_LIGHT3, GL_AMBIENT,  [0.03, 0.02, 0.01, 1.0])
            glLightfv(GL_LIGHT3, GL_DIFFUSE,  [0.85, 0.65, 0.35, 1.0])
            glLightfv(GL_LIGHT3, GL_SPECULAR, [0.30, 0.25, 0.10, 1.0])
            glLightfv(GL_LIGHT3, GL_POSITION, [lp[0], lp[1], lp[2], 1.0])
            glLightf(GL_LIGHT3,  GL_CONSTANT_ATTENUATION,  1.0)
            glLightf(GL_LIGHT3,  GL_LINEAR_ATTENUATION,    0.040)
            glLightf(GL_LIGHT3,  GL_QUADRATIC_ATTENUATION, 0.010)
        else:
            glDisable(GL_LIGHT3)

        # GL_LIGHT4 — Vault cold spotlight
        lp = cls.LIGHT_POSITIONS[3]
        if cls.lights_on[3]:
            glEnable(GL_LIGHT4)
            glLightfv(GL_LIGHT4, GL_AMBIENT,  [0.02, 0.02, 0.04, 1.0])
            glLightfv(GL_LIGHT4, GL_DIFFUSE,  [0.60, 0.70, 0.95, 1.0])
            glLightfv(GL_LIGHT4, GL_SPECULAR, [0.70, 0.80, 1.00, 1.0])
            glLightfv(GL_LIGHT4, GL_POSITION, [lp[0], lp[1], lp[2], 1.0])
            glLightf(GL_LIGHT4,  GL_CONSTANT_ATTENUATION,  1.0)
            glLightf(GL_LIGHT4,  GL_LINEAR_ATTENUATION,    0.050)
            glLightf(GL_LIGHT4,  GL_QUADRATIC_ATTENUATION, 0.012)
        else:
            glDisable(GL_LIGHT4)

        # GL_LIGHT5 — Security office cold blue-white
        lp = cls.LIGHT_POSITIONS[4]
        if cls.lights_on[4]:
            glEnable(GL_LIGHT5)
            glLightfv(GL_LIGHT5, GL_AMBIENT,  [0.02, 0.02, 0.04, 1.0])
            glLightfv(GL_LIGHT5, GL_DIFFUSE,  [0.55, 0.62, 0.90, 1.0])
            glLightfv(GL_LIGHT5, GL_SPECULAR, [0.50, 0.55, 0.80, 1.0])
            glLightfv(GL_LIGHT5, GL_POSITION, [lp[0], lp[1], lp[2], 1.0])
            glLightf(GL_LIGHT5,  GL_CONSTANT_ATTENUATION,  1.0)
            glLightf(GL_LIGHT5,  GL_LINEAR_ATTENUATION,    0.055)
            glLightf(GL_LIGHT5,  GL_QUADRATIC_ATTENUATION, 0.015)
        else:
            glDisable(GL_LIGHT5)

        # GL_LIGHT6 — Kitchen fluorescent cold white
        lp = cls.LIGHT_POSITIONS[5]
        if cls.lights_on[5]:
            glEnable(GL_LIGHT6)
            glLightfv(GL_LIGHT6, GL_AMBIENT,  [0.04, 0.04, 0.05, 1.0])
            glLightfv(GL_LIGHT6, GL_DIFFUSE,  [0.70, 0.72, 0.80, 1.0])
            glLightfv(GL_LIGHT6, GL_SPECULAR, [0.40, 0.40, 0.50, 1.0])
            glLightfv(GL_LIGHT6, GL_POSITION, [lp[0], lp[1], lp[2], 1.0])
            glLightf(GL_LIGHT6,  GL_CONSTANT_ATTENUATION,  1.0)
            glLightf(GL_LIGHT6,  GL_LINEAR_ATTENUATION,    0.035)
            glLightf(GL_LIGHT6,  GL_QUADRATIC_ATTENUATION, 0.008)
        else:
            glDisable(GL_LIGHT6)

        # GL_LIGHT7 — Emergency red (activates when other lights broken)
        lp = cls.LIGHT_POSITIONS[6]
        if cls.lights_on[6]:
            glEnable(GL_LIGHT7)
            glLightfv(GL_LIGHT7, GL_AMBIENT,  [0.08, 0.00, 0.00, 1.0])
            glLightfv(GL_LIGHT7, GL_DIFFUSE,  [0.50, 0.02, 0.02, 1.0])
            glLightfv(GL_LIGHT7, GL_SPECULAR, [0.20, 0.00, 0.00, 1.0])
            glLightfv(GL_LIGHT7, GL_POSITION, [lp[0], lp[1], lp[2], 1.0])
            glLightf(GL_LIGHT7,  GL_CONSTANT_ATTENUATION,  0.8)
            glLightf(GL_LIGHT7,  GL_LINEAR_ATTENUATION,    0.012)
            glLightf(GL_LIGHT7,  GL_QUADRATIC_ATTENUATION, 0.003)
        else:
            glDisable(GL_LIGHT7)

    # ══════════════════════════════════════════════════════
    # FLOOR HELPERS
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_tiled_floor(cls, cx, cz, w, d, tile_a, tile_b, y=0.0, tile_sz=None):
        """Draw a checkerboard-tiled floor slab.

        Args:
            cx, cz: Centre of the floor area (world X/Z).
            w, d:   Width (X) and depth (Z) of the floor area.
            tile_a, tile_b: Alternating tile colors.
            y:      Y height for the floor surface.
            tile_sz: Tile size override; defaults to cls.TILE_SZ.
        """
        ts = tile_sz if tile_sz else cls.TILE_SZ
        half_w = w / 2.0
        half_d = d / 2.0
        ix = 0
        x = cx - half_w + ts / 2.0
        while x < cx + half_w:
            iz = 0
            z = cz - half_d + ts / 2.0
            while z < cz + half_d:
                color = tile_a if (ix + iz) % 2 == 0 else tile_b
                set_material(color)
                half = ts / 2.0
                glBegin(GL_QUADS)
                glNormal3f(0.0, 1.0, 0.0)
                glVertex3f(x - half, y, z - half)
                glVertex3f(x + half, y, z - half)
                glVertex3f(x + half, y, z + half)
                glVertex3f(x - half, y, z + half)
                glEnd()
                z += ts
                iz += 1
            x += ts
            ix += 1

    @classmethod
    def _draw_solid_floor(cls, cx, cz, w, d, color, y=0.0):
        """Draw a plain solid-color floor slab."""
        set_material(color)
        hw = w / 2.0
        hd = d / 2.0
        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(cx - hw, y, cz - hd)
        glVertex3f(cx + hw, y, cz - hd)
        glVertex3f(cx + hw, y, cz + hd)
        glVertex3f(cx - hw, y, cz + hd)
        glEnd()

    @classmethod
    def _draw_ceiling_slab(cls, cx, cz, w, d, color, y):
        """Draw a ceiling slab (normal pointing down)."""
        set_material(color)
        hw = w / 2.0
        hd = d / 2.0
        glBegin(GL_QUADS)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(cx - hw, y, cz - hd)
        glVertex3f(cx + hw, y, cz - hd)
        glVertex3f(cx + hw, y, cz + hd)
        glVertex3f(cx - hw, y, cz + hd)
        glEnd()

    # ══════════════════════════════════════════════════════
    # SHARED PROP DRAWERS
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_door_frame(cls, x, z, facing, h=None, w=None):
        """Draw a door frame at (x, z). Facing 'x' or 'z'.

        Args:
            x, z:   Centre of the door gap.
            facing: 'x' = door opening faces along X axis,
                    'z' = door opening faces along Z axis.
            h:      Door height (defaults to DOOR_H).
            w:      Door width (defaults to DOOR_W).
        """
        dh = h if h else cls.DOOR_H
        dw = w if w else cls.DOOR_W
        ft = cls.DOOR_FT
        ft2 = ft + 0.1
        mid_h = dh / 2.0
        top_y = dh + ft / 2.0

        if facing == 'z':
            # Vertical posts left & right
            draw_cube(x - dw / 2.0, mid_h, z, ft, dh, ft2, cls.C_DOOR_FRAME)
            draw_cube(x + dw / 2.0, mid_h, z, ft, dh, ft2, cls.C_DOOR_FRAME)
            # Horizontal lintel
            draw_cube(x, top_y, z, dw + ft * 2, ft, ft2, cls.C_DOOR_FRAME)
        else:
            draw_cube(x, mid_h, z - dw / 2.0, ft2, dh, ft, cls.C_DOOR_FRAME)
            draw_cube(x, mid_h, z + dw / 2.0, ft2, dh, ft, cls.C_DOOR_FRAME)
            draw_cube(x, top_y, z, ft2, ft, dw + ft * 2, cls.C_DOOR_FRAME)

    @classmethod
    def _draw_wall_sconce(cls, x, y, z, facing, light_on):
        """Draw a wall-mounted light sconce.

        Args:
            x, y, z: Position of the sconce centre.
            facing:  'px', 'nx', 'pz', 'nz' — which direction the sconce faces.
            light_on: Whether the light is currently on.
        """
        bulb_color   = cls.C_BULB_WARM   if light_on else cls.C_BULB_DEAD
        bulb_emissive = cls.C_BULB_WARM_EM if light_on else None

        # Wall bracket arm
        set_material(cls.C_METAL_DARK)
        glPushMatrix()
        glTranslatef(x, y, z)
        if facing in ('px', 'nx'):
            glScalef(0.3, 0.06, 0.06)
        else:
            glScalef(0.06, 0.06, 0.3)
        glutSolidCube(1)
        glPopMatrix()

        # Shade bowl (cone-like — flattened sphere)
        set_material(cls.C_METAL_MED)
        glPushMatrix()
        glTranslatef(x, y - 0.08, z)
        glScalef(0.28, 0.14, 0.28)
        glutSolidSphere(1.0, 10, 6)
        glPopMatrix()

        # Bulb
        draw_sphere(x, y + 0.05, z, 0.10, bulb_color, emissive=bulb_emissive, slices=8, stacks=8)

    @classmethod
    def _draw_pendant_light(cls, x, y_ceiling, drop, light_on):
        """Draw a pendant / hanging bulb from the ceiling.

        Args:
            x, y_ceiling: Ceiling attachment point X and Y height.
            drop: How far down the cord hangs.
            light_on: State.
        """
        bulb_y = y_ceiling - drop
        bulb_color    = cls.C_BULB_WARM    if light_on else cls.C_BULB_DEAD
        bulb_emissive = cls.C_BULB_WARM_EM if light_on else None

        # Cord
        draw_cube(x, y_ceiling - drop / 2.0, 0.0 if x == 0.0 else x,
                  0.04, drop, 0.04, (0.12, 0.12, 0.12))
        # Cap
        draw_cube(x, y_ceiling - 0.1, 0.0, 0.25, 0.08, 0.25, (0.18, 0.18, 0.18))
        # Bulb
        draw_sphere(x, bulb_y, 0.0, 0.28, bulb_color, emissive=bulb_emissive)

    @classmethod
    def _draw_vent_grate(cls, x, y, z, w, h, facing):
        """Draw a decorative vent grate (grid of thin bars).

        Args:
            x, y, z: Centre of the vent opening.
            w, h:    Vent width and height.
            facing:  'x' = grate faces along X, 'z' faces along Z, 'y' = floor.
        """
        set_material(cls.C_VENT_GRATE)
        bar_t = 0.06
        spacing = 0.35

        # Horizontal bars across width
        bar_y = -h / 2.0 + spacing / 2.0
        while bar_y < h / 2.0:
            glPushMatrix()
            glTranslatef(x, y, z)
            if facing == 'z':
                glScalef(w, bar_t, bar_t)
            elif facing == 'x':
                glScalef(bar_t, bar_t, w)
            else:
                glTranslatef(0.0, 0.0, bar_y)
                glScalef(w, bar_t, bar_t)
            glutSolidCube(1)
            glPopMatrix()
            bar_y += spacing

        # Vertical bars across height
        bar_x = -w / 2.0 + spacing / 2.0
        while bar_x < w / 2.0:
            glPushMatrix()
            glTranslatef(x, y, z)
            if facing == 'z':
                glTranslatef(bar_x, 0.0, 0.0)
                glScalef(bar_t, h, bar_t)
            elif facing == 'x':
                glTranslatef(0.0, bar_x, 0.0)
                glScalef(bar_t, h, bar_t)
            else:
                glTranslatef(bar_x, 0.0, 0.0)
                glScalef(bar_t, bar_t, h)
            glutSolidCube(1)
            glPopMatrix()
            bar_x += spacing

    @classmethod
    def _draw_hangable_bar(cls, x, y, z, length):
        """Draw an overhead grabable horizontal bar (cylinder approximated).

        Args:
            x, y, z: Centre position.
            length:  Length along X axis.
        """
        # Main bar
        draw_cube(x, y, z, length, 0.10, 0.10, cls.C_HANG_BAR)

        # End caps / mounting brackets
        for sx in (-1, 1):
            draw_cube(x + sx * length / 2.0, y + 0.15, z,
                      0.10, 0.30, 0.10, cls.C_METAL_DARK)

    # ══════════════════════════════════════════════════════
    # ROOM 1 — GRAND FOYER
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_foyer(cls, t):
        """Draw the Grand Foyer — central double-height hub.

        Args:
            t: Elapsed time (drives animation).
        """
        cx, cz = cls.FOYER_X, cls.FOYER_Z
        hw = cls.FOYER_W / 2.0
        hd = cls.FOYER_D / 2.0
        H  = cls.FOYER_H
        wt = cls.WALL_T

        # ── Floor (herringbone-style: alternating gold & dark tiles)
        cls._draw_tiled_floor(cx, cz, cls.FOYER_W, cls.FOYER_D,
                              cls.C_TILE_GOLD, cls.C_TILE_A, tile_sz=1.5)

        # ── Ceiling
        cls._draw_ceiling_slab(cx, cz, cls.FOYER_W, cls.FOYER_D,
                                cls.C_CEILING, H)

        # ── Perimeter walls (with door gaps: S=entry, E=corridor, N=alcoves)
        # South wall — main entrance doors (double gap)
        gap_w = cls.DOOR_W * 2.0 + 0.5
        seg = (cls.FOYER_W - gap_w) / 2.0
        draw_cube(cx - hw + seg / 2.0, H / 2.0, cz + hd,
                  seg, H, wt, cls.C_WALL_STONE)
        draw_cube(cx + hw - seg / 2.0, H / 2.0, cz + hd,
                  seg, H, wt, cls.C_WALL_STONE)
        # Transom above double doors
        draw_cube(cx, cls.DOOR_H + (H - cls.DOOR_H) / 2.0, cz + hd,
                  gap_w + 0.2, H - cls.DOOR_H, wt, cls.C_WALL_STONE)

        # North wall — gap to corridor (east side) and utility (west side)
        draw_cube(cx, H / 2.0, cz - hd,
                  cls.FOYER_W, H, wt, cls.C_WALL_STONE)

        # West wall — solid
        draw_cube(cx - hw, H / 2.0, cz,
                  wt, H, cls.FOYER_D, cls.C_WALL_STONE)

        # East wall — gap leading to corridor
        e_gap = cls.DOOR_W + 0.5
        e_seg_n = (cls.FOYER_D - e_gap) * 0.35
        e_seg_s = (cls.FOYER_D - e_gap) * 0.65
        draw_cube(cx + hw, H / 2.0, cz - hd + e_seg_n / 2.0,
                  wt, H, e_seg_n, cls.C_WALL_STONE)
        draw_cube(cx + hw, H / 2.0, cz + hd - e_seg_s / 2.0,
                  wt, H, e_seg_s, cls.C_WALL_STONE)
        draw_cube(cx + hw, cls.DOOR_H + (H - cls.DOOR_H) / 2.0,
                  cz - hd + e_seg_n + e_gap / 2.0,
                  wt, H - cls.DOOR_H, e_gap + 0.2, cls.C_WALL_STONE)

        # ── Gold skirting boards along walls
        draw_cube(cx, 0.12, cz - hd + wt / 2.0, cls.FOYER_W, 0.24, 0.12, cls.C_GOLD_TRIM)
        draw_cube(cx, 0.12, cz + hd - wt / 2.0, cls.FOYER_W, 0.24, 0.12, cls.C_GOLD_TRIM)
        draw_cube(cx - hw + wt / 2.0, 0.12, cz, 0.12, 0.24, cls.FOYER_D, cls.C_GOLD_TRIM)

        # ── 8 marble columns (two rows of 4)
        col_xs = [-9.0, -3.0, 3.0, 9.0]
        for col_x in col_xs:
            for col_z in [-5.0, 5.0]:
                shaft_h = H - 0.8
                # Base plinth
                draw_cube(col_x, 0.2, col_z, 1.2, 0.4, 1.2, cls.C_MARBLE_DARK)
                # Shaft
                draw_cube(col_x, shaft_h / 2.0 + 0.4, col_z,
                          0.7, shaft_h, 0.7, cls.C_PILLAR)
                # Capital (flared top)
                draw_cube(col_x, H - 0.4, col_z, 1.0, 0.4, 1.0, cls.C_MARBLE_DARK)
                # Gold ring mid-shaft
                draw_cube(col_x, shaft_h * 0.5, col_z,
                          0.85, 0.12, 0.85, cls.C_GOLD_TRIM)

        # ── Mezzanine balcony (left & right, running E-W)
        mez_y  = cls.MEZZANINE_Y
        mez_t  = cls.MEZZANINE_T
        mez_w  = 6.0
        mez_d  = cls.FOYER_D * 0.6
        for sx in (-1, 1):
            bx = sx * (hw - mez_w / 2.0)
            # Floor slab
            draw_cube(bx, mez_y - mez_t / 2.0, cz, mez_w, mez_t, mez_d,
                      cls.C_MARBLE_DARK)
            # Balustrade railing (low wall)
            rail_x = bx + sx * (mez_w / 2.0 - 0.08)
            draw_cube(rail_x, mez_y + 0.5, cz, 0.15, 1.0, mez_d, cls.C_MARBLE_WHITE)
            # Spindles every 1.2 units
            sp_z = cz - mez_d / 2.0 + 0.6
            while sp_z < cz + mez_d / 2.0:
                draw_cube(rail_x, mez_y + 0.25, sp_z,
                          0.07, 0.5, 0.07, cls.C_MARBLE_WHITE)
                sp_z += 1.2

        # ── Sweeping staircases (left: west side, right: east side)
        stair_steps = 7
        stair_run   = 1.0
        stair_rise  = mez_y / stair_steps
        for sx in (-1, 1):
            stair_x = sx * (hw - 5.5)
            for step in range(stair_steps):
                sw = 3.0
                sx_center = stair_x
                step_y = (step * stair_rise) + stair_rise / 2.0
                step_z = cz + hd - 2.0 - step * stair_run - stair_run / 2.0
                draw_cube(sx_center, step_y, step_z,
                          sw, stair_rise, stair_run, cls.C_MARBLE_DARK)
                # Step nosing (gold trim)
                draw_cube(sx_center, step_y + stair_rise / 2.0,
                          step_z - stair_run / 2.0 + 0.04,
                          sw, 0.06, 0.08, cls.C_GOLD_TRIM)

        # ── Chandelier
        cls._draw_chandelier(cx, cz, H, t)

        # ── Grand entrance double door frames
        cls._draw_door_frame(cx - cls.DOOR_W / 2.0 - 0.3,
                             cz + hd, 'z',
                             h=cls.DOOR_H, w=cls.DOOR_W)
        cls._draw_door_frame(cx + cls.DOOR_W / 2.0 + 0.3,
                             cz + hd, 'z',
                             h=cls.DOOR_H, w=cls.DOOR_W)

        # ── Decorative wall painting — west wall
        draw_cube(cx - hw + 0.1, H * 0.55, cz, 0.08, 3.0, 4.5, cls.C_GOLD_TRIM)    # Frame
        draw_cube(cx - hw + 0.15, H * 0.55, cz, 0.04, 2.8, 4.2, (0.20, 0.12, 0.08))  # Canvas

    @classmethod
    def _draw_chandelier(cls, cx, cz, ceiling_h, t):
        """Draw the grand chandelier with breakable bulbs.

        Args:
            cx, cz: Horizontal centre (above foyer).
            ceiling_h: Ceiling height.
            t: Elapsed time (subtle sway).
        """
        drop_y = ceiling_h - 1.0   # Main body Y
        light_on = cls.lights_on[0]

        # Suspension chain (series of small cubes)
        for i in range(8):
            chain_y = ceiling_h - 0.1 - i * 0.12
            draw_cube(cx, chain_y, cz, 0.08, 0.08, 0.08, cls.C_BRASS)

        # Central crown ring (horizontal)
        ring_r = 1.8
        for i in range(12):
            angle = math.radians(i * 30)
            rx = cx + math.cos(angle) * ring_r
            rz = cz + math.sin(angle) * ring_r
            draw_cube(rx, drop_y, rz, 0.18, 0.08, 0.18, cls.C_BRASS)

        # Inner ring
        ring_r2 = 0.9
        for i in range(8):
            angle = math.radians(i * 45)
            rx = cx + math.cos(angle) * ring_r2
            rz = cz + math.sin(angle) * ring_r2
            draw_cube(rx, drop_y - 0.15, rz, 0.12, 0.06, 0.12, cls.C_BRASS)

        # Centre boss sphere
        draw_sphere(cx, drop_y - 0.25, cz, 0.3, cls.C_BRASS)

        # Candle arms (6 arms radiating out)
        bulb_color    = cls.C_BULB_WARM    if light_on else cls.C_BULB_DEAD
        bulb_emissive = cls.C_BULB_WARM_EM if light_on else None

        for i in range(6):
            angle = math.radians(i * 60)
            arm_x = cx + math.cos(angle) * ring_r
            arm_z = cz + math.sin(angle) * ring_r
            # Arm
            draw_cube(cx + math.cos(angle) * ring_r * 0.5,
                      drop_y, cz + math.sin(angle) * ring_r * 0.5,
                      ring_r * 0.8, 0.07, 0.07, cls.C_BRASS)
            # Candle socket
            draw_cube(arm_x, drop_y + 0.12, arm_z, 0.12, 0.24, 0.12, cls.C_BRASS)
            # Bulb / flame
            draw_sphere(arm_x, drop_y + 0.30, arm_z, 0.12,
                        bulb_color, emissive=bulb_emissive, slices=8, stacks=8)

        # Drip chains hanging down
        for i in range(6):
            angle = math.radians(i * 60 + 30)
            dx = math.cos(angle) * ring_r * 1.1
            dz = math.sin(angle) * ring_r * 1.1
            for j in range(5):
                draw_cube(cx + dx, drop_y - 0.2 - j * 0.2, cz + dz,
                          0.06, 0.12, 0.06, cls.C_BRASS)

    # ══════════════════════════════════════════════════════
    # ROOM 2 — MAIN CORRIDOR
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_corridor(cls):
        """Draw the Main Corridor — spine connecting N rooms with hangable bars."""
        cx, cz = cls.CORR_X, cls.CORR_Z
        hw = cls.CORR_W / 2.0
        hd = cls.CORR_D / 2.0
        H  = cls.CORR_H
        wt = cls.WALL_T

        # Floor — dark concrete tiles
        cls._draw_tiled_floor(cx, cz, cls.CORR_W, cls.CORR_D,
                              cls.C_TILE_A, cls.C_WALL_DARK, tile_sz=2.0)

        # Ceiling
        cls._draw_ceiling_slab(cx, cz, cls.CORR_W, cls.CORR_D,
                                cls.C_CEILING_DARK, H)

        # Long walls
        draw_cube(cx - hw, H / 2.0, cz, wt, H, cls.CORR_D, cls.C_WALL_PLASTER)
        draw_cube(cx + hw, H / 2.0, cz, wt, H, cls.CORR_D, cls.C_WALL_PLASTER)

        # North end wall (solid — leads to vault passage)
        draw_cube(cx, H / 2.0, cz - hd, cls.CORR_W, H, wt, cls.C_WALL_PLASTER)

        # South end — door back to foyer (already handled by foyer east wall gap)
        # Door frame
        cls._draw_door_frame(cx, cz + hd, 'z')

        # ── Overhead pipe rack (structural)
        pipe_y = H - 0.5
        draw_cube(cx, pipe_y, cz, cls.CORR_W - 0.2, 0.15, cls.CORR_D - 0.2,
                  cls.C_PIPE)  # Sparse ceiling grid — just the cross-beams
        # Longitudinal pipes
        for px_off in (-hw + 0.5, 0.0, hw - 0.5):
            draw_cube(cx + px_off, pipe_y, cz,
                      0.12, 0.12, cls.CORR_D, cls.C_PIPE)

        # ── Hangable bars (5 positions along corridor)
        for bx, by, bz, blen in cls.HANGABLE_BARS[:5]:
            cls._draw_hangable_bar(bx, by, bz, blen)

        # ── Wall sconce lights
        sconce_zs = [cz - 8.0, cz + 6.0]
        for i, scz in enumerate(sconce_zs):
            lo = cls.lights_on[i + 1]
            cls._draw_wall_sconce(cx - hw + 0.12, H - 1.0, scz, 'px', lo)
            cls._draw_wall_sconce(cx + hw - 0.12, H - 1.0, scz, 'nx', lo)

        # ── Laser tripwire beams (3 lines at floor level — glowing red quads)
        for lz in [cz - 4.0, cz + 0.0, cz + 8.0]:
            set_material(cls.C_LASER, emissive=cls.C_LASER_EM)
            glBegin(GL_QUADS)
            glNormal3f(0.0, 1.0, 0.0)
            glVertex3f(cx - hw + 0.6, 0.25, lz - 0.03)
            glVertex3f(cx + hw - 0.6, 0.25, lz - 0.03)
            glVertex3f(cx + hw - 0.6, 0.25, lz + 0.03)
            glVertex3f(cx - hw + 0.6, 0.25, lz + 0.03)
            glEnd()
            # Emitter boxes on each wall
            draw_cube(cx - hw + 0.3, 0.30, lz, 0.15, 0.15, 0.15, cls.C_METAL_DARK,
                      emissive=cls.C_LASER_EM)
            draw_cube(cx + hw - 0.3, 0.30, lz, 0.15, 0.15, 0.15, cls.C_METAL_DARK,
                      emissive=cls.C_LASER_EM)

        # ── CCTV camera boxes at ceiling corners
        for ccx, ccz in [(cx - hw + 0.4, cz - hd + 0.4),
                          (cx + hw - 0.4, cz - hd + 0.4),
                          (cx - hw + 0.4, cz + hd - 0.4),
                          (cx + hw - 0.4, cz + hd - 0.4)]:
            draw_cube(ccx, H - 0.3, ccz, 0.25, 0.20, 0.30, cls.C_METAL_DARK)
            draw_sphere(ccx, H - 0.45, ccz, 0.08, (0.05, 0.05, 0.08),
                        emissive=(0.0, 0.0, 0.5))

        # ── Side closets for cover (2 alcove-style recesses in west wall)
        for clz in [cz - 6.0, cz + 4.0]:
            draw_cube(cx - hw - 0.6, H / 2.0, clz, 1.2, H, 2.5, cls.C_WALL_DARK)
            cls._draw_door_frame(cx - hw, clz, 'x', h=2.8, w=2.0)

        # ── Door to Security Office (north-west branch)
        cls._draw_door_frame(cx - hw, cz - hd + 3.0, 'x')

        # ── Door to Trophy Vault (north end)
        cls._draw_door_frame(cx, cz - hd, 'z')
        # Keycard scanner panel
        draw_cube(cx + cls.DOOR_W / 2.0 + 0.5, 1.2, cz - hd + 0.2,
                  0.15, 0.30, 0.08, cls.C_METAL_DARK)
        kpad_em = cls.C_KEYPAD_ON if cls.lights_on[3] else cls.C_KEYPAD_OFF
        draw_sphere(cx + cls.DOOR_W / 2.0 + 0.5, 1.35, cz - hd + 0.25,
                    0.06, (0.1, 0.1, 0.1), emissive=kpad_em)

    # ══════════════════════════════════════════════════════
    # ROOM 3 — SECURITY OFFICE
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_security_office(cls):
        """Draw the Security Office — guard command post with monitors and loot."""
        cx, cz = cls.SEC_X, cls.SEC_Z
        hw = cls.SEC_W / 2.0
        hd = cls.SEC_D / 2.0
        H  = cls.SEC_H
        wt = cls.WALL_T

        # Floor
        cls._draw_tiled_floor(cx, cz, cls.SEC_W, cls.SEC_D,
                              cls.C_CONCRETE, cls.C_TILE_A, tile_sz=2.0)

        # Ceiling
        cls._draw_ceiling_slab(cx, cz, cls.SEC_W, cls.SEC_D, cls.C_CEILING_DARK, H)

        # Walls
        draw_cube(cx, H / 2.0, cz - hd, cls.SEC_W, H, wt, cls.C_WALL_DARK)  # North
        draw_cube(cx, H / 2.0, cz + hd, cls.SEC_W, H, wt, cls.C_WALL_DARK)  # South
        draw_cube(cx - hw, H / 2.0, cz, wt, H, cls.SEC_D, cls.C_WALL_DARK)  # West
        # East wall — has door + one-way glass
        e_seg = (cls.SEC_D - cls.DOOR_W) / 2.0
        draw_cube(cx + hw, H / 2.0, cz - hd + e_seg / 2.0,
                  wt, H, e_seg, cls.C_WALL_DARK)
        draw_cube(cx + hw, H / 2.0, cz + hd - e_seg / 2.0,
                  wt, H, e_seg, cls.C_WALL_DARK)
        draw_cube(cx + hw, cls.DOOR_H + (H - cls.DOOR_H) / 2.0,
                  cz - hd + e_seg + cls.DOOR_W / 2.0,
                  wt, H - cls.DOOR_H, cls.DOOR_W, cls.C_WALL_DARK)
        cls._draw_door_frame(cx + hw, cz - hd + e_seg + cls.DOOR_W / 2.0, 'x')

        # One-way glass window (south side of east wall)
        draw_cube(cx + hw, 1.8, cz + hd - 1.5, 0.1, 1.6, 2.2, cls.C_GLASS)

        # ── Monitor bank — 3 screens on north wall
        desk_y = 1.0  # Desk surface height
        desk_z = cz - hd + 0.8

        # Desk surface
        draw_cube(cx, desk_y, desk_z, cls.SEC_W * 0.7, 0.12, 1.4, cls.C_WOOD_MED)
        # Desk legs
        for dx in [-cls.SEC_W * 0.3, cls.SEC_W * 0.3]:
            draw_cube(cx + dx, desk_y / 2.0, desk_z, 0.1, desk_y, 0.1, cls.C_WOOD_DARK)

        # Monitors (3 screens)
        lo = cls.lights_on[4]
        for mi, mx_off in enumerate([-3.5, 0.0, 3.5]):
            mon_x = cx + mx_off
            mon_y = desk_y + 0.55
            mon_z = desk_z + 0.05
            # Monitor stand
            draw_cube(mon_x, desk_y + 0.22, mon_z - 0.2, 0.12, 0.24, 0.12, cls.C_METAL_DARK)
            draw_cube(mon_x, desk_y + 0.12, mon_z - 0.2, 0.4, 0.06, 0.3, cls.C_METAL_DARK)
            # Monitor body
            draw_cube(mon_x, mon_y, mon_z, 1.6, 0.95, 0.1, cls.C_METAL_DARK)
            # Screen (glowing blue when on)
            scr_col = cls.C_MONITOR_ON if lo else cls.C_MONITOR_OFF
            scr_em  = cls.C_MONITOR_EM if lo else None
            draw_cube(mon_x, mon_y, mon_z + 0.06, 1.5, 0.88, 0.02, scr_col, emissive=scr_em)

        # ── Overhead light fixture
        lo = cls.lights_on[4]
        draw_cube(cx, H - 0.15, cz, cls.SEC_W * 0.6, 0.12, 0.5,
                  cls.C_METAL_DARK)
        bc = cls.C_BULB_COLD if lo else cls.C_BULB_DEAD
        be = cls.C_BULB_COLD_EM if lo else None
        for fx in [-2.0, 0.0, 2.0]:
            draw_sphere(cx + fx, H - 0.3, cz, 0.14, bc, emissive=be, slices=8, stacks=8)

        # ── Filing cabinet cluster (hidden loot drawer)
        cab_x = cx + hw - 1.0
        cab_z = cz + hd - 1.0
        for fi in range(3):
            draw_cube(cab_x - fi * 1.2, 1.5, cab_z, 0.9, 3.0, 0.8, cls.C_METAL_MED)
            # Drawer handles
            for di in range(4):
                draw_cube(cab_x - fi * 1.2, 0.4 + di * 0.7, cab_z - 0.42,
                          0.3, 0.06, 0.06, cls.C_METAL_LIGHT)

        # ── Swivel chair
        draw_cube(cx, 0.5, desk_z + 1.0, 0.6, 0.06, 0.6, cls.C_METAL_DARK)  # Seat
        draw_cube(cx, 0.28, desk_z + 1.0, 0.08, 0.55, 0.08, cls.C_METAL_DARK)  # Post
        # Wheels
        for wx, wz in [(-0.3, 0.0), (0.3, 0.0), (0.0, -0.3), (0.0, 0.3)]:
            draw_sphere(cx + wx, 0.12, desk_z + 1.0 + wz, 0.07,
                        (0.1, 0.1, 0.1), slices=6, stacks=4)

    # ══════════════════════════════════════════════════════
    # ROOM 4 — TROPHY VAULT
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_vault(cls, t):
        """Draw the Trophy Vault — the primary target room.

        Args:
            t: Elapsed time (drives bobbing animation).
        """
        cx, cz = cls.VAULT_X, cls.VAULT_Z
        hw = cls.VAULT_W / 2.0
        hd = cls.VAULT_D / 2.0
        H  = cls.VAULT_H
        wt = cls.WALL_T

        # Floor — pressure-plate tiles (alternate gold/dark to suggest sensors)
        cls._draw_tiled_floor(cx, cz, cls.VAULT_W, cls.VAULT_D,
                              cls.C_TILE_GOLD, cls.C_METAL_DARK, tile_sz=1.5)

        # Ceiling
        cls._draw_ceiling_slab(cx, cz, cls.VAULT_W, cls.VAULT_D, cls.C_CEILING_DARK, H)

        # Solid walls (reinforced steel look)
        draw_cube(cx, H / 2.0, cz - hd, cls.VAULT_W, H, wt, cls.C_METAL_DARK)  # North
        draw_cube(cx, H / 2.0, cz + hd, cls.VAULT_W, H, wt, cls.C_METAL_DARK)  # South → door
        draw_cube(cx - hw, H / 2.0, cz, wt, H, cls.VAULT_D, cls.C_METAL_DARK)  # West
        draw_cube(cx + hw, H / 2.0, cz, wt, H, cls.VAULT_D, cls.C_METAL_DARK)  # East

        # South wall — vault door frame + door panel
        s_seg = (cls.VAULT_W - cls.DOOR_W) / 2.0
        draw_cube(cx - hw + s_seg / 2.0, H / 2.0, cz + hd,
                  s_seg, H, wt, cls.C_METAL_DARK)
        draw_cube(cx + hw - s_seg / 2.0, H / 2.0, cz + hd,
                  s_seg, H, wt, cls.C_METAL_DARK)
        draw_cube(cx, cls.DOOR_H + (H - cls.DOOR_H) / 2.0, cz + hd,
                  cls.DOOR_W, H - cls.DOOR_H, wt, cls.C_METAL_DARK)
        cls._draw_door_frame(cx, cz + hd, 'z')

        # Heavy vault door (thick slab, slightly ajar)
        draw_cube(cx - cls.DOOR_W / 2.0 - 0.3, cls.DOOR_H / 2.0, cz + hd + 0.4,
                  0.4, cls.DOOR_H, cls.DOOR_W - 0.2, cls.C_METAL_MED)

        # ── Spotlights aimed at display case (4 positions)
        lo = cls.lights_on[3]
        spot_positions = [
            (cx - 3.0, H - 0.4, cz - 3.0),
            (cx + 3.0, H - 0.4, cz - 3.0),
            (cx - 3.0, H - 0.4, cz + 3.0),
            (cx + 3.0, H - 0.4, cz + 3.0),
        ]
        for sp_x, sp_y, sp_z in spot_positions:
            draw_cube(sp_x, sp_y, sp_z, 0.3, 0.3, 0.3, cls.C_METAL_DARK)
            bc = cls.C_BULB_COLD if lo else cls.C_BULB_DEAD
            be = cls.C_BULB_COLD_EM if lo else None
            draw_sphere(sp_x, sp_y - 0.18, sp_z, 0.10, bc, emissive=be, slices=8, stacks=6)

        # ── Glass display case
        case_y = 1.2
        case_h = 1.2
        case_w = 1.6
        case_d = 1.0
        # Base plinth
        draw_cube(cx, 0.3, cz - 1.5, case_w + 0.2, 0.6, case_d + 0.2, cls.C_MARBLE_DARK)
        # Glass sides (semi-transparent effect — thin slabs)
        draw_cube(cx, case_y, cz - 1.5, case_w, 0.06, case_d, cls.C_GLASS)     # Top
        draw_cube(cx, case_y / 2.0, cz - 1.5 - case_d / 2.0,
                  case_w, case_h, 0.05, cls.C_GLASS)  # Front glass
        draw_cube(cx, case_y / 2.0, cz - 1.5 + case_d / 2.0,
                  case_w, case_h, 0.05, cls.C_GLASS)  # Back glass
        draw_cube(cx - case_w / 2.0, case_y / 2.0, cz - 1.5,
                  0.05, case_h, case_d, cls.C_GLASS)   # Left glass
        draw_cube(cx + case_w / 2.0, case_y / 2.0, cz - 1.5,
                  0.05, case_h, case_d, cls.C_GLASS)   # Right glass

        # ── Golden Idol (collectible) — bobbing inside case
        bob_y = 0.72 + math.sin(t * cls.BOB_SPEED) * cls.BOB_AMPLITUDE
        draw_sphere(cx, bob_y, cz - 1.5, cls.COLLECT_R,
                    cls.C_IDOL, emissive=cls.C_IDOL_EM)

        # ── Hidden floor hatch (darker tile square in NE corner)
        hatch_x = cx + hw - 1.5
        hatch_z = cz - hd + 1.5
        draw_cube(hatch_x, 0.03, hatch_z, 1.4, 0.06, 1.4, cls.C_METAL_DARK)
        # Hatch handle ring
        draw_sphere(hatch_x, 0.1, hatch_z, 0.1, cls.C_BRASS)

        # ── Wall trophies (decorative cubes on north wall)
        for tri, tx in enumerate([-4.0, 0.0, 4.0]):
            draw_cube(cx + tx, H * 0.6, cz - hd + 0.2, 0.6, 0.8, 0.3, cls.C_BRASS)
            draw_sphere(cx + tx, H * 0.6 + 0.55, cz - hd + 0.2,
                        0.18, cls.C_GOLD_TRIM, emissive=cls.C_IDOL_EM)

    # ══════════════════════════════════════════════════════
    # ROOM 5 — LIBRARY
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_library(cls, t):
        """Draw the Library — tall shelves, upper walkway, hidden stash room.

        Args:
            t: Elapsed time.
        """
        cx, cz = cls.LIB_X, cls.LIB_Z
        hw = cls.LIB_W / 2.0
        hd = cls.LIB_D / 2.0
        H  = cls.LIB_H
        wt = cls.WALL_T

        # Floor — warm wood
        cls._draw_solid_floor(cx, cz, cls.LIB_W, cls.LIB_D, cls.C_WOOD_FLOOR)

        # Ceiling
        cls._draw_ceiling_slab(cx, cz, cls.LIB_W, cls.LIB_D, cls.C_CEILING_DARK, H)

        # Walls
        draw_cube(cx, H / 2.0, cz - hd, cls.LIB_W, H, wt, cls.C_WALL_PLASTER)
        draw_cube(cx, H / 2.0, cz + hd, cls.LIB_W, H, wt, cls.C_WALL_PLASTER)
        draw_cube(cx + hw, H / 2.0, cz, wt, H, cls.LIB_D, cls.C_WALL_PLASTER)

        # West wall — door to corridor
        w_seg = (cls.LIB_D - cls.DOOR_W) / 2.0
        draw_cube(cx - hw, H / 2.0, cz - hd + w_seg / 2.0,
                  wt, H, w_seg, cls.C_WALL_PLASTER)
        draw_cube(cx - hw, H / 2.0, cz + hd - w_seg / 2.0,
                  wt, H, w_seg, cls.C_WALL_PLASTER)
        draw_cube(cx - hw, cls.DOOR_H + (H - cls.DOOR_H) / 2.0,
                  cz - hd + w_seg + cls.DOOR_W / 2.0,
                  wt, H - cls.DOOR_H, cls.DOOR_W, cls.C_WALL_PLASTER)
        cls._draw_door_frame(cx - hw, cz - hd + w_seg + cls.DOOR_W / 2.0, 'x')

        # ── Upper mezzanine walkway (east side)
        mez_y  = cls.MEZZANINE_Y
        mez_t  = cls.MEZZANINE_T
        draw_cube(cx, mez_y - mez_t / 2.0, cz,
                  cls.LIB_W * 0.45, mez_t, cls.LIB_D * 0.8,
                  cls.C_WOOD_DARK)

        # Balustrade
        draw_cube(cx - cls.LIB_W * 0.22, mez_y + 0.5, cz,
                  0.12, 1.0, cls.LIB_D * 0.8, cls.C_WOOD_MED)

        # Hangable grab bar above walkway
        cls._draw_hangable_bar(cls.HANGABLE_BARS[7][0],
                               cls.HANGABLE_BARS[7][1],
                               cls.HANGABLE_BARS[7][2],
                               cls.HANGABLE_BARS[7][3])

        # ── Bookshelves (2 columns × 3 rows)
        shelf_positions = [
            (cx + 2.0, cz - 5.0),
            (cx + 2.0, cz - 1.5),
            (cx + 2.0, cz + 2.0),
        ]
        for sx, sz in shelf_positions:
            cls._draw_bookshelf(sx, sz, H - 1.0)

        # East wall shelves
        for esz in [cz - 4.5, cz + 0.5, cz + 5.5]:
            cls._draw_bookshelf(cx + hw - 1.0, esz, H - 1.0, against_wall=True)

        # ── Rolling ladder
        draw_cube(cx + hw - 1.5, 2.0, cz - 4.0,
                  0.1, 4.0, 0.1, cls.C_WOOD_DARK)  # Left rail
        draw_cube(cx + hw - 0.8, 2.0, cz - 4.0,
                  0.1, 4.0, 0.1, cls.C_WOOD_DARK)  # Right rail
        for rung in range(7):
            draw_cube(cx + hw - 1.15, 0.4 + rung * 0.55, cz - 4.0,
                      0.65, 0.06, 0.06, cls.C_WOOD_MED)

        # ── Antique desk
        desk_x = cx - 1.0
        desk_z = cz + 4.0
        draw_cube(desk_x, 0.9, desk_z, 2.2, 0.1, 1.0, cls.C_MAHOGANY)
        for dlx, dlz in [(-0.9, -0.4), (0.9, -0.4), (-0.9, 0.4), (0.9, 0.4)]:
            draw_cube(desk_x + dlx, 0.45, desk_z + dlz, 0.12, 0.9, 0.12, cls.C_MAHOGANY)

        # ── Hidden room gap — behind last north-wall shelf (no wall behind it)
        # The "hidden room" is an alcove cut into the north wall
        hidden_x = cx + hw - 1.5
        hidden_z = cz - hd - 2.0
        draw_cube(hidden_x, H / 2.0, hidden_z, 3.0, H, 4.0, cls.C_WALL_DARK)
        cls._draw_solid_floor(hidden_x, hidden_z, 3.0, 4.0, cls.C_CONCRETE)
        cls._draw_ceiling_slab(hidden_x, hidden_z, 3.0, 4.0, cls.C_CEILING_DARK, H)

        # Hidden gem collectible inside
        gem_y = 0.5 + math.sin(t * cls.BOB_SPEED + 1.0) * cls.BOB_AMPLITUDE
        draw_sphere(hidden_x, gem_y, hidden_z, cls.COLLECT_R,
                    cls.C_GEM, emissive=cls.C_GEM_EM)

        # Floor vent grate leading into hidden passage
        vo = cls.VENT_OPENINGS[3]
        cls._draw_vent_grate(vo[0], vo[1], vo[2], vo[3], vo[4], vo[5])

    @classmethod
    def _draw_bookshelf(cls, cx, cz, height, against_wall=False):
        """Draw a single tall bookshelf unit with books.

        Args:
            cx, cz: Centre position.
            height: Shelf height.
            against_wall: If True, shelf is pushed against east wall.
        """
        depth = 0.6 if not against_wall else 0.4
        width = 1.4
        # Frame
        draw_cube(cx, height / 2.0, cz, width, height, depth, cls.C_SHELF)

        # Shelves (horizontal boards)
        shelf_count = 5
        for si in range(shelf_count + 1):
            sy = si * (height / shelf_count) if si < shelf_count else height - 0.05
            draw_cube(cx, sy, cz, width - 0.06, 0.05, depth - 0.06, cls.C_WOOD_MED)

        # Books (small colorful cubes on each shelf)
        book_colors = [cls.C_BOOK_A, cls.C_BOOK_B, cls.C_BOOK_C,
                       cls.C_BRASS, cls.C_MAHOGANY]
        for si in range(shelf_count):
            by = si * (height / shelf_count) + 0.18
            bx = cx - width / 2.0 + 0.12
            while bx < cx + width / 2.0 - 0.12:
                bc = book_colors[int(bx * 7 + si * 3) % len(book_colors)]
                bw = 0.12 + (int(bx * 13) % 3) * 0.04
                draw_cube(bx + bw / 2.0, by, cz, bw, 0.30, depth * 0.85, bc)
                bx += bw + 0.01

    # ══════════════════════════════════════════════════════
    # ROOM 6 — UTILITY ROOM
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_utility_room(cls):
        """Draw the Utility Room — vents, catwalk, boiler, fuse box."""
        cx, cz = cls.UTIL_X, cls.UTIL_Z
        hw = cls.UTIL_W / 2.0
        hd = cls.UTIL_D / 2.0
        H  = cls.UTIL_H
        wt = cls.WALL_T

        # Floor
        cls._draw_solid_floor(cx, cz, cls.UTIL_W, cls.UTIL_D, cls.C_CONCRETE)

        # Ceiling
        cls._draw_ceiling_slab(cx, cz, cls.UTIL_W, cls.UTIL_D, cls.C_CEILING_DARK, H)

        # Walls
        draw_cube(cx, H / 2.0, cz - hd, cls.UTIL_W, H, wt, cls.C_WALL_DARK)
        draw_cube(cx, H / 2.0, cz + hd, cls.UTIL_W, H, wt, cls.C_WALL_DARK)
        draw_cube(cx + hw, H / 2.0, cz, wt, H, cls.UTIL_D, cls.C_WALL_DARK)

        # West wall — vent opening + door to foyer
        u_seg = (cls.UTIL_D - cls.DOOR_W) / 2.0
        draw_cube(cx - hw, H / 2.0, cz - hd + u_seg / 2.0,
                  wt, H, u_seg, cls.C_WALL_DARK)
        draw_cube(cx - hw, H / 2.0, cz + hd - u_seg / 2.0,
                  wt, H, u_seg, cls.C_WALL_DARK)
        draw_cube(cx - hw, cls.DOOR_H + (H - cls.DOOR_H) / 2.0,
                  cz - hd + u_seg + cls.DOOR_W / 2.0,
                  wt, H - cls.DOOR_H, cls.DOOR_W, cls.C_WALL_DARK)
        cls._draw_door_frame(cx - hw, cz - hd + u_seg + cls.DOOR_W / 2.0, 'x')

        # ── Wall vent (west-facing, in west wall)
        vo = cls.VENT_OPENINGS[0]
        draw_cube(vo[0] + 0.1, vo[1], vo[2], wt, vo[4], vo[3], cls.C_WALL_DARK)
        cls._draw_vent_grate(vo[0] + 0.26, vo[1], vo[2], vo[3], vo[4], 'x')

        # ── Floor vent (with grate)
        vo2 = cls.VENT_OPENINGS[1]
        cls._draw_vent_grate(vo2[0], vo2[1], vo2[2], vo2[3], vo2[4], 'y')

        # ── Catwalk at mid-height
        cat_y = cls.MEZZANINE_Y - 0.5
        cat_t = cls.MEZZANINE_T
        draw_cube(cx, cat_y - cat_t / 2.0, cz,
                  cls.UTIL_W - 0.4, cat_t, cls.UTIL_D * 0.4, cls.C_METAL_DARK)
        # Catwalk railings
        draw_cube(cx - (cls.UTIL_W - 0.4) / 2.0, cat_y + 0.4, cz,
                  0.06, 0.8, cls.UTIL_D * 0.4, cls.C_METAL_MED)
        draw_cube(cx + (cls.UTIL_W - 0.4) / 2.0, cat_y + 0.4, cz,
                  0.06, 0.8, cls.UTIL_D * 0.4, cls.C_METAL_MED)
        # Grating texture on catwalk (grid of thin bars)
        for gx in range(int(cls.UTIL_W)):
            draw_cube(cx - cls.UTIL_W / 2.0 + gx * 1.0 + 0.5,
                      cat_y, cz, 0.06, cat_t * 1.2, cls.UTIL_D * 0.4, cls.C_METAL_DARK)

        # ── Boiler / furnace
        boiler_x = cx + hw - 1.5
        boiler_z = cz + hd - 1.5
        draw_cube(boiler_x, 1.4, boiler_z, 2.0, 2.8, 1.5, cls.C_METAL_DARK)
        # Boiler door
        draw_cube(boiler_x, 0.8, boiler_z - 0.76, 0.7, 0.55, 0.08, cls.C_METAL_MED)
        # Pressure gauge
        draw_sphere(boiler_x + 0.5, 2.0, boiler_z - 0.78, 0.12, cls.C_METAL_LIGHT)
        # Exhaust pipes going up
        for px_off in [-0.4, 0.4]:
            draw_cube(boiler_x + px_off, H - 1.0, boiler_z, 0.14, (H - 2.8) * 2.0, 0.14,
                      cls.C_PIPE)

        # ── Fuse box (on east wall — interactable)
        fbox_x = cx + hw - 0.1
        fbox_z = cz - hd + 2.0
        draw_cube(fbox_x, 1.8, fbox_z, 0.1, 0.8, 0.55, cls.C_METAL_MED)
        # Switches
        for fi in range(4):
            sw_on = cls.lights_on[fi + 1]
            sw_color = (0.05, 0.55, 0.10) if sw_on else (0.55, 0.05, 0.05)
            draw_cube(fbox_x - 0.06, 1.55 + fi * 0.15, fbox_z, 0.06, 0.06, 0.08, sw_color)

        # ── Overhead pipe maze (decorative)
        for pz_off in [-3.0, 0.0, 3.0]:
            draw_cube(cx, H - 0.4, cz + pz_off, cls.UTIL_W * 0.8, 0.12, 0.12, cls.C_PIPE)
        for px_off in [-cls.UTIL_W * 0.3, 0.0, cls.UTIL_W * 0.3]:
            draw_cube(cx + px_off, H - 0.4, cz, 0.12, 0.12, cls.UTIL_D * 0.8, cls.C_PIPE)

    # ══════════════════════════════════════════════════════
    # ROOM 7 — KITCHEN
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_kitchen(cls, t):
        """Draw the Kitchen / Prep Room — cabinets, island, fridge, hanging bars.

        Args:
            t: Elapsed time.
        """
        cx, cz = cls.KITCH_X, cls.KITCH_Z
        hw = cls.KITCH_W / 2.0
        hd = cls.KITCH_D / 2.0
        H  = cls.KITCH_H
        wt = cls.WALL_T

        # Floor — light grey tiles
        cls._draw_tiled_floor(cx, cz, cls.KITCH_W, cls.KITCH_D,
                              cls.C_MARBLE_WHITE, cls.C_TILE_B, tile_sz=1.5)

        # Ceiling
        cls._draw_ceiling_slab(cx, cz, cls.KITCH_W, cls.KITCH_D, cls.C_CEILING, H)

        # Walls
        draw_cube(cx, H / 2.0, cz - hd, cls.KITCH_W, H, wt, cls.C_WALL_PLASTER)
        draw_cube(cx, H / 2.0, cz + hd, cls.KITCH_W, H, wt, cls.C_WALL_PLASTER)
        draw_cube(cx - hw, H / 2.0, cz, wt, H, cls.KITCH_D, cls.C_WALL_PLASTER)
        # East wall — door to barracks + door to foyer
        e_gap1 = cls.DOOR_W
        e_gap2 = cls.DOOR_W
        spacing = cls.KITCH_D - e_gap1 - e_gap2 - 2.0
        draw_cube(cx + hw, H / 2.0, cz - hd + 0.8,
                  wt, H, 0.8, cls.C_WALL_PLASTER)
        draw_cube(cx + hw, H / 2.0, cz,
                  wt, H, spacing, cls.C_WALL_PLASTER)
        draw_cube(cx + hw, H / 2.0, cz + hd - 0.8,
                  wt, H, 0.8, cls.C_WALL_PLASTER)
        draw_cube(cx + hw, cls.DOOR_H + (H - cls.DOOR_H) / 2.0, cz - hd + 0.8 + e_gap1 / 2.0,
                  wt, H - cls.DOOR_H, e_gap1, cls.C_WALL_PLASTER)
        draw_cube(cx + hw, cls.DOOR_H + (H - cls.DOOR_H) / 2.0, cz + hd - 0.8 - e_gap2 / 2.0,
                  wt, H - cls.DOOR_H, e_gap2, cls.C_WALL_PLASTER)

        # ── Upper cabinet row — north wall (hidden loot inside)
        upper_cab_y = 2.8
        upper_cab_h = 0.9
        upper_cab_d = 0.5
        for ucx in range(int(cx - hw + 0.8), int(cx + hw - 0.5), 1):
            # Cabinet body
            draw_cube(ucx + 0.45, upper_cab_y + upper_cab_h / 2.0,
                      cz - hd + upper_cab_d / 2.0 + 0.26,
                      0.85, upper_cab_h, upper_cab_d, cls.C_WOOD_LIGHT)
            # Cabinet door + handle
            draw_cube(ucx + 0.45, upper_cab_y + upper_cab_h / 2.0,
                      cz - hd + upper_cab_d + 0.28,
                      0.8, upper_cab_h - 0.08, 0.04, cls.C_WOOD_MED)
            draw_sphere(ucx + 0.45, upper_cab_y + upper_cab_h / 2.0,
                        cz - hd + upper_cab_d + 0.32, 0.04, cls.C_METAL_LIGHT)

        # ── Upper cabinet row — west wall
        for ucz in range(int(cz - hd + 0.8), int(cz + hd - 0.5), 1):
            draw_cube(cx - hw + upper_cab_d / 2.0 + 0.26,
                      upper_cab_y + upper_cab_h / 2.0, ucz + 0.45,
                      upper_cab_d, upper_cab_h, 0.85, cls.C_WOOD_LIGHT)
            draw_cube(cx - hw + upper_cab_d + 0.28,
                      upper_cab_y + upper_cab_h / 2.0, ucz + 0.45,
                      0.04, upper_cab_h - 0.08, 0.8, cls.C_WOOD_MED)

        # ── Kitchen stash collectible (inside upper north-cabinet, visible when open)
        stash_y = 2.5 + math.sin(t * cls.BOB_SPEED + 2.0) * cls.BOB_AMPLITUDE
        draw_sphere(cx - 2.0, stash_y, cz - hd + 0.4, cls.COLLECT_R,
                    cls.C_STASH, emissive=cls.C_STASH_EM)

        # ── Lower cabinet countertop (L-shape along north + west wall)
        lower_h = 1.0
        lower_d = 0.7
        # North wall bank
        draw_cube(cx, lower_h / 2.0, cz - hd + lower_d / 2.0,
                  cls.KITCH_W - 2.0, lower_h, lower_d, cls.C_WOOD_DARK)
        # Countertop surface
        draw_cube(cx, lower_h + 0.06, cz - hd + lower_d / 2.0,
                  cls.KITCH_W - 2.0, 0.12, lower_d + 0.1, cls.C_MARBLE_WHITE)
        # Lower cabinet doors
        for lcd_x in range(int(cx - hw + 0.7), int(cx + hw - 1.0), 1):
            draw_cube(lcd_x + 0.45, lower_h / 2.0, cz - hd + lower_d + 0.04,
                      0.82, lower_h - 0.1, 0.05, cls.C_WOOD_MED)
            draw_cube(lcd_x + 0.45, lower_h * 0.5, cz - hd + lower_d + 0.08,
                      0.2, 0.06, 0.06, cls.C_METAL_LIGHT)

        # ── Kitchen island (centre)
        draw_cube(cx, lower_h / 2.0, cz, 3.5, lower_h, 1.5, cls.C_WOOD_DARK)
        draw_cube(cx, lower_h + 0.06, cz, 3.6, 0.12, 1.6, cls.C_MARBLE_WHITE)

        # ── Refrigerator (can hide inside — like a ClosetObstacle)
        fridge_x = cx + hw - 1.0
        fridge_z = cz - hd + 1.2
        draw_cube(fridge_x, 1.6, fridge_z, 1.2, 3.2, 1.0, cls.C_METAL_LIGHT)
        # Fridge handle
        draw_cube(fridge_x - 0.62, 1.8, fridge_z, 0.06, 0.8, 0.06, cls.C_METAL_DARK)
        # Fridge door seam
        draw_cube(fridge_x, 0.9, fridge_z - 0.51, 1.15, 0.06, 0.06, cls.C_METAL_MED)
        # Fridge logo dot
        draw_sphere(fridge_x + 0.2, 1.4, fridge_z - 0.51, 0.05,
                    cls.C_BULB_COLD, emissive=cls.C_BULB_COLD_EM)

        # ── Hanging utensil rack (2 bars — hangable)
        for bar in cls.HANGABLE_BARS[5:7]:
            cls._draw_hangable_bar(bar[0], bar[1], bar[2], bar[3])
            # Dangling utensils (small cubes)
            bar_hw = bar[3] / 2.0
            u_x = bar[0] - bar_hw + 0.5
            while u_x < bar[0] + bar_hw - 0.5:
                draw_cube(u_x, bar[1] - 0.3, bar[2], 0.05, 0.4, 0.05, cls.C_METAL_DARK)
                draw_cube(u_x, bar[1] - 0.55, bar[2], 0.18, 0.12, 0.06, cls.C_METAL_LIGHT)
                u_x += 0.7

        # ── Ceiling fluorescent light
        lo = cls.lights_on[5]
        draw_cube(cx, H - 0.12, cz, cls.KITCH_W * 0.5, 0.08, 0.35, cls.C_METAL_LIGHT)
        bc = cls.C_BULB_COLD if lo else cls.C_BULB_DEAD
        be = cls.C_BULB_COLD_EM if lo else None
        for fx in [-2.5, 0.0, 2.5]:
            draw_cube(cx + fx, H - 0.2, cz, 1.8, 0.1, 0.3, bc,
                      emissive=be)

        # ── Stacked supply crates in SW corner
        for scy in range(3):
            draw_cube(cx - hw + 0.85, 0.85 + scy * 1.05, cz + hd - 0.9,
                      1.5, 1.0, 1.5, cls.C_WOOD_MED)

    # ══════════════════════════════════════════════════════
    # ROOM 8 — GUARD BARRACKS
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_barracks(cls, t):
        """Draw the Guard Barracks — lockers, bunk beds, loot.

        Args:
            t: Elapsed time.
        """
        cx, cz = cls.BUNK_X, cls.BUNK_Z
        hw = cls.BUNK_W / 2.0
        hd = cls.BUNK_D / 2.0
        H  = cls.BUNK_H
        wt = cls.WALL_T

        # Floor
        cls._draw_solid_floor(cx, cz, cls.BUNK_W, cls.BUNK_D, cls.C_CONCRETE)

        # Ceiling
        cls._draw_ceiling_slab(cx, cz, cls.BUNK_W, cls.BUNK_D, cls.C_CEILING_DARK, H)

        # Walls
        draw_cube(cx, H / 2.0, cz - hd, cls.BUNK_W, H, wt, cls.C_WALL_DARK)
        draw_cube(cx, H / 2.0, cz + hd, cls.BUNK_W, H, wt, cls.C_WALL_DARK)
        draw_cube(cx + hw, H / 2.0, cz, wt, H, cls.BUNK_D, cls.C_WALL_DARK)

        # West wall — door to kitchen
        w_seg = (cls.BUNK_D - cls.DOOR_W) / 2.0
        draw_cube(cx - hw, H / 2.0, cz - hd + w_seg / 2.0,
                  wt, H, w_seg, cls.C_WALL_DARK)
        draw_cube(cx - hw, H / 2.0, cz + hd - w_seg / 2.0,
                  wt, H, w_seg, cls.C_WALL_DARK)
        draw_cube(cx - hw, cls.DOOR_H + (H - cls.DOOR_H) / 2.0,
                  cz - hd + w_seg + cls.DOOR_W / 2.0,
                  wt, H - cls.DOOR_H, cls.DOOR_W, cls.C_WALL_DARK)
        cls._draw_door_frame(cx - hw, cz - hd + w_seg + cls.DOOR_W / 2.0, 'x')

        # ── Row of metal lockers (east wall)
        for li in range(4):
            lx = cx + hw - 0.5
            lz = cz - hd + 0.8 + li * 1.5
            draw_cube(lx, 1.8, lz, 0.8, 3.6, 1.3, cls.C_LOCKER)
            draw_cube(lx, 1.8, lz, 0.76, 3.55, 1.25, cls.C_LOCKER_ACCENT)
            # Locker seam (top/bottom split)
            draw_cube(lx - 0.41, 1.8, lz, 0.02, 3.4, 1.2, cls.C_METAL_DARK)
            # Handle
            draw_sphere(lx - 0.42, 1.8, lz, 0.06, cls.C_METAL_LIGHT)
            draw_sphere(lx - 0.42, 1.0, lz, 0.06, cls.C_METAL_LIGHT)
            # Ventilation slits
            for vs in range(5):
                draw_cube(lx - 0.41, 2.5 + vs * 0.25, lz,
                          0.02, 0.04, 1.1, cls.C_METAL_DARK)

        # ── 3 Bunk bed stacks
        for bi in range(3):
            bx = cx - hw + 1.4 + bi * 3.5
            bz = cz + hd - 1.6

            # Bottom bunk frame
            draw_cube(bx, 0.35, bz, 2.4, 0.08, 1.1, cls.C_WOOD_DARK)
            # Bottom legs
            for dlx, dlz in [(-1.1, -0.45), (1.1, -0.45), (-1.1, 0.45), (1.1, 0.45)]:
                draw_cube(bx + dlx, 0.18, bz + dlz, 0.1, 0.35, 0.1, cls.C_METAL_DARK)
            # Bottom mattress
            draw_cube(bx, 0.44, bz, 2.2, 0.12, 0.95, cls.C_METAL_MED)

            # Upper bunk frame
            draw_cube(bx, 1.8, bz, 2.4, 0.08, 1.1, cls.C_WOOD_DARK)
            # Vertical posts
            for dlx, dlz in [(-1.1, -0.45), (1.1, -0.45), (-1.1, 0.45), (1.1, 0.45)]:
                draw_cube(bx + dlx, 1.1, bz + dlz, 0.1, 1.5, 0.1, cls.C_METAL_DARK)
            # Upper mattress
            draw_cube(bx, 1.9, bz, 2.2, 0.12, 0.95, cls.C_METAL_MED)

            # Guard rail on top bunk
            draw_cube(bx, 2.35, bz + 0.5, 2.2, 0.35, 0.06, cls.C_METAL_DARK)

        # ── Loot items (cash bags) on floor
        cash_y = 0.38 + math.sin(t * cls.BOB_SPEED + 0.5) * cls.BOB_AMPLITUDE
        draw_sphere(cx - 1.0, cash_y, cz + 1.0, cls.COLLECT_R,
                    cls.C_CASH, emissive=cls.C_CASH_EM)

        # ── Dim overhead fixture
        draw_cube(cx, H - 0.2, cz, cls.BUNK_W * 0.4, 0.1, 0.4, cls.C_METAL_DARK)
        draw_sphere(cx, H - 0.35, cz, 0.15, cls.C_BULB_DEAD)

    # ══════════════════════════════════════════════════════
    # KEYCARD COLLECTIBLE — Security Office
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_keycard(cls, t):
        """Draw the keycard collectible on the security office desk."""
        kx, ky, kz = cls.COLLECTIBLES[1][0], cls.COLLECTIBLES[1][1], cls.COLLECTIBLES[1][2]
        bob_y = 1.2 + math.sin(t * cls.BOB_SPEED + 3.0) * cls.BOB_AMPLITUDE
        # Card body
        set_material(cls.C_KEYCARD, emissive=cls.C_KEYCARD_EM)
        glPushMatrix()
        glTranslatef(kx, bob_y, kz)
        glRotatef(t * 60.0, 0.0, 1.0, 0.0)   # Slow spin
        glScalef(0.35, 0.06, 0.55)
        glutSolidCube(1)
        glPopMatrix()
        # Chip
        draw_cube(kx, bob_y + 0.04, kz + 0.05,
                  0.12, 0.04, 0.14, cls.C_BRASS)

    # ══════════════════════════════════════════════════════
    # HUD OVERLAY
    # ══════════════════════════════════════════════════════

    @classmethod
    def _draw_hud(cls):
        """Draw 2D HUD overlay with light status and level info."""
        draw_text_2d(20, 760, "LEVEL 2 — THE GRAND HEIST ARENA")
        draw_text_2d(20, 730, "WASD: Move   Mouse: Look   ESC: Free Cursor")
        draw_text_2d(20, 700, "L: Toggle next light (simulate projectile hit)")

        # Light status bar
        draw_text_2d(20, 50, "LIGHTS:  [1]Chandelier  [2]Corridor-A  "
                              "[3]Corridor-B  [4]Vault  [5]Office  [6]Kitchen")
        status = ""
        labels = ["CHAN", "CORR-A", "CORR-B", "VAULT", "OFFICE", "KITCH"]
        for i, label in enumerate(labels):
            state = "ON " if cls.lights_on[i] else "OFF"
            status += f"  {label}:{state}"
        draw_text_2d(20, 28, status)

        if cls.lights_on[6]:
            draw_text_2d(20, 670, "! EMERGENCY LIGHTS ACTIVE !")

    # ══════════════════════════════════════════════════════
    # MAIN DRAW ENTRY POINT
    # ══════════════════════════════════════════════════════

    @classmethod
    def draw(cls, time_elapsed):
        """Draw the entire Level 2 scene. Called every frame by the game loop.

        Args:
            time_elapsed: Total elapsed time in seconds (drives animations).
        """
        cls.setup_lighting()

        # Core rooms
        cls._draw_foyer(time_elapsed)
        cls._draw_corridor()
        cls._draw_security_office()
        cls._draw_vault(time_elapsed)
        cls._draw_library(time_elapsed)
        cls._draw_utility_room()
        cls._draw_kitchen(time_elapsed)
        cls._draw_barracks(time_elapsed)

        # Standalone collectibles
        cls._draw_keycard(time_elapsed)

        # HUD
        cls._draw_hud()
