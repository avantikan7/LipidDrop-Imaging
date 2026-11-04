from tune_overlay import *

records=[]
for idx in [4,31]:
    a=tifffile.imread(SOURCE/'images'/f'images_p{idx:03d}.ome.tiff')[:,256:768,256:768]
    nuc=tifffile.imread(ROOT/f'p{idx:03d}_GFP_nuclei_masks.tif')
    fig,axs=plt.subplots(2,3,figsize=(15,10),layout='constrained')
    for row,config in enumerate(['native','local128']):
        f=np.load(OUT/f'p{idx:03d}_{config}_flows.npz')
        for col,(cp,flow) in enumerate([(-1,.6),(0,.6),(0,.4)]):
            m=dynamics.resize_and_compute_masks(f['dp'],f['prob'],niter=200,cellprob_threshold=cp,flow_threshold=flow,min_size=15,device=torch.device('cpu'))
            tifffile.imwrite(OUT/f'p{idx:03d}_{config}_cp{cp}_flow{flow}_refine.tif',m.astype(np.uint32))
            rec=dict(position=idx,config=config,cellprob_threshold=cp,flow_threshold=flow,**metrics(m,nuc));records.append(rec)
            axs[row,col].imshow(overlay(a,m));axs[row,col].axis('off');axs[row,col].set_title(f'{config}: cp={cp}, flow={flow} | {m.max()} masks')
    fig.suptitle(seq['stage_positions'][idx]['name']+' | intermediate settings on BF')
    fig.savefig(OUT/f'p{idx:03d}_refine.jpg',dpi=120);plt.close(fig)
(OUT/'refine_results.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
