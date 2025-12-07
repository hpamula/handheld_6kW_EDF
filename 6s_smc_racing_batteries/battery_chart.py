import json
import re
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# 1. SETUP: Make sure this filename matches your actual file
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
    # Default to "?" if not found or text is weird
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
    
    # Power Factor Text
    pf_text = f"{pf_val}{phi_sym}"
    price_text = f"${int(price)}"
    
    # Final Label
    label_text = f"{short_name} {cap_short}{gamma_sym} {c_val}C {price_text} {pf_text}"

    points.append({
      'x': mah_per_mm3,
      'y': mah_per_g,
      'color': color,
      'marker': marker,
      'label': label_text
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

    for p in points:
      ax.scatter(p['x'], p['y'], c=p['color'], marker=p['marker'], s=150, alpha=0.8, edgecolors='white', linewidth=0.5)
      # Centered Alignment
      ax.annotate(p['label'], (p['x'], p['y']), 
            xytext=(0, 10), textcoords='offset points', 
            fontsize=10, color='white', linespacing=1.2,
            ha='center', va='bottom')

    ax.set_xlabel('Volumetric Density (mAh / mm³)', fontsize=14)
    ax.set_ylabel('Gravimetric Density (mAh / g)', fontsize=14)
    ax.set_title('SMC Battery Comparison', fontsize=16)

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

    ax.legend(handles=legend_elements, loc='upper left', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.2)
    plt.tight_layout()
    plt.savefig('battery_chart.png', dpi=600)
  except Exception as e:
    print(f"Error drawing chart: {e}")