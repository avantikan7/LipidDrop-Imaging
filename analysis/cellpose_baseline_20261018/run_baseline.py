from pathlib import Path
import json, time, csv, hashlib
import numpy as np
import tifffile
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from skimage.segmentation import find_boundaries
from cellpose import models
import importlib.metadata

ROOT = Path(__file__).parent
SOURCE = Path(r'C:\Users\spraman\Desktop\Jeff\neuron_imaging\Imaging\20261018_FP_autofocus_test_002')
POSITIONS = [4, 13, 22, 31, 40]
MODES = {'GFP_nuclei':[2], 'DAPI_membrane':[1], 'DAPI_GFP':[1,2], 'BF':[0]}
torch.set_num_threads(8)
seq = json.loads((SOURCE/'useq-sequence.json').read_text())
def norm(x):
    lo,hi=np.percentile(x,[1,99])
    return np.clip((x.astype(float)-lo)/max(hi-lo,1),0,1)

if __name__ == '__main__':
    print('Loading pretrained cpsam_v2 on CPU', flush=True)
    model=models.CellposeModel(gpu=False, pretrained_model=str(ROOT/'cpsam_v2'))
    records=[]
    for idx in POSITIONS:
        a=tifffile.imread(SOURCE/'images'/f'images_p{idx:03d}.ome.tiff')[:,256:768,256:768]
        fig,axes=plt.subplots(2,4,figsize=(16,8))
        for col,(mode,chs) in enumerate(MODES.items()):
            out=ROOT/f'p{idx:03d}_{mode}_masks.tif'
            start=time.time()
            if out.exists():
                masks=tifffile.imread(out)
                seconds=None
            else:
                masks,_,_=model.eval(a[chs], channel_axis=0)
                seconds=round(time.time()-start,2)
                tifffile.imwrite(out,masks.astype(np.uint32),metadata={'axes':'YX'})
            n=int(masks.max())
            areas=np.bincount(masks.ravel())[1:]
            records.append(dict(position=idx,well=seq['stage_positions'][idx]['name'],mode=mode,count=n,median_area_px=float(np.median(areas)) if n else 0,coverage=float(np.mean(masks>0)),seconds=seconds))
            if len(chs)==2:
                base=np.stack([norm(a[1]),norm(a[2]),np.zeros(a.shape[1:])],axis=-1)
            else:
                base=np.repeat(norm(a[chs[0]])[...,None],3,axis=-1)
            overlay=base.copy()
            overlay[find_boundaries(masks,mode='inner')]=[0,1,1]
            axes[0,col].imshow(base)
            axes[1,col].imshow(overlay)
            axes[0,col].set_title(mode)
            axes[1,col].set_title(f'{n} masks')
            for ax in axes[:,col]: ax.axis('off')
            print(idx,mode,n,seconds,flush=True)
            (ROOT/'results.json').write_text(json.dumps(records,indent=2))
        fig.suptitle(f"{seq['stage_positions'][idx]['name']} | native-resolution central 512 x 512 crop | default CPSAM v2")
        fig.tight_layout()
        fig.savefig(ROOT/f'p{idx:03d}_comparison.png',dpi=140)
        plt.close(fig)
    with (ROOT/'results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=records[0].keys());w.writeheader();w.writerows(records)
    (ROOT/'run_metadata.json').write_text(json.dumps(dict(source=str(SOURCE),cellpose=importlib.metadata.version('cellpose'),torch=torch.__version__,model='cpsam_v2',device='cpu',crop_yx=[256,768,256,768],positions=POSITIONS,channels=MODES,eval_arguments={'channel_axis':0},other_eval_parameters='installed defaults; no training, diameter adjustment, threshold sweep, or rescaling'),indent=2))
