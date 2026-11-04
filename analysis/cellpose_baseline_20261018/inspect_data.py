from pathlib import Path
import json
import numpy as np
import tifffile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SOURCE = Path(r'C:\Users\spraman\Desktop\Jeff\neuron_imaging\Imaging\20261018_FP_autofocus_test_002')
OUT = Path(__file__).parent
seq = json.loads((SOURCE / 'useq-sequence.json').read_text())
fig, axes = plt.subplots(5, 3, figsize=(12, 19))
records = []
for row, idx in enumerate([4, 13, 22, 31, 40]):
    path = SOURCE / 'images' / f'images_p{idx:03d}.ome.tiff'
    with tifffile.TiffFile(path) as tif:
        a = tif.series[0].asarray()
        print(path.name, a.shape, tif.series[0].axes, flush=True)
    for c, name in enumerate(['BF', 'DAPI membrane', 'GFP nuclei']):
        lo, hi = np.percentile(a[c], [1, 99])
        axes[row,c].imshow(a[c], cmap='gray', vmin=lo, vmax=hi)
        axes[row,c].set_title(f'{seq["stage_positions"][idx]["name"]} | {name}')
        axes[row,c].axis('off')
        records.append(dict(position=idx, channel=name, p1=float(lo), p99=float(hi)))
fig.tight_layout()
fig.savefig(OUT / 'channel_overview.png', dpi=120)
(OUT/'inspection.json').write_text(json.dumps(records, indent=2))
