import pygame as pg
from pygame.locals import *
import sys
import math
from OpenGL.GL import *
from OpenGL.GLU import *

WIDTH, HEIGHT = 800, 600

# -----------------
# Global parameters
# -----------------
camera_radius = 15.0   # Distance from origin
camera_phi = 0.0       # Rotation around Y-axis (left/right)
camera_theta = 0.15    # Slight tilt down
camera_height = 0.0    # Up/down translation

mouse_sensitivity = 1

auto_scroll_offset = 0.0     # Moves the DNA downward
auto_scroll_speed = 0.03     # Speed of downward motion
auto_twist_angle = 0.0       # Twist around the vertical axis
auto_twist_speed = -0.4      # Negative => counter-clockwise

helix_turns = 12             # Number of helical turns
helix_points_per_turn = 50   # Points to define each turn
helix_height = 30.0          # Vertical height of each DNA segment
helix_radius = 1.0           # Radius of the helix
base_pair_step = 8           # Interval between rungs

movement_speed = 0.2         # Speed of camera movement
rotation_speed = 2.0         # Speed of camera rotation
param_change_speed = 0.1     # Speed for parameter changes (radius, height, etc.)

# For textures
texture_id = None

def load_texture(filename):
    surface = pg.image.load(filename)
    # Convert image to string
    img_data = pg.image.tostring(surface, "RGBA", 1)
    width, height = surface.get_size()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
        GL_RGBA, GL_UNSIGNED_BYTE, img_data
    )

    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    glBindTexture(GL_TEXTURE_2D, 0)  # Unbind
    return tex_id


def init_pygame_opengl():
    pg.init()
    pg.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pg.display.set_caption('Infinite Scrolling DNA Sequence')

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    # Smooth lines (optional)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glLineWidth(2.0)

    # Basic perspective
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, (WIDTH / float(HEIGHT)), 0.1, 200.0)
    glMatrixMode(GL_MODELVIEW)

    # --------
    # Lighting
    # --------
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    # Light parameters
    light_ambient = [0.1, 0.1, 0.1, 1.0]
    light_diffuse = [0.8, 0.8, 0.8, 1.0]
    light_position = [10.0, 10.0, 10.0, 1.0]  # A simple positional light

    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)

    # Let glColor* calls set the material diffuse + ambient reflection
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # ------
    # Texture
    # ------
    global texture_id
    try:
        texture_id = load_texture("base_pair_texture.png")
    except:
        print("Texture image not found or failed to load.")
        texture_id = None


def handle_input():
    """
    Handle keyboard and mouse input for camera and parameter adjustments.
    """
    global camera_radius, camera_phi, camera_theta, camera_height
    global helix_radius, helix_height, auto_scroll_speed

    keys = pg.key.get_pressed()
    if keys[pg.K_ESCAPE]:
        pg.quit()
        sys.exit()

    # Camera movement
    if keys[pg.K_w]:
        camera_radius -= movement_speed
    if keys[pg.K_s]:
        camera_radius += movement_speed
    if keys[pg.K_a]:
        camera_phi -= math.radians(rotation_speed)
    if keys[pg.K_d]:
        camera_phi += math.radians(rotation_speed)
    if keys[pg.K_q]:
        camera_height += movement_speed
    if keys[pg.K_e]:
        camera_height -= movement_speed

    # Parameters adjustments

    # helix_radius
    if keys[pg.K_r]:
        helix_radius += param_change_speed
    if keys[pg.K_f]:
        helix_radius = max(0.1, helix_radius - param_change_speed)

    # helix_height
    if keys[pg.K_t]:
        helix_height += param_change_speed
    if keys[pg.K_g]:
        helix_height = max(1.0, helix_height - param_change_speed)

    # auto_scroll_speed
    if keys[pg.K_y]:
        auto_scroll_speed += 0.001
    if keys[pg.K_h]:
        auto_scroll_speed = max(0.0, auto_scroll_speed - 0.001)

    # Mouse rotation (hold left mouse button)
    mouse_buttons = pg.mouse.get_pressed()
    if mouse_buttons[0]:
        mouse_rel = pg.mouse.get_rel()
        camera_phi += mouse_rel[0] * mouse_sensitivity * 0.01
        camera_theta += mouse_rel[1] * mouse_sensitivity * 0.01
    else:
        pg.mouse.get_rel()


def update_animation():
    global auto_scroll_offset, auto_twist_angle, helix_height
    auto_scroll_offset -= auto_scroll_speed
    # Keep offset in [0, helix_height)
    auto_scroll_offset %= helix_height
    auto_twist_angle += auto_twist_speed


def draw_single_dna_segment(y_offset):
    total_points = helix_turns * helix_points_per_turn
    backbone1 = []
    backbone2 = []

    for i in range(total_points + 1):
        frac = i / float(total_points)
        angle = frac * helix_turns * 2.0 * math.pi
        # y from -H/2 to +H/2
        y = frac * helix_height - (helix_height / 2.0) + y_offset

        x1 = helix_radius * math.cos(angle)
        z1 = helix_radius * math.sin(angle)
        x2 = helix_radius * math.cos(angle + math.pi)
        z2 = helix_radius * math.sin(angle + math.pi)

        backbone1.append((x1, y, z1))
        backbone2.append((x2, y, z2))

    # Draw backbone #1
    glColor3f(0.8, 0.8, 0.0)  # yellow-ish
    glBegin(GL_LINE_STRIP)
    for (x, y, z) in backbone1:
        glNormal3f(0.0, 1.0, 0.0)  # Simple normal
        glVertex3f(x, y, z)
    glEnd()

    # Draw backbone #2
    glColor3f(0.0, 0.8, 0.8)  # cyan-ish
    glBegin(GL_LINE_STRIP)
    for (x, y, z) in backbone2:
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(x, y, z)
    glEnd()

    if texture_id is not None:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)

    glColor3f(1.0, 1.0, 1.0)  # White
    for i in range(0, total_points + 1, base_pair_step):
        x1, y1, z1 = backbone1[i]
        x2, y2, z2 = backbone2[i]

        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        rung_thickness = 0.05

        glBegin(GL_QUADS)
        # Bottom-left
        glNormal3f(0.0, 1.0, 0.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(x1, y1, z1)

        # Bottom-right
        glNormal3f(0.0, 1.0, 0.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(x2, y2, z2)

        # Top-right
        glNormal3f(0.0, 1.0, 0.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(x2, y2 + rung_thickness, z2)

        # Top-left
        glNormal3f(0.0, 1.0, 0.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(x1, y1 + rung_thickness, z1)
        glEnd()

    if texture_id is not None:
        glDisable(GL_TEXTURE_2D)


def draw_dna():
    num_strands = 3
    spacing = 3.0

    for strand_index in range(num_strands):
        glPushMatrix()
        offset_x = (strand_index - 1) * spacing
        glTranslatef(offset_x, 0.0, 0.0)

        for k in [-1, 0, 1]:
            seg_offset = auto_scroll_offset + k * helix_height
            draw_single_dna_segment(seg_offset)

        glPopMatrix()

def main():
    init_pygame_opengl()
    clock = pg.time.Clock()

    # Hide the mouse and grab it for dragging
    pg.mouse.set_visible(False)
    pg.event.set_grab(True)

    running = True
    while running:
        clock.tick(60)  # Aim for 60 FPS

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

        glRotatef(auto_twist_angle, 0.0, 1.0, 0.0)

        draw_dna()

        # Swap buffers
        pg.display.flip()

    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
