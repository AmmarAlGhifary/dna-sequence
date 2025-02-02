import pygame as pg
from pygame.locals import *
import sys
import math
from OpenGL.GL import *
from OpenGL.GLU import *

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Camera parameters
camera_radius = 15.0   # Distance from origin
camera_phi = 0.0       # Rotation around Y-axis (left/right)
camera_theta = 0.15    # Slight tilt down
camera_height = 0.0    # Up/down translation

# Mouse rotation sensitivity
mouse_sensitivity = 0.2

# Automatic animation controls
auto_scroll_offset = 0.0     # Moves the DNA downward
auto_scroll_speed = 0.03     # Speed of downward motion
auto_twist_angle = 0.0       # Twist around the vertical axis
auto_twist_speed = -0.4      # Negative => counter-clockwise

# DNA parameters
helix_turns = 12             # Number of helical turns
helix_points_per_turn = 50   # Points to define each turn
helix_height = 30.0          # Vertical height of each DNA segment
helix_radius = 1.0           # Radius of the helix
base_pair_step = 8           # Interval between rungs

# Movement speed
movement_speed = 0.2
rotation_speed = 2.0


def init_pygame_opengl():
    """
    Initialize Pygame and OpenGL context.
    """
    pg.init()
    pg.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pg.display.set_caption('Infinite Scrolling DNA - Pygame & PyOpenGL')

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    # (Optional) Smoother lines
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glLineWidth(2.0)

    # Set perspective
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, (WIDTH / float(HEIGHT)), 0.1, 200.0)
    glMatrixMode(GL_MODELVIEW)


def handle_input():
    """
    Handle user input from keyboard and mouse.
    Adjust camera parameters or exit the application.
    """
    global camera_radius, camera_phi, camera_theta, camera_height

    keys = pg.key.get_pressed()
    if keys[pg.K_ESCAPE]:
        pg.quit()
        sys.exit()

    # Move closer/farther
    if keys[pg.K_w]:
        camera_radius -= movement_speed
    if keys[pg.K_s]:
        camera_radius += movement_speed

    # Rotate left/right
    if keys[pg.K_a]:
        camera_phi -= math.radians(rotation_speed)
    if keys[pg.K_d]:
        camera_phi += math.radians(rotation_speed)

    # Move camera up/down
    if keys[pg.K_q]:
        camera_height += movement_speed
    if keys[pg.K_e]:
        camera_height -= movement_speed

    # Mouse drag for free rotation
    mouse_buttons = pg.mouse.get_pressed()
    if mouse_buttons[0]:
        mouse_rel = pg.mouse.get_rel()
        camera_phi += mouse_rel[0] * mouse_sensitivity * 0.01
        camera_theta += mouse_rel[1] * mouse_sensitivity * 0.01
    else:
        # If not dragging, reset relative motion
        pg.mouse.get_rel()


def update_animation():
    """
    Update any automatic DNA animations (scroll, twist, etc.)
    """
    global auto_scroll_offset, auto_twist_angle
    # Move the helix downward (decrement offset)
    auto_scroll_offset -= auto_scroll_speed
    # Wrap offset so we never get a jump
    auto_scroll_offset %= helix_height

    # Twist around the vertical (Y) axis
    auto_twist_angle += auto_twist_speed


def draw_single_dna_segment(y_offset):
    """
    Draw a single DNA helix segment from -helix_height/2 to +helix_height/2,
    shifted vertically by 'y_offset'.
    """
    total_points = helix_turns * helix_points_per_turn
    backbone1 = []
    backbone2 = []

    for i in range(total_points + 1):
        frac = i / float(total_points)
        angle = frac * helix_turns * 2.0 * math.pi
        # y from -H/2 to +H/2
        y = frac * helix_height - (helix_height / 2.0) + y_offset

        # One backbone
        x1 = helix_radius * math.cos(angle)
        z1 = helix_radius * math.sin(angle)

        # Opposite backbone is pi out of phase
        x2 = helix_radius * math.cos(angle + math.pi)
        z2 = helix_radius * math.sin(angle + math.pi)

        backbone1.append((x1, y, z1))
        backbone2.append((x2, y, z2))

    # Draw backbone #1
    glColor3f(0.8, 0.8, 0.0)  # yellow-ish
    glBegin(GL_LINE_STRIP)
    for (x, y, z) in backbone1:
        glVertex3f(x, y, z)
    glEnd()

    # Draw backbone #2
    glColor3f(0.0, 0.8, 0.8)  # cyan-ish
    glBegin(GL_LINE_STRIP)
    for (x, y, z) in backbone2:
        glVertex3f(x, y, z)
    glEnd()

    # Draw base pair "rungs"
    glColor3f(1.0, 1.0, 1.0)  # white
    glBegin(GL_LINES)
    for i in range(0, total_points + 1, base_pair_step):
        x1, y1, z1 = backbone1[i]
        x2, y2, z2 = backbone2[i]
        glVertex3f(x1, y1, z1)
        glVertex3f(x2, y2, z2)
    glEnd()


def draw_dna():
    """
    Draw multiple copies of the DNA segment so it appears infinite.
    We draw at offsets in [-1, 0, +1] * helix_height around auto_scroll_offset.
    """
    # Because we use a modular offset, we can tile 3 segments:
    # one in the "center", one above it, one below it.
    for k in [-1, 0, 1]:
        seg_offset = auto_scroll_offset + k * helix_height
        draw_single_dna_segment(seg_offset)


def main():
    init_pygame_opengl()
    clock = pg.time.Clock()

    # Hide the mouse and grab it for dragging
    pg.mouse.set_visible(False)
    pg.event.set_grab(True)

    running = True
    while running:
        clock.tick(60)  # 60 FPS

        # Process events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

        # Handle user/camera input
        handle_input()
        # Update DNA motion
        update_animation()

        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Compute camera position in spherical coordinates
        cam_x = camera_radius * math.cos(camera_theta) * math.sin(camera_phi)
        cam_y = camera_height + camera_radius * math.sin(camera_theta)
        cam_z = camera_radius * math.cos(camera_theta) * math.cos(camera_phi)

        # Look at the origin
        gluLookAt(
            cam_x, cam_y, cam_z,  # Eye
            0.0, 0.0, 0.0,        # Center
            0.0, 1.0, 0.0         # Up
        )

        # Apply a gentle twist around Y-axis
        glRotatef(auto_twist_angle, 0.0, 1.0, 0.0)

        # Draw the “infinite” DNA
        draw_dna()

        # Swap buffers
        pg.display.flip()

    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
