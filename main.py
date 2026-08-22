"""
Honour Among Thieves — Single-file submission build.

Merged from:
  - utils/drawing.py   (drawing helpers)
  - levels/tutorial.py (TutorialLevel class)
  - levels/level2.py   (HeistLevel — Grand Mansion Arena)
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

# Level 2 — must be imported after OpenGL is in scope
from levels.level2 import HeistLevel
from utils.inventory import InventoryManager, InventoryItem


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
    glColor3f(r, g, b)  # Ensure it works with GL_COLOR_MATERIAL
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


_is_aiming = False

def draw_crosshair(window_width, window_height, is_aiming=False):
    """Draw tactical 2D crosshair reticle in the middle of the screen ONLY when aiming."""
    if not is_aiming:
        return  # Crosshair is DISABLED / HIDDEN when not aiming

    cx = window_width / 2.0
    cy = window_height / 2.0

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Glowing Cyan Reticle during Active Aiming (Hold Left Click)
    color = (0.2, 0.95, 1.0, 0.95)
    gap = 6.0
    size = 16.0
    line_w = 2.5

    glColor4f(*color)
    glLineWidth(line_w)

    glBegin(GL_LINES)
    # Left bar
    glVertex2f(cx - gap - size, cy)
    glVertex2f(cx - gap, cy)
    # Right bar
    glVertex2f(cx + gap, cy)
    glVertex2f(cx + gap + size, cy)
    # Top bar
    glVertex2f(cx, cy + gap)
    glVertex2f(cx, cy + gap + size)
    # Bottom bar
    glVertex2f(cx, cy - gap - size)
    glVertex2f(cx, cy - gap)
    glEnd()

    # Center dot
    glPointSize(4.0)
    glBegin(GL_POINTS)
    glVertex2f(cx, cy)
    glEnd()

    glLineWidth(1.0)
    glPointSize(1.0)
    glDisable(GL_BLEND)

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
# THIEF CHARACTER DRAWING  (Assigned to: Nafiz — main character visuals)
# Blocky OpenGL rendition of the hooded thief: dark outfit, tan cape,
# utility belt, chunky gloves, heavy boots. "Made by a rookie" aesthetic.
# ══════════════════════════════════════════════════════════════════════════════

class MainCharacter:
    """The main blocky thief character. Made by a rookie."""

    # ── palette ──────────────────────────────────────────────────────────────
    C_SKIN        = (0.85, 0.75, 0.65)   # Pale-ish skin
    C_SMIRK       = (0.70, 0.10, 0.10)   # Red smirk / face mark
    C_HAIR        = (0.05, 0.05, 0.05)   # Black hair
    C_TORSO       = (0.08, 0.10, 0.15)   # Dark blue/black shirt
    C_TORSO_DARK  = (0.05, 0.06, 0.10)   # Darker shadow
    C_BELT        = (0.40, 0.25, 0.12)   # Brown belt
    C_BUCKLE      = (0.75, 0.75, 0.80)   # Metallic studs/buckle
    C_CAPE        = (0.75, 0.55, 0.25)   # Tan/brown cape
    C_CAPE_TORN   = (0.60, 0.40, 0.15)   # Darker torn edge
    C_GLOVE       = (0.45, 0.28, 0.15)   # Brown leather glove
    C_LEG         = (0.10, 0.10, 0.12)   # Dark pants
    C_BOOT        = (0.35, 0.20, 0.10)   # Brown boots
    C_BOOT_SOLE   = (0.15, 0.10, 0.05)   # Boot sole
    C_BOOT_CAP    = (0.40, 0.25, 0.12)   # Boot cap
    C_DAGGER_HILT = (0.55, 0.05, 0.05)   # Dark red dagger handle
    C_DAGGER_BLD  = (0.60, 0.60, 0.65)   # Blade (steel)

    def __init__(self, x=0.0, y=0.0, z=0.0, yaw_deg=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw_deg = yaw_deg

    def draw(self, time_elapsed=0.0, is_moving=False, is_holding=False):
        """Draw the blocky thief character with animation."""
        # Animation calculations
        if is_moving:
            swing = math.sin(time_elapsed * 12.0) * 45.0
            bob_y = abs(math.sin(time_elapsed * 12.0)) * 0.1
        else:
            swing = 0.0
            bob_y = math.sin(time_elapsed * 2.0) * 0.03

        glPushMatrix()
        glTranslatef(self.x, self.y + bob_y, self.z)
        glRotatef(self.yaw_deg, 0.0, 1.0, 0.0)

        # ── LEFT LEG & BOOT ──────────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(-0.17, 1.0, 0.0)           # Move to hip joint
        glRotatef(swing, 1.0, 0.0, 0.0)         # Swing leg
        glTranslatef(0.17, -1.0, 0.0)           # Move back
        
        draw_cube(-0.17, 0.70, 0.0,   0.21, 0.60, 0.21, self.C_LEG)          # Leg
        draw_cube(-0.18, 0.20, 0.0,   0.22, 0.40, 0.28, self.C_BOOT)         # Boot
        draw_cube(-0.18, 0.04, 0.02,  0.24, 0.08, 0.32, self.C_BOOT_SOLE)    # Boot sole
        glPopMatrix()

        # ── RIGHT LEG & BOOT ─────────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.17, 1.0, 0.0)
        glRotatef(-swing, 1.0, 0.0, 0.0)
        glTranslatef(-0.17, -1.0, 0.0)
        
        draw_cube( 0.17, 0.70, 0.0,   0.21, 0.60, 0.21, self.C_LEG)
        draw_cube( 0.18, 0.20, 0.0,   0.22, 0.40, 0.28, self.C_BOOT)
        draw_cube( 0.18, 0.04, 0.02,  0.24, 0.08, 0.32, self.C_BOOT_SOLE)
        glPopMatrix()

        # ── UTILITY BELT ─────────────────────────────────────────────────────────
        draw_cube(0.0, 1.07, 0.0,     0.60, 0.14, 0.34, self.C_BELT)
        draw_cube(0.0, 1.07, 0.18,    0.14, 0.14, 0.06, self.C_BUCKLE)       # Buckle
        draw_cube(-0.22, 1.07, 0.14,  0.14, 0.16, 0.12, self.C_BELT)         # Pouch L
        draw_cube( 0.22, 1.07, 0.14,  0.14, 0.16, 0.12, self.C_BELT)         # Pouch R

        # ── TORSO ────────────────────────────────────────────────────────────────
        draw_cube(0.0, 1.30, 0.0,     0.56, 0.60, 0.32, self.C_TORSO)
        draw_cube(0.0, 1.38, 0.16,    0.40, 0.30, 0.06, self.C_TORSO_DARK)   # Chest pad

        # ── LEFT ARM ─────────────────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(-0.40, 1.5, 0.0)           # Shoulder joint
        if is_holding:
            glRotatef(-65.0, 1.0, 0.0, 0.0)      # Raise arms forward carrying box
            glRotatef(15.0, 0.0, 1.0, 0.0)
        else:
            glRotatef(-swing, 1.0, 0.0, 0.0)
        glTranslatef(0.40, -1.5, 0.0)
        
        draw_cube(-0.40, 1.38, 0.0,   0.18, 0.44, 0.20, self.C_TORSO)        # Upper arm
        draw_cube(-0.42, 1.08, 0.04,  0.20, 0.28, 0.22, self.C_GLOVE)        # Forearm
        draw_cube(-0.44, 0.96, 0.06,  0.22, 0.18, 0.22, self.C_GLOVE)        # Hand
        glPopMatrix()

        # ── RIGHT ARM ────────────────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.40, 1.5, 0.0)
        if is_holding:
            glRotatef(-65.0, 1.0, 0.0, 0.0)
            glRotatef(-15.0, 0.0, 1.0, 0.0)
        else:
            glRotatef(swing, 1.0, 0.0, 0.0)
        glTranslatef(-0.40, -1.5, 0.0)
        
        draw_cube( 0.40, 1.38, 0.0,   0.18, 0.44, 0.20, self.C_TORSO)
        draw_cube( 0.44, 1.10, -0.04, 0.20, 0.28, 0.22, self.C_GLOVE)
        draw_cube( 0.46, 0.98, -0.06, 0.22, 0.18, 0.22, self.C_GLOVE)
        glPopMatrix()

        # Cape has been removed

        # ── NECK & HEAD ──────────────────────────────────────────────────────────
        draw_cube(0.0, 1.64, 0.0,     0.18, 0.16, 0.18, self.C_SKIN)
        draw_cube(0.0, 1.86, 0.0,     0.40, 0.38, 0.38, self.C_SKIN)
        
        # Eyes
        draw_cube(-0.10, 1.90, 0.19,  0.10, 0.08, 0.04, (0.06, 0.04, 0.04))
        draw_cube( 0.10, 1.90, 0.19,  0.10, 0.08, 0.04, (0.06, 0.04, 0.04))
        
        # Red smirk/mark
        draw_cube(0.0, 1.76, 0.19,    0.28, 0.05, 0.03, self.C_SMIRK)

        # ── HAIR (Spikes + Top-knot) ─────────────────────────────────────────────
        draw_cube(0.0,   2.06, -0.04, 0.38, 0.12, 0.32, self.C_HAIR)   # Base
        draw_cube(0.0,   2.16,  0.0,  0.12, 0.22, 0.12, self.C_HAIR)   # Top-knot
        draw_cube( 0.14, 2.14,  0.0,  0.10, 0.10, 0.10, self.C_HAIR)   # Right spike
        draw_cube(-0.18, 2.12,  0.0,  0.08, 0.08, 0.08, self.C_HAIR)   # Left spike

        # ── DAGGER ───────────────────────────────────────────────────────────────
        draw_cube(0.0, 1.22, -0.28,   0.22, 0.06, 0.06, self.C_DAGGER_BLD)   # Guard (steel)
        draw_cube(0.0, 1.12, -0.30,   0.08, 0.22, 0.08, self.C_DAGGER_HILT)  # Grip (red)
        draw_cube(0.0, 1.00, -0.30,   0.12, 0.08, 0.12, self.C_DAGGER_BLD)   # Pommel (steel)
        draw_cube(0.0, 1.34, -0.30,   0.05, 0.20, 0.05, self.C_DAGGER_BLD)   # Blade tip

        glPopMatrix()


class ThinPoliceModel:
    """Thin police officer with Papa's Pizzeria spacing."""
    C_SKIN       = (0.85, 0.75, 0.65)
    C_UNIFORM    = (0.10, 0.15, 0.40)   # Blue
    C_UNIFORM_DK = (0.05, 0.10, 0.30)
    C_BADGE      = (0.90, 0.80, 0.10)   # Yellow
    C_BELT       = (0.10, 0.10, 0.10)   # Black
    C_SHOE       = (0.05, 0.05, 0.05)   # Black
    C_HAT        = (0.10, 0.15, 0.40)
    C_HAT_VISOR  = (0.05, 0.05, 0.05)

    def __init__(self, x=0.0, y=0.0, z=0.0, yaw_deg=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw_deg = yaw_deg

    def draw(self, time_elapsed=0.0, is_moving=False, is_attacking=False):
        if is_attacking:
            l_arm = -80.0 + math.sin(time_elapsed * 25.0) * 45.0
            r_arm = -80.0 - math.sin(time_elapsed * 25.0) * 45.0
            swing = 0.0
            bob_y = math.sin(time_elapsed * 10.0) * 0.05
        elif is_moving:
            swing = math.sin(time_elapsed * 12.0) * 45.0
            l_arm = -swing
            r_arm = swing
            bob_y = abs(math.sin(time_elapsed * 12.0)) * 0.1
        else:
            swing = 0.0
            l_arm = 0.0
            r_arm = 0.0
            bob_y = math.sin(time_elapsed * 2.0) * 0.03

        glPushMatrix()
        glTranslatef(self.x, self.y + bob_y, self.z)
        glRotatef(self.yaw_deg, 0.0, 1.0, 0.0)

        # ── LEFT LEG (Thin & Spaced) ──────────────────────────────────────────
        glPushMatrix()
        glTranslatef(-0.15, 1.0, 0.0)
        glRotatef(swing, 1.0, 0.0, 0.0)
        glTranslatef(0.15, -1.0, 0.0)
        draw_cube(-0.15, 0.55, 0.0,   0.10, 0.90, 0.10, self.C_UNIFORM_DK) # Thin leg
        draw_cube(-0.15, 0.08, 0.05,  0.12, 0.16, 0.20, self.C_SHOE)       # Shoe
        glPopMatrix()

        # ── RIGHT LEG (Thin & Spaced) ─────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.15, 1.0, 0.0)
        glRotatef(-swing, 1.0, 0.0, 0.0)
        glTranslatef(-0.15, -1.0, 0.0)
        draw_cube( 0.15, 0.55, 0.0,   0.10, 0.90, 0.10, self.C_UNIFORM_DK) # Thin leg
        draw_cube( 0.15, 0.08, 0.05,  0.12, 0.16, 0.20, self.C_SHOE)       # Shoe
        glPopMatrix()

        # ── TORSO (Very thin) ─────────────────────────────────────────────────
        draw_cube(0.0, 1.35, 0.0,     0.25, 0.70, 0.15, self.C_UNIFORM)
        
        # Belt
        draw_cube(0.0, 1.00, 0.0,     0.26, 0.10, 0.16, self.C_BELT)
        draw_cube(0.0, 1.00, 0.09,    0.08, 0.08, 0.02, self.C_BADGE) # Buckle
        
        # Badge
        draw_cube(-0.06, 1.55, 0.08,  0.06, 0.06, 0.02, self.C_BADGE)

        # ── LEFT ARM (Thin) ───────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(-0.18, 1.6, 0.0)
        glRotatef(l_arm, 1.0, 0.0, 0.0)
        glTranslatef(0.18, -1.6, 0.0)
        draw_cube(-0.18, 1.30, 0.0,   0.08, 0.60, 0.08, self.C_UNIFORM)
        draw_cube(-0.18, 0.95, 0.0,   0.10, 0.10, 0.10, self.C_SKIN) # Hand
        glPopMatrix()

        # ── RIGHT ARM (Thin) ──────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.18, 1.6, 0.0)
        glRotatef(r_arm, 1.0, 0.0, 0.0)
        glTranslatef(-0.18, -1.6, 0.0)
        draw_cube( 0.18, 1.30, 0.0,   0.08, 0.60, 0.08, self.C_UNIFORM)
        draw_cube( 0.18, 0.95, 0.0,   0.10, 0.10, 0.10, self.C_SKIN) # Hand
        glPopMatrix()

        # ── HEAD (Large, Papa's style) ────────────────────────────────────────
        draw_cube(0.0, 1.76, 0.0,     0.10, 0.12, 0.10, self.C_SKIN) # Neck
        draw_cube(0.0, 2.05, 0.0,     0.45, 0.45, 0.45, self.C_SKIN) # Huge Head
        
        # Eyes
        draw_cube(-0.12, 2.10, 0.23,  0.08, 0.08, 0.04, self.C_SHOE)
        draw_cube( 0.12, 2.10, 0.23,  0.08, 0.08, 0.04, self.C_SHOE)

        # Mustache
        draw_cube(0.0, 1.95, 0.24,    0.20, 0.05, 0.04, self.C_SHOE)

        # Hat
        draw_cube(0.0, 2.30, 0.0,     0.46, 0.10, 0.46, self.C_HAT)
        draw_cube(0.0, 2.25, 0.25,    0.46, 0.04, 0.15, self.C_HAT_VISOR)
        draw_cube(0.0, 2.30, 0.24,    0.08, 0.08, 0.02, self.C_BADGE)

        glPopMatrix()


class FatPoliceModel:
    """Fat police officer with wide torso."""
    C_SKIN       = (0.85, 0.75, 0.65)
    C_UNIFORM    = (0.10, 0.15, 0.40)
    C_UNIFORM_DK = (0.05, 0.10, 0.30)
    C_BADGE      = (0.90, 0.80, 0.10)
    C_BELT       = (0.10, 0.10, 0.10)
    C_SHOE       = (0.05, 0.05, 0.05)
    C_HAT        = (0.10, 0.15, 0.40)
    C_HAT_VISOR  = (0.05, 0.05, 0.05)

    def __init__(self, x=0.0, y=0.0, z=0.0, yaw_deg=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw_deg = yaw_deg

    def draw(self, time_elapsed=0.0, is_moving=False, is_attacking=False):
        if is_attacking:
            l_arm = -80.0 + math.sin(time_elapsed * 25.0) * 45.0
            r_arm = -80.0 - math.sin(time_elapsed * 25.0) * 45.0
            swing = 0.0
            bob_y = math.sin(time_elapsed * 10.0) * 0.05
        elif is_moving:
            swing = math.sin(time_elapsed * 8.0) * 35.0
            l_arm = -swing
            r_arm = swing
            bob_y = abs(math.sin(time_elapsed * 8.0)) * 0.15
        else:
            swing = 0.0
            l_arm = 0.0
            r_arm = 0.0
            bob_y = math.sin(time_elapsed * 1.5) * 0.04

        glPushMatrix()
        glTranslatef(self.x, self.y + bob_y, self.z)
        glRotatef(self.yaw_deg, 0.0, 1.0, 0.0)

        # ── LEFT LEG (Stubby) ─────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(-0.25, 0.6, 0.0)
        glRotatef(swing, 1.0, 0.0, 0.0)
        glTranslatef(0.25, -0.6, 0.0)
        draw_cube(-0.25, 0.35, 0.0,   0.25, 0.50, 0.25, self.C_UNIFORM_DK)
        draw_cube(-0.25, 0.08, 0.05,  0.28, 0.16, 0.30, self.C_SHOE)
        glPopMatrix()

        # ── RIGHT LEG (Stubby) ────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.25, 0.6, 0.0)
        glRotatef(-swing, 1.0, 0.0, 0.0)
        glTranslatef(-0.25, -0.6, 0.0)
        draw_cube( 0.25, 0.35, 0.0,   0.25, 0.50, 0.25, self.C_UNIFORM_DK)
        draw_cube( 0.25, 0.08, 0.05,  0.28, 0.16, 0.30, self.C_SHOE)
        glPopMatrix()

        # ── TORSO (Wide & Roundish) ───────────────────────────────────────────
        draw_cube(0.0, 1.15, 0.0,     0.70, 0.90, 0.55, self.C_UNIFORM)
        
        # Belt (below belly)
        draw_cube(0.0, 0.70, 0.0,     0.72, 0.10, 0.57, self.C_BELT)
        draw_cube(0.0, 0.70, 0.29,    0.10, 0.10, 0.02, self.C_BADGE) # Buckle
        
        # Badge
        draw_cube(-0.18, 1.35, 0.28,  0.08, 0.08, 0.02, self.C_BADGE)

        # ── LEFT ARM (Thick) ──────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(-0.45, 1.4, 0.0)
        glRotatef(l_arm, 1.0, 0.0, 0.0)
        glTranslatef(0.45, -1.4, 0.0)
        draw_cube(-0.45, 1.05, 0.0,   0.20, 0.70, 0.20, self.C_UNIFORM)
        draw_cube(-0.45, 0.65, 0.0,   0.16, 0.16, 0.16, self.C_SKIN) # Hand
        glPopMatrix()

        # ── RIGHT ARM (Thick) ─────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.45, 1.4, 0.0)
        glRotatef(r_arm, 1.0, 0.0, 0.0)
        glTranslatef(-0.45, -1.4, 0.0)
        draw_cube( 0.45, 1.05, 0.0,   0.20, 0.70, 0.20, self.C_UNIFORM)
        draw_cube( 0.45, 0.65, 0.0,   0.16, 0.16, 0.16, self.C_SKIN) # Hand
        glPopMatrix()

        # ── HEAD (Small relative to body) ─────────────────────────────────────
        draw_cube(0.0, 1.65, 0.0,     0.20, 0.10, 0.20, self.C_SKIN) # Neck
        draw_cube(0.0, 1.85, 0.0,     0.32, 0.32, 0.32, self.C_SKIN) # Head
        
        # Eyes
        draw_cube(-0.08, 1.90, 0.17,  0.06, 0.06, 0.03, self.C_SHOE)
        draw_cube( 0.08, 1.90, 0.17,  0.06, 0.06, 0.03, self.C_SHOE)

        # Mustache
        draw_cube(0.0, 1.78, 0.17,    0.16, 0.06, 0.04, self.C_SHOE)

        # Hat
        draw_cube(0.0, 2.05, 0.0,     0.34, 0.10, 0.34, self.C_HAT)
        draw_cube(0.0, 2.00, 0.17,    0.34, 0.04, 0.15, self.C_HAT_VISOR)
        draw_cube(0.0, 2.05, 0.17,    0.06, 0.06, 0.02, self.C_BADGE)

        glPopMatrix()


# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE OBSTACLES  (Assigned to: Ahona — Feature 1: Interactive Obstacle Design)
# ══════════════════════════════════════════════════════════════════════════════

class Obstacle:
    """Base class for interactive 3D world obstacles."""

    def __init__(self, x, y, z, width, height, depth, rotation=0.0,
                 is_interactive=True, can_hide_inside=False, can_be_pushed=False,
                 color=(0.5, 0.5, 0.5), accent_color=(0.3, 0.3, 0.3)):
        self.x = float(x)
        self.y = float(y)  # Base ground Y level
        self.z = float(z)
        self.width = float(width)
        self.height = float(height)
        self.depth = float(depth)
        self.rotation = float(rotation)
        self.is_interactive = is_interactive
        self.can_hide_inside = can_hide_inside
        self.can_be_pushed = can_be_pushed
        self.color = color
        self.accent_color = accent_color
        self.is_player_hiding = False

    def draw(self):
        """Render 3D GLUT/OpenGL geometry. Subclasses override this."""
        pass

    def interact(self, camera):
        """Triggered when the player interacts with this obstacle. Returns True if state changed."""
        return False

    def get_bounding_box(self):
        """Return axis-aligned bounding box (min_x, max_x, min_y, max_y, min_z, max_z)."""
        hw = self.width / 2.0
        hd = self.depth / 2.0
        return (
            self.x - hw, self.x + hw,
            self.y, self.y + self.height,
            self.z - hd, self.z + hd
        )

    def distance_to(self, target_x, target_z):
        """Calculate planar 2D distance from obstacle center to target position."""
        dx = self.x - target_x
        dz = self.z - target_z
        return math.sqrt(dx * dx + dz * dz)


class BoxObstacle(Obstacle):
    """
    Wooden Crate / Box Obstacle.
    Can be pushed for cover or used to block paths and reach items.
    """

    def __init__(self, x, y, z, size=1.5, rotation=0.0,
                 color=(0.55, 0.41, 0.08), accent_color=(0.35, 0.25, 0.05)):
        super().__init__(
            x=x, y=y, z=z,
            width=size, height=size, depth=size,
            rotation=rotation,
            is_interactive=True,
            can_hide_inside=False,
            can_be_pushed=True,
            color=color,
            accent_color=accent_color
        )
        self.size = size

    def interact(self, camera):
        if not self.can_be_pushed:
            return False
        rad_yaw = math.radians(camera.yaw)
        self.x += math.cos(rad_yaw) * 1.5
        self.z += math.sin(rad_yaw) * 1.5
        print("Pushed the box!")
        return True

    def draw(self):
        s = self.size
        by = self.y + s / 2.0

        glPushMatrix()
        glTranslatef(self.x, by, self.z)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)

        # Main crate body
        set_material(self.color)
        glPushMatrix()
        glScalef(s, s, s)
        glutSolidCube(1)
        glPopMatrix()

        # Wooden planks / cross-framing details
        set_material(self.accent_color)
        plank_off = s / 2.0 + 0.01

        # Horizontal & vertical planks on front/back faces
        for dz in (-plank_off, plank_off):
            glPushMatrix()
            glTranslatef(0.0, 0.0, dz)
            glScalef(s * 0.9, 0.1, 0.04)
            glutSolidCube(1)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.0, 0.0, dz)
            glScalef(0.1, s * 0.9, 0.04)
            glutSolidCube(1)
            glPopMatrix()

        # Metal corner brackets (small dark cubes)
        set_material((0.2, 0.2, 0.2))
        hs = s / 2.0
        for dx in (-hs, hs):
            for dy in (-hs + 0.1, hs - 0.1):
                for dz in (-hs, hs):
                    glPushMatrix()
                    glTranslatef(dx, dy, dz)
                    glutSolidCube(0.12)
                    glPopMatrix()

        glPopMatrix()


class ClosetObstacle(Obstacle):
    """
    Tall Wooden Closet / Wardrobe.
    Allows player to hide inside to evade guard line of sight.
    """

    def __init__(self, x, y, z, width=1.6, height=3.2, depth=1.2, rotation=0.0,
                 color=(0.36, 0.22, 0.12), accent_color=(0.24, 0.14, 0.07)):
        super().__init__(
            x=x, y=y, z=z,
            width=width, height=height, depth=depth,
            rotation=rotation,
            is_interactive=True,
            can_hide_inside=True,
            color=color,
            accent_color=accent_color
        )
        self.is_open = False
        # Animation state (0.0 = fully closed, 1.0 = fully open)
        self._anim_progress = 0.0   # Current visual interpolation progress
        self._anim_start_time = None  # time.time() when animation started
        self._anim_duration = 0.5     # Seconds to fully open/close
        self._anim_opening = True     # Direction of animation

    def _update_anim(self):
        """Advance the door-swing animation and return the current eased progress."""
        if self._anim_start_time is None:
            return self._anim_progress

        elapsed = time.time() - self._anim_start_time
        t = min(elapsed / self._anim_duration, 1.0)

        # Ease-in-out cubic
        if t < 0.5:
            ease = 4.0 * t * t * t
        else:
            p = t - 1.0
            ease = 1.0 + 4.0 * p * p * p

        if self._anim_opening:
            self._anim_progress = ease
        else:
            self._anim_progress = 1.0 - ease

        if t >= 1.0:
            self._anim_start_time = None  # Animation complete

        return self._anim_progress

    def interact(self, camera):
        self.is_open = not self.is_open
        self._anim_opening = self.is_open
        self._anim_start_time = time.time()
        print("Closet door", "opened" if self.is_open else "closed")
        return True

    def draw(self):
        w, h, d = self.width, self.height, self.depth
        cy = self.y + h / 2.0
        t = 0.1  # Panel thickness

        glPushMatrix()
        glTranslatef(self.x, cy, self.z)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)

        # Back panel
        set_material(self.color)
        glPushMatrix()
        glTranslatef(0.0, 0.0, -d / 2.0 + t / 2.0)
        glScalef(w, h, t)
        glutSolidCube(1)
        glPopMatrix()

        # Left side panel
        glPushMatrix()
        glTranslatef(-w / 2.0 + t / 2.0, 0.0, 0.0)
        glScalef(t, h, d)
        glutSolidCube(1)
        glPopMatrix()

        # Right side panel
        glPushMatrix()
        glTranslatef(w / 2.0 - t / 2.0, 0.0, 0.0)
        glScalef(t, h, d)
        glutSolidCube(1)
        glPopMatrix()

        # Top ceiling panel & moulding
        set_material(self.accent_color)
        glPushMatrix()
        glTranslatef(0.0, h / 2.0 - t / 2.0, 0.0)
        glScalef(w + 0.1, t * 1.5, d + 0.1)
        glutSolidCube(1)
        glPopMatrix()

        # Bottom floor panel
        glPushMatrix()
        glTranslatef(0.0, -h / 2.0 + t / 2.0, 0.0)
        glScalef(w, t, d)
        glutSolidCube(1)
        glPopMatrix()

        # Dual Closet Doors (front face)
        door_w = (w - t * 2) / 2.0 - 0.02
        door_h = h - t * 2 - 0.1
        front_z = d / 2.0 - t / 2.0

        set_material(self.color)

        # Advance the swing animation each frame
        anim = self._update_anim()  # 0.0 = closed, 1.0 = fully open
        swing_angle = anim * 90.0   # 0 → 90 degrees

        # ── LEFT DOOR GROUP ──
        # Pivot is at the LEFT hinge edge (x = -door_w - 0.01)
        glPushMatrix()
        glTranslatef(-door_w - 0.01, 0.0, front_z)  # Move pivot to hinge
        glRotatef(-swing_angle, 0.0, 1.0, 0.0)       # Swing open
        glTranslatef(door_w + 0.01, 0.0, -front_z)  # Move back

        glPushMatrix()
        glTranslatef(-door_w / 2.0 - 0.01, 0.0, front_z)
        glScalef(door_w, door_h, t * 0.8)
        glutSolidCube(1)
        glPopMatrix()

        set_material((0.85, 0.75, 0.3))  # Brass handles
        glPushMatrix()
        glTranslatef(-0.06, 0.0, front_z + t)
        glutSolidSphere(0.06, 8, 8)
        glPopMatrix()

        glPopMatrix()

        # ── RIGHT DOOR GROUP ──
        # Pivot is at the RIGHT hinge edge (x = door_w + 0.01)
        set_material(self.color)
        glPushMatrix()
        glTranslatef(door_w + 0.01, 0.0, front_z)   # Move pivot to hinge
        glRotatef(swing_angle, 0.0, 1.0, 0.0)        # Swing open
        glTranslatef(-door_w - 0.01, 0.0, -front_z) # Move back

        glPushMatrix()
        glTranslatef(door_w / 2.0 + 0.01, 0.0, front_z)
        glScalef(door_w, door_h, t * 0.8)
        glutSolidCube(1)
        glPopMatrix()

        set_material((0.85, 0.75, 0.3))  # Brass handles
        glPushMatrix()
        glTranslatef(0.06, 0.0, front_z + t)
        glutSolidSphere(0.06, 8, 8)
        glPopMatrix()

        glPopMatrix()

        glPopMatrix()


class DumpsterObstacle(Obstacle):
    """
    Industrial Metal Dumpster.
    Provides cover and can be hidden inside with a cinematic jump-in animation.

    Hide sequence  (press F near dumpster when outside):
      Phase 1 — LID_OPEN   (0.40 s): lids swing open.
      Phase 2 — JUMP_IN    (0.55 s): character runs to dumpster then arcs in.
      Phase 3 — LID_CLOSE  (0.35 s): lids close over player. Camera snaps inside.
      Phase 4 — HIDDEN     (∞):      player is inside, movement locked.

    Exit sequence (press F near dumpster when inside):
      Phase 5 — LID_OPEN_X  (0.35 s): lids swing open.
      Phase 6 — JUMP_OUT    (0.55 s): character arcs out. Camera restored.
      Phase 7 — LID_CLOSE_X (0.35 s): lids swing closed behind player.
    """

    # ── phase constants ──────────────────────────────────────────────────────
    _PH_NONE       = 0
    _PH_LID_OPEN   = 1
    _PH_JUMP_IN    = 2
    _PH_LID_CLOSE  = 3
    _PH_HIDDEN     = 4
    _PH_LID_OPEN_X = 5
    _PH_JUMP_OUT   = 6
    _PH_LID_CLO_X  = 7

    _PHASE_DUR = {1: 0.40, 2: 0.55, 3: 0.35, 5: 0.35, 6: 0.55, 7: 0.35}
    _NEXT_PHASE = {1: 2, 2: 3, 3: 4, 5: 6, 6: 7, 7: 0}

    def __init__(self, x, y, z, width=2.6, height=1.6, depth=1.6, rotation=0.0,
                 color=(0.18, 0.35, 0.24), accent_color=(0.12, 0.22, 0.15)):
        super().__init__(
            x=x, y=y, z=z,
            width=width, height=height, depth=depth,
            rotation=rotation,
            is_interactive=True,
            can_hide_inside=True,
            color=color,
            accent_color=accent_color
        )
        self.saved_camera_pos = None
        self._hide_phase  = self._PH_NONE
        self._phase_start = 0.0
        self._camera_ref  = None
        # Character start position & yaw captured when hide starts
        self._char_start  = (0.0, 0.0, 0.0, 0.0)   # (x, y_feet, z, yaw_deg)
        # Landing position for exit jump (restored camera feet level)
        self._char_exit   = (0.0, 0.0, 0.0)         # (x, y_feet, z)

    # ── helpers ─────────────────────────────────────────────────────────────

    def _phase_t(self):
        """Normalised [0, 1] time within the current phase."""
        dur = self._PHASE_DUR.get(self._hide_phase, 1.0)
        return min((time.time() - self._phase_start) / dur, 1.0)

    @staticmethod
    def _ease_out(t):
        return 1.0 - (1.0 - t) ** 2

    @staticmethod
    def _ease_in_out(t):
        if t < 0.5:
            return 4.0 * t * t * t
        p = t - 1.0
        return 1.0 + 4.0 * p * p * p

    def _lid_progress(self):
        """Return lid open amount [0=closed, 1=open] for the current phase."""
        ph = self._hide_phase
        t  = self._phase_t()
        if   ph == self._PH_LID_OPEN:   return self._ease_in_out(t)
        elif ph == self._PH_JUMP_IN:    return 1.0
        elif ph == self._PH_LID_CLOSE:  return 1.0 - self._ease_in_out(t)
        elif ph == self._PH_HIDDEN:     return 0.0
        elif ph == self._PH_LID_OPEN_X: return self._ease_in_out(t)
        elif ph == self._PH_JUMP_OUT:   return 1.0
        elif ph == self._PH_LID_CLO_X:  return 1.0 - self._ease_in_out(t)
        return 0.0   # _PH_NONE

    def _advance_phase(self):
        """Tick the state machine; fire side-effects on transitions."""
        if self._hide_phase in (self._PH_NONE, self._PH_HIDDEN):
            return
        dur = self._PHASE_DUR.get(self._hide_phase, 1.0)
        if time.time() - self._phase_start < dur:
            return

        next_ph = self._NEXT_PHASE.get(self._hide_phase, self._PH_NONE)
        cam = self._camera_ref

        # ── transition side-effects ──────────────────────────────────────────
        if next_ph == self._PH_HIDDEN and cam:
            # Snap camera inside dumpster
            cam.x = self.x
            cam.z = self.z
            cam.y = self.y + self.height * 0.5

        if next_ph == self._PH_NONE and cam:
            # Exit animation fully done: unlock movement
            cam.movement_locked = False
            self.is_player_hiding = False

        self._hide_phase  = next_ph
        self._phase_start = time.time()

    # ── public API ───────────────────────────────────────────────────────────

    def is_animating(self):
        """True while any hide/exit animation phase is running."""
        return self._hide_phase not in (self._PH_NONE, self._PH_HIDDEN)

    def get_character_pose(self):
        """Return (x, y_feet, z, yaw_deg, visible) for overriding the player draw,
        or None when the normal camera-driven draw should be used."""
        ph = self._hide_phase
        if ph == self._PH_NONE:
            return None

        cx, cy, cz, cyaw = self._char_start
        dumpster_top = self.y + self.height + 0.15   # Just above the rim
        dx, dz = self.x, self.z

        # Yaw that faces from character start toward dumpster center
        angle_rad = math.atan2(dz - cz, dx - cx)
        yaw_toward = -math.degrees(angle_rad) + 90.0

        # ── Phase 1: stand at start, face dumpster ───────────────────────────
        if ph == self._PH_LID_OPEN:
            return (cx, cy, cz, yaw_toward, True)

        # ── Phase 2: run to dumpster then leap in ────────────────────────────
        elif ph == self._PH_JUMP_IN:
            t = self._phase_t()
            RUN_END = 0.55   # Fraction of phase spent running
            if t <= RUN_END:
                rt = self._ease_out(t / RUN_END)
                x = cx + (dx - cx) * rt
                z = cz + (dz - cz) * rt
                return (x, cy, z, yaw_toward, True)
            else:
                # Leap upward arc into the dumpster
                jt = (t - RUN_END) / (1.0 - RUN_END)
                # Parabolic: rises to peak then descends into dumpster
                peak_h = dumpster_top + 0.6
                if jt < 0.5:
                    y = cy + (peak_h - cy) * (jt / 0.5)
                else:
                    y = peak_h + (dumpster_top - 0.4 - peak_h) * ((jt - 0.5) / 0.5)
                visible = jt < 0.85   # Vanish as they drop in
                return (dx, y, dz, yaw_toward, visible)

        # ── Phases 3, 4, 5: inside — character invisible ─────────────────────
        elif ph in (self._PH_LID_CLOSE, self._PH_HIDDEN, self._PH_LID_OPEN_X):
            return (cx, cy, cz, cyaw, False)

        # ── Phase 6: leap out of dumpster ────────────────────────────────────
        elif ph == self._PH_JUMP_OUT:
            t = self._phase_t()
            ex, ey, ez = self._char_exit
            angle_out = math.atan2(ez - dz, ex - dx)
            yaw_out   = -math.degrees(angle_out) + 90.0
            if t < 0.15:
                return (dx, dumpster_top, dz, yaw_out, False)  # Appear just before jump
            jt = self._ease_out((t - 0.15) / 0.85)
            x  = dx + (ex - dx) * jt
            z  = dz + (ez - dz) * jt
            peak_h = dumpster_top + 0.8
            if jt < 0.5:
                y = dumpster_top + (peak_h - dumpster_top) * (jt / 0.5)
            else:
                y = peak_h + (ey - peak_h) * ((jt - 0.5) / 0.5)
            return (x, y, z, yaw_out, True)

        # ── Phase 7: lids closing, character stands at exit pos ──────────────
        elif ph == self._PH_LID_CLO_X:
            ex, ey, ez = self._char_exit
            angle_out = math.atan2(ez - dz, ex - dx)
            yaw_out   = -math.degrees(angle_out) + 90.0
            return (ex, ey, ez, yaw_out, True)

        return None

    def interact(self, camera):
        # Ignore new interactions while an animation is in progress
        if self._hide_phase not in (self._PH_NONE, self._PH_HIDDEN):
            return False

        self._camera_ref = camera

        if not self.is_player_hiding:
            # ── START HIDING ─────────────────────────────────────────────────
            char_yaw = -camera.yaw + 90.0
            self._char_start = (camera.x, camera.y - 1.0, camera.z, char_yaw)
            self.saved_camera_pos = (camera.x, camera.y, camera.z)
            camera.movement_locked = True
            self.is_player_hiding = True
            self._hide_phase  = self._PH_LID_OPEN
            self._phase_start = time.time()
            print("Dumpster: starting hide animation")
        else:
            # ── START EXITING ────────────────────────────────────────────────
            # Restore camera immediately so it's outside for the exit anim
            if self.saved_camera_pos:
                camera.x, camera.y, camera.z = self.saved_camera_pos
            # Exit landing = restored camera feet position
            sx, sy, sz = self.saved_camera_pos
            self._char_exit = (sx, sy - 1.0, sz)
            self._hide_phase  = self._PH_LID_OPEN_X
            self._phase_start = time.time()
            print("Dumpster: starting exit animation")

        return True

    def draw(self):
        # Tick state machine every frame
        self._advance_phase()

        w, h, d = self.width, self.height, self.depth
        cy = self.y + h / 2.0

        glPushMatrix()
        glTranslatef(self.x, cy, self.z)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)

        # Main dumpster steel tub
        set_material(self.color)
        glPushMatrix()
        glScalef(w, h * 0.85, d)
        glutSolidCube(1)
        glPopMatrix()

        # Top heavy rim moulding / ledge
        set_material(self.accent_color)
        glPushMatrix()
        glTranslatef(0.0, h * 0.42, 0.0)
        glScalef(w + 0.1, 0.12, d + 0.1)
        glutSolidCube(1)
        glPopMatrix()

        # Black plastic lids (cinematic animated split top)
        set_material((0.1, 0.1, 0.12))
        lid_w = w / 2.0 - 0.05
        lid_d = d * 0.95
        lid_angle = 5.0 + self._lid_progress() * 75.0   # 5° resting tilt → 80° flung open

        # Left lid — pivots at its inner right edge
        glPushMatrix()
        glTranslatef(-0.02, h * 0.46, 0.0)
        glRotatef(-lid_angle, 0.0, 0.0, 1.0)
        glTranslatef(-lid_w / 2.0, 0.0, 0.0)
        glScalef(lid_w, 0.08, lid_d)
        glutSolidCube(1)
        glPopMatrix()

        # Right lid — pivots at its inner left edge
        glPushMatrix()
        glTranslatef(0.02, h * 0.46, 0.0)
        glRotatef(lid_angle, 0.0, 0.0, 1.0)
        glTranslatef(lid_w / 2.0, 0.0, 0.0)
        glScalef(lid_w, 0.08, lid_d)
        glutSolidCube(1)
        glPopMatrix()

        # Side handles / lifting pegs
        set_material((0.4, 0.4, 0.45))
        for dx in (-w / 2.0 - 0.08, w / 2.0 + 0.08):
            glPushMatrix()
            glTranslatef(dx, 0.0, 0.0)
            glScalef(0.12, 0.12, 0.6)
            glutSolidCube(1)
            glPopMatrix()

        # Bottom heavy caster wheels
        set_material((0.1, 0.1, 0.1))
        wheel_r = 0.12
        for dx in (-w * 0.4, w * 0.4):
            for dz in (-d * 0.4, d * 0.4):
                glPushMatrix()
                glTranslatef(dx, -h * 0.45, dz)
                glutSolidSphere(wheel_r, 8, 8)
                glPopMatrix()

        glPopMatrix()


class BottleObstacle(Obstacle):
    """A collectible glass bottle placed on surfaces in the tutorial area."""

    def __init__(self, x, y, z):
        super().__init__(
            x=x, y=y, z=z,
            width=0.3, height=0.5, depth=0.3,
            is_interactive=True,
            color=(0.2, 0.85, 0.6)
        )
        self.picked_up = False

    def interact(self, camera):
        return False   # Auto-pickup when player walks close; F key is not used for bottles

    def get_bounding_box(self):
        """Return zero bounding box so bottles never create physical collision blocks."""
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def draw(self):
        if self.picked_up:
            return

        glPushMatrix()
        glTranslatef(self.x, self.y + 0.2, self.z)

        # Glass material styling
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        set_material((0.25, 0.85, 0.6), emissive=(0.1, 0.5, 0.35))

        # Main bottle cylinder body
        glPushMatrix()
        glScalef(0.24, 0.35, 0.24)
        glutSolidCube(1)
        glPopMatrix()

        # Bottle neck
        glPushMatrix()
        glTranslatef(0.0, 0.22, 0.0)
        glScalef(0.10, 0.16, 0.10)
        glutSolidCube(1)
        glPopMatrix()

        # Cork cap
        set_material((0.55, 0.38, 0.2), emissive=None)
        glPushMatrix()
        glTranslatef(0.0, 0.32, 0.0)
        glutSolidSphere(0.06, 8, 8)
        glPopMatrix()

        glDisable(GL_BLEND)
        glPopMatrix()




class ObstacleManager:
    """Manages collection of interactive obstacles within a level."""

    def __init__(self):
        self.obstacles = []

    def add_obstacle(self, obstacle):
        self.obstacles.append(obstacle)

    def draw_all(self):
        for obs in self.obstacles:
            obs.draw()

    def get_obstacles(self):
        return self.obstacles

    def try_interact(self, camera):
        closest_obs = None
        min_dist = 3.0
        for obs in self.obstacles:
            dist = obs.distance_to(camera.x, camera.z)
            if dist < min_dist:
                closest_obs = obs
                min_dist = dist
        if closest_obs:
            return closest_obs.interact(camera)
        return False


# ══════════════════════════════════════════════════════════════════════════════
# PROJECTILE SYSTEM  (Fired from hands to destroy light sources)
# ══════════════════════════════════════════════════════════════════════════════

class Projectile:
    """A fast-moving projectile fired from the player's hands."""
    def __init__(self, x, y, z, vx, vy, vz, lifetime=2.5):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.lifetime = lifetime
        self.alive = True
        self.radius = 0.12

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        set_material((0.2, 0.9, 1.0), emissive=(0.3, 1.0, 1.0))
        glutSolidSphere(self.radius, 10, 10)
        glPopMatrix()


class ProjectileManager:
    """Manages active projectiles fired by the main character."""
    projectiles = []

    @classmethod
    def shoot(cls, camera):
        lx, ly, lz = camera._look_direction()
        speed = 65.0 # Fast projectile velocity
        start_x = camera.x + lx * 0.4
        start_y = camera.y - 0.1 + ly * 0.4
        start_z = camera.z + lz * 0.4

        cls.projectiles.append(Projectile(start_x, start_y, start_z, lx * speed, ly * speed, lz * speed))

    @classmethod
    def update(cls, dt, colliders=None):
        active = []
        cz = PolicePatrolRoom.ROOM_CENTER_Z
        light_positions = [
            (-4.0, PolicePatrolRoom.ROOM_HEIGHT - 0.5, cz),
            ( 4.0, PolicePatrolRoom.ROOM_HEIGHT - 0.5, cz)
        ]

        if colliders is None:
            from __main__ import TutorialLevel
            try:
                colliders = TutorialLevel.get_all_colliders()
            except Exception:
                colliders = []

        for p in cls.projectiles:
            p.update(dt)
            if not p.alive:
                continue

            # 1. Check Light Fixture hits
            hit_light = False
            for idx, (lx, ly, lz) in enumerate(light_positions):
                if PolicePatrolRoom.lights_active[idx]:
                    dx = p.x - lx
                    dy = p.y - ly
                    dz = p.z - lz
                    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                    if dist <= 0.95:
                        PolicePatrolRoom.lights_active[idx] = False
                        p.alive = False
                        hit_light = True
                        print(f"Destroyed Light Source {idx + 1}!")
                        break

            if hit_light:
                continue

            # 2. Check collision against physical world colliders (walls, pillars, tables, boxes, dumpsters, wardrobes)
            if colliders:
                for c in colliders:
                    c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z = c[:6]
                    if (c_min_x <= p.x <= c_max_x and
                        c_min_y <= p.y <= c_max_y and
                        c_min_z <= p.z <= c_max_z):
                        p.alive = False
                        break

            # 3. Check floor, ceiling, and level boundary limits
            if p.y <= 0.05 or p.y >= 4.8:
                p.alive = False

            if p.alive:
                active.append(p)
        cls.projectiles = active

    @classmethod
    def draw(cls):
        for p in cls.projectiles:
            p.draw()

    @classmethod
    def reset(cls):
        cls.projectiles.clear()


# ══════════════════════════════════════════════════════════════════════════════
# GLASS BOTTLE THROW & DISTRACTION SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

class ActiveBottle:
    """A thrown 3D glass bottle model traveling along a parabolic trajectory."""

    def __init__(self, x, y, z, vx, vy, vz):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.gravity = 14.0
        self.alive = True
        self.spin = 0.0

    def update(self, dt):
        if not self.alive:
            return
        self.spin += 480.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= self.gravity * dt
        self.z += self.vz * dt

        # Impact with floor (y <= 0.05)
        if self.y <= 0.05:
            self.y = 0.05
            self.alive = False
            BottleManager.spawn_shatter_debris(self.x, self.z)
            PolicePatrolRoom.distract_nearest_npc(self.x, self.z)

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.spin, 1.0, 0.5, 0.2)

        # 3D Glass bottle model tumbling through the air
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        set_material((0.25, 0.85, 0.6), emissive=(0.1, 0.5, 0.35))

        # Main bottle cylinder body
        glPushMatrix()
        glScalef(0.20, 0.30, 0.20)
        glutSolidCube(1)
        glPopMatrix()

        # Bottle neck
        glPushMatrix()
        glTranslatef(0.0, 0.18, 0.0)
        glScalef(0.08, 0.14, 0.08)
        glutSolidCube(1)
        glPopMatrix()

        # Cork cap
        set_material((0.55, 0.38, 0.2), emissive=None)
        glPushMatrix()
        glTranslatef(0.0, 0.26, 0.0)
        glutSolidSphere(0.05, 8, 8)
        glPopMatrix()

        glDisable(GL_BLEND)
        glPopMatrix()


class ShatteredGlassDebris:
    """Shattered glass shards on the floor at a bottle impact location."""

    def __init__(self, x, z, lifetime=8.0):
        self.x = x
        self.z = z
        self.lifetime = lifetime
        self.alive = True

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.x, 0.03, self.z)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        set_material((0.3, 0.95, 0.7), emissive=(0.2, 0.8, 0.5))
        for ox, oz, rot in ((-0.15, 0.1, 20), (0.12, -0.08, 60), (-0.05, -0.15, 110), (0.1, 0.15, 140)):
            glPushMatrix()
            glTranslatef(ox, 0.0, oz)
            glRotatef(rot, 0.0, 1.0, 0.0)
            glScalef(0.12, 0.02, 0.08)
            glutSolidCube(1)
            glPopMatrix()
        glDisable(GL_BLEND)
        glPopMatrix()


class BottleManager:
    """Manages bottle inventory, parabolic trajectory aiming, throwing, and debris."""
    bottles_count = 0
    is_aiming_throw = False
    active_bottles = []
    shattered_debris = []

    @classmethod
    def check_auto_pickups(cls, camera):
        """Automatically pick up glass bottles when player gets close (no F key required)."""
        if camera is None:
            return
        from __main__ import TutorialLevel, inventory, InventoryItem
        try:
            manager = TutorialLevel.get_obstacle_manager()
            for obs in manager.obstacles:
                if isinstance(obs, BottleObstacle) and not obs.picked_up:
                    dx = obs.x - camera.x
                    dz = obs.z - camera.z
                    dist = math.sqrt(dx * dx + dz * dz)
                    if dist <= 1.3:
                        obs.picked_up = True
                        cls.bottles_count += 1
                        inventory.add_item(InventoryItem("Glass Bottle", (0.2, 0.85, 0.6), value=50, count=1, description="Distraction Glass Bottle"))
                        print(f"Auto-picked up Glass Bottle! (Bottles in inventory: {cls.bottles_count})")
        except Exception:
            pass

    @classmethod
    def update(cls, dt, camera=None):
        cls.check_auto_pickups(camera)

        alive_bottles = []
        for b in cls.active_bottles:
            b.update(dt)
            if b.alive:
                alive_bottles.append(b)
        cls.active_bottles = alive_bottles

        alive_debris = []
        for d in cls.shattered_debris:
            d.update(dt)
            if d.alive:
                alive_debris.append(d)
        cls.shattered_debris = alive_debris

    @classmethod
    def spawn_shatter_debris(cls, x, z):
        cls.shattered_debris.append(ShatteredGlassDebris(x, z))

    @classmethod
    def shoot_throw(cls, camera):
        if cls.bottles_count <= 0:
            print("No glass bottles left in inventory!")
            return

        cls.bottles_count -= 1
        from __main__ import inventory
        active_item = inventory.get_active_item()
        if active_item is not None and active_item.name == "Glass Bottle":
            active_item.count -= 1
            if active_item.count <= 0:
                inventory.slots[inventory.active_hotbar_index] = None
        else:
            for i in range(inventory.TOTAL_SLOTS):
                slot_item = inventory.slots[i]
                if slot_item is not None and slot_item.name == "Glass Bottle":
                    slot_item.count -= 1
                    if slot_item.count <= 0:
                        inventory.slots[i] = None
                    break

        lx, ly, lz = camera._look_direction()
        speed = 13.0
        start_x = camera.x + lx * 0.4
        start_y = camera.y - 0.2 + ly * 0.4
        start_z = camera.z + lz * 0.4

        vx = lx * speed
        vy = (ly + 0.35) * speed
        vz = lz * speed

        cls.active_bottles.append(ActiveBottle(start_x, start_y, start_z, vx, vy, vz))
        print(f"Threw Glass Bottle! ({cls.bottles_count} remaining)")

    @classmethod
    def draw_trajectory_line(cls, camera):
        """Draw a 3D parabolic trajectory line and floor landing target ring when aiming a throw."""
        if not cls.is_aiming_throw or cls.bottles_count <= 0:
            return

        lx, ly, lz = camera._look_direction()
        speed = 13.0
        start_x = camera.x + lx * 0.4
        start_y = camera.y - 0.2 + ly * 0.4
        start_z = camera.z + lz * 0.4

        vx = lx * speed
        vy = (ly + 0.35) * speed
        vz = lz * speed
        g = 14.0

        points = []
        landing_x, landing_z = start_x, start_z
        dt_step = 0.05
        t = 0.0
        for _ in range(40):
            px = start_x + vx * t
            py = start_y + vy * t - 0.5 * g * t * t
            pz = start_z + vz * t
            if py <= 0.03:
                py = 0.03
                points.append((px, py, pz))
                landing_x, landing_z = px, pz
                break
            points.append((px, py, pz))
            t += dt_step

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # 1. Parabolic trajectory line
        glColor4f(0.2, 0.95, 0.6, 0.85)
        glLineWidth(2.5)
        glBegin(GL_LINE_STRIP)
        for pt in points:
            glVertex3f(pt[0], pt[1], pt[2])
        glEnd()

        # 2. Landing target ring on floor
        glColor4f(0.2, 0.95, 0.6, 0.9)
        glBegin(GL_LINE_LOOP)
        segments = 24
        ring_r = 0.6
        for i in range(segments):
            theta = (2.0 * math.pi * i) / segments
            rx = landing_x + ring_r * math.cos(theta)
            rz = landing_z + ring_r * math.sin(theta)
            glVertex3f(rx, 0.04, rz)
        glEnd()

        glLineWidth(1.0)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    @classmethod
    def draw(cls, camera):
        for b in cls.active_bottles:
            b.draw()

        for d in cls.shattered_debris:
            d.draw()

        cls.draw_trajectory_line(camera)

    @classmethod
    def reset(cls):
        cls.bottles_count = 0
        cls.is_aiming_throw = False
        cls.active_bottles.clear()
        cls.shattered_debris.clear()


# ══════════════════════════════════════════════════════════════════════════════
# PATROLLING NPC  (walks along waypoints)
# ══════════════════════════════════════════════════════════════════════════════

class PatrollingNPC:
    """An NPC that walks between a list of waypoints in a loop.

    Args:
        model:      A drawable model instance (ThinPoliceModel / FatPoliceModel).
        waypoints:  List of (x, z) tuples forming a closed patrol loop.
        speed:      Movement speed in world units per second.
        pause_time: Seconds to pause at each waypoint before moving on.
    """

    def __init__(self, model, waypoints, speed=2.0, pause_time=1.0):
        self.model = model
        self.waypoints = waypoints
        self.speed = speed
        self.pause_time = pause_time

        # Collision body half-width (set based on model type)
        if isinstance(model, FatPoliceModel):
            self.body_half_w = 0.45
            self.body_height = 2.2
        else:
            self.body_half_w = 0.30
            self.body_height = 2.4

        # State
        self._wp_index = 0
        self._pausing = True
        self._pause_start = 0.0
        self._last_time = None
        self._blocked = False   # True when path is obstructed

        # Detection & Chase properties
        self.detection_radius = 5.5  # Medium radius circle around police
        self.alert_meter = 0.0       # 0.0 (normal) -> 1.0 (triggered)
        self.time_to_trigger = 2.5   # Seconds inside radius to trigger
        self.time_to_cooldown = 2.0  # Seconds outside radius to cool down
        self.is_chasing = False      # True when running after player
        self.is_beating_up = False   # True when close enough to attack player

        # Distraction properties
        self.target_investigate_pos = None
        self.investigate_timer = 0.0

    def distract(self, target_x, target_z):
        """Distract officer to investigate noise at (target_x, target_z), UNLESS already in Red state / chasing / beating up."""
        if self.alert_meter >= 1.0 or self.is_chasing or self.is_beating_up:
            return  # In Red state — bottle throwing does not affect police!

        self.target_investigate_pos = (target_x, target_z)
        self.investigate_timer = 4.0   # Investigate for 4 seconds in Yellow status
        self.alert_meter = 0.5         # Yellow alert cone!
        print(f"Police officer distracted to investigate ({target_x:.1f}, {target_z:.1f})!")

    def _check_collision(self, new_x, new_z, colliders):
        """Return True if proposed (new_x, new_z) would overlap any collider."""
        if not colliders:
            return False
        hw = self.body_half_w
        feet_y = self.model.y
        head_y = feet_y + self.body_height
        for c in colliders:
            c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z = c[:6]
            if feet_y >= c_max_y or head_y <= c_min_y:
                continue
            if (new_x + hw > c_min_x and new_x - hw < c_max_x and
                new_z + hw > c_min_z and new_z - hw < c_max_z):
                return True
        return False

    def update(self, time_elapsed, colliders=None, player_pos=None, is_player_hiding=False):
        """Advance patrol, chase & detection logic. Call once per frame."""
        if self._last_time is None:
            self._last_time = time_elapsed
            self._pause_start = time_elapsed
            wx, wz = self.waypoints[self._wp_index]
            self.model.x = wx
            self.model.z = wz
            return

        dt = time_elapsed - self._last_time
        self._last_time = time_elapsed

        is_fat = isinstance(self.model, FatPoliceModel)
        room_lights_on = any(PolicePatrolRoom.lights_active)

        # ── Hiding Check: Dumpster/Closet resets police immediately to normal ─
        if is_player_hiding:
            self.alert_meter = 0.0
            self.is_chasing = False
            self.is_beating_up = False
            self.target_investigate_pos = None
            self.investigate_timer = 0.0
            self._blocked = False

        # ── Distraction Investigation State ─────────────────────────────────
        elif self.target_investigate_pos is not None and not self.is_chasing and not self.is_beating_up:
            self.alert_meter = 0.5  # Yellow status indicator cone
            tx, tz = self.target_investigate_pos
            dx = tx - self.model.x
            dz = tz - self.model.z
            dist = math.sqrt(dx * dx + dz * dz)

            if dist > 0.35:
                # Walk smoothly to the distraction landing spot
                self.model.yaw_deg = -math.degrees(math.atan2(dz, dx)) + 90.0
                step = min(self.speed * dt, dist)
                proposed_x = self.model.x + (dx / dist) * step
                proposed_z = self.model.z + (dz / dist) * step

                if not self._check_collision(proposed_x, proposed_z, colliders):
                    self.model.x = proposed_x
                    self.model.z = proposed_z
                    self._blocked = False
                elif not self._check_collision(proposed_x, self.model.z, colliders):
                    self.model.x = proposed_x
                    self._blocked = False
                elif not self._check_collision(self.model.x, proposed_z, colliders):
                    self.model.z = proposed_z
                    self._blocked = False
                else:
                    self._blocked = True
            else:
                # Arrived at distraction spot: investigate for 4 seconds in Yellow state
                self._blocked = True
                self.investigate_timer -= dt
                if self.investigate_timer <= 0.0:
                    # Done investigating — resume patrol seamlessly from nearest waypoint!
                    self.target_investigate_pos = None
                    self.alert_meter = 0.0
                    self._blocked = False
                    self._pausing = True
                    self._pause_start = time_elapsed
                    best_wp = 0
                    min_wp_d = 99999.0
                    for w_idx, (wx, wz) in enumerate(self.waypoints):
                        wd = (wx - self.model.x)**2 + (wz - self.model.z)**2
                        if wd < min_wp_d:
                            min_wp_d = wd
                            best_wp = w_idx
                    self._wp_index = best_wp
            return   # Prevent normal patrol logic from firing concurrently during distraction!

        # ── Detection Logic ──────────────────────────────────────────────────
        elif player_pos is not None:
            px, pz = player_pos[0], player_pos[1]
            dx = px - self.model.x
            dz = pz - self.model.z
            dist = math.sqrt(dx * dx + dz * dz)

            facing_rad = math.radians(90.0 - self.model.yaw_deg)
            facing_x = math.cos(facing_rad)
            facing_z = math.sin(facing_rad)

            if room_lights_on and pz >= 10.0:
                # ── LIGHTS ON: Instant Line-of-Sight Spotting if facing player ──
                spotted = False
                if 0.1 <= dist <= 14.0:
                    vx, vz = dx / dist, dz / dist
                    dot = facing_x * vx + facing_z * vz
                    if dot >= 0.5: # Facing towards player (within 60 degrees)
                        spotted = True

                if spotted:
                    self.alert_meter = 1.0
                else:
                    self.alert_meter = max(0.0, self.alert_meter - (dt / self.time_to_cooldown))
            else:
                # ── LIGHTS OFF (DARK): Enable Radius & Flashlight Features ──────
                if is_fat:
                    # ── FAT POLICE: Omnidirectional medium radius circle ─────────
                    if dist <= self.detection_radius:
                        self.alert_meter = min(1.0, self.alert_meter + (dt / self.time_to_trigger))
                    else:
                        self.alert_meter = max(0.0, self.alert_meter - (dt / self.time_to_cooldown))
                else:
                    # ── THIN POLICE: Flashlight cone vision ───────────────────────
                    flashlight_range = 7.5
                    flashlight_fov = math.radians(50.0)

                    in_flashlight = False
                    if 0.1 <= dist <= flashlight_range:
                        vx, vz = dx / dist, dz / dist
                        dot = max(-1.0, min(1.0, facing_x * vx + facing_z * vz))
                        angle_diff = math.acos(dot)
                        if angle_diff <= flashlight_fov / 2.0:
                            in_flashlight = True

                    if in_flashlight:
                        # Walking into thin police flashlight cone triggers instantly!
                        self.alert_meter = 1.0
                    else:
                        self.alert_meter = max(0.0, self.alert_meter - (dt / self.time_to_cooldown))
        else:
            self.alert_meter = max(0.0, self.alert_meter - (dt / self.time_to_cooldown))

        # ── Red Alert / Triggered Behavior: Chase or Beat Up ─────────────────
        if self.alert_meter >= 1.0 and player_pos is not None and not is_player_hiding:
            px, pz = player_pos[0], player_pos[1]
            dx = px - self.model.x
            dz = pz - self.model.z
            dist = math.sqrt(dx * dx + dz * dz)

            # Face the player
            self.model.yaw_deg = -math.degrees(math.atan2(dz, dx)) + 90.0

            if dist <= 1.3:
                # Close range: BEAT UP the main character!
                self.is_chasing = False
                self.is_beating_up = True
                self._blocked = True
                return
            else:
                # Further range: RUN after the main character!
                self.is_chasing = True
                self.is_beating_up = False
                chase_spd = 3.6  # Run speed
                step = min(chase_spd * dt, dist)
                proposed_x = self.model.x + (dx / dist) * step
                proposed_z = self.model.z + (dz / dist) * step

                if not self._check_collision(proposed_x, proposed_z, colliders):
                    self.model.x = proposed_x
                    self.model.z = proposed_z
                    self._blocked = False
                elif not self._check_collision(proposed_x, self.model.z, colliders):
                    self.model.x = proposed_x
                    self._blocked = False
                elif not self._check_collision(self.model.x, proposed_z, colliders):
                    self.model.z = proposed_z
                    self._blocked = False
                else:
                    self._blocked = True
                return
        else:
            self.is_chasing = False
            self.is_beating_up = False

        # ── Normal Patrol Movement ────────────────────────────────────────────
        if self._pausing:
            if time_elapsed - self._pause_start >= self.pause_time:
                self._pausing = False
                self._blocked = False
                next_idx = (self._wp_index + 1) % len(self.waypoints)
                tx, tz = self.waypoints[next_idx]
                dx = tx - self.model.x
                dz = tz - self.model.z
                self.model.yaw_deg = -math.degrees(math.atan2(dz, dx)) + 90.0
            return

        next_idx = (self._wp_index + 1) % len(self.waypoints)
        tx, tz = self.waypoints[next_idx]
        dx = tx - self.model.x
        dz = tz - self.model.z
        dist = math.sqrt(dx * dx + dz * dz)

        if dist < 0.15:
            self.model.x = tx
            self.model.z = tz
            self._wp_index = next_idx
            self._pausing = True
            self._blocked = False
            self._pause_start = time_elapsed
        else:
            step = self.speed * dt
            if step > dist:
                step = dist
            proposed_x = self.model.x + (dx / dist) * step
            proposed_z = self.model.z + (dz / dist) * step

            if not self._check_collision(proposed_x, proposed_z, colliders):
                self.model.x = proposed_x
                self.model.z = proposed_z
                self._blocked = False
            elif not self._check_collision(proposed_x, self.model.z, colliders):
                self.model.x = proposed_x
                self._blocked = False
            elif not self._check_collision(self.model.x, proposed_z, colliders):
                self.model.z = proposed_z
                self._blocked = False
            else:
                self._blocked = True

            self.model.yaw_deg = -math.degrees(math.atan2(dz, dx)) + 90.0

    def draw_detection_circle(self):
        """Draw medium radius detection circle on ground around Fat Police."""
        if self.alert_meter >= 1.0:
            color = (1.0, 0.15, 0.15)        # Red when triggered
        elif self.alert_meter > 0.01:
            color = (1.0, 0.85, 0.0)        # Yellow when alerting
        else:
            color = (0.25, 0.45, 0.75)      # Soft blue when normal

        set_material(color, emissive=color)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        segments = 32
        for i in range(segments):
            theta = (2.0 * math.pi * i) / segments
            cx = self.model.x + self.detection_radius * math.cos(theta)
            cz = self.model.z + self.detection_radius * math.sin(theta)
            glVertex3f(cx, 0.03, cz)
        glEnd()
        glLineWidth(1.0)

    def draw_flashlight_cone(self, time_elapsed):
        """Draw projected flashlight cone on floor extending forward for Thin Police."""
        facing_rad = math.radians(90.0 - self.model.yaw_deg)
        fov_rad = math.radians(50.0)
        half_fov = fov_rad / 2.0
        r = 7.5

        if self.alert_meter >= 1.0:
            color = (1.0, 0.15, 0.15, 0.45)    # Red when triggered / beating up
            emissive = (1.0, 0.2, 0.2)
        else:
            color = (1.0, 0.90, 0.3, 0.35)    # Bright yellow flashlight cone
            emissive = (0.9, 0.8, 0.2)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        set_material((color[0], color[1], color[2]), emissive=emissive)

        # 1. Floor projected cone fan
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(self.model.x, 0.03, self.model.z)
        segments = 24
        for i in range(segments + 1):
            a = (facing_rad - half_fov) + (fov_rad * i / segments)
            cx = self.model.x + r * math.cos(a)
            cz = self.model.z + r * math.sin(a)
            glVertex3f(cx, 0.03, cz)
        glEnd()

        # 2. Outline around flashlight cone
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex3f(self.model.x, 0.04, self.model.z)
        for i in range(segments + 1):
            a = (facing_rad - half_fov) + (fov_rad * i / segments)
            cx = self.model.x + r * math.cos(a)
            cz = self.model.z + r * math.sin(a)
            glVertex3f(cx, 0.04, cz)
        glEnd()
        glLineWidth(1.0)
        glDisable(GL_BLEND)

    def draw_indicator_cone(self, time_elapsed):
        """Draw small cone on top of police head:
        - No colour: Normal
        - Yellow: Alert
        - Red: Triggered (after staying in circle)
        """
        if self.alert_meter <= 0.01:
            return  # Normal: no colour cone

        if self.alert_meter >= 1.0:
            color = (1.0, 0.15, 0.15)      # Red = triggered
            emissive = (1.0, 0.25, 0.25)
        else:
            color = (1.0, 0.85, 0.0)      # Yellow = alert
            emissive = (0.8, 0.65, 0.0)

        bob = math.sin(time_elapsed * 6.0) * 0.05
        cone_y = self.model.y + self.body_height + 0.45 + bob

        glPushMatrix()
        glTranslatef(self.model.x, cone_y, self.model.z)
        glRotatef(90.0, 1.0, 0.0, 0.0)    # Cone pointing down toward police head
        set_material(color, emissive=emissive)
        glutSolidCone(0.22, 0.45, 12, 12)
        glPopMatrix()

    def draw(self, time_elapsed, colliders=None, player_pos=None, is_player_hiding=False):
        """Draw the patrolling NPC model, detection ring/flashlight, and head status cone."""
        self.update(time_elapsed, colliders, player_pos, is_player_hiding)

        if isinstance(self.model, FatPoliceModel):
            self.draw_detection_circle()
        else:
            self.draw_flashlight_cone(time_elapsed)

        is_moving = ((not self._pausing and not self._blocked) or self.is_chasing)
        self.model.draw(time_elapsed, is_moving=is_moving, is_attacking=self.is_beating_up)

        self.draw_indicator_cone(time_elapsed)


# ══════════════════════════════════════════════════════════════════════════════
# POLICE PATROL ROOM  (connected room beyond the tutorial door)
# ══════════════════════════════════════════════════════════════════════════════

class PolicePatrolRoom:
    """A secondary room accessible through the tutorial's +Z door.

    The room is centered at (0, 0, ROOM_CENTER_Z) — directly beyond the
    tutorial room's front wall.  Two police officers patrol inside.
    """

    # ── Dimensions ────────────────────────────────────────────────────────────
    ROOM_WIDTH       = 18.0
    ROOM_DEPTH       = 16.0
    ROOM_HEIGHT      = 5.0
    WALL_THICKNESS   = 0.5
    TILE_SIZE        = 2.0

    # The tutorial room's front wall sits at z = +10.
    # This room starts right after that wall (plus a short corridor gap).
    CORRIDOR_LENGTH  = 4.0      # Short hallway linking the two rooms
    ROOM_CENTER_Z    = 10.0 + CORRIDOR_LENGTH + ROOM_DEPTH / 2.0

    # ── Colors ────────────────────────────────────────────────────────────────
    COLOR_WALL         = (0.28, 0.30, 0.35)
    COLOR_WALL_ACCENT  = (0.22, 0.24, 0.28)
    COLOR_FLOOR_DARK   = (0.20, 0.20, 0.22)
    COLOR_FLOOR_LIGHT  = (0.26, 0.26, 0.28)
    COLOR_CEILING      = (0.12, 0.12, 0.14)
    COLOR_DESK         = (0.35, 0.25, 0.15)
    COLOR_DESK_TOP     = (0.30, 0.20, 0.12)
    COLOR_FILING_CAB   = (0.40, 0.42, 0.45)
    COLOR_LAMP         = (0.90, 0.85, 0.60)
    COLOR_LAMP_EMISSIVE = (0.80, 0.75, 0.40)

    # ── Patrol waypoints (x, z) — inside the room ────────────────────────────
    _THIN_WAYPOINTS = None
    _FAT_WAYPOINTS  = None

    @classmethod
    def _get_thin_waypoints(cls):
        if cls._THIN_WAYPOINTS is None:
            cz = cls.ROOM_CENTER_Z
            hw = cls.ROOM_WIDTH / 2.0 - 2.0
            hd = cls.ROOM_DEPTH / 2.0 - 2.0
            cls._THIN_WAYPOINTS = [
                (-hw, cz - hd),
                (-hw, cz + hd),
                ( hw, cz + hd),
                ( hw, cz - hd),
            ]
        return cls._THIN_WAYPOINTS

    @classmethod
    def _get_fat_waypoints(cls):
        if cls._FAT_WAYPOINTS is None:
            cz = cls.ROOM_CENTER_Z
            cls._FAT_WAYPOINTS = [
                ( 3.0, cz - 4.0),
                (-3.0, cz - 4.0),
                (-3.0, cz + 4.0),
                ( 3.0, cz + 4.0),
            ]
        return cls._FAT_WAYPOINTS

    # ── NPC instances (lazily created) ────────────────────────────────────────
    _patrol_npcs = None

    @classmethod
    def get_patrol_npcs(cls):
        if cls._patrol_npcs is None:
            thin_wps = cls._get_thin_waypoints()
            fat_wps  = cls._get_fat_waypoints()

            thin_cop = ThinPoliceModel(x=thin_wps[0][0], y=0.0, z=thin_wps[0][1])
            fat_cop  = FatPoliceModel(x=fat_wps[0][0],  y=0.0, z=fat_wps[0][1])

            cls._patrol_npcs = [
                PatrollingNPC(thin_cop, thin_wps, speed=2.5, pause_time=1.2),
                PatrollingNPC(fat_cop,  fat_wps,  speed=1.8, pause_time=1.8),
            ]
        return cls._patrol_npcs

    lights_active = [True, True]

    # ── Lighting ──────────────────────────────────────────────────────────────
    @classmethod
    def setup_lighting(cls):
        """Configure GL_LIGHT2 and GL_LIGHT3 for this room."""
        cz = cls.ROOM_CENTER_Z

        if cls.lights_active[0]:
            glEnable(GL_LIGHT2)
            glLightfv(GL_LIGHT2, GL_AMBIENT,  [0.06, 0.06, 0.08, 1.0])
            glLightfv(GL_LIGHT2, GL_DIFFUSE,  [0.70, 0.65, 0.45, 1.0])
            glLightfv(GL_LIGHT2, GL_SPECULAR, [0.30, 0.28, 0.18, 1.0])
            glLightfv(GL_LIGHT2, GL_POSITION, [-4.0, cls.ROOM_HEIGHT - 0.5, cz, 1.0])
            glLightf(GL_LIGHT2, GL_CONSTANT_ATTENUATION,  1.0)
            glLightf(GL_LIGHT2, GL_LINEAR_ATTENUATION,    0.04)
            glLightf(GL_LIGHT2, GL_QUADRATIC_ATTENUATION, 0.008)
        else:
            glDisable(GL_LIGHT2)

        if cls.lights_active[1]:
            glEnable(GL_LIGHT3)
            glLightfv(GL_LIGHT3, GL_AMBIENT,  [0.06, 0.06, 0.08, 1.0])
            glLightfv(GL_LIGHT3, GL_DIFFUSE,  [0.70, 0.65, 0.45, 1.0])
            glLightfv(GL_LIGHT3, GL_SPECULAR, [0.30, 0.28, 0.18, 1.0])
            glLightfv(GL_LIGHT3, GL_POSITION, [ 4.0, cls.ROOM_HEIGHT - 0.5, cz, 1.0])
            glLightf(GL_LIGHT3, GL_CONSTANT_ATTENUATION,  1.0)
            glLightf(GL_LIGHT3, GL_LINEAR_ATTENUATION,    0.04)
            glLightf(GL_LIGHT3, GL_QUADRATIC_ATTENUATION, 0.008)
        else:
            glDisable(GL_LIGHT3)

    # ── Floor ─────────────────────────────────────────────────────────────────
    @classmethod
    def draw_floor(cls):
        cz = cls.ROOM_CENTER_Z
        hw = cls.ROOM_WIDTH  / 2.0
        hd = cls.ROOM_DEPTH  / 2.0

        x = -hw + cls.TILE_SIZE / 2.0
        ix = 0
        while x < hw:
            z = cz - hd + cls.TILE_SIZE / 2.0
            iz = 0
            while z < cz + hd:
                color = cls.COLOR_FLOOR_DARK if (ix + iz) % 2 == 0 else cls.COLOR_FLOOR_LIGHT
                draw_floor_tile(x, z, cls.TILE_SIZE, color)
                z += cls.TILE_SIZE
                iz += 1
            x += cls.TILE_SIZE
            ix += 1

        # Corridor floor
        corr_z_start = 10.0 + cls.WALL_THICKNESS / 2.0
        corr_z_end   = cz - hd
        cz_tile = corr_z_start + cls.TILE_SIZE / 2.0
        ix = 0
        # Corridor is as wide as the tutorial door (3.0 units)
        cx_start = -1.5
        while cz_tile < corr_z_end:
            x = cx_start + cls.TILE_SIZE / 2.0
            iy = 0
            while x < 1.5:
                color = cls.COLOR_FLOOR_DARK if (ix + iy) % 2 == 0 else cls.COLOR_FLOOR_LIGHT
                draw_floor_tile(x, cz_tile, cls.TILE_SIZE, color)
                x += cls.TILE_SIZE
                iy += 1
            cz_tile += cls.TILE_SIZE
            ix += 1

    # ── Ceiling ───────────────────────────────────────────────────────────────
    @classmethod
    def draw_ceiling(cls):
        cz = cls.ROOM_CENTER_Z
        hw = cls.ROOM_WIDTH  / 2.0
        hd = cls.ROOM_DEPTH  / 2.0

        set_material(cls.COLOR_CEILING)
        glBegin(GL_QUADS)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-hw, cls.ROOM_HEIGHT, cz - hd)
        glVertex3f( hw, cls.ROOM_HEIGHT, cz - hd)
        glVertex3f( hw, cls.ROOM_HEIGHT, cz + hd)
        glVertex3f(-hw, cls.ROOM_HEIGHT, cz + hd)
        glEnd()

        # Corridor ceiling
        corr_z_start = 10.0
        corr_z_end   = cz - hd
        glBegin(GL_QUADS)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-1.5, cls.ROOM_HEIGHT, corr_z_start)
        glVertex3f( 1.5, cls.ROOM_HEIGHT, corr_z_start)
        glVertex3f( 1.5, cls.ROOM_HEIGHT, corr_z_end)
        glVertex3f(-1.5, cls.ROOM_HEIGHT, corr_z_end)
        glEnd()

    # ── Walls ─────────────────────────────────────────────────────────────────
    @classmethod
    def draw_walls(cls):
        cz = cls.ROOM_CENTER_Z
        hw = cls.ROOM_WIDTH  / 2.0
        hd = cls.ROOM_DEPTH  / 2.0
        wall_y = cls.ROOM_HEIGHT / 2.0
        wt = cls.WALL_THICKNESS

        # Left wall
        draw_cube(-hw, wall_y, cz, wt, cls.ROOM_HEIGHT, cls.ROOM_DEPTH, cls.COLOR_WALL)
        # Right wall
        draw_cube( hw, wall_y, cz, wt, cls.ROOM_HEIGHT, cls.ROOM_DEPTH, cls.COLOR_WALL)
        # Far wall (+Z)
        draw_cube(0.0, wall_y, cz + hd, cls.ROOM_WIDTH, cls.ROOM_HEIGHT, wt, cls.COLOR_WALL)

        # Near wall (-Z side) — gap for corridor entrance (3 units wide, matching tutorial door)
        door_w = 3.0
        seg_w = (cls.ROOM_WIDTH - door_w) / 2.0
        near_z = cz - hd
        draw_cube(-hw + seg_w / 2.0, wall_y, near_z, seg_w, cls.ROOM_HEIGHT, wt, cls.COLOR_WALL)
        draw_cube( hw - seg_w / 2.0, wall_y, near_z, seg_w, cls.ROOM_HEIGHT, wt, cls.COLOR_WALL)
        # Lintel above entrance
        draw_cube(0.0, 3.5 + (cls.ROOM_HEIGHT - 3.5) / 2.0, near_z,
                  door_w, cls.ROOM_HEIGHT - 3.5, wt, cls.COLOR_WALL)

        # Corridor side walls
        corr_z_start = 10.0
        corr_z_end   = near_z
        corr_len = corr_z_end - corr_z_start
        corr_mid_z = (corr_z_start + corr_z_end) / 2.0
        draw_cube(-1.5 - wt / 2.0, wall_y, corr_mid_z, wt, cls.ROOM_HEIGHT, corr_len, cls.COLOR_WALL_ACCENT)
        draw_cube( 1.5 + wt / 2.0, wall_y, corr_mid_z, wt, cls.ROOM_HEIGHT, corr_len, cls.COLOR_WALL_ACCENT)

    # ── Overhead lights ───────────────────────────────────────────────────────
    @classmethod
    def draw_lights(cls):
        cz = cls.ROOM_CENTER_Z
        positions = (-4.0, 4.0)
        for idx, lx in enumerate(positions):
            bulb_y = cls.ROOM_HEIGHT - 0.5
            draw_cube(lx, cls.ROOM_HEIGHT - 0.2, cz, 0.05, 0.6, 0.05, (0.15, 0.15, 0.15))
            if cls.lights_active[idx]:
                draw_sphere(lx, bulb_y, cz, 0.22, cls.COLOR_LAMP, emissive=cls.COLOR_LAMP_EMISSIVE)
            else:
                # Broken / destroyed light fixture
                draw_sphere(lx, bulb_y, cz, 0.18, (0.12, 0.12, 0.12), emissive=None)
            draw_cube(lx, cls.ROOM_HEIGHT - 0.05, cz, 0.28, 0.1, 0.28, (0.2, 0.2, 0.2))

    # ── Props (desks, filing cabinet) ─────────────────────────────────────────
    @classmethod
    def draw_props(cls):
        cz = cls.ROOM_CENTER_Z
        hw = cls.ROOM_WIDTH / 2.0

        # Desk against the far wall
        desk_x = -4.0
        desk_z = cz + cls.ROOM_DEPTH / 2.0 - 1.5
        desk_w, desk_d, desk_h = 3.0, 1.2, 1.0
        draw_cube(desk_x, desk_h / 2.0, desk_z, desk_w, 0.12, desk_d, cls.COLOR_DESK_TOP)  # Top
        for dx_off in (-1, 1):
            for dz_off in (-1, 1):
                draw_cube(desk_x + dx_off * (desk_w / 2.0 - 0.1), desk_h / 4.0,
                          desk_z + dz_off * (desk_d / 2.0 - 0.1),
                          0.12, desk_h / 2.0, 0.12, cls.COLOR_DESK)

        # Second desk on the right side
        desk2_x = 4.0
        desk2_z = cz + cls.ROOM_DEPTH / 2.0 - 1.5
        draw_cube(desk2_x, desk_h / 2.0, desk2_z, desk_w, 0.12, desk_d, cls.COLOR_DESK_TOP)
        for dx_off in (-1, 1):
            for dz_off in (-1, 1):
                draw_cube(desk2_x + dx_off * (desk_w / 2.0 - 0.1), desk_h / 4.0,
                          desk2_z + dz_off * (desk_d / 2.0 - 0.1),
                          0.12, desk_h / 2.0, 0.12, cls.COLOR_DESK)

        # Filing cabinet on left wall
        cab_x = -hw + 1.0
        cab_z = cz
        draw_cube(cab_x, 1.0, cab_z, 0.8, 2.0, 0.6, cls.COLOR_FILING_CAB)
        # Drawer handles
        for dy_off in (0.4, 0.8, 1.2, 1.6):
            draw_cube(cab_x + 0.42, dy_off, cab_z, 0.04, 0.06, 0.15, (0.25, 0.25, 0.25))

    # ── 3D sign ───────────────────────────────────────────────────────────────
    @classmethod
    def draw_room_label(cls):
        cz = cls.ROOM_CENTER_Z
        draw_text_3d(0.0, 3.2, cz - cls.ROOM_DEPTH / 2.0 + 1.5, "POLICE PATROL ROOM")

    # ── Colliders ─────────────────────────────────────────────────────────────
    _colliders = None

    @classmethod
    def get_colliders(cls):
        """Return collision AABBs for this room (walls, props, corridor)."""
        if cls._colliders is not None:
            return cls._colliders

        cls._colliders = []
        import sys
        main_mod = sys.modules[__name__]
        original_draw_cube = main_mod.draw_cube

        def mock_draw_cube(x, y, z, sx, sy, sz, color, emissive=None):
            c_min_y = y - sy / 2.0
            c_max_y = y + sy / 2.0
            if c_max_y > 0.1 and sy > 0.08:
                hw = sx / 2.0
                hz = sz / 2.0
                cls._colliders.append((x - hw, x + hw, c_min_y, c_max_y, z - hz, z + hz, None))

        main_mod.draw_cube = mock_draw_cube
        try:
            cls.draw_walls()
            cls.draw_props()
        finally:
            main_mod.draw_cube = original_draw_cube

        return cls._colliders

    # ── Dynamic colliders (police NPCs) ─────────────────────────────────────
    @classmethod
    def get_dynamic_colliders(cls):
        """Return fresh AABBs for the patrolling police at their current positions.

        Called every frame so the player collides with moving NPCs.
        Each police officer is approximated as a vertical capsule-ish AABB.
        """
        colliders = []
        for npc in cls.get_patrol_npcs():
            m = npc.model
            # Approximate body width based on model type
            if isinstance(m, FatPoliceModel):
                half_w = 0.45   # Wider body
                height = 2.2
            else:
                half_w = 0.30   # Thin body
                height = 2.4
            colliders.append((
                m.x - half_w, m.x + half_w,    # min_x, max_x
                m.y,          m.y + height,    # min_y, max_y
                m.z - half_w, m.z + half_w,    # min_z, max_z
                None                            # owner (not pushable)
            ))
        return colliders

    @classmethod
    def distract_nearest_npc(cls, target_x, target_z):
        """Alert the police officer closest to (target_x, target_z) to investigate the noise."""
        if not cls._patrol_npcs:
            return

        closest_npc = None
        min_dist = 99999.0
        for npc in cls.get_patrol_npcs():
            # Skip officers that are in Red Alert (chasing or beating up player)
            if npc.alert_meter >= 1.0 or npc.is_chasing or npc.is_beating_up:
                continue

            dx = npc.model.x - target_x
            dz = npc.model.z - target_z
            dist = math.sqrt(dx * dx + dz * dz)
            if dist < min_dist:
                min_dist = dist
                closest_npc = npc

        if closest_npc:
            closest_npc.distract(target_x, target_z)

    # ── Main draw entry ───────────────────────────────────────────────────────
    @classmethod
    def reset_npcs(cls):
        """Reset all police NPCs to initial patrol positions and normal state, and restore lights."""
        cls.lights_active = [True, True]
        ProjectileManager.reset()
        BottleManager.reset()
        if cls._patrol_npcs:
            for npc in cls._patrol_npcs:
                npc.alert_meter = 0.0
                npc.is_chasing = False
                npc.is_beating_up = False
                npc.target_investigate_pos = None
                npc.investigate_timer = 0.0
                npc._wp_index = 0
                npc._pausing = True
                npc._pause_start = 0.0
                wx, wz = npc.waypoints[0]
                npc.model.x = wx
                npc.model.z = wz

    @classmethod
    def draw(cls, time_elapsed, world_colliders=None, player_pos=None):
        cls.setup_lighting()
        cls.draw_floor()
        cls.draw_ceiling()
        cls.draw_walls()
        cls.draw_lights()
        cls.draw_props()
        cls.draw_room_label()

        # Build the collider list for NPCs: world geometry + player body
        npc_colliders = list(world_colliders) if world_colliders else []
        is_hiding = False
        if hasattr(TutorialLevel, 'get_obstacle_manager'):
            for obs in TutorialLevel.get_obstacle_manager().obstacles:
                if getattr(obs, 'is_player_hiding', False):
                    is_hiding = True
                    break

        if player_pos is not None and not is_hiding:
            px, pz = player_pos
            player_hw = 0.4
            npc_colliders.append((
                px - player_hw, px + player_hw,   # min_x, max_x
                0.0,            1.8,               # min_y, max_y (feet to head)
                pz - player_hw, pz + player_hw,   # min_z, max_z
                None
            ))

        # Draw patrolling police NPCs with collision, detection radius, and status cone
        for npc in cls.get_patrol_npcs():
            npc.draw(time_elapsed, colliders=npc_colliders,
                     player_pos=player_pos, is_player_hiding=is_hiding)


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

    obstacle_manager = None

    @classmethod
    def get_obstacle_manager(cls):
        """Get or initialize Ahona's obstacle manager for the level."""
        if cls.obstacle_manager is None:
            cls.obstacle_manager = ObstacleManager()
            # Box / Wooden Crate
            cls.obstacle_manager.add_obstacle(
                BoxObstacle(x=-4.0, y=0.0, z=-2.0, size=1.5, rotation=15.0)
            )
            # Wardrobe / Closet (Hiding Cover)
            cls.obstacle_manager.add_obstacle(
                ClosetObstacle(x=7.5, y=0.0, z=-4.0, width=1.6, height=3.2, depth=1.2, rotation=-90.0)
            )
            # Industrial Metal Dumpster
            cls.obstacle_manager.add_obstacle(
                DumpsterObstacle(x=-6.5, y=0.0, z=4.0, width=2.6, height=1.6, depth=1.6, rotation=30.0)
            )
            # Collectible Glass Bottles
            cls.obstacle_manager.add_obstacle(BottleObstacle(x=-3.2, y=0.8, z=4.0))   # On crate stack
            cls.obstacle_manager.add_obstacle(BottleObstacle(x=4.0, y=0.95, z=2.0))   # On table
            cls.obstacle_manager.add_obstacle(BottleObstacle(x=0.0, y=0.0, z=8.5))    # Corridor entrance
        return cls.obstacle_manager

    @classmethod
    def draw_wooden_box(cls):
        """Draw Ahona's interactive obstacle system (Box, Closet, Dumpster)."""
        cls.get_obstacle_manager().draw_all()

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

    _colliders = None

    @classmethod
    def get_colliders(cls):
        """Automatically extract collision AABBs from draw calls."""
        if cls._colliders is not None:
            return cls._colliders

        cls._colliders = []
        import sys
        
        # We hook the global draw_cube in the main module where TutorialLevel resides
        main_mod = sys.modules[__name__]
        original_draw_cube = main_mod.draw_cube

        def mock_draw_cube(x, y, z, sx, sy, sz, color, emissive=None):
            # A cube spans [y - sy/2, y + sy/2]
            c_min_y = y - sy / 2.0
            c_max_y = y + sy / 2.0
            
            # Filter out flat floors (max_y < 0.1) and pure ceiling slabs
            # Keep everything that has vertical extent above floor level
            if c_max_y > 0.1 and sy > 0.08:
                hw = sx / 2.0
                hz = sz / 2.0
                cls._colliders.append((x - hw, x + hw, c_min_y, c_max_y, z - hz, z + hz, None))
                
        main_mod.draw_cube = mock_draw_cube

        try:
            # Call all geometric draw functions that might contain walls or obstacles
            cls.draw_walls()
            cls.draw_alcove()
            cls.draw_table()
            cls.draw_pillars()
            cls.draw_stacked_crates()
            # We don't call draw_wooden_box because ObstacleManager uses its own transforms,
            # but we can manually add obstacle bounds.
            for obs in cls.get_obstacle_manager().obstacles:
                if obs is cls._grabbed_box or isinstance(obs, BottleObstacle):
                    continue  # Skip grabbed box and BottleObstacle from static physical colliders
                min_x, max_x, min_y, max_y, min_z, max_z = obs.get_bounding_box()
                if max_y > 0.1:
                    cls._colliders.append((min_x, max_x, min_y, max_y, min_z, max_z, obs))
        finally:
            main_mod.draw_cube = original_draw_cube

        # Merge static colliders from the connected police patrol room
        cls._colliders.extend(PolicePatrolRoom.get_colliders())

        return cls._colliders

    @classmethod
    def get_all_colliders(cls):
        """Return static colliders + dynamic police NPC colliders.

        Called every frame. Static geometry is cached; police positions are fresh.
        """
        static = cls.get_colliders()
        dynamic = PolicePatrolRoom.get_dynamic_colliders()
        return static + dynamic

    _grabbed_box = None       # Currently attached BoxObstacle (held in hands)
    _grab_distance = 1.15     # Distance in front of player's hands

    @classmethod
    def interact(cls, camera):
        """Handle F-key interactions: attach/release box to hands, or closet/dumpster."""
        manager = cls.get_obstacle_manager()

        # If already holding a box, F always releases it
        if cls._grabbed_box is not None:
            print("Released the box.")
            cls._grabbed_box = None
            cls._colliders = None
            return True

        # Find the closest obstacle within interaction range
        closest_obs = None
        min_dist = 3.0
        for obs in manager.obstacles:
            dist = obs.distance_to(camera.x, camera.z)
            if dist < min_dist:
                closest_obs = obs
                min_dist = dist

        if closest_obs is None:
            return False

        # If closest is a pushable box → attach directly to character's hands
        if isinstance(closest_obs, BoxObstacle) and getattr(closest_obs, 'can_be_pushed', False):
            cls._grabbed_box = closest_obs
            cls._colliders = None
            print("Attached box to hands! Press F to release.")
            return True

        # Otherwise use normal interaction (closet open/close, dumpster hide/exit)
        result = closest_obs.interact(camera)
        if result:
            cls._colliders = None
        return result

    @classmethod
    def update_grabbed_box(cls, camera):
        """Position and rotate the attached box right in front of the character's hands."""
        box = cls._grabbed_box
        if box is None:
            return

        rad_yaw = math.radians(camera.yaw)
        forward_x = math.cos(rad_yaw)
        forward_z = math.sin(rad_yaw)

        # Snap box position right in front of the player's hands
        box.x = camera.x + forward_x * cls._grab_distance
        box.z = camera.z + forward_z * cls._grab_distance
        box.rotation = -camera.yaw + 90.0

    @classmethod
    def draw(cls, time_elapsed, camera_pos=None):
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

        # Show grab HUD hint
        if cls._grabbed_box is not None:
            draw_text_2d(20, 670, "Carrying Box  |  Press [F] to drop/release")

        # Projectile, Bottle and Light HUD hints
        draw_text_2d(20, 640, "[Hold Right Click] 1st Person Aim & Crosshair  |  [Release Right Click] Fire Fast Projectile")

        from __main__ import inventory
        active_item = inventory.get_active_item()
        if active_item is not None and active_item.name == "Glass Bottle" and active_item.count > 0:
            draw_text_2d(20, 610, f"Selected: Glass Bottle (x{active_item.count})  |  [Hold Q] Aim Trajectory Line  |  [Release Q] Throw Bottle")
        else:
            draw_text_2d(20, 610, f"Selected: Hand Projectiles  |  [Press Q] Shoot Light Projectile  |  (Press 1-9 to Select Bottle)")

        active_count = sum(PolicePatrolRoom.lights_active)
        status_str = f"Patrol Room Lights: {active_count}/2 Active ({'Room Bright - Instant Spotting!' if active_count > 0 else 'Room Dark - Stealth Active!'})"
        draw_text_2d(20, 580, status_str)

        # Check if player is being beaten up by any officer
        is_busted = False
        for npc in PolicePatrolRoom.get_patrol_npcs():
            if npc.is_beating_up:
                is_busted = True
                break

        if is_busted:
            draw_text_2d(340, 430, "BUSTED! The police caught and beat you up!")
            draw_text_2d(420, 390, "Press [R] to restart")

        # Draw the connected police patrol room.
        # Pass all static colliders (both rooms + obstacles) so the police
        # collide with desks, pushed boxes, closets, dumpsters, walls, etc.
        npc_colliders = cls.get_colliders()
        PolicePatrolRoom.draw(time_elapsed, world_colliders=npc_colliders,
                              player_pos=camera_pos)


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

        self.keys_pressed = {b'w': False, b's': False, b'a': False, b'd': False, b' ': False}
        self.y_velocity = 0.0
        self.ground_y = y  # Store initial Y as the ground level

        self.mouse_last_x = WindowConfig.WIDTH  // 2
        self.mouse_last_y = WindowConfig.HEIGHT // 2
        self.captured     = True
        self.first_move   = True
        self.movement_locked = False

    def _look_direction(self):
        rad_yaw   = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        lx = math.cos(rad_pitch) * math.cos(rad_yaw)
        ly = math.sin(rad_pitch)
        lz = math.cos(rad_pitch) * math.sin(rad_yaw)
        return lx, ly, lz

    def process_movement(self, colliders=None):
        """Update position based on currently pressed keys, with full 3D collision.

        Colliders are 6-tuples: (min_x, max_x, min_y, max_y, min_z, max_z)
        in world space. camera.y is eye-level, which is PLAYER_EYE_HEIGHT
        above the player's feet in world space.
        """
        if self.movement_locked or _is_aiming:
            return

        PLAYER_EYE_HEIGHT = 1.0   # camera.y sits this far above the feet

        rad_yaw   = math.radians(self.yaw)
        forward_x = math.cos(rad_yaw)
        forward_z = math.sin(rad_yaw)
        right_x   = math.cos(rad_yaw - math.pi / 2.0)
        right_z   = math.sin(rad_yaw - math.pi / 2.0)
        spd = Camera.MOVE_SPEED

        new_x = self.x
        new_z = self.z

        if self.keys_pressed.get(b'w'): new_x += forward_x * spd; new_z += forward_z * spd
        if self.keys_pressed.get(b's'): new_x -= forward_x * spd; new_z -= forward_z * spd
        if self.keys_pressed.get(b'a'): new_x += right_x   * spd; new_z += right_z   * spd
        if self.keys_pressed.get(b'd'): new_x -= right_x   * spd; new_z -= right_z   * spd

        # ── Spatial Broad-Phase Filter ────────────────────────────────────────
        if colliders:
            px, pz = self.x, self.z
            colliders = [
                c for c in colliders
                if (c[0] - 4.0 <= px <= c[1] + 4.0 and c[4] - 4.0 <= pz <= c[5] + 4.0)
            ]

        # ── Player physical parameters (world space) ─────────────────────────
        pr = 0.4                                    # Horizontal collision radius
        feet_y = self.y - PLAYER_EYE_HEIGHT         # Feet in world space
        head_y = feet_y + 1.8                       # Head in world space
        step_up = 0.35                              # Maximum auto-step height (smooth threshold walking)

        # ── XZ wall blocking ─────────────────────────────────────────────────
        pushed_something = False
        if colliders:
            collision_x = False
            collision_z = False

            grabbed_box = getattr(TutorialLevel, '_grabbed_box', None)
            if grabbed_box is not None:
                b_size = getattr(grabbed_box, 'size', 1.5)
                b_hw = b_size / 2.0
                hold_dist = 1.15
                b_min_y, b_max_y = grabbed_box.y, grabbed_box.y + b_size
                
                # Check proposed box pos for new_x
                target_bx = new_x + forward_x * hold_dist
                target_bz = self.z + forward_z * hold_dist
                for c2 in colliders:
                    c2_owner = c2[6] if len(c2) > 6 else None
                    if c2_owner is grabbed_box:
                        continue
                    if (b_min_y < c2[3] and b_max_y > c2[2] and
                        target_bx + b_hw > c2[0] and target_bx - b_hw < c2[1] and
                        target_bz + b_hw > c2[4] and target_bz - b_hw < c2[5]):
                        collision_x = True
                        break

                # Check proposed box pos for new_z
                target_bx = self.x + forward_x * hold_dist
                target_bz = new_z + forward_z * hold_dist
                for c2 in colliders:
                    c2_owner = c2[6] if len(c2) > 6 else None
                    if c2_owner is grabbed_box:
                        continue
                    if (b_min_y < c2[3] and b_max_y > c2[2] and
                        target_bx + b_hw > c2[0] and target_bx - b_hw < c2[1] and
                        target_bz + b_hw > c2[4] and target_bz - b_hw < c2[5]):
                        collision_z = True
                        break

            for c in colliders:
                c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z = c[:6]
                owner = c[6] if len(c) > 6 else None
                # Block only if the player's body overlaps the collider vertically
                # AND the player is NOT standing on top (feet below top - step_up)
                if (feet_y < c_max_y - step_up and head_y > c_min_y and
                    new_x + pr > c_min_x and new_x - pr < c_max_x and
                    self.z + pr > c_min_z and self.z - pr < c_max_z):
                    if owner and getattr(owner, 'can_be_pushed', False):
                        # Check if box would collide with a wall at its new position
                        box_new_x = owner.x + (new_x - self.x)
                        box_bb = owner.get_bounding_box()
                        box_hw = (box_bb[1] - box_bb[0]) / 2.0
                        box_hd = (box_bb[5] - box_bb[4]) / 2.0
                        box_min_y, box_max_y = box_bb[2], box_bb[3]
                        box_blocked = False
                        for c2 in colliders:
                            c2_owner = c2[6] if len(c2) > 6 else None
                            if c2_owner is owner:
                                continue  # Skip self
                            if (box_min_y < c2[3] and box_max_y > c2[2] and
                                box_new_x + box_hw > c2[0] and box_new_x - box_hw < c2[1] and
                                owner.z + box_hd > c2[4] and owner.z - box_hd < c2[5]):
                                box_blocked = True
                                break
                        if box_blocked:
                            collision_x = True
                            break
                        owner.x = box_new_x
                        pushed_something = True
                    else:
                        collision_x = True
                        break

            for c in colliders:
                c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z = c[:6]
                owner = c[6] if len(c) > 6 else None
                if (feet_y < c_max_y - step_up and head_y > c_min_y and
                    self.x + pr > c_min_x and self.x - pr < c_max_x and
                    new_z + pr > c_min_z and new_z - pr < c_max_z):
                    if owner and getattr(owner, 'can_be_pushed', False):
                        # Check if box would collide with a wall at its new position
                        box_new_z = owner.z + (new_z - self.z)
                        box_bb = owner.get_bounding_box()
                        box_hw = (box_bb[1] - box_bb[0]) / 2.0
                        box_hd = (box_bb[5] - box_bb[4]) / 2.0
                        box_min_y, box_max_y = box_bb[2], box_bb[3]
                        box_blocked = False
                        for c2 in colliders:
                            c2_owner = c2[6] if len(c2) > 6 else None
                            if c2_owner is owner:
                                continue  # Skip self
                            if (box_min_y < c2[3] and box_max_y > c2[2] and
                                owner.x + box_hw > c2[0] and owner.x - box_hw < c2[1] and
                                box_new_z + box_hd > c2[4] and box_new_z - box_hd < c2[5]):
                                box_blocked = True
                                break
                        if box_blocked:
                            collision_z = True
                            break
                        owner.z = box_new_z
                        pushed_something = True
                    else:
                        collision_z = True
                        break

            if not collision_x:
                self.x = new_x
            if not collision_z:
                self.z = new_z
        else:
            self.x = new_x
            self.z = new_z

        # ── Determine what the player is currently standing on ────────────────
        # (used for jump trigger — must be computed BEFORE gravity)
        standing_surface = 0.0   # World-space Y of the floor
        if colliders:
            for c in colliders:
                c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z = c[:6]
                if (self.x + pr > c_min_x and self.x - pr < c_max_x and
                    self.z + pr > c_min_z and self.z - pr < c_max_z):
                    # Player feet are at or very near the top of this surface
                    if abs(feet_y - c_max_y) < 0.15 and c_max_y > standing_surface:
                        standing_surface = c_max_y

        standing_camera_y = standing_surface + PLAYER_EYE_HEIGHT
        on_ground = abs(self.y - standing_camera_y) < 0.15

        # ── Jump trigger ─────────────────────────────────────────────────────
        if self.keys_pressed.get(b' ') and on_ground:
            self.y_velocity = .25

        # ── Apply gravity ────────────────────────────────────────────────────
        prev_feet = self.y - PLAYER_EYE_HEIGHT      # Feet before gravity
        self.y += self.y_velocity
        self.y_velocity -= 0.014
        new_feet = self.y - PLAYER_EYE_HEIGHT        # Feet after gravity

        # ── Landing detection (sweep test) ───────────────────────────────────
        # Find the highest surface the player is falling through this frame.
        best_landing = 0.0    # World-space floor
        if colliders:
            for c in colliders:
                c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z = c[:6]
                if (self.x + pr > c_min_x and self.x - pr < c_max_x and
                    self.z + pr > c_min_z and self.z - pr < c_max_z):
                    # Landing: player feet were above (or at) the surface,
                    # and have now fallen to or below the surface
                    if (prev_feet >= c_max_y - 0.08 and
                        new_feet <= c_max_y + 0.05 and
                        c_max_y > best_landing):
                        best_landing = c_max_y

        landing_camera_y = best_landing + PLAYER_EYE_HEIGHT
        if self.y < landing_camera_y:
            self.y = landing_camera_y
            self.y_velocity = 0.0

        # ── Absolute floor safety net ────────────────────────────────────────
        if self.y < self.ground_y:
            self.y = self.ground_y
            self.y_velocity = 0.0
            
        return pushed_something

    def is_moving(self):
        """Return True if any movement key is pressed."""
        return any(self.keys_pressed.get(k) for k in (b'w', b's', b'a', b'd'))

    def apply(self, colliders=None):
        """Apply camera transform with Ray-AABB camera collision anti-clipping."""
        lx, ly, lz = self._look_direction()

        if _is_aiming:
            # ── 1ST PERSON AIMING VIEW ─────────────────────────────────────────
            cam_x = self.x
            cam_y = self.y + 0.5  # Eye height
            cam_z = self.z
            tx = cam_x + lx
            ty = cam_y + ly
            tz = cam_z + lz
            glLoadIdentity()
            gluLookAt(cam_x, cam_y, cam_z,
                      tx, ty, tz,
                      0.0, 1.0, 0.0)
            return

        # ── 3RD PERSON VIEW ───────────────────────────────────────────────────
        tx = self.x
        ty = self.y + 1.0   # Target position (head height)
        tz = self.z

        max_distance = 3.0
        height_offset = 0.2

        dx = -lx * max_distance
        dy = height_offset - ly * max_distance
        dz = -lz * max_distance

        target_dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if target_dist > 0.001:
            ux = dx / target_dist
            uy = dy / target_dist
            uz = dz / target_dist
        else:
            ux, uy, uz = 0.0, 0.0, -1.0

        actual_dist = target_dist

        if colliders:
            px, pz = self.x, self.z
            nearby_colliders = [
                c for c in colliders
                if (c[0] - 4.0 <= px <= c[1] + 4.0 and c[4] - 4.0 <= pz <= c[5] + 4.0)
            ]
            for c in nearby_colliders:
                c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z = c[:6]
                box_min_x, box_max_x = c_min_x - 0.15, c_max_x + 0.15
                box_min_y, box_max_y = c_min_y - 0.15, c_max_y + 0.15
                box_min_z, box_max_z = c_min_z - 0.15, c_max_z + 0.15

                t_min = 0.0
                t_max = actual_dist

                if abs(ux) > 1e-6:
                    t1 = (box_min_x - tx) / ux
                    t2 = (box_max_x - tx) / ux
                    t_min = max(t_min, min(t1, t2))
                    t_max = min(t_max, max(t1, t2))
                elif tx < box_min_x or tx > box_max_x:
                    continue

                if abs(uy) > 1e-6:
                    t1 = (box_min_y - ty) / uy
                    t2 = (box_max_y - ty) / uy
                    t_min = max(t_min, min(t1, t2))
                    t_max = min(t_max, max(t1, t2))
                elif ty < box_min_y or ty > box_max_y:
                    continue

                if abs(uz) > 1e-6:
                    t1 = (box_min_z - tz) / uz
                    t2 = (box_max_z - tz) / uz
                    t_min = max(t_min, min(t1, t2))
                    t_max = min(t_max, max(t1, t2))
                elif tz < box_min_z or tz > box_max_z:
                    continue

                if t_min <= t_max and t_min > 0.0:
                    actual_dist = min(actual_dist, max(0.5, t_min - 0.2))

        cam_x = tx + ux * actual_dist
        cam_y = ty + uy * actual_dist
        cam_z = tz + uz * actual_dist

        glLoadIdentity()
        gluLookAt(cam_x, cam_y, cam_z,
                  tx, ty, tz,
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
player_character = MainCharacter()
inventory = InventoryManager()

_light_toggle_index = 0   # Cycles through HeistLevel breakable lights via 'l'
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

    current_level_cls = None
    if game_state.current == GameState.TUTORIAL:
        current_level_cls = TutorialLevel
    elif game_state.current == GameState.STEALING_AREA:
        current_level_cls = HeistLevel

    if current_level_cls and hasattr(current_level_cls, 'get_all_colliders'):
        colliders = current_level_cls.get_all_colliders()
    elif current_level_cls and hasattr(current_level_cls, 'get_colliders'):
        colliders = current_level_cls.get_colliders()
    else:
        colliders = None

    if camera.process_movement(colliders):
        if current_level_cls:
            current_level_cls._colliders = None
    camera.apply(colliders)

    # Update grabbed box position (pull mechanic)
    if game_state.current == GameState.TUTORIAL:
        TutorialLevel.update_grabbed_box(camera)

    time_elapsed = time.time() - start_time

    # Update & render projectiles and glass bottles
    ProjectileManager.update(0.016, colliders=colliders)
    ProjectileManager.draw()
    BottleManager.update(0.016, camera=camera)
    BottleManager.draw(camera)

    if current_level_cls:
        current_level_cls.draw(time_elapsed, camera_pos=(camera.x, camera.z))
        if hasattr(current_level_cls, 'check_proximity_pickups'):
            current_level_cls.check_proximity_pickups(camera.x, camera.y - 1.0, camera.z, inventory)

    inventory.draw_hud(WindowConfig.WIDTH, WindowConfig.HEIGHT, delta_time=0.016)

    # Check if a DumpsterObstacle is overriding the player character pose
    # (during jump-in / jump-out cinematic animations).
    char_pose_override = None
    if current_level_cls and hasattr(current_level_cls, 'get_obstacle_manager'):
        for _obs in current_level_cls.get_obstacle_manager().obstacles:
            if isinstance(_obs, DumpsterObstacle):
                _pose = _obs.get_character_pose()
                if _pose is not None:
                    char_pose_override = _pose
                    break

    if not _is_aiming:
        if char_pose_override is not None:
            _px, _py, _pz, _pyaw, _pvis = char_pose_override
            if _pvis:
                player_character.x       = _px
                player_character.y       = _py
                player_character.z       = _pz
                player_character.yaw_deg = _pyaw
                player_character.draw(time_elapsed, True)
        else:
            # Normal: character follows the camera
            player_character.x       = camera.x
            player_character.y       = camera.y - 1.0
            player_character.z       = camera.z
            player_character.yaw_deg = -camera.yaw + 90.0
            is_holding = (game_state.current == GameState.TUTORIAL and getattr(TutorialLevel, '_grabbed_box', None) is not None)
            player_character.draw(time_elapsed, camera.is_moving(), is_holding=is_holding)

    # Draw crosshair reticle when camera is captured
    if camera.captured:
        draw_crosshair(WindowConfig.WIDTH, WindowConfig.HEIGHT, is_aiming=_is_aiming)

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
    global _light_toggle_index

    if key == b'\x1b':
        camera.toggle_capture()
        return

    # 'e' / 'E' / Tab — toggle Minecraft Inventory Overlay
    if key in (b'e', b'E', b'\t'):
        is_open = inventory.toggle_open()
        if is_open:
            camera.captured = False
            glutSetCursor(GLUT_CURSOR_INHERIT)
        else:
            camera.captured = True
            camera.first_move = True
            glutSetCursor(GLUT_CURSOR_NONE)
        return

    # Hotbar slot selection (1..9)
    if key in (b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9'):
        inventory.select_hotbar(int(key.decode()) - 1)
        print(f"Selected Hotbar Slot {int(key.decode())}")

    # '2' — jump to Level 2 (Grand Heist Arena) for testing
    if key == b'2':
        game_state.current = GameState.STEALING_AREA
        sp = HeistLevel.spawn_pos()
        camera.x, camera.y, camera.z = sp[0], sp[1], sp[2]
        camera.yaw   = -90.0   # Face north into the arena
        camera.pitch = 0.0
        print("Switched to Level 2 — Grand Heist Arena")
        return

    # '1' — jump back to Tutorial
    if key == b'1':
        game_state.current = GameState.TUTORIAL
        sp = TutorialLevel.spawn_pos()
        camera.x, camera.y, camera.z = sp[0], sp[1], sp[2]
        camera.yaw   = 90.0
        camera.pitch = 0.0
        print("Switched to Tutorial Level")
        return

    # 'l' / 'L' — cycle breakable lights off (simulates projectile hit)
    if key in (b'l', b'L'):
        HeistLevel.toggle_light(_light_toggle_index % 6)
        print(f"Light {_light_toggle_index % 6} toggled "
              f"({'ON' if HeistLevel.lights_on[_light_toggle_index % 6] else 'OFF'})")
        _light_toggle_index += 1
        return

    # 'f' / 'F' — interaction
    if key in (b'f', b'F'):
        if game_state.current == GameState.TUTORIAL:
            TutorialLevel.interact(camera)
        return

    # 'q' / 'Q' — Shoot projectile OR throw bottle if selected from inventory
    if key in (b'q', b'Q'):
        if camera.captured:
            active_item = inventory.get_active_item()
            if active_item is not None and active_item.name == "Glass Bottle" and active_item.count > 0:
                BottleManager.is_aiming_throw = True
            else:
                ProjectileManager.shoot(camera)
        return

    # 'r' / 'R' — restart tutorial level / reset player position & police
    if key in (b'r', b'R'):
        if game_state.current == GameState.TUTORIAL:
            sp = TutorialLevel.spawn_pos()
            camera.x, camera.y, camera.z = sp[0], sp[1], sp[2]
            camera.yaw = 90.0
            camera.pitch = 0.0
            PolicePatrolRoom.reset_npcs()
            if getattr(TutorialLevel, '_grabbed_box', None) is not None:
                TutorialLevel._grabbed_box = None
                TutorialLevel._colliders = None
            print("Restarted tutorial level!")
            return

    camera.on_key_down(key)


def keyboard_up(key, x, y):
    if key in (b'q', b'Q'):
        if BottleManager.is_aiming_throw:
            BottleManager.is_aiming_throw = False
            BottleManager.shoot_throw(camera)
    camera.on_key_up(key)


def mouse_motion(x, y):
    camera.on_mouse_move(x, y)


def mouse_click(button, state, x, y):
    global _is_aiming
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if inventory.is_open:
            inventory.handle_mouse_click(x, y, WindowConfig.WIDTH, WindowConfig.HEIGHT)

    elif button == GLUT_RIGHT_BUTTON:
        if state == GLUT_DOWN:
            if camera.captured:
                _is_aiming = True
        elif state == GLUT_UP:
            if _is_aiming and camera.captured:
                _is_aiming = False
                ProjectileManager.shoot(camera)


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
    glutMouseFunc(mouse_click)
    glutPassiveMotionFunc(mouse_motion)
    glutMotionFunc(mouse_motion)

    glutSetCursor(GLUT_CURSOR_NONE)

    print("=== Honour Among Thieves ===")
    print("Tutorial Area loaded. Press '2' to enter Level 2 — Grand Heist Arena.")
    print("Controls: WASD to move, Mouse to look, ESC to release cursor")
    print("Level 2 keys: '2' = Heist Arena, '1' = Tutorial, 'L' = break next light")
    print()

    glutMainLoop()


if __name__ == "__main__":
    main()
