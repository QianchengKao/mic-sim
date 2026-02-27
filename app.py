import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from geometry import get_mic_layout, get_polygon_data

st.set_page_config(page_title="Microphone Array Simulator", layout="wide")

st.title("Microphone Array Simulator")

# --- Export Report Feature ---
if st.button("📄 Export Report (Print as PDF)"):
    # Inject CSS to hide Streamlit header, footer, and buttons during print
    print_styles = """
    <style>
        @media print {
            .stButton, header, footer, [data-testid="stToolbar"], .stInfo {
                display: none !important;
            }
            .main {
                padding-top: 0 !important;
            }
        }
    </style>
    <script>window.print();</script>
    """
    components.html(print_styles, height=0)
    st.info("💡 Tip: Select 'Save as PDF' in the browser Print destination. (Some browsers need a click inside the page first)")

# --- Simple Design Parameters ---
# Use session state for R to maintain D=2R relationship
if 'r_val' not in st.session_state:
    st.session_state.r_val = 50.0

if 'd_val' not in st.session_state:
    st.session_state.d_val = 100.0

def update_r_from_d():
    st.session_state.r_val = st.session_state.d_val / 2.0

def update_d_from_r():
    st.session_state.d_val = st.session_state.r_val * 2.0

col_r, col_d = st.columns(2)
with col_r:
    st.number_input("Radius R (mm)", min_value=0.5, step=0.5, key="r_val", on_change=update_d_from_r)

with col_d:
    st.number_input("Diameter D (mm)", min_value=1.0, step=1.0, key="d_val", on_change=update_r_from_d)

# Final radius to use
final_r = st.session_state.r_val
mics = get_mic_layout(final_r)

# --- Array Layout Diagram & Coordinates ---
st.subheader("Microphone Array Layout & Coordinates")
col_plot, col_table = st.columns([1.2, 1])

with col_plot:
    # Scale down the figure slightly
    fig_layout, ax_layout = plt.subplots(figsize=(5, 5))
    circle_ref = plt.Circle((0, 0), final_r, color='lightgray', fill=False, linestyle='--')
    ax_layout.add_patch(circle_ref)
    ax_layout.scatter(mics[:, 0], mics[:, 1], color='blue', s=80, zorder=5)
    for i, (mx, my) in enumerate(mics):
        ax_layout.text(mx + 0.05*final_r, my + 0.05*final_r, f"M{i+1}", fontsize=10, weight='bold')

    # Helper lines for extensions
    ax_layout.plot([mics[4][0], mics[6][0]], [mics[4][1], mics[6][1]], 'g--', alpha=0.5)
    ax_layout.plot([mics[2][0], mics[7][0]], [mics[2][1], mics[7][1]], 'm--', alpha=0.5)

    ax_layout.set_aspect('equal')
    lim_layout = final_r * 2.5
    ax_layout.set_xlim(-lim_layout, lim_layout)
    ax_layout.set_ylim(-lim_layout, lim_layout)
    
    # Visual cues for the custom coordinate system (X-up, Y-left)
    # Note: In standard plot, Up is +Y_std, Left is -X_std
    ax_layout.annotate('', xy=(0, lim_layout*0.8), xytext=(0, 0), arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))
    ax_layout.text(0, lim_layout*0.85, "X (Up)", ha='center', fontsize=9, color='gray')
    ax_layout.annotate('', xy=(-lim_layout*0.8, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))
    ax_layout.text(-lim_layout*0.85, 0, "Y (Left)", ha='right', va='center', fontsize=9, color='gray')
    
    ax_layout.axis('off')
    st.pyplot(fig_layout)

with col_table:
    st.markdown("##### Mic Coordinates (mm)")
    st.caption("Coordinate System: **X+ (Up)** = Standard Y | **Y+ (Left)** = Standard -X")
    coord_list = []
    for i, (mx, my) in enumerate(mics):
        # User X is UP (standard Y), User Y is LEFT (standard -X)
        user_x = my
        user_y = -mx
        coord_list.append({
            "Mic": f"M{i+1}",
            "X [mm]": round(user_x, 6),
            "Y [mm]": round(user_y, 6)
        })
    st.table(coord_list)
    
    # Export 8-Mic coordinates
    df_8mic = pd.DataFrame(coord_list)
    csv_8mic = df_8mic.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download M1-M8 CSV",
        data=csv_8mic,
        file_name=f"mic_layout_R{final_r}.csv",
        mime="text/csv",
    )
    
    with st.expander("Python Format (M1-M8)"):
        # Format for copy-paste to code
        points = [[round(my, 6), round(-mx, 6)] for mx, my in mics]
        st.code(f"mics_1_8 = {points}", language='python')

# --- Define the 11-12 Shapes ---
shapes_to_show = [
    # Row 1 (3 items)
    {"indices": (0, 2, 4), "name": "M1-M3-M5 Triangle"},
    {"indices": (4, 6, 0), "name": "M5-M7-M1 Triangle"},
    {"indices": (0, 1, 5), "name": "M1-M2-M6 Triangle"},
    # Row 2 (3 items)
    {"indices": (2, 4, 6, 7), "name": "M3-M5-M7-M8 Square"},
    {"indices": (2, 4, 5, 1), "name": "M3-M5-M6-M2 Rectangle"},
    {"indices": (0, 1, 2, 3, 4, 5), "name": "M1-M2-M3-M4-M5-M6 Hexagon"},
    # Row 3 (3 items: 125, 267, 167)
    {"indices": (0, 1, 4), "name": "M1-M2-M5 Triangle"},
    {"indices": (1, 5, 6), "name": "M2-M6-M7 Triangle"},
    {"indices": (0, 5, 6), "name": "M1-M6-M7 Triangle"},
    # Row 4 (3 items: 127, 137, 147)
    {"indices": (0, 1, 6), "name": "M1-M2-M7 Triangle"},
    {"indices": (0, 2, 6), "name": "M1-M3-M7 Triangle"},
    {"indices": (0, 3, 6), "name": "M1-M4-M7 Triangle"},
]

def plot_shape_to_col(st_col, shape_meta, mics, r_val):
    with st_col:
        indices = shape_meta["indices"]
        t_data = get_polygon_data(mics, indices)
        
        fig, ax = plt.subplots(figsize=(4, 4))
        circle_bg = plt.Circle((0, 0), r_val, color='lightgray', fill=False, linestyle='--', alpha=0.5)
        ax.add_patch(circle_bg)
        
        v_coords = t_data['vertices']
        num_v = len(indices)

        # Special handling for M1-M6 Hexagon/Circle to use ARCS
        is_hexagon_circle = (indices == (0, 1, 2, 3, 4, 5))
        
        if is_hexagon_circle:
            # Draw as smooth arcs on the circle
            theta = np.linspace(0, 2*np.pi, 200)
            ax.plot(r_val * np.cos(theta), r_val * np.sin(theta), color='steelblue', linewidth=2.5, zorder=3)
        else:
            # Draw as standard polygon with straight lines
            v_closed = np.concatenate((v_coords, [v_coords[0]]), axis=0)
            ax.plot(v_closed[:, 0], v_closed[:, 1], color='steelblue', linestyle='-', linewidth=2.5, zorder=3)
        
        ax.scatter(v_coords[:, 0], v_coords[:, 1], color='black', s=60, zorder=5)
        
        # Labels for Mic numbers
        for idx, m_idx in enumerate(indices):
            vx, vy = v_coords[idx]
            norm = np.linalg.norm([vx, vy])
            shift = (np.array([vx, vy]) / norm) * 0.15 * r_val if norm > 1e-6 else np.array([0, 0.15 * r_val])
            ax.text(vx + shift[0], vy + shift[1], f"M{m_idx+1}", 
                    color='black', ha='center', va='center', fontweight='bold', fontsize=11)
            
            center = np.mean(v_coords, axis=0)
            angle_pos = np.array([vx, vy]) + (center - [vx, vy]) * 0.25
            ax.text(angle_pos[0], angle_pos[1], f"{t_data['angles'][idx]:.0f}°", 
                    color='green', fontweight='bold', fontsize=10, ha='center', va='center',
                    bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', pad=1))

        # Side lengths (Chord lengths)
        sides = t_data['sides']
        v_closed = np.concatenate((v_coords, [v_coords[0]]), axis=0)
        for k in range(num_v):
            p1, p2 = v_closed[k], v_closed[k+1]
            mid = (p1 + p2) / 2
            
            # For the circle, we place the label slightly outside the arc
            edge_vector = p2 - p1
            if np.linalg.norm(edge_vector) > 1e-6:
                perp_vector = np.array([-edge_vector[1], edge_vector[0]]) 
                perp_vector = perp_vector / np.linalg.norm(perp_vector)
                # Ensure it's pointing outward
                center = np.mean(v_coords, axis=0)
                if np.dot(perp_vector, mid - center) < 0:
                    perp_vector = -perp_vector
                
                # If it's the circle, push label further out to not touch the arc
                offset = 0.15 if is_hexagon_circle else 0.12
                label_pos = mid + perp_vector * offset * r_val
            else:
                label_pos = mid
            
            ax.text(label_pos[0], label_pos[1], f"{sides[k]:.1f}", 
                    color='red', fontsize=11, fontweight='bold', ha='center', va='center',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2))
        
        ax.set_aspect('equal')
        v_x, v_y = v_coords[:, 0], v_coords[:, 1]
        cx, cy = (np.min(v_x) + np.max(v_x)) / 2, (np.min(v_y) + np.max(v_y)) / 2
        span = max(np.max(v_x) - np.min(v_x), np.max(v_y) - np.min(v_y))
        limit_half = max(span * 0.75, r_val * 0.5)
        ax.set_xlim(cx - limit_half, cx + limit_half)
        ax.set_ylim(cy - limit_half, cy + limit_half)
        ax.set_title(shape_meta["name"], fontsize=12)
        ax.axis('off')
        st.pyplot(fig)

st.divider()
st.subheader("Sub-array Analysis")

# Row 1 (3 items)
cols1 = st.columns(3)
for i in range(3):
    plot_shape_to_col(cols1[i], shapes_to_show[i], mics, final_r)

# Row 2 (3 items)
cols2 = st.columns(3)
for i in range(3):
    plot_shape_to_col(cols2[i], shapes_to_show[i+3], mics, final_r)

# Row 3 (3 items)
cols3 = st.columns(3)
for i in range(3):
    plot_shape_to_col(cols3[i], shapes_to_show[i+6], mics, final_r)

# Row 4 (3 items)
cols4 = st.columns(3)
for i in range(3):
    plot_shape_to_col(cols4[i], shapes_to_show[i+9], mics, final_r)

st.divider()
st.subheader("Sub-array Raw Coordinates (Copy-Paste Friendly)")

# Flattened data for easy copying to Excel/Code
flat_coord_data = []
for shape in shapes_to_show:
    indices = shape["indices"]
    for m_idx in indices:
        mx, my = mics[m_idx]
        # Coordinate System: X is UP (standard Y), Y is LEFT (standard -X)
        user_x = my
        user_y = -mx
        flat_coord_data.append({
            "Shape": shape["name"],
            "Mic": f"M{m_idx+1}",
            "X [mm]": round(user_x, 6),
            "Y [mm]": round(user_y, 6)
        })

# Use st.dataframe with column configuration for better width control
# This helps fit the data onto the page while maintaining readability
st.dataframe(
    flat_coord_data, 
    width='stretch',
    column_config={
        "Shape": st.column_config.TextColumn("Shape", width="medium"),
        "Mic": st.column_config.TextColumn("Mic", width="small"),
        "X [mm]": st.column_config.NumberColumn("X [mm]", format="%.6f", width="small"),
        "Y [mm]": st.column_config.NumberColumn("Y [mm]", format="%.6f", width="small"),
    }
)

# Show Python Code Format (Array of Arrays) in an expander
with st.expander("Show Python Code Format (Array of Arrays)"):
    # (Existing code for Python export)
    # ...
    code_str = "# Sub-array Coordinate Dictionary (X-Up, Y-Left)\n"
    code_str += "mic_configs = {\n"
    for shape in shapes_to_show:
        indices = shape["indices"]
        coords = []
        for m_idx in indices:
            mx, my = mics[m_idx]
            coords.append([round(my, 6), round(-mx, 6)]) # [X_up, Y_left]
        code_str += f"    '{shape['name']}': {coords},\n"
    code_str += "}"
    st.code(code_str, language='python')

st.divider()

# --- Summary Shape Table for the Report ---
st.subheader("Sub-array Geometry Summary (Sides & Angles)")
summary_data = []
for shape in shapes_to_show:
    indices = shape["indices"]
    data = get_polygon_data(mics, indices)
    summary_data.append({
        "Shape Name": shape["name"],
        "Side Lengths [mm]": ", ".join([f"{s:.1f}" for s in data['sides']]),
        "Interior Angles [°]": ", ".join([f"{a:.1f}" for a in data['angles']])
    })

st.table(summary_data)  # Use st.table for the printable report instead of st.dataframe

st.success("All 12 shapes and precision coordinates are ready.")

# Quick Re-trigger Button at the bottom for convenience
if st.button("📄 Print Page as Report"):
    components.html("<script>window.print();</script>", height=0)
