"""Live lipid-droplet segmentation demo (no hardware, no Raman widget).

Opens a z-stack's BODIPY channel in napari, segments it plane by plane with a
Cellpose model, and fills in a labels layer, aim points and Raman grids as each
plane finishes.

    ./launch_cellpose4_napari.sh is for the widget; run this one with
    ~/miniconda3/envs/confocal_control_gui_cellpose4/bin/python \
        tools/segment_droplets_napari.py [tif] [--channel 2] [--planes 10 20]
"""

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "raman-mda-engine"))

DEFAULT_TIF = (
    "~/Downloads/microscopy_onibasu_stellaris_avantika_Oct_11_SVF_Batch1_Day7_"
    "40x_BODIPY_CMDR.lif - Series011.tif"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tif", nargs="?", default=DEFAULT_TIF)
    ap.add_argument("--channel", type=int, default=2, help="BODIPY channel index")
    ap.add_argument("--model", default="bodipy_confocal_dino_100ep")
    ap.add_argument("--planes", type=int, nargs=2, metavar=("START", "STOP"),
                    help="only segment planes START..STOP-1")
    ap.add_argument("--density", type=int, default=6, help="grid spacing in pixels")
    ap.add_argument("--margin", type=float, default=2.0, help="grid margin from droplet edge")
    ap.add_argument("--min-rel-intensity", type=float, default=0.3)
    args = ap.parse_args()

    import napari
    import tifffile
    from napari.qt.threading import thread_worker

    stack = tifffile.imread(Path(args.tif).expanduser())
    if stack.ndim == 4:                        # Z, C, Y, X
        stack = stack[:, args.channel]
    elif stack.ndim == 2:
        stack = stack[None]
    stack = stack.astype(np.float32)
    z0, z1 = args.planes or (0, len(stack))

    viewer = napari.Viewer(title="Lipid droplet segmentation (dry run)")
    viewer.add_image(stack, name="BODIPY", colormap="green", blending="additive",
                     contrast_limits=np.percentile(stack, [1, 99.8]))
    labels = viewer.add_labels(np.zeros(stack.shape, np.uint16), name="droplets")
    aim = viewer.add_points(np.empty((0, 3)), name="aim", size=8, face_color="red",
                            ndim=3)
    grid = viewer.add_points(np.empty((0, 3)), name="raman grid", size=2,
                             face_color="yellow", ndim=3)
    viewer.dims.set_point(0, z0)

    @thread_worker
    def segment():
        from cellpose import models

        from raman_mda_engine.aiming.droplets import droplet_targets

        yield ("status", "loading model ...")
        model = models.CellposeModel(pretrained_model=args.model, gpu=True)
        for z in range(z0, z1):
            plane = stack[z]
            lo, hi = np.percentile(plane, [1, 99.8])
            if hi <= lo:
                continue
            norm = np.clip((plane - lo) / (hi - lo), 0, 1)
            masks, _, _ = model.eval(norm, diameter=None, flow_threshold=0.6,
                                     cellprob_threshold=-2, normalize=False)
            targets = droplet_targets(
                masks, density=args.density, margin=args.margin, image=plane,
                min_rel_intensity=args.min_rel_intensity,
            )
            keep = np.isin(masks, [t["label"] for t in targets])
            yield ("plane", z, np.where(keep, masks, 0).astype(np.uint16), targets)
        yield ("status", "done")

    def on_yield(msg):
        if msg[0] == "status":
            viewer.status = msg[1]
            print(msg[1], flush=True)
            return
        _, z, masks, targets = msg
        labels.data[z] = masks
        labels.refresh()
        zcol = lambda p: np.column_stack([np.full(len(p), z), p])  # noqa: E731
        if targets:
            aim.add(zcol(np.array([t["aim"] for t in targets])))
            pts = np.concatenate([t["grid"] for t in targets])
            if len(pts):
                grid.add(zcol(pts))
        viewer.dims.set_point(0, z)
        viewer.status = f"plane {z}: {len(targets)} droplets"
        print(viewer.status, flush=True)

    worker = segment()
    worker.yielded.connect(on_yield)
    worker.start()
    napari.run()


if __name__ == "__main__":
    main()
