"""Controlled comparison: add BF to DAPI+GFP, keeping inference settings fixed."""
from tune_overlay import models, torch, np, tifffile, plt, SOURCE, ROOT, seq, norm, overlay
from pathlib import Path
import json, time

OUT=ROOT/'bf_third_channel'
OUT.mkdir(exist_ok=True)
PARAMS=dict(channel_axis=0,normalize={'tile_norm_blocksize':128},cellprob_threshold=0.,flow_threshold=.6,min_size=15)

def stats(m):
    area=np.bincount(m.ravel())[1:]
    return dict(count=int(m.max()),coverage=float(np.mean(m>0)),median_area_px=float(np.median(area)) if len(area) else 0)

if __name__=='__main__':
    model=models.CellposeModel(gpu=False,pretrained_model=str(ROOT/'cpsam_v2'))
    records=[]
    for idx in [31,4,13,22,40]:
        a=tifffile.imread(SOURCE/'images'/f'images_p{idx:03d}.ome.tiff')
        old=tifffile.imread(ROOT/'tuned_bf'/f'p{idx:03d}_full_selected_masks.tif')
        path=OUT/f'p{idx:03d}_three_channel_masks.tif'
        start=time.time()
        if path.exists():new=tifffile.imread(path)
        else:
            new,_,_=model.eval(a[[1,2,0]],**PARAMS)
            tifffile.imwrite(path,new.astype(np.uint32),metadata={'axes':'YX'})
        rec=dict(position=idx,well=seq['stage_positions'][idx]['name'],two_channel=stats(old),three_channel=stats(new),
                 added_mask_pixels=int(np.sum((new>0)&(old==0))),removed_mask_pixels=int(np.sum((old>0)&(new==0))),seconds=round(time.time()-start,2))
        if idx==31:
            rec['left_half_coverage']={'two_channel':float(np.mean(old[:,:512]>0)),'three_channel':float(np.mean(new[:,:512]>0))}
        records.append(rec)
        print(json.dumps(rec),flush=True)
        (OUT/'results.json').write_text(json.dumps(records,indent=2))
        plt.imsave(OUT/f'p{idx:03d}_three_channel_bf.png',overlay(a,new))
        for label,sl in [('full',np.s_[:,:]),*([('left_detail',np.s_[256:768,0:512])] if idx==31 else [])]:
            fig,axs=plt.subplots(1,3,figsize=(15,5),layout='constrained')
            images=[np.repeat(norm(a[0])[...,None],3,axis=-1),overlay(a,old),overlay(a,new)]
            for ax,img,title in zip(axs,images,['BF reference',f'DAPI + GFP: {old.max()} total masks',f'DAPI + GFP + BF: {new.max()} total masks']):
                ax.imshow(img[sl]);ax.set_title(title);ax.axis('off')
            fig.suptitle(rec['well']+' | '+('left-side detail (x 0:512, y 256:768)' if label=='left_detail' else 'full field')+' | fixed inference settings')
            fig.savefig(OUT/f'p{idx:03d}_{label}_comparison.png',dpi=150);plt.close(fig)
    (OUT/'settings.json').write_text(json.dumps(dict(model='cpsam_v2',input_channel_indices=[1,2,0],input_channels=['DAPI membrane','GFP nuclei','BF'],parameters=PARAMS,positions=[31,4,13,22,40],comparison='Existing full-field selected DAPI+GFP masks, same settings; no registration correction or model training.'),indent=2))
