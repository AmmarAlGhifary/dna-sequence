import pygame as pg
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

def constants() -> None:
    global WIDTH, HEIGHT
    # Screen size
    WIDTH = 800
    HEIGHT = 600  # Reduced to 600 for a more typical aspect ratio

class VBO:
    def __init__(self, data):
        self.vbo_id = glGenBuffers(1)
        self.bind()
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
    
    def bind(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
    
    def unbind(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)
    
    def delete(self):
        glDeleteBuffers(1, [self.vbo_id])

def generate_helix_points(num_points=100, radius=1.5, twist=2.0):
    """
    Generates interleaved points for two helix strands.
    For each iteration i:
      - One point on the main strand (x1, y, z1)
      - One point on the complementary strand (x2, y, z2)
    Returns a NumPy array of shape (num_points*2, 3).
    """
    points = []
    for i in range(num_points):
        angle = i * twist * np.pi / num_points
        y = -i * 0.1 

        # Main strand
        x1 = radius * np.cos(angle)
        z1 = radius * np.sin(angle)
        
        x2 = radius * np.cos(angle + np.pi)
        z2 = radius * np.sin(angle + np.pi)
        
        points.extend([(x1, y, z1), (x2, y, z2)])
    
    return np.array(points, dtype=np.float32)

# Gambar helix pake VBO
# Diambil dari https://learnopengl.com/Getting-started/Hello-Triangle
def draw_helix(vbo, num_vertices):
    vbo.bind()
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, None)
    
    glColor3f(0, 0, 1)  # Blue color
    glDrawArrays(GL_LINE_STRIP, 0, num_vertices)
    
    glDisableClientState(GL_VERTEX_ARRAY)
    vbo.unbind()

def main():
    pg.init()
    constants()
    
    # Create an OpenGL-capable window
    screen = pg.display.set_mode((WIDTH, HEIGHT), pg.OPENGL | pg.DOUBLEBUF)
    pg.display.set_caption("DNA Helix Visualization")


    # -------- Codebase from https://learnopengl.com/Getting-started/Hello-Triangle
    # Pake ini untuk setup Matrix dan GL
    # ---- Setup Projection Matrix ----
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, WIDTH / HEIGHT, 0.1, 50.0)


    # ---- Setup Modelview Matrix ----
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    #Aktifin GL 
    glEnable(GL_DEPTH_TEST) 
    glClearColor(1.0, 1.0, 1.0, 1.0)
    # ---
 

    helix_points = generate_helix_points()
    vbo = VBO(helix_points)
    num_vertices = len(helix_points)

    rotation = [0, 0]
    animation_speed = 0.05 
    current_offset = 0.0

    clock = pg.time.Clock()
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key == pg.K_LEFT:
                    rotation[1] -= 5
                elif event.key == pg.K_RIGHT:
                    rotation[1] += 5
                elif event.key == pg.K_UP:
                    rotation[0] -= 5
                elif event.key == pg.K_DOWN:
                    rotation[0] += 5

        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Move camera/object
        glTranslatef(0.0, 0.0, -5.0)

        glTranslatef(0.0, current_offset, 0.0)

        # Apply any rotations from keyboard input
        glRotatef(rotation[0], 1, 0, 0) 
        glRotatef(rotation[1], 0, 1, 0) 

        draw_helix(vbo, num_vertices)

        current_offset += animation_speed

        pg.display.flip()

        clock.tick(60)

    # Cleanup
    vbo.delete()
    pg.quit()

if __name__ == "__main__":
    main()
