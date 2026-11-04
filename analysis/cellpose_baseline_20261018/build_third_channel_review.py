from build_bf_viewer import image_data, objects, ROOT, SOURCE, norm, seq, np, tifffile, json, Path

OUT=ROOT/'bf_third_channel'
VIZ=Path(r'C:\Users\spraman\.codex\visualizations\2026\10\23\01a169f9-1af3-7851-83cf-09b59d32e411\cellpose-third-channel.html')

def build(size):
    fields=[]
    for idx in [31,4,13,22,40]:
        a=tifffile.imread(SOURCE/'images'/f'images_p{idx:03d}.ome.tiff')
        f=dict(name=seq['stage_positions'][idx]['name'],position=idx,bf=image_data(norm(a[0]),size,65),
               fl=image_data(np.stack([norm(a[1]),norm(a[2]),np.zeros(a.shape[1:])],axis=-1),size,65),
               warning='Weak GFP: interpret with caution' if idx==40 else '')
        f['default']=objects(tifffile.imread(ROOT/'tuned_bf'/f'p{idx:03d}_full_selected_masks.tif'))
        f['selected']=objects(tifffile.imread(OUT/f'p{idx:03d}_three_channel_masks.tif'))
        fields.append(f)
    data=dict(fields=fields,settings='Both: local normalization 128 px; cellprob 0; flow 0.6')
    s=(ROOT/'tuned_bf'/'viewer_template.html').read_text(encoding='utf-8')
    s=s.replace('cellpose-bf-review','cellpose-third-channel-review')
    s=s.replace('GFP + DAPI segmentation on brightfield','Does adding BF change the masks?')
    s=s.replace('Settings<select','Model inputs<select').replace('Selected settings','DAPI + GFP + BF').replace('Default settings','DAPI + GFP')
    s=s.replace("let field=0, variant='selected', zoom=1, cx=512, cy=512", "let field=0, variant='selected', zoom=2, cx=256, cy=512")
    s=s.replace("load();restore(window.openai?.widgetState);","q('zoom').value='2';load();restore(window.openai?.widgetState);")
    s=s.replace("(variant==='selected'?data.settings:'Default: diameter unset, cellprob 0, flow 0.4')", "(variant==='selected'?'DAPI + GFP + BF':'DAPI + GFP')+' · '+data.settings")
    s=s.replace('settings:variant','inputChannels:variant===\'selected\'?\'DAPI + GFP + BF\':\'DAPI + GFP\'')
    return s.replace('__DATA__',json.dumps(data,separators=(',',':')))

if __name__=='__main__':
    content=build(768)
    if len(content.encode())>=1000000:content=build(512)
    assert len(content.encode())<1000000
    VIZ.write_text(content,encoding='utf-8')
    print(VIZ,len(content.encode()))
    rows=json.loads((OUT/'results.json').read_text())
    h='<!doctype html><html><head><meta charset="utf-8"><title>BF as third input channel</title><style>body{font:17px/1.5 system-ui;max-width:1400px;margin:32px auto;padding:0 24px}img{max-width:100%}td,th{padding:10px;border:1px solid #ccc}table{border-collapse:collapse}</style></head><body><h1>Adding BF as a third Cellpose input</h1>'
    h+='<p>Controlled comparison using pretrained cpsam_v2: DAPI + GFP versus DAPI + GFP + BF. Both use local normalization 128 px, cellprob threshold 0, flow threshold 0.6, min_size 15, and no diameter rescaling. Five full 1024 × 1024 fields were tested. No training, registration correction, or weighted blending was performed. BF is an input to the new run, so agreement with BF is not independent validation.</p>'
    h+='<p>Mask coverage is the fraction of pixels assigned to any object. Reduced coverage alone does not establish improved segmentation: it can represent tighter boundaries or missing cells. Counts are not accuracy measurements. D9 has weak GFP signal.</p><p>Visual review of the left D8 detail shows several broad fluorescence-derived regions becoming tighter around BF-visible bodies. The tradeoff is reduced detection: in the central D8 crop, 51 of 61 GFP-only nuclear candidates overlap a two-channel mask by at least 50%, versus 47 with BF added. Those automatic nuclear masks are a consistency check, not ground truth, and that central crop differs from the left-half coverage region.</p><table><tr><th>Field</th><th>2-channel count</th><th>3-channel count</th><th>2-channel coverage</th><th>3-channel coverage</th></tr>'
    for r in rows:h+=f'<tr><td>{r["well"]}</td><td>{r["two_channel"]["count"]}</td><td>{r["three_channel"]["count"]}</td><td>{r["two_channel"]["coverage"]:.1%}</td><td>{r["three_channel"]["coverage"]:.1%}</td></tr>'
    d=rows[0]['left_half_coverage']
    h+=f'</table><h2>D8 left side</h2><p>Coverage in the full left half (x 0:512, all y): {d["two_channel"]:.1%} without BF, {d["three_channel"]:.1%} with BF. The close-up below shows x 0:512, y 256:768.</p><img src="p031_left_detail_comparison.png" alt="D8 left-side comparison">'
    for r in rows:
        i=r['position'];h+=f'<h2>{r["well"]}</h2><img src="p{i:03d}_full_comparison.png" alt="Two versus three input channel masks"><p><a href="p{i:03d}_three_channel_bf.png">Native-resolution BF overlay</a> · <a href="p{i:03d}_three_channel_masks.tif">Three-channel integer masks</a></p>'
    h+='<p><a href="settings.json">Exact settings</a> · <a href="results.json">Measurements</a></p><p>Label 0 is background. Object IDs are local to each file and do not match across runs. Inline images are compressed and contours simplified; use native-resolution PNGs and TIFFs for precise boundaries.</p></body></html>'
    (OUT/'report.html').write_text(h,encoding='utf-8')
