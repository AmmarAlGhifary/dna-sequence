import pygame as pg
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

def constants():
    """Window dimensions."""
    global WIDTH, HEIGHT
    WIDTH = 800
    HEIGHT = 600

class VBO:
    def __init__(self, vertices, normals, indices):
        self.vertex_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        self.normal_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.normal_vbo)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)

        self.index_vbo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_vbo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        self.num_indices = len(indices)

    def delete(self):
        glDeleteBuffers(1, [self.vertex_vbo])
        glDeleteBuffers(1, [self.normal_vbo])
        glDeleteBuffers(1, [self.index_vbo])

def normalize(v):
    return v / np.linalg.norm(v)

def generate_small_cylinder(p1, p2, radius=0.02, sides=8):
    # Direction vector
    d = p2 - p1
    length = np.linalg.norm(d)
    if length < 1e-8:
        # Degenerate case: points are the same
        return np.array([], dtype=np.float32), np.array([], dtype=np.float32), np.array([], dtype=np.uint32)

    d_hat = d / length

    up = np.array([0, 1, 0], dtype=np.float32)
    if np.abs(np.dot(d_hat, up)) > 0.99:
        up = np.array([1, 0, 0], dtype=np.float32)

    N = normalize(np.cross(d_hat, up))
    B = normalize(np.cross(d_hat, N))

    vertices = []
    normals  = []
    indices  = []

    ring0_start_index = 0
    ring1_start_index = sides  # after ring0

    # For each side, place a vertex
    for i in range(sides):
        theta = 2.0 * np.pi * i / sides
        offset = radius * (np.cos(theta) * N + np.sin(theta) * B)
        # ring0 vertex
        v0 = p1 + offset
        # ring1 vertex
        v1 = p2 + offset

        vertices.append(v0)
        vertices.append(v1)

    for i in range(sides):
        theta = 2.0 * np.pi * i / sides
        offset_dir = normalize(np.cos(theta) * N + np.sin(theta) * B)
        normals.append(offset_dir)
        normals.append(offset_dir)

    for i in range(sides):
        i_next = (i + 1) % sides
        v0  = ring0_start_index + 2*i
        v0n = ring0_start_index + 2*i_next
        v1  = ring1_start_index + 2*i
        v1n = ring1_start_index + 2*i_next

        indices += [v0, v0n, v1,
                    v0n, v1n, v1]

    return (np.array(vertices, dtype=np.float32),
            np.array(normals,  dtype=np.float32),
            np.array(indices,  dtype=np.uint32))

def generate_dna(num_segments=40,
                 helix_radius=0.5,
                 strand_thickness=0.03,
                 ring_sides=8,
                 num_turns=5,
                 vertical_spacing=0.1,
                 rung_gap=5,
                 rung_radius=0.02):
    
    total_segments = num_segments * num_turns
    dtheta = 2.0 * np.pi * num_turns / total_segments

    def build_strand(phase_offset=0.0):
        strand_vertices = []
        strand_normals  = []
        # We'll store the center positions at each step so we can place rungs later
        center_positions = []

        for i in range(total_segments + 1):
            theta = i * dtheta + phase_offset
            # Helix center
            center = np.array([
                helix_radius * np.cos(theta),
                -i * vertical_spacing,
                helix_radius * np.sin(theta)
            ], dtype=np.float32)

            center_positions.append(center)

        ring_list_vs = []
        ring_list_ns = []

        for i in range(total_segments + 1):
            # center i
            c_i = center_positions[i]

            # Approx tangent by difference to next center (or prev if at the end)
            if i < total_segments:
                c_next = center_positions[i + 1]
                T = c_next - c_i
            else:
                c_prev = center_positions[i - 1]
                T = c_i - c_prev

            T = normalize(T)

            # Build normal frame
            up = np.array([0, 1, 0], dtype=np.float32)
            # If T is nearly parallel to up, pick another
            if np.abs(np.dot(T, up)) > 0.99:
                up = np.array([1, 0, 0], dtype=np.float32)

            N = normalize(np.cross(T, up))
            B = normalize(np.cross(T, N))

            ring_vs = []
            ring_ns = []
            for j in range(ring_sides):
                phi = 2.0 * np.pi * j / ring_sides
                offset = strand_thickness * (np.cos(phi) * N + np.sin(phi) * B)
                pos = c_i + offset
                ring_vs.append(pos)
                ring_ns.append(normalize(offset))  # outward normal

            ring_list_vs.append(ring_vs)
            ring_list_ns.append(ring_ns)

        # Flatten ring data
        flat_vs = []
        flat_ns = []
        for ring_vs, ring_ns in zip(ring_list_vs, ring_list_ns):
            for v in ring_vs:
                flat_vs.append(v)
            for n in ring_ns:
                flat_ns.append(n)

        # Build indices
        indices = []
        for i in range(total_segments):
            ring_start = i * ring_sides
            next_ring  = (i + 1) * ring_sides
            for j in range(ring_sides):
                j_next = (j + 1) % ring_sides
                c_j   = ring_start + j
                c_j1  = ring_start + j_next
                n_j   = next_ring  + j
                n_j1  = next_ring  + j_next
                indices += [c_j, c_j1, n_j,
                            c_j1, n_j1, n_j]

        return (np.array(flat_vs, dtype=np.float32),
                np.array(flat_ns, dtype=np.float32),
                np.array(indices, dtype=np.uint32),
                np.array(center_positions, dtype=np.float32))

    # Build the two strands
    strand1_vs, strand1_ns, strand1_idx, centers1 = build_strand(phase_offset=0.0)
    strand2_vs, strand2_ns, strand2_idx, centers2 = build_strand(phase_offset=np.pi)

    # Now we offset strand2’s indices
    offset_strand2 = strand1_vs.shape[0]  # number of vertices in strand1
    strand2_idx = strand2_idx + offset_strand2

    rung_vs_total = []
    rung_ns_total = []
    rung_idx_total = []
    current_vertex_offset = offset_strand2 + strand2_vs.shape[0]

    for i in range(0, total_segments + 1, rung_gap):
        p1 = centers1[i]
        p2 = centers2[i]
        rung_vs, rung_ns, rung_idx = generate_small_cylinder(p1, p2, radius=rung_radius, sides=8)
        # Shift rung_idx by the current vertex offset
        rung_idx += current_vertex_offset

        rung_vs_total.append(rung_vs)
        rung_ns_total.append(rung_ns)
        rung_idx_total.append(rung_idx)

        current_vertex_offset += rung_vs.shape[0]  # advance for next rung

    if len(rung_vs_total) > 0:
        rung_vs_total = np.concatenate(rung_vs_total, axis=0)
        rung_ns_total = np.concatenate(rung_ns_total, axis=0)
        rung_idx_total = np.concatenate(rung_idx_total, axis=0)
    else:
        # No rungs if rung_gap is invalid
        rung_vs_total = np.array([], dtype=np.float32)
        rung_ns_total = np.array([], dtype=np.float32)
        rung_idx_total = np.array([], dtype=np.uint32)

    # Combine all geometry
    combined_vertices = np.concatenate((strand1_vs, strand2_vs, rung_vs_total), axis=0)
    combined_normals  = np.concatenate((strand1_ns, strand2_ns, rung_ns_total), axis=0)
    combined_indices  = np.concatenate((strand1_idx, strand2_idx, rung_idx_total), axis=0)

    return combined_vertices, combined_normals, combined_indices

def draw_dna(vbo):
    # Simple material
    glMaterialfv(GL_FRONT, GL_AMBIENT,  (0.1, 0.1, 0.1, 1.0))
    glMaterialfv(GL_FRONT, GL_DIFFUSE,  (0.7, 0.7, 0.7, 1.0))
    glMaterialfv(GL_FRONT, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
    glMaterialf(GL_FRONT, GL_SHININESS, 50.0)

    # Bind vertex data
    glBindBuffer(GL_ARRAY_BUFFER, vbo.vertex_vbo)
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, None)

    # Bind normal data
    glBindBuffer(GL_ARRAY_BUFFER, vbo.normal_vbo)
    glEnableClientState(GL_NORMAL_ARRAY)
    glNormalPointer(GL_FLOAT, 0, None)

    # Bind index data
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo.index_vbo)
    glDrawElements(GL_TRIANGLES, vbo.num_indices, GL_UNSIGNED_INT, None)

    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_NORMAL_ARRAY)

def main():
    pg.init()
    constants()

    screen = pg.display.set_mode((WIDTH, HEIGHT), pg.OPENGL | pg.DOUBLEBUF)
    pg.display.set_caption("Basic DNA Visualization")

    # Projection
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, WIDTH / HEIGHT, 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_DEPTH_TEST)
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glShadeModel(GL_SMOOTH)

    # Lighting
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 5.0, 5.0, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT,  (0.2, 0.2, 0.2, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  (0.8, 0.8, 0.8, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

    vertices, normals, indices = generate_dna(
        num_segments=40,       # segments per turn
        helix_radius=0.5,      # distance from axis to each strand
        strand_thickness=0.03, # thickness of each strand
        ring_sides=8,
        num_turns=5,
        vertical_spacing=0.08,
        rung_gap=5,            # a rung every 5 segments
        rung_radius=0.02       # thickness of the rung cylinders
    )
    vbo = VBO(vertices, normals, indices)

    rotation = [0.0, 0.0]   # x, y rotation
    animation_speed = 0.02
    current_offset  = 0.0
    zoom = -6.0

    clock = pg.time.Clock()
    running = True

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    rotation[1] -= 5
                elif event.key == pg.K_RIGHT:
                    rotation[1] += 5
                elif event.key == pg.K_UP:
                    rotation[0] -= 5
                elif event.key == pg.K_DOWN:
                    rotation[0] += 5
                elif event.key == pg.K_z:
                    zoom += 0.5
                elif event.key == pg.K_x:
                    zoom -= 0.5
                elif event.key == pg.K_SPACE:
                    animation_speed = 0.0 if animation_speed != 0 else 0.02

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glTranslatef(0.0, 0.0, zoom)
        glRotatef(rotation[0], 1, 0, 0)
        glRotatef(rotation[1], 0, 1, 0)

        glTranslatef(0.0, current_offset, 0.0)

        draw_dna(vbo)

        current_offset += animation_speed
        if current_offset > 10.0:
            current_offset = 0.0

        pg.display.flip()
        clock.tick(60)

    vbo.delete()
    pg.quit()

if __name__ == "__main__":
    main()
