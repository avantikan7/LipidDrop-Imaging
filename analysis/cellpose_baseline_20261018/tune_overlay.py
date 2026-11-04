"""Reproducible fixed-weight inference sweep and BF overlays; source images are read only."""
from pathlib import Path
import json, time, csv, argparse
import numpy as np
import tifffile, torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from skimage.segmentation import find_boundaries
from cellpose import models, dynamics
from run_baseline import SOURCE, ROOT, norm, seq

OUT=ROOT/'tuned_bf'
OUT.mkdir(exist_ok=True)
CONFIGS={'native':{},'diam45':{'diameter':45},'diam60':{'diameter':60},
         'local128':{'normalize':{'tile_norm_blocksize':128}}}
torch.set_num_threads(8)

def overlay(a,m):
    b=np.repeat(norm(a[0])[...,None],3,axis=-1)
    b[find_boundaries(m,mode='inner')]=[0,1,1]
    return b

def metrics(m,nuc):
    n=int(m.max()); areas=np.bincount(m.ravel())[1:]
    owners=[]
    for k in range(1,int(nuc.max())+1):
        v=m[nuc==k]; ids,counts=np.unique(v[v>0],return_counts=True)
        owners.append(int(ids[counts.argmax()]) if len(ids) and counts.max()/len(v)>=0.5 else 0)
    counts=np.bincount(owners,minlength=n+1)[1:]
    return dict(count=n,coverage=float(np.mean(m>0)),median_area=float(np.median(areas)) if n else 0,
                nuclear_candidates=int(nuc.max()),nuclei_assigned=sum(v>0 for v in owners),
                masks_with_multiple_nuclear_candidates=int(np.sum(counts>1)),
                masks_without_nuclear_candidate=int(np.sum(counts==0)))

def sweep(model):
    records=[]
    for idx in [4,31]:
        a=tifffile.imread(SOURCE/'images'/f'images_p{idx:03d}.ome.tiff')[:,256:768,256:768]
        nuc=tifffile.imread(ROOT/f'p{idx:03d}_GFP_nuclei_masks.tif')
        for config,kwargs in CONFIGS.items():
            cache=OUT/f'p{idx:03d}_{config}_flows.npz'
            if cache.exists():
                f=np.load(cache); dp,prob=f['dp'],f['prob']
            else:
                _,flows,_=model.eval(a[[1,2]],channel_axis=0,compute_masks=False,**kwargs)
                dp,prob=flows[1:3];np.savez_compressed(cache,dp=dp,prob=prob)
            fig,axs=plt.subplots(2,3,figsize=(15,10))
            for row,flow in enumerate([0.4,0.8]):
                for col,threshold in enumerate([-2,0,2]):
                    key=f'{config}_cp{threshold}_flow{flow}'
                    masks=dynamics.resize_and_compute_masks(dp,prob,niter=int(200*kwargs.get('diameter',30)/30),
                        cellprob_threshold=threshold,flow_threshold=flow,min_size=15,device=torch.device('cpu'))
                    tifffile.imwrite(OUT/f'p{idx:03d}_{key}.tif',masks.astype(np.uint32),metadata={'axes':'YX'})
                    rec=dict(position=idx,config=config,cellprob_threshold=threshold,flow_threshold=flow,**metrics(masks,nuc))
                    records.append(rec)
                    axs[row,col].imshow(overlay(a,masks));axs[row,col].axis('off')
                    axs[row,col].set_title(f'cellprob={threshold}, flow={flow} | {masks.max()} masks')
                    print(idx,key,rec,flush=True)
            fig.suptitle(f'{seq["stage_positions"][idx]["name"]} | {config} | GFP + DAPI masks on BF | central crop')
            fig.tight_layout();fig.savefig(OUT/f'p{idx:03d}_{config}_sweep.jpg',dpi=120);plt.close(fig)
            (OUT/'sweep_results.json').write_text(json.dumps(records,indent=2))
    with (OUT/'sweep_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=records[0]);w.writeheader();w.writerows(records)

def full(model,config,threshold,flow):
    records=[]
    for idx in [4,13,22,31,40]:
        a=tifffile.imread(SOURCE/'images'/f'images_p{idx:03d}.ome.tiff')
        for label,kwargs in [('default',{}),('selected',dict(**CONFIGS[config],cellprob_threshold=threshold,flow_threshold=flow))]:
            path=OUT/f'p{idx:03d}_full_{label}_masks.tif'
            if path.exists():m=tifffile.imread(path)
            else:
                m,_,_=model.eval(a[[1,2]],channel_axis=0,**kwargs)
                tifffile.imwrite(path,m.astype(np.uint32),metadata={'axes':'YX'})
            plt.imsave(OUT/f'p{idx:03d}_full_{label}_bf.png',overlay(a,m))
            records.append(dict(position=idx,well=seq['stage_positions'][idx]['name'],variant=label,count=int(m.max()),parameters=kwargs))
            print('FULL',idx,label,int(m.max()),flush=True)
        b=tifffile.imread(OUT/f'p{idx:03d}_full_default_masks.tif')
        s=tifffile.imread(OUT/f'p{idx:03d}_full_selected_masks.tif')
        fig,axs=plt.subplots(1,3,figsize=(18,6))
        axs[0].imshow(norm(a[0]),cmap='gray');axs[0].set_title('BF reference')
        axs[1].imshow(overlay(a,b));axs[1].set_title(f'Default: {b.max()} masks')
        axs[2].imshow(overlay(a,s));axs[2].set_title(f'Selected: {s.max()} masks')
        for ax in axs:ax.axis('off')
        fig.suptitle(seq['stage_positions'][idx]['name']+' | full 1024 x 1024 field')
        fig.tight_layout();fig.savefig(OUT/f'p{idx:03d}_full_compare.jpg',dpi=150);plt.close(fig)
        (OUT/'full_results.json').write_text(json.dumps(records,indent=2))
    (OUT/'selected_settings.json').write_text(json.dumps(dict(model='cpsam_v2',config=config,**CONFIGS[config],
        cellprob_threshold=threshold,flow_threshold=flow,min_size=15,channel_axis=0,channels=['DAPI membrane','GFP nuclei'],
        selection='Visual review on central crops p004 and p031; nuclear overlap is a proxy, not ground truth.',
        full_positions=[4,13,22,31,40],no_registration='Channels overlaid at acquisition pixel coordinates; no registration correction applied.'),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['sweep','full']);p.add_argument('--config',default='native');p.add_argument('--threshold',type=float,default=0);p.add_argument('--flow',type=float,default=.4);args=p.parse_args()
    model=models.CellposeModel(gpu=False,pretrained_model=str(ROOT/'cpsam_v2'))
    if args.mode=='sweep':sweep(model)
    else:full(model,args.config,args.threshold,args.flow)
