"""
main.py — Game entry point for Honour Among Thieves.

Sets up the 3D OpenGL/GLUT window, lighting, and render loop.
Calls the active level's draw function each frame.

Includes a temporary free-look camera (WASD + mouse) so team members can
inspect level geometry. Mehrab will replace this with his camera system.

Only uses OpenGL/GLUT functions allowed by the course template + glDepth.
"""

import sys
import os
import math
import time

# Ensure the project root (where the OpenGL package lives) is on sys.path
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from levels import tutorial as tutorial_level

# ──────────────────────────────────────────────
# Window Settings
# ──────────────────────────────────────────────

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_TITLE = b"Honour Among Thieves"

# ──────────────────────────────────────────────
# Game State
# ──────────────────────────────────────────────

# Which level is currently active
# Values: "tutorial", "stealing_area", "police_station", "cutscene", etc.
current_level = "tutorial"

# ──────────────────────────────────────────────
# Temporary Camera (will be replaced by Mehrab's camera system)
# ──────────────────────────────────────────────

# Camera position — start in the spawn alcove
camera_x = tutorial_level.SPAWN_POS[0]
camera_y = tutorial_level.SPAWN_POS[1]
camera_z = tutorial_level.SPAWN_POS[2]

# Camera angles (degrees)
camera_yaw = 90.0      # Horizontal rotation (start facing +Z into the room)
camera_pitch = 0.0      # Vertical rotation

# Movement speed
MOVE_SPEED = 0.15
MOUSE_SENSITIVITY = 0.15

# Key states for smooth movement
keys_pressed = {
    b'w': False,
    b's': False,
    b'a': False,
    b'd': False,
}

# Mouse tracking
mouse_last_x = WINDOW_WIDTH // 2
mouse_last_y = WINDOW_HEIGHT // 2
mouse_captured = True
first_mouse_move = True

# Time tracking
start_time = 0.0

# ──────────────────────────────────────────────
# OpenGL Initialization
# ──────────────────────────────────────────────


def init():
    """Initialize OpenGL settings for 3D rendering."""
    glClearColor(0.02, 0.02, 0.05, 1.0)  # Near-black background (night sky)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_NORMALIZE)

    # Global ambient light (very dim)
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.05, 0.05, 0.07, 1.0])

    # Enable smooth shading
    glShadeModel(GL_SMOOTH)

    # Depth buffer setup
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)


def setup_projection():
    """Set up the perspective projection matrix."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 200.0)
    glMatrixMode(GL_MODELVIEW)


# ──────────────────────────────────────────────
# Temporary Camera Controls
# ──────────────────────────────────────────────


def update_camera():
    """Apply the free-look camera transform based on current position and angles."""
    # Calculate look direction from yaw and pitch
    rad_yaw = math.radians(camera_yaw)
    rad_pitch = math.radians(camera_pitch)

    look_x = math.cos(rad_pitch) * math.cos(rad_yaw)
    look_y = math.sin(rad_pitch)
    look_z = math.cos(rad_pitch) * math.sin(rad_yaw)

    glLoadIdentity()
    gluLookAt(
        camera_x, camera_y, camera_z,
        camera_x + look_x, camera_y + look_y, camera_z + look_z,
        0.0, 1.0, 0.0
    )


def process_movement():
    """Update camera position based on currently pressed keys."""
    global camera_x, camera_y, camera_z

    rad_yaw = math.radians(camera_yaw)

    # Forward/backward direction (on XZ plane)
    forward_x = math.cos(rad_yaw)
    forward_z = math.sin(rad_yaw)

    # Strafe direction (perpendicular to forward on XZ plane)
    right_x = math.cos(rad_yaw - math.pi / 2.0)
    right_z = math.sin(rad_yaw - math.pi / 2.0)

    if keys_pressed.get(b'w', False):
        camera_x += forward_x * MOVE_SPEED
        camera_z += forward_z * MOVE_SPEED
    if keys_pressed.get(b's', False):
        camera_x -= forward_x * MOVE_SPEED
        camera_z -= forward_z * MOVE_SPEED
    if keys_pressed.get(b'a', False):
        camera_x += right_x * MOVE_SPEED
        camera_z += right_z * MOVE_SPEED
    if keys_pressed.get(b'd', False):
        camera_x -= right_x * MOVE_SPEED
        camera_z -= right_z * MOVE_SPEED


# ──────────────────────────────────────────────
# GLUT Callbacks
# ──────────────────────────────────────────────


def display():
    """Main render callback — clears, sets camera, draws active level."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    setup_projection()
    process_movement()
    update_camera()

    # Calculate elapsed time for animations
    time_elapsed = time.time() - start_time

    # Draw the active level
    if current_level == "tutorial":
        tutorial_level.draw(time_elapsed)

    glutSwapBuffers()


def idle():
    """Idle callback — requests a redisplay to keep the render loop running."""
    glutPostRedisplay()


def reshape(width, height):
    """Handle window resize."""
    global WINDOW_WIDTH, WINDOW_HEIGHT
    if height == 0:
        height = 1
    WINDOW_WIDTH = width
    WINDOW_HEIGHT = height
    glViewport(0, 0, width, height)
    setup_projection()


def keyboard_down(key, x, y):
    """Handle key press events."""
    global mouse_captured

    if key == b'\x1b':  # Escape
        # Toggle mouse capture
        mouse_captured = not mouse_captured
        if mouse_captured:
            glutSetCursor(GLUT_CURSOR_NONE)
        else:
            glutSetCursor(GLUT_CURSOR_INHERIT)
        return

    if key in keys_pressed:
        keys_pressed[key] = True


def keyboard_up(key, x, y):
    """Handle key release events."""
    if key in keys_pressed:
        keys_pressed[key] = False


def mouse_motion(x, y):
    """Handle mouse movement for camera look."""
    global camera_yaw, camera_pitch, mouse_last_x, mouse_last_y, first_mouse_move

    if not mouse_captured:
        return

    if first_mouse_move:
        mouse_last_x = x
        mouse_last_y = y
        first_mouse_move = False
        return

    dx = x - mouse_last_x
    dy = mouse_last_y - y  # Inverted Y

    mouse_last_x = x
    mouse_last_y = y

    camera_yaw += dx * MOUSE_SENSITIVITY
    camera_pitch += dy * MOUSE_SENSITIVITY

    # Clamp pitch to avoid gimbal lock
    if camera_pitch > 89.0:
        camera_pitch = 89.0
    if camera_pitch < -89.0:
        camera_pitch = -89.0

    # Warp cursor to center to keep continuous mouse look
    center_x = WINDOW_WIDTH // 2
    center_y = WINDOW_HEIGHT // 2
    if abs(x - center_x) > 100 or abs(y - center_y) > 100:
        glutWarpPointer(center_x, center_y)
        mouse_last_x = center_x
        mouse_last_y = center_y


# ──────────────────────────────────────────────
# Main Entry Point
# ──────────────────────────────────────────────


def main():
    """Initialize GLUT, create window, register callbacks, start main loop."""
    global start_time

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 50)
    glutCreateWindow(WINDOW_TITLE)

    init()
    start_time = time.time()

    # Register callbacks
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutPassiveMotionFunc(mouse_motion)
    glutMotionFunc(mouse_motion)

    # Hide cursor for FPS-style mouse look
    glutSetCursor(GLUT_CURSOR_NONE)

    print("=== Honour Among Thieves ===")
    print("Tutorial Area loaded.")
    print("Controls: WASD to move, Mouse to look, ESC to release cursor")
    print()

    glutMainLoop()


if __name__ == "__main__":
    main()
