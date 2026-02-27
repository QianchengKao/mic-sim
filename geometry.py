import numpy as np

def get_mic_layout(radius):
    """
    Returns the coordinates of the 8 mics based on the circle radius (D).
    1-6 are on the circle, clockwise starting from the top.
    7 is on the extension of 5-6 with a distance (sqrt(3)-1)D from 6.
    8 is on the extension of 3-2 with a distance (sqrt(3)-1)D from 2.
    """
    # 1-6 angles: 90deg, 30deg, -30deg, -90deg, -150deg, 150deg
    angles_deg = [90, 30, -30, -90, -150, 150]
    mics = []
    for angle in angles_deg:
        rad = np.radians(angle)
        mics.append(np.array([radius * np.cos(rad), radius * np.sin(rad)]))
    
    # Mic 7: extension of 5-6 (index 4 and 5)
    # distance 6-7 = (sqrt(3)-1)D
    m5 = mics[4]
    m6 = mics[5]
    dist_67 = (np.sqrt(3) - 1) * radius
    direction_56 = (m6 - m5) / np.linalg.norm(m6 - m5)
    m7 = m6 + direction_56 * dist_67
    mics.append(m7)
    
    # Mic 8: extension of 3-2 (index 2 and 1)
    m3 = mics[2]
    m2 = mics[1]
    direction_32 = (m2 - m3) / np.linalg.norm(m2 - m3)
    m8 = m2 + direction_32 * dist_67 # Using same distance
    mics.append(m8)
    
    return np.array(mics)

def get_triangles_from_mics(mics, combinations=None):
    """
    Generates triangles for the given combinations of mic indices.
    If combinations is None, maybe return all possible or some specific ones.
    """
    if combinations is None:
        # Default: just a few for demonstration
        import itertools
        combinations = list(itertools.combinations(range(len(mics)), 3))
    
    triangles = []
    for combo in combinations:
        v = mics[list(combo)] # v0, v1, v2
        
        # Side lengths:
        # a = v1-v2, b = v0-v2, c = v0-v1
        a = np.linalg.norm(v[2] - v[1])
        b = np.linalg.norm(v[2] - v[0])
        c = np.linalg.norm(v[1] - v[0])
        
        sides = [c, a, b] # side names: c(0-1), a(1-2), b(2-0)
        
        # Law of Cosines to get angle at vertex
        def get_angle(opp, adj1, adj2):
            if adj1*adj2 == 0: return 0
            val = (adj1**2 + adj2**2 - opp**2) / (2 * adj1 * adj2)
            return np.degrees(np.arccos(np.clip(val, -1, 1)))

        # angle0 is at v0 (between v0-v1 and v0-v2), opposite to side a
        angle0 = get_angle(a, b, c)
        # angle1 is at v1 (between v1-v0 and v1-v2), opposite to side b
        angle2 = get_angle(b, a, c)
        # angle2 is at v2 (between v2-v0 and v2-v1), opposite to side c
        angle3 = 180 - angle0 - angle2 # using angle3 as placeholder name
        
        angles = [angle0, angle2, angle3]
        
        # Consistent sorting for "equivalence" check (e.g., congruent triangles)
        sorted_sides = sorted([round(s, 2) for s in [a, b, c]])
        
        triangles.append({
            'indices': combo,
            'vertices': v,
            'sides': [c, a, b],
            'angles': angles,
            'sig': tuple(sorted_sides)
        })
    return triangles

def get_polygon_data(mics, indices):
    """
    Generic function to calculate sides and interior angles for any convex polygon.
    """
    v = mics[list(indices)]
    n = len(v)
    v_closed = np.concatenate((v, [v[0]]), axis=0)
    
    # Sides
    sides = []
    for i in range(n):
        sides.append(np.linalg.norm(v_closed[i+1] - v_closed[i]))
    
    # Angles (interior)
    angles = []
    for i in range(n):
        v_prev = v[i-1] # Wraps around to last
        v_curr = v[i]
        v_next = v[(i+1)%n]
        
        vec1 = v_prev - v_curr
        vec2 = v_next - v_curr
        
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1*norm2 == 0:
            angles.append(0)
        else:
            angle = np.degrees(np.arccos(np.clip(dot / (norm1 * norm2), -1, 1)))
            angles.append(angle)
            
    return {
        'indices': indices,
        'vertices': v,
        'sides': sides,
        'angles': angles
    }

def get_shapes_from_mics(mics, indices_list):
    """
    Returns data for polygons like quadrilaterals.
    """
    shapes = []
    for indices in indices_list:
        v = mics[list(indices)]
        
        # Calculate perimeter / segments
        closed_vertices = np.concatenate((v, [v[0]]), axis=0)
        sides = []
        for i in range(len(v)):
            sides.append(np.linalg.norm(closed_vertices[i+1] - closed_vertices[i]))
            
        shapes.append({
            'indices': indices,
            'vertices': v,
            'sides': sides
        })
    return shapes
