"""
utils/inventory.py — Minecraft-style Inventory System for Honour Among Thieves.

Features:
  - 36 total slots (9-slot Hotbar + 27-slot Main Inventory Grid).
  - Bottom-center Hotbar HUD overlay always visible.
  - Full Minecraft-style dark slate grid overlay toggled via 'E' or 'Tab'.
  - Item stack counts, custom item colors, and dollar loot valuation.
  - Interactive item drag/swap via mouse clicks in inventory mode.
  - Proximity loot pickup and HUD toast notifications.
"""

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

from utils.drawing import set_material, draw_text_2d, draw_cube


class InventoryItem:
    """Represents an individual item in the inventory."""
    def __init__(self, name, color, value=0, count=1, description="Stolen Loot"):
        self.name = name
        self.color = color          # Tuple RGB (r, g, b)
        self.value = value          # Dollar value
        self.count = count          # Stack count
        self.description = description


class InventoryManager:
    """Manages player inventory, hotbar, 2D HUD, and slot interactions."""

    HOTBAR_SIZE = 9
    MAIN_GRID_SIZE = 27
    TOTAL_SLOTS = 36    # 0..8 = Hotbar, 9..35 = Main Inventory Grid

    def __init__(self):
        self.slots = [None] * self.TOTAL_SLOTS
        self.active_hotbar_index = 0
        self.is_open = False
        self.held_slot_index = None       # Index of item being moved via mouse click
        self.notifications = []            # List of (text, expire_time) for pickup toasts
        self.total_loot_value = 0

    def toggle_open(self):
        """Toggle the full inventory overlay."""
        self.is_open = not self.is_open
        if not self.is_open:
            self.held_slot_index = None
        return self.is_open

    def add_notification(self, text):
        """Add a temporary popup notification to the HUD."""
        self.notifications.append((text, 3.0))

    def add_item(self, item):
        """Add an item to the first available slot or stack with existing item."""
        # Try to stack first
        for i in range(self.TOTAL_SLOTS):
            slot_item = self.slots[i]
            if slot_item is not None and slot_item.name == item.name:
                slot_item.count += item.count
                self.total_loot_value += item.value * item.count
                self.add_notification(f"+ Stacked {item.name} (${item.value:,})")
                return True

        # Find first empty slot
        for i in range(self.TOTAL_SLOTS):
            if self.slots[i] is None:
                self.slots[i] = item
                self.total_loot_value += item.value * item.count
                self.add_notification(f"+ Collected {item.name} (${item.value:,})")
                return True

        self.add_notification("! Inventory Full!")
        return False

    def select_hotbar(self, index):
        """Select active hotbar slot 0..8."""
        if 0 <= index < self.HOTBAR_SIZE:
            self.active_hotbar_index = index

    def get_active_item(self):
        """Return the item currently held in active hotbar slot."""
        return self.slots[self.active_hotbar_index]

    # ──────────────────────────────────────────────────────────────────────────
    # 2D HUD RENDERERS
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_2d_rect(self, x1, y1, x2, y2, color, alpha=1.0):
        """Draw a filled 2D rectangle in orthographic screen space."""
        r, g, b = color
        glColor4f(r, g, b, alpha)
        glBegin(GL_QUADS)
        glVertex2f(x1, y1)
        glVertex2f(x2, y1)
        glVertex2f(x2, y2)
        glVertex2f(x1, y2)
        glEnd()

    def _draw_2d_border(self, x1, y1, x2, y2, color, thickness=2):
        """Draw a 2D rectangle border line."""
        r, g, b = color
        glColor4f(r, g, b, 1.0)
        glLineWidth(thickness)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x1, y1)
        glVertex2f(x2, y1)
        glVertex2f(x2, y2)
        glVertex2f(x1, y2)
        glEnd()
        glLineWidth(1)

    def draw_hud(self, window_width=1200, window_height=800, delta_time=0.016):
        """Main 2D HUD draw entry point — renders notifications, hotbar, and full inventory."""
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, window_width, 0, window_height)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # 1. Notifications / Toasts (Top Right)
        self._draw_notifications(window_width, window_height, delta_time)

        # 2. Hotbar (Bottom Center)
        self._draw_hotbar(window_width, window_height)

        # 3. Full Inventory Overlay (Center Screen — when open)
        if self.is_open:
            self._draw_full_inventory(window_width, window_height)

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()

    def _draw_notifications(self, win_w, win_h, dt):
        """Draw active popup toast notifications."""
        new_notes = []
        y = win_h - 40
        for text, timer in self.notifications:
            timer -= dt
            if timer > 0:
                new_notes.append((text, timer))
                alpha = min(1.0, timer)
                # Toast background
                self._draw_2d_rect(win_w - 320, y - 20, win_w - 20, y + 10, (0.1, 0.1, 0.1), alpha * 0.8)
                self._draw_2d_border(win_w - 320, y - 20, win_w - 20, y + 10, (0.8, 0.7, 0.2), 1)
                draw_text_2d(win_w - 310, y - 10, text, win_w, win_h)
                y -= 35
        self.notifications = new_notes

    def _draw_hotbar(self, win_w, win_h):
        """Draw Minecraft-style 9-slot Hotbar at bottom center."""
        slot_sz = 50
        gap = 6
        total_w = self.HOTBAR_SIZE * slot_sz + (self.HOTBAR_SIZE - 1) * gap
        start_x = (win_w - total_w) / 2.0
        start_y = 20.0

        # Background panel
        self._draw_2d_rect(start_x - 10, start_y - 10, start_x + total_w + 10, start_y + slot_sz + 10,
                           (0.12, 0.12, 0.12), 0.85)
        self._draw_2d_border(start_x - 10, start_y - 10, start_x + total_w + 10, start_y + slot_sz + 10,
                            (0.3, 0.3, 0.3), 2)

        for i in range(self.HOTBAR_SIZE):
            sx = start_x + i * (slot_sz + gap)
            sy = start_y

            # Inset slot background
            self._draw_2d_rect(sx, sy, sx + slot_sz, sy + slot_sz, (0.08, 0.08, 0.08), 0.9)
            
            # Active slot selection highlight
            if i == self.active_hotbar_index:
                self._draw_2d_border(sx - 2, sy - 2, sx + slot_sz + 2, sy + slot_sz + 2, (1.0, 0.84, 0.0), 3)
            else:
                self._draw_2d_border(sx, sy, sx + slot_sz, sy + slot_sz, (0.25, 0.25, 0.25), 1)

            # Slot number key label (1-9)
            draw_text_2d(int(sx + 4), int(sy + slot_sz - 14), str(i + 1), win_w, win_h)

            # Draw item in slot
            item = self.slots[i]
            if item is not None:
                self._draw_item_in_slot(sx, sy, slot_sz, item, win_w, win_h)

    def _draw_full_inventory(self, win_w, win_h):
        """Draw full Minecraft 9x3 grid inventory overlay."""
        panel_w = 520
        panel_h = 440
        px = (win_w - panel_w) / 2.0
        py = (win_h - panel_h) / 2.0

        # Main Minecraft dark panel
        self._draw_2d_rect(px, py, px + panel_w, py + panel_h, (0.15, 0.15, 0.15), 0.95)
        self._draw_2d_border(px, py, px + panel_w, py + panel_h, (0.4, 0.4, 0.4), 3)
        self._draw_2d_border(px + 4, py + 4, px + panel_w - 4, py + panel_h - 4, (0.05, 0.05, 0.05), 1)

        # Header Title & Loot Value Counter
        draw_text_2d(int(px + 20), int(py + panel_h - 30), "INVENTORY  --  STOLEN LOOT", win_w, win_h)
        draw_text_2d(int(px + panel_w - 220), int(py + panel_h - 30), f"Loot Value: ${self.total_loot_value:,}", win_w, win_h)

        slot_sz = 46
        gap = 8

        # 1. Main Grid (9x3 slots) — Slots 9..35
        grid_start_x = px + 20
        grid_start_y = py + 120

        for row in range(3):
            for col in range(9):
                idx = 9 + row * 9 + col
                sx = grid_start_x + col * (slot_sz + gap)
                sy = grid_start_y + (2 - row) * (slot_sz + gap)

                self._draw_2d_rect(sx, sy, sx + slot_sz, sy + slot_sz, (0.08, 0.08, 0.08), 0.95)
                self._draw_2d_border(sx, sy, sx + slot_sz, sy + slot_sz, (0.3, 0.3, 0.3), 1)

                if idx == self.held_slot_index:
                    self._draw_2d_border(sx, sy, sx + slot_sz, sy + slot_sz, (0.2, 0.8, 1.0), 2)

                item = self.slots[idx]
                if item is not None:
                    self._draw_item_in_slot(sx, sy, slot_sz, item, win_w, win_h)

        # Separator line
        self._draw_2d_rect(px + 15, py + 100, px + panel_w - 15, py + 102, (0.3, 0.3, 0.3), 1.0)

        # 2. Hotbar Row inside Inventory (Slots 0..8)
        hotbar_y = py + 35
        for col in range(9):
            idx = col
            sx = grid_start_x + col * (slot_sz + gap)
            sy = hotbar_y

            self._draw_2d_rect(sx, sy, sx + slot_sz, sy + slot_sz, (0.08, 0.08, 0.08), 0.95)
            if col == self.active_hotbar_index:
                self._draw_2d_border(sx, sy, sx + slot_sz, sy + slot_sz, (1.0, 0.84, 0.0), 2)
            else:
                self._draw_2d_border(sx, sy, sx + slot_sz, sy + slot_sz, (0.3, 0.3, 0.3), 1)

            if idx == self.held_slot_index:
                self._draw_2d_border(sx, sy, sx + slot_sz, sy + slot_sz, (0.2, 0.8, 1.0), 2)

            item = self.slots[idx]
            if item is not None:
                self._draw_item_in_slot(sx, sy, slot_sz, item, win_w, win_h)

        # Footer Hint Controls
        draw_text_2d(int(px + 20), int(py + 12), "[Click]: Select/Swap  |  [E/Tab]: Close  |  [1-9]: Select Hotbar", win_w, win_h)

    def _draw_item_in_slot(self, sx, sy, sz, item, win_w, win_h):
        """Draw an item icon block, label, and stack count inside a slot."""
        cx = sx + sz / 2.0
        cy = sy + sz / 2.0
        icon_sz = sz * 0.45

        # Item 2D colored icon box
        self._draw_2d_rect(cx - icon_sz / 2.0, cy - icon_sz / 2.0,
                           cx + icon_sz / 2.0, cy + icon_sz / 2.0, item.color, 1.0)
        self._draw_2d_border(cx - icon_sz / 2.0, cy - icon_sz / 2.0,
                            cx + icon_sz / 2.0, cy + icon_sz / 2.0, (1.0, 1.0, 1.0), 1)

        # Stack count (bottom-right)
        if item.count > 1:
            draw_text_2d(int(sx + sz - 14), int(sy + 4), str(item.count), win_w, win_h)

    # ──────────────────────────────────────────────────────────────────────────
    # MOUSE INTERACTION & SLOT CLICK SWAPPING
    # ──────────────────────────────────────────────────────────────────────────

    def handle_mouse_click(self, mouse_x, mouse_y, win_w, win_h):
        """Handle item selection and slot swapping via mouse clicks."""
        if not self.is_open:
            return False

        # Invert GLUT mouse Y coordinate to match Ortho2D coordinate system
        inv_y = win_h - mouse_y

        panel_w = 520
        panel_h = 440
        px = (win_w - panel_w) / 2.0
        py = (win_h - panel_h) / 2.0

        slot_sz = 46
        gap = 8
        grid_start_x = px + 20
        grid_start_y = py + 120

        clicked_slot = None

        # Check Main Grid (9x3 slots) — Slots 9..35
        for row in range(3):
            for col in range(9):
                idx = 9 + row * 9 + col
                sx = grid_start_x + col * (slot_sz + gap)
                sy = grid_start_y + (2 - row) * (slot_sz + gap)
                if sx <= mouse_x <= sx + slot_sz and sy <= inv_y <= sy + slot_sz:
                    clicked_slot = idx
                    break

        # Check Hotbar Row (Slots 0..8)
        if clicked_slot is None:
            hotbar_y = py + 35
            for col in range(9):
                sx = grid_start_x + col * (slot_sz + gap)
                sy = hotbar_y
                if sx <= mouse_x <= sx + slot_sz and sy <= inv_y <= sy + slot_sz:
                    clicked_slot = col
                    break

        if clicked_slot is not None:
            if self.held_slot_index is None:
                # Pick up / select item in slot
                if self.slots[clicked_slot] is not None:
                    self.held_slot_index = clicked_slot
            else:
                # Swap items between held_slot_index and clicked_slot
                idx_a = self.held_slot_index
                idx_b = clicked_slot
                self.slots[idx_a], self.slots[idx_b] = self.slots[idx_b], self.slots[idx_a]
                self.held_slot_index = None
            return True

        return False
