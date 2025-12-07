import json
import re
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.sparse.csgraph import minimum_spanning_tree
from sklearn.preprocessing import MinMaxScaler

# 1. SETUP
file_path = 'extracted_manual_scaled.json'

print(f"Attempting to load {file_path}...")

try:
  with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
  print(f"Successfully loaded {len(data)} rows.")
except Exception as e:
  print(f"CRITICAL ERROR loading file: {e}")
  data = []

points = []

# Mappings
category_map = {
  'HCL-EC': 'E',
  'HCL-HP': 'P',
  'HCL-HV2': 'V',
  'HCL-RS': 'R',
  'SRD-V4': 'S'
}

category_full_names = {
  'E': 'HCL-EC (Economy)',
  'P': 'HCL-HP (High Performance)',
  'V': 'HCL-HV2 (High Voltage)',
  'R': 'HCL-RS (Racing Series)',
  'S': 'SRD-V4 (Speedrun)'
}

def get_short_name(full_name):
  for key, short in category_map.items():
    if key in full_name:
      return short
  return '?'

print("Processing data rows...")

for i, row in enumerate(data):
  try:
    if len(row) < 11:
      continue

    # Extract fields
    name_str = row[0]
    price_str = row[1]
    avail_str = row[2]
    mah_str = row[4]
    c_rate_str = row[6]
    pf_str = row[7]
    size_str = row[8]
    weight_str = row[9]
    wire_str = row[10]

    # Parse numerical values
    dims = re.findall(r'(\d+(?:\.\d+)?)', size_str)
    if len(dims) < 3: 
      continue
    volume = float(dims[0]) * float(dims[1]) * float(dims[2])

    w_match = re.search(r'(\d+(?:\.\d+)?)', weight_str)
    if not w_match: continue
    weight = float(w_match.group(1))

    mah_match = re.search(r'(\d+)', mah_str)
    if not mah_match: continue
    mah = float(mah_match.group(1))

    price_match = re.search(r'(\d+(?:\.\d+)?)', price_str)
    price = float(price_match.group(1)) if price_match else 0

    # Power Factor Logic
    pf_val = "?"
    pf_match = re.search(r'^(\d+)', pf_str.strip())
    if pf_match: 
        pf_val = pf_match.group(1)

    # Wire
    wire_match = re.search(r'(\d+)', wire_str)
    wire_awg = int(wire_match.group(1)) if wire_match else 0
    
    # C-Rate
    c_match = re.search(r'(\d+)', c_rate_str)
    c_val = c_match.group(1) if c_match else "?"

    # Metrics
    mah_per_mm3 = mah / volume
    mah_per_g = mah / weight
    
    # Colors/Markers
    color = 'green' if 'In Stock' in avail_str else 'red'
    marker = 'o'
    if wire_awg == 8: marker = 'o'
    elif wire_awg == 10: marker = 's'
    elif wire_awg == 12: marker = '^'

    # Unicode Labels
    cap_short = int(mah / 100)
    short_name = get_short_name(name_str)
    gamma_sym = "\u03B3" 
    phi_sym = "\u03C6"
    
    pf_text = f"{pf_val}{phi_sym}"
    price_text = f"${int(price)}"
    
    # Final Label
    label_text = f"{short_name} {cap_short}{gamma_sym} {c_val}C {price_text} {pf_text}"

    points.append({
      'x': mah_per_mm3,
      'y': mah_per_g,
      'color': color,
      'marker': marker,
      'label': label_text,
      'category': short_name
    })

  except Exception as e:
    continue

if not points:
  print("ERROR: No valid data points.")
else:
  print(f"Generating chart with {len(points)} points...")
  try:
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(16, 14))

    # 1. DATA PREPARATION FOR NORMALIZATION
    # We need to normalize X and Y to 0-1 range so Euclidean distance matches visual distance
    all_x = np.array([p['x'] for p in points]).reshape(-1, 1)
    all_y = np.array([p['y'] for p in points]).reshape(-1, 1)
    
    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()
    
    all_x_norm = scaler_x.fit_transform(all_x)
    all_y_norm = scaler_y.fit_transform(all_y)
    
    # Update points with normalized coordinates for calculation (keep original for plotting)
    for i, p in enumerate(points):
        p['x_norm'] = all_x_norm[i][0]
        p['y_norm'] = all_y_norm[i][0]

    # 2. DRAW CONNECTIONS (MST on Normalized Data)
    cat_groups = {}
    for i, p in enumerate(points):
        cat = p['category']
        if cat not in cat_groups:
            cat_groups[cat] = []
        cat_groups[cat].append(i)

    for cat, indices in cat_groups.items():
        if len(indices) < 2:
            continue
        
        # Use NORMALIZED coordinates for distance calculation
        coords_norm = np.array([[points[i]['x_norm'], points[i]['y_norm']] for i in indices])
        
        # Compute MST on normalized data
        dists_matrix = squareform(pdist(coords_norm))
        mst = minimum_spanning_tree(dists_matrix)
        mst_coo = mst.tocoo()
        
        # Draw edges using ORIGINAL coordinates
        for j, k in zip(mst_coo.row, mst_coo.col):
            p1 = points[indices[j]]
            p2 = points[indices[k]]
            ax.plot([p1['x'], p2['x']], [p1['y'], p2['y']], 
                    color='white', alpha=0.7, linewidth=1, linestyle='-', zorder=1)

    # 3. DRAW POINTS & LABELS
    for p in points:
        ax.scatter(p['x'], p['y'], c=p['color'], marker=p['marker'], s=150, alpha=1, edgecolors='white', linewidth=0.5, zorder=3)
        ax.annotate(p['label'], (p['x'], p['y']), 
              xytext=(0, 10), textcoords='offset points', 
              fontsize=14, color='white', linespacing=1.2,
              ha='center', va='bottom', zorder=4)

    ax.set_xlabel('Volumetric Density (mAh / mm³)', fontsize=16)
    ax.set_ylabel('Gravimetric Density (mAh / g)', fontsize=16)
    ax.set_title('SMC Battery Comparison', fontsize=18)

    gamma_u = "\u03B3"
    phi_u = "\u03C6"

    legend_elements = [
      Line2D([], [], color='none', label=r'$\bf{Wire\ Size}$'),
      Line2D([0], [0], marker='o', color='w', label='8 AWG', markerfacecolor='gray', markersize=10),
      Line2D([0], [0], marker='s', color='w', label='10 AWG', markerfacecolor='gray', markersize=10),
      Line2D([0], [0], marker='^', color='w', label='12 AWG', markerfacecolor='gray', markersize=10),
      Line2D([], [], color='none', label=''), 
      Line2D([], [], color='none', label=r'$\bf{Availability}$'),
      Line2D([0], [0], marker='o', color='w', label='In Stock', markerfacecolor='green', markersize=10),
      Line2D([0], [0], marker='o', color='w', label='Out of Stock', markerfacecolor='red', markersize=10),
      Line2D([], [], color='none', label=''), 
      Line2D([], [], color='none', label=r'$\bf{Definitions}$'),
      Line2D([], [], color='none', label=f'{gamma_u}: Capacity / 100'),
      Line2D([], [], color='none', label=f'{phi_u}: Power Factor'),
      Line2D([], [], color='none', label=''), 
      Line2D([], [], color='none', label=r'$\bf{Categories}$'),
      Line2D([], [], color='none', label=f"E: {category_full_names['E']}"),
      Line2D([], [], color='none', label=f"P: {category_full_names['P']}"),
      Line2D([], [], color='none', label=f"V: {category_full_names['V']}"),
      Line2D([], [], color='none', label=f"R: {category_full_names['R']}"),
      Line2D([], [], color='none', label=f"S: {category_full_names['S']}"),
    ]

    ax.legend(handles=legend_elements, loc='upper left', fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig('clustered_battery_chart.png', dpi=600)
  except Exception as e:
    print(f"Error drawing chart: {e}")