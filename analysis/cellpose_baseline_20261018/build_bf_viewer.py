from pathlib import Path
import json, base64, io
import cv2
import numpy as np
import tifffile
from PIL import Image
from run_baseline import ROOT, SOURCE, norm, seq

OUT=ROOT/'tuned_bf'
VIZ=Path(r'C:\Users\spraman\.codex\visualizations\2026\10\23\01a169f9-1af3-7851-83cf-09b59d32e411\cellpose-bf-overlay.html')

def image_data(a,size,quality):
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255))
    if size!=1024:im=im.resize((size,size),Image.Resampling.LANCZOS)
    b=io.BytesIO();im.save(b,format='WEBP',quality=quality)
    return 'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()

def objects(m):
    result=[]
    for k in range(1,int(m.max())+1):
        mask=np.uint8(m==k)
        ys,xs=np.where(mask)
        if not len(xs):continue
        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        contour=max(contours,key=cv2.contourArea)
        p=cv2.approxPolyDP(contour,2.0,True).reshape(-1,2).tolist()
        result.append(dict(id=k,a=len(xs),c=[round(float(xs.mean())),round(float(ys.mean()))],
                           edge=bool(xs.min()==0 or ys.min()==0 or xs.max()==1023 or ys.max()==1023),p=p))
    return result

def build(size=768,quality=65):
    fields=[]
    for idx in [4,13,22,31,40]:
        a=tifffile.imread(SOURCE/'images'/f'images_p{idx:03d}.ome.tiff')
        f=dict(name=seq['stage_positions'][idx]['name'],position=idx,
               bf=image_data(norm(a[0]),size,quality),
               fl=image_data(np.stack([norm(a[1]),norm(a[2]),np.zeros(a.shape[1:])],axis=-1),size,quality),
               warning='Weak GFP: counts are not reliable' if idx==40 else '')
        for variant in ['default','selected']:
            f[variant]=objects(tifffile.imread(OUT/f'p{idx:03d}_full_{variant}_masks.tif'))
        fields.append(f)
    data=dict(fields=fields,settings='Local normalization 128 px; diameter unset; cellprob 0; flow 0.6')
    template=(OUT/'viewer_template.html').read_text(encoding='utf-8')
    return template.replace('__DATA__',json.dumps(data,separators=(',',':')))

if __name__=='__main__':
    content=build(768,65)
    if len(content.encode())>=1000000:content=build(512,65)
    assert len(content.encode())<1000000, 'Inline viewer exceeds size budget'
    VIZ.write_text(content,encoding='utf-8')
    print('Viewer',VIZ,len(content.encode()),flush=True)
