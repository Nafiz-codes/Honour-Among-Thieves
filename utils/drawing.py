"""
drawing.py — Shared drawing helper functions for Honour Among Thieves.

All geometry uses only OpenGL/GLUT primitives allowed by the course template.
Any team member can import and use these helpers.
"""

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *


def set_material(color, emissive=None):
    """Apply a material color (r, g, b) to subsequent geometry.

    Args:
        color: Tuple of (r, g, b) floats in 0.0-1.0 range.
        emissive: Optional (r, g, b) emissive glow color. Defaults to no emission.
    """
    r, g, b = color
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [r * 0.3, g * 0.3, b * 0.3, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [r, g, b, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.2, 0.2, 0.2, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 20.0)
    if emissive:
        er, eg, eb = emissive
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [er, eg, eb, 1.0])
    else:
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])


def draw_cube(x, y, z, sx, sy, sz, color, emissive=None):
    """Draw a solid cube at position (x, y, z) with scale (sx, sy, sz).

    The cube is centered at the given position. Scale values represent
    the full width/height/depth of the cube.

    Args:
        x, y, z: World position (center of cube).
        sx, sy, sz: Scale factors (full size in each axis).
        color: Tuple of (r, g, b) floats.
        emissive: Optional (r, g, b) emissive glow color.
    """
    set_material(color, emissive)
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glutSolidCube(1)
    glPopMatrix()


def draw_sphere(x, y, z, radius, color, emissive=None, slices=16, stacks=16):
    """Draw a solid sphere at position (x, y, z).

    Args:
        x, y, z: World position (center of sphere).
        radius: Sphere radius.
        color: Tuple of (r, g, b) floats.
        emissive: Optional (r, g, b) emissive glow color.
        slices: Number of longitudinal divisions.
        stacks: Number of latitudinal divisions.
    """
    set_material(color, emissive)
    glPushMatrix()
    glTranslatef(x, y, z)
    glutSolidSphere(radius, slices, stacks)
    glPopMatrix()


def draw_floor_tile(x, z, size, color):
    """Draw a single floor quad on the XZ plane at y=0.

    Args:
        x, z: World position of the tile center.
        size: Side length of the square tile.
        color: Tuple of (r, g, b) floats.
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

    The quad is oriented based on the normal direction:
    - normal (0,1,0): horizontal quad (floor/ceiling) on XZ plane at height y
    - normal (0,0,1) or (0,0,-1): vertical quad on XY plane at depth z
    - normal (1,0,0) or (-1,0,0): vertical quad on YZ plane at position x

    Args:
        x, y, z: Center position of the quad.
        width: Width of the quad.
        height: Height of the quad.
        normal: Tuple (nx, ny, nz) — the face normal direction.
        color: Tuple of (r, g, b) floats.
    """
    set_material(color)
    hw = width / 2.0
    hh = height / 2.0
    nx, ny, nz = normal

    glBegin(GL_QUADS)
    glNormal3f(nx, ny, nz)

    if abs(ny) > 0.5:
        # Horizontal quad (floor/ceiling)
        glVertex3f(x - hw, y, z - hh)
        glVertex3f(x + hw, y, z - hh)
        glVertex3f(x + hw, y, z + hh)
        glVertex3f(x - hw, y, z + hh)
    elif abs(nz) > 0.5:
        # Vertical quad facing along Z
        glVertex3f(x - hw, y - hh, z)
        glVertex3f(x + hw, y - hh, z)
        glVertex3f(x + hw, y + hh, z)
        glVertex3f(x - hw, y + hh, z)
    else:
        # Vertical quad facing along X
        glVertex3f(x, y - hh, z - hw)
        glVertex3f(x, y - hh, z + hw)
        glVertex3f(x, y + hh, z + hw)
        glVertex3f(x, y + hh, z - hw)

    glEnd()


def draw_text_2d(x, y, text, window_width=1200, window_height=800):
    """Render bitmap text on the 2D HUD overlay.

    Temporarily switches to orthographic projection to draw screen-space text,
    then restores the previous projection.

    Args:
        x, y: Screen pixel coordinates (origin at bottom-left).
        text: String to render.
        window_width: Current window width in pixels.
        window_height: Current window height in pixels.
    """
    # Disable lighting so text color isn't affected by scene lights
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    # Save current matrices
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw white text
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # Restore matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)


def draw_text_3d(x, y, z, text):
    """Render bitmap text at a 3D world position.

    Useful for in-world labels and markers.

    Args:
        x, y, z: World position for the text.
        text: String to render.
    """
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos3f(x, y, z)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glEnable(GL_LIGHTING)
