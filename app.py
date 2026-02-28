import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from geometry import get_mic_layout, get_polygon_data

st.set_page_config(page_title="Microphone Array Simulator", layout="wide")

# --- Hide Streamlit Header, Footer, and Profile ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("Microphone Array Simulator")

# --- Simple Design Parameters ---
if 'r_val' not in st.session_state:
    st.session_state.r_val = 50.0

if 'd_val' not in st.session_state:
    st.session_state.d_val = 100.0

if 'l_val' not in st.session_state:
    st.session_state.l_val = round(50.0 * np.sqrt(3), 2)

def update_from_r():
    st.session_state.d_val = st.session_state.r_val * 2.0
    st.session_state.l_val = round(st.session_state.r_val * np.sqrt(3), 2)

def update_from_d():
    st.session_state.r_val = st.session_state.d_val / 2.0
    st.session_state.l_val = round(st.session_state.r_val * np.sqrt(3), 2)

def update_from_l():
    st.session_state.r_val = st.session_state.l_val / np.sqrt(3)
    st.session_state.d_val = st.session_state.r_val * 2.0

col_r, col_d, col_l = st.columns(3)
with col_r:
    st.number_input("Radius R (mm)", min_value=0.5, step=0.5, key="r_val", on_change=update_from_r)

with col_d:
    st.number_input("Diameter D (mm)", min_value=1.0, step=1.0, key="d_val", on_change=update_from_d)

with col_l:
    st.number_input("Triangle side L (M1-M3-M5) [mm]", min_value=1.0, step=1.0, key="l_val", on_change=update_from_l)

# Final radius to use
final_r = st.session_state.r_val
mics = get_mic_layout(final_r)

# --- PDF Generation Function ---
def create_pdf_report(mics, r_val, d_val, shapes, polygon_func):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph(f"Microphone Array Simulator Report", styles['Title']))
    elements.append(Paragraph(f"Configuration: Radius R={r_val}mm, Diameter D={d_val}mm", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # 1. Main Layout Table
    elements.append(Paragraph("1. Microphone Coordinates (M1-M8)", styles['Heading2']))
    elements.append(Paragraph("System: X+ (Up), Y+ (Left)", styles['Italic']))
    
    coord_data = [["Mic", "X [mm]", "Y [mm]"]]
    for i, (mx, my) in enumerate(mics):
        coord_data.append([f"M{i+1}", f"{my:.4f}", f"{-mx:.4f}"])
    
    t = Table(coord_data, colWidths=[60, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ]))
    elements.append(t)
    elements.append(PageBreak())
    
    # 2. Sub-array Geometry Summary
    elements.append(Paragraph("2. Sub-array Analysis Summary", styles['Heading2']))
    summary_table_data = [["Shape", "Sides [mm]", "Angles [°]"]]
    for s in shapes:
        data = polygon_func(mics, s["indices"])
        sides_str = ", ".join([f"{x:.1f}" for x in data['sides']])
        angles_str = ", ".join([f"{x:.0f}" for x in data['angles']])
        summary_table_data.append([s["name"], sides_str, angles_str])
        
    t_sum = Table(summary_table_data, colWidths=[180, 150, 120])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT')
    ]))
    elements.append(t_sum)
    elements.append(PageBreak())

    # 3. Individual Plots (One per page or two per page)
    elements.append(Paragraph("3. Sub-array Plots", styles['Heading2']))
    for i, s in enumerate(shapes):
        elements.append(Paragraph(f"Shape {i+1}: {s['name']}", styles['Heading3']))
        
        # Create a temp figure for PDF
        tmp_fig, tmp_ax = plt.subplots(figsize=(4, 4))
        indices = s["indices"]
        data = polygon_func(mics, indices)
        circle_bg = plt.Circle((0, 0), r_val, color='lightgray', fill=False, linestyle='--')
        tmp_ax.add_patch(circle_bg)
        v = data['vertices']
        
        if indices == (0, 1, 2, 3, 4, 5): # Hexagon/Circle
            theta = np.linspace(0, 2*np.pi, 200)
            tmp_ax.plot(r_val * np.cos(theta), r_val * np.sin(theta), color='blue', lw=2)
        else:
            v_plot = np.concatenate((v, [v[0]]), axis=0)
            tmp_ax.plot(v_plot[:, 0], v_plot[:, 1], 'b-', lw=2)
            
        tmp_ax.scatter(v[:, 0], v[:, 1], color='black', s=40)
        tmp_ax.set_aspect('equal')
        tmp_ax.axis('off')
        
        img_buf = io.BytesIO()
        tmp_fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=100)
        plt.close(tmp_fig)
        
        img_buf.seek(0)
        elements.append(Image(img_buf, width=250, height=250))
        # Add page break every 2 plots to keep it neat
        if (i+1) % 2 == 0:
            elements.append(PageBreak())
        else:
            elements.append(Spacer(1, 20))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- Export Report Feature ---
st.subheader("📊 Report Center")
col_e1, col_e2 = st.columns(2)

with col_e1:
    if st.button("📄 Generate PDF Report (Stable Version)"):
        # Generate the PDF in background
        with st.spinner("Generating High-Quality PDF..."):
            pdf_buf = create_pdf_report(mics, final_r, st.session_state.d_val, shapes_to_show, get_polygon_data)
            st.download_button(
                label="⬇️ Download PDF Report",
                data=pdf_buf,
                file_name=f"MicArray_Report_D{st.session_state.d_val}mm.pdf",
                mime="application/pdf"
            )
            st.success("PDF Ready! Click the download button.")

with col_e2:
    if st.button("🖨️ Browser Printing Mode (Alt)"):
        st.info("ℹ️ To save: 1. Press **Ctrl + P** (Win) or **Cmd + P** (Mac) manually. 2. Set 'Destination' to 'Save as PDF'.")
        # Simplify page for printing and force page breaks correctly
        print_styles = """
            <style>
                @media print {
                    /* Hide navigation, buttons and extra UI */
                    .stButton, header, footer, [data-testid="stToolbar"], .stInfo, [data-testid="stExpander"], #MainMenu {
                        display: none !important;
                    }
                    /* Reset page margins and container width */
                    .main .block-container {
                        padding-top: 10mm !important;
                        padding-bottom: 10mm !important;
                        max-width: 100% !important;
                    }
                }
            </style>
        """
        st.markdown(print_styles, unsafe_allow_html=True)
        st.success("✅ Layout optimized. Please use your browser's print shortcut (Cmd+P or Ctrl+P).")

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
    ax_layout.annotate('', xy=(0, lim_layout*0.8), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1.5, color='red'))
    ax_layout.annotate('', xy=(lim_layout*0.8, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1.5, color='red'))

    ax_layout.set_title("Microphone Array Layout", fontsize=14)
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

# Move the duplicate report block at the top if it exists
# (Already handled by the previous replacement)

st.success("All 12 shapes and precision coordinates are ready.")

# Quick Re-trigger Button at the bottom for convenience
if st.button("📄 Print Page as Report", key="bottom_print_btn"):
    components.html("<script>window.print();</script>", height=0)
