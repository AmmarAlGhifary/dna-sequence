import pygame as pg
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

def constants() -> None:
    global WIDTH, HEIGHT
    WIDTH = 800
    HEIGHT = 600

class VBO:
    def __init__(self, vertices, normals=None):
        self.vertex_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        self.normal_vbo = None
        if normals is not None:
            self.normal_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.normal_vbo)
            glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
    
    def delete(self):
        glDeleteBuffers(1, [self.vertex_vbo])
        if self.normal_vbo:
            glDeleteBuffers(1, [self.normal_vbo])

def generate_helix_cylinders(num_segments=100, radius=0.3, helix_radius=1.5):
    vertices = []
    normals = []
    
    for i in range(num_segments):
        angle = 2 * np.pi * i / num_segments
        y = -i * 0.1
        
        # Helix direction vector
        dx = -helix_radius * np.sin(angle)
        dz = helix_radius * np.cos(angle)
        direction = np.array([dx, 0, dz])
        direction /= np.linalg.norm(direction)
        
        # Create circle around helix path
        for circle_angle in np.linspace(0, 2*np.pi, 16):
            cx = radius * np.cos(circle_angle)
            cz = radius * np.sin(circle_angle)
            
            # Calculate vertex position
            vertex = np.array([
                helix_radius * np.cos(angle) + cx * direction[0],
                y,
                helix_radius * np.sin(angle) + cx * direction[2]
            ])
            
            # Normal calculation
            normal = vertex - np.array([helix_radius * np.cos(angle), y, helix_radius * np.sin(angle)])
            normal /= np.linalg.norm(normal)
            
            vertices.append(vertex)
            normals.append(normal)
    
    return np.array(vertices, dtype=np.float32), np.array(normals, dtype=np.float32)

def draw_helix(vbo, num_vertices):
    # Set material properties
    glMaterialfv(GL_FRONT, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
    glMaterialfv(GL_FRONT, GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0))
    glMaterialfv(GL_FRONT, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
    glMaterialf(GL_FRONT, GL_SHININESS, 50.0)

    # Bind and draw VBO
    glBindBuffer(GL_ARRAY_BUFFER, vbo.vertex_vbo)
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, None)
    
    if vbo.normal_vbo:
        glBindBuffer(GL_ARRAY_BUFFER, vbo.normal_vbo)
        glEnableClientState(GL_NORMAL_ARRAY)
        glNormalPointer(GL_FLOAT, 0, None)
    
    glDrawArrays(GL_TRIANGLE_STRIP, 0, num_vertices)
    
    glDisableClientState(GL_VERTEX_ARRAY)
    if vbo.normal_vbo:
        glDisableClientState(GL_NORMAL_ARRAY)

def main():
    pg.init()
    constants()
    
    screen = pg.display.set_mode((WIDTH, HEIGHT), pg.OPENGL | pg.DOUBLEBUF)
    pg.display.set_caption("DNA Helix Visualization")

    # Projection setup
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, WIDTH/HEIGHT, 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    
    # OpenGL configuration
    glEnable(GL_DEPTH_TEST)
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glShadeModel(GL_SMOOTH)
    
    # Lighting setup
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 5.0, 5.0, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

    # Generate geometry
    vertices, normals = generate_helix_cylinders()
    vbo = VBO(vertices, normals)
    num_vertices = len(vertices)

    # Animation variables
    rotation = [0, 0]
    animation_speed = 0.05
    current_offset = 0.0
    zoom = -5.0

    clock = pg.time.Clock()
    running = True
    
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT: rotation[1] -= 5
                elif event.key == pg.K_RIGHT: rotation[1] += 5
                elif event.key == pg.K_UP: rotation[0] -= 5
                elif event.key == pg.K_DOWN: rotation[0] += 5
                elif event.key == pg.K_z: zoom += 0.5
                elif event.key == pg.K_x: zoom -= 0.5
                elif event.key == pg.K_SPACE: 
                    animation_speed = 0 if animation_speed else 0.05

        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera setup
        glTranslatef(0.0, 0.0, zoom)
        glRotatef(rotation[0], 1, 0, 0)
        glRotatef(rotation[1], 0, 1, 0)
        glTranslatef(0.0, current_offset, 0.0)

        # Draw helix
        draw_helix(vbo, num_vertices)

        # Update animation
        current_offset += animation_speed

        pg.display.flip()
        clock.tick(60)

    vbo.delete()
    pg.quit()

if __name__ == "__main__":
    main()