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

    def draw(self, time_elapsed=0.0, is_moving=False):
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
        glRotatef(-swing, 1.0, 0.0, 0.0)
        glTranslatef(0.40, -1.5, 0.0)
        
        draw_cube(-0.40, 1.38, 0.0,   0.18, 0.44, 0.20, self.C_TORSO)        # Upper arm
        draw_cube(-0.42, 1.08, 0.04,  0.20, 0.28, 0.22, self.C_GLOVE)        # Forearm
        draw_cube(-0.44, 0.96, 0.06,  0.22, 0.18, 0.22, self.C_GLOVE)        # Hand
        glPopMatrix()

        # ── RIGHT ARM ────────────────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.40, 1.5, 0.0)
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

    def draw(self, time_elapsed=0.0, is_moving=False):
        if is_moving:
            swing = math.sin(time_elapsed * 12.0) * 45.0
            bob_y = abs(math.sin(time_elapsed * 12.0)) * 0.1
        else:
            swing = 0.0
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
        glRotatef(-swing, 1.0, 0.0, 0.0)
        glTranslatef(0.18, -1.6, 0.0)
        draw_cube(-0.18, 1.30, 0.0,   0.08, 0.60, 0.08, self.C_UNIFORM)
        draw_cube(-0.18, 0.95, 0.0,   0.10, 0.10, 0.10, self.C_SKIN) # Hand
        glPopMatrix()

        # ── RIGHT ARM (Thin) ──────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.18, 1.6, 0.0)
        glRotatef(swing, 1.0, 0.0, 0.0)
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

    def draw(self, time_elapsed=0.0, is_moving=False):
        if is_moving:
            swing = math.sin(time_elapsed * 8.0) * 35.0  # Slower, heavier swing
            bob_y = abs(math.sin(time_elapsed * 8.0)) * 0.15 # Heavier bob
        else:
            swing = 0.0
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
        glRotatef(-swing, 1.0, 0.0, 0.0)
        glTranslatef(0.45, -1.4, 0.0)
        draw_cube(-0.45, 1.05, 0.0,   0.20, 0.70, 0.20, self.C_UNIFORM)
        draw_cube(-0.45, 0.65, 0.0,   0.16, 0.16, 0.16, self.C_SKIN) # Hand
        glPopMatrix()

        # ── RIGHT ARM (Thick) ─────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.45, 1.4, 0.0)
        glRotatef(swing, 1.0, 0.0, 0.0)
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
            can_be_pushed=False,
            color=color,
            accent_color=accent_color
        )

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
        # Left door
        glPushMatrix()
        glTranslatef(-door_w / 2.0 - 0.01, 0.0, front_z)
        glScalef(door_w, door_h, t * 0.8)
        glutSolidCube(1)
        glPopMatrix()

        # Right door
        glPushMatrix()
        glTranslatef(door_w / 2.0 + 0.01, 0.0, front_z)
        glScalef(door_w, door_h, t * 0.8)
        glutSolidCube(1)
        glPopMatrix()

        # Metallic door handles
        set_material((0.85, 0.75, 0.3))  # Brass handles
        glPushMatrix()
        glTranslatef(-0.06, 0.0, front_z + t)
        glutSolidSphere(0.06, 8, 8)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.06, 0.0, front_z + t)
        glutSolidSphere(0.06, 8, 8)
        glPopMatrix()

        glPopMatrix()


class DumpsterObstacle(Obstacle):
    """
    Industrial Metal Dumpster.
    Provides cover and can be pushed or hid inside.
    """

    def __init__(self, x, y, z, width=2.6, height=1.6, depth=1.6, rotation=0.0,
                 color=(0.18, 0.35, 0.24), accent_color=(0.12, 0.22, 0.15)):
        super().__init__(
            x=x, y=y, z=z,
            width=width, height=height, depth=depth,
            rotation=rotation,
            is_interactive=True,
            can_hide_inside=True,
            can_be_pushed=True,
            color=color,
            accent_color=accent_color
        )

    def draw(self):
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

        # Black plastic lids (angled/split top)
        set_material((0.1, 0.1, 0.12))
        lid_w = w / 2.0 - 0.05
        lid_d = d * 0.95
        glPushMatrix()
        glTranslatef(-lid_w / 2.0 - 0.02, h * 0.46, 0.0)
        glRotatef(5.0, 0.0, 0.0, 1.0)  # Slightly open lid
        glScalef(lid_w, 0.08, lid_d)
        glutSolidCube(1)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(lid_w / 2.0 + 0.02, h * 0.46, 0.0)
        glRotatef(-5.0, 0.0, 0.0, 1.0)
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
                cls._colliders.append((x - hw, x + hw, c_min_y, c_max_y, z - hz, z + hz))
                
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
                min_x, max_x, min_y, max_y, min_z, max_z = obs.get_bounding_box()
                if max_y > 0.1:
                    cls._colliders.append((min_x, max_x, min_y, max_y, min_z, max_z))
        finally:
            main_mod.draw_cube = original_draw_cube

        return cls._colliders

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

        self.keys_pressed = {b'w': False, b's': False, b'a': False, b'd': False, b' ': False}
        self.y_velocity = 0.0
        self.ground_y = y  # Store initial Y as the ground level

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

    def process_movement(self, colliders=None):
        """Update position based on currently pressed keys, with full 3D collision.

        Colliders are 6-tuples: (min_x, max_x, min_y, max_y, min_z, max_z)
        in world space. camera.y is eye-level, which is PLAYER_EYE_HEIGHT
        above the player's feet in world space.
        """
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

        # ── Player physical parameters (world space) ─────────────────────────
        pr = 0.4                                    # Horizontal collision radius
        feet_y = self.y - PLAYER_EYE_HEIGHT         # Feet in world space
        head_y = feet_y + 1.8                       # Head in world space
        step_up = 0.05                              # Maximum auto-step height

        # ── XZ wall blocking ─────────────────────────────────────────────────
        if colliders:
            collision_x = False
            collision_z = False

            for (c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z) in colliders:
                # Block only if the player's body overlaps the collider vertically
                # AND the player is NOT standing on top (feet below top - step_up)
                if (feet_y < c_max_y - step_up and head_y > c_min_y and
                    new_x + pr > c_min_x and new_x - pr < c_max_x and
                    self.z + pr > c_min_z and self.z - pr < c_max_z):
                    collision_x = True
                    break

            for (c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z) in colliders:
                if (feet_y < c_max_y - step_up and head_y > c_min_y and
                    self.x + pr > c_min_x and self.x - pr < c_max_x and
                    new_z + pr > c_min_z and new_z - pr < c_max_z):
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
            for (c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z) in colliders:
                if (self.x + pr > c_min_x and self.x - pr < c_max_x and
                    self.z + pr > c_min_z and self.z - pr < c_max_z):
                    # Player feet are at or very near the top of this surface
                    if abs(feet_y - c_max_y) < 0.15 and c_max_y > standing_surface:
                        standing_surface = c_max_y

        standing_camera_y = standing_surface + PLAYER_EYE_HEIGHT
        on_ground = abs(self.y - standing_camera_y) < 0.15

        # ── Jump trigger ─────────────────────────────────────────────────────
        if self.keys_pressed.get(b' ') and on_ground:
            self.y_velocity = 0.22

        # ── Apply gravity ────────────────────────────────────────────────────
        prev_feet = self.y - PLAYER_EYE_HEIGHT      # Feet before gravity
        self.y += self.y_velocity
        self.y_velocity -= 0.01
        new_feet = self.y - PLAYER_EYE_HEIGHT        # Feet after gravity

        # ── Landing detection (sweep test) ───────────────────────────────────
        # Find the highest surface the player is falling through this frame.
        best_landing = 0.0    # World-space floor
        if colliders:
            for (c_min_x, c_max_x, c_min_y, c_max_y, c_min_z, c_max_z) in colliders:
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

    def is_moving(self):
        """Return True if any movement key is pressed."""
        return any(self.keys_pressed.get(k) for k in (b'w', b's', b'a', b'd'))

    def apply(self):
        """Apply camera transform to the OpenGL modelview matrix."""
        lx, ly, lz = self._look_direction()
        
        # 3rd person: Camera is behind and slightly above the player
        distance = 3.0
        height_offset = 1.2
        
        cam_x = self.x - lx * distance
        cam_y = self.y + height_offset - ly * distance
        cam_z = self.z - lz * distance

        glLoadIdentity()
        gluLookAt(cam_x, cam_y, cam_z,
                  self.x, self.y + 1.0, self.z,
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
_temp_thin_police = ThinPoliceModel(x=3.0, y=0.0, z=6.0, yaw_deg=-45)
_temp_fat_police = FatPoliceModel(x=-3.0, y=0.0, z=6.0, yaw_deg=45)
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

    colliders = current_level_cls.get_colliders() if current_level_cls else None
    camera.process_movement(colliders)
    camera.apply()

    time_elapsed = time.time() - start_time

    if current_level_cls:
        current_level_cls.draw(time_elapsed)

    # Update player character to match the camera's position
    # The camera y represents the head level (approx 1.0 unit above ground)
    player_character.x = camera.x
    player_character.y = camera.y - 1.0
    player_character.z = camera.z
    # Adjust yaw so the character faces the direction the camera is looking
    player_character.yaw_deg = -camera.yaw + 90.0
    player_character.draw(time_elapsed, camera.is_moving())

    # Temporary: Draw the police models for review
    if game_state.current == GameState.TUTORIAL:
        _temp_thin_police.draw(time_elapsed, is_moving=False)
        _temp_fat_police.draw(time_elapsed, is_moving=False)

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
    print("Tutorial Area loaded. Press '2' to enter Level 2 — Grand Heist Arena.")
    print("Controls: WASD to move, Mouse to look, ESC to release cursor")
    print("Level 2 keys: '2' = Heist Arena, '1' = Tutorial, 'L' = break next light")
    print()

    glutMainLoop()


if __name__ == "__main__":
    main()
