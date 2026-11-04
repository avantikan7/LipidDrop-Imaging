from pathlib import Path
import json
import numpy as np
import tifffile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from skimage.segmentation import find_boundaries
from run_baseline import ROOT,SOURCE,norm,seq

OUT=ROOT/'tuned_bf'

def example():
    a=tifffile.imread(SOURCE/'images'/'images_p004.ome.tiff')
    m=tifffile.imread(OUT/'p004_full_selected_masks.tif')
    edge=find_boundaries(m,mode='inner')
    bf=np.repeat(norm(a[0])[...,None],3,axis=-1)
    fl=np.stack([norm(a[1]),norm(a[2]),np.zeros(a.shape[1:])],axis=-1)
    fig,axs=plt.subplots(2,3,figsize=(12,8),layout='constrained')
    for row,(y,x,label) in enumerate([(128,640,'Less crowded region'),(512,256,'Crowded region')]):
        sl=np.s_[y:y+256,x:x+256]
        images=[bf[sl].copy(),fl[sl].copy(),bf[sl].copy()]
        for i in [1,2]:images[i][edge[sl]]=[0,1,1]
        for col,image in enumerate(images):
            axs[row,col].imshow(image);axs[row,col].axis('off')
            axs[row,col].set_title(['BF reference','Fluorescence + outlines','Same outlines on BF'][col])
        axs[row,0].text(0,1.12,label,transform=axs[row,0].transAxes,weight='bold')
    fig.suptitle('D5: membrane red, nuclei green, segmentation cyan | selected settings')
    fig.savefig(OUT/'interpretation_examples.png',dpi=160);plt.close(fig)

def report():
    rows=json.loads((OUT/'full_results.json').read_text())
    table=''.join('<tr><td>'+seq['stage_positions'][p]['name']+'</td>'+''.join('<td>'+str(next(r['count'] for r in rows if r['position']==p and r['variant']==v))+'</td>' for v in ['default','selected'])+'</tr>' for p in [4,13,22,31,40])
    text='''<!doctype html><html><head><meta charset="utf-8"><title>GFP + DAPI masks on BF</title><style>body{font:17px/1.55 system-ui,sans-serif;max-width:1400px;margin:35px auto;padding:0 24px;color:#24303b}img{max-width:100%}td,th{padding:10px 24px;border:1px solid #ccd4db}table{border-collapse:collapse}a{color:#1265a8}code{font-size:15px}</style></head><body>
<h1>GFP + DAPI segmentation, viewed on BF</h1>
<p>Selected working settings: <b>128-pixel local normalization, cellprob_threshold=0, flow_threshold=0.6, diameter unset, min_size=15</b>. Model weights remain the pretrained cpsam_v2 weights; no training was performed. This is a visually selected compromise, not a measured optimum.</p>
<p>The masks mainly identify nuclear-centered cell-body candidates. They do not describe complete neurons, assign crossing neurites to individual cells, or establish a validated cell count. In dense areas, some masks can contain multiple nuclear candidates and some boundaries remain ambiguous.</p>
<h2>How to read the overlay</h2><p>Cyan lines are segmentation boundaries inferred from DAPI + GFP only; BF was not supplied to the model. Fluorescence is shown as membrane red and nuclei green. Compare an outline with both the BF cell-body appearance and the nuclear location. A larger region is not necessarily a better cell boundary. The three channels use the original acquisition coordinates; no registration correction or distortion correction was applied.</p>
<img src="interpretation_examples.png" alt="BF and fluorescence examples with identical segmentation outlines">
<h2>Parameter comparison and choice</h2>
<p>Tested 24 combinations per crop: native resolution, diameter 45 px, diameter 60 px, or local normalization 128 px; cell probability thresholds -2, 0, 2; flow thresholds 0.4 and 0.8. Refined native and local-normalization candidates with thresholds -1 and 0 and flow 0.6, with repeated 0/0.4 controls. This gives 28 unique combinations on each of two central crops (p004, p031). The other full fields were not used to select settings.</p>
<p>Negative thresholds admitted broad extensions and more potential merges in crowded regions. Threshold +2 contracted masks toward nuclei. The 45/60-pixel diameter settings often produced compact regions and did not solve neurite segmentation. Local normalization recovered additional body candidates in uneven fluorescence; flow 0.6 preserved more candidates than 0.4 without using the most permissive tested setting. Merges remain a known tradeoff, especially in D5.</p>
<p>GFP-only masks from the baseline were used only as a consistency check, not ground truth. A nuclear candidate was counted as assigned when at least 50% of its pixels fell within one combined-channel mask. In the D5 crop, assigned nuclear candidates increased from 68/87 to 82/87, but masks containing multiple nuclear candidates also increased from 2 to 6. In D8, assignment increased from 46/61 to 49/61 and the multi-candidate mask count stayed at 1. These diagnostic numbers are not precision, recall, accuracy, or proof of one cell per mask.</p>
<h2>Full-field results</h2><p>Five complete 1024 × 1024 fields, one central field per well, were segmented with both settings. This is five of the dataset's 45 fields. Counts include objects touching image edges. Full-field counts are not directly comparable to the earlier cropped counts, and normalization/context changes can affect masks within a crop.</p>
<table><tr><th>Field</th><th>Default masks</th><th>Selected masks</th></tr>'''+table+'''</table><p>D9 has weak GFP signal across all nine acquired fields. Its combined-channel masks should not be interpreted as reliable nuclei-supported cell detections.</p>'''
    for p in [4,13,22,31,40]:
        text+=f'<h3>{seq["stage_positions"][p]["name"]}</h3><img src="p{p:03d}_full_compare.jpg" alt="Default and selected masks on BF"><p><a href="p{p:03d}_full_selected_bf.png">Native-resolution BF overlay</a> · <a href="p{p:03d}_full_selected_masks.tif">Selected integer labels</a> · <a href="p{p:03d}_full_default_masks.tif">Default integer labels</a></p>'
    text+='<h2>Sweep evidence</h2>'
    for p in [4,31]:
        text+=f'<h3>{seq["stage_positions"][p]["name"]}</h3><img src="p{p:03d}_refine.jpg" alt="Intermediate settings on BF"><p>'
        text+=' · '.join(f'<a href="p{p:03d}_{c}_sweep.jpg">{c} sweep</a>' for c in ['native','diam45','diam60','local128'])+'</p>'
    text+='''<p><a href="selected_settings.json">Exact selected settings</a> · <a href="sweep_results.csv">Sweep diagnostics</a> · <a href="refine_results.json">Refinement diagnostics</a> · <a href="full_results.json">Full-field counts</a></p>
<p>Saved label TIFFs preserve the original 1024 × 1024 geometry. Label 0 is background; positive values identify objects within each file. IDs do not correspond across different settings or fields. Inline display uses compressed images and simplified contours; the TIFF labels and native-resolution PNG overlays are the precise outputs.</p></body></html>'''
    (OUT/'report.html').write_text(text,encoding='utf-8')

if __name__=='__main__':
    example()
    if len(json.loads((OUT/'full_results.json').read_text()))==10:report()
