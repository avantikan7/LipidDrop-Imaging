"""Single-well dish plan (35 mm dish, 12 mm glass well) for the navigation panel.

Software only: writes a plate JSON the "Load well plate config..." button
accepts, and computes imaging-tile centers (stage micrometers) covering the
circular well. No hardware is touched.

    python tools/dish_plan.py plan dish.json --center-x 0 --center-y 0
    python tools/dish_plan.py tiles --fov-um 400 --overlap 0.1 --radius-um 5500
"""
import argparse
from pathlib import Path

import sys

from useq import WellPlate, WellPlatePlan

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "napari-raman-widget"))
from napari_raman_widget.dish_workflow import tile_centers  # noqa: E402


def dish_plan(center_xy=(0.0, 0.0), well_mm=12.0, dish_mm=35.0):
    """1x1 circular plate; `center_xy` is the well center in stage um."""
    plate = WellPlate(rows=1, columns=1, well_spacing=(dish_mm, dish_mm),
                      well_size=(well_mm, well_mm), circular_wells=True,
                      name=f"{dish_mm:g} mm dish, {well_mm:g} mm well")
    return WellPlatePlan(plate=plate, a1_center_xy=tuple(center_xy),
                         selected_wells=((0,), (0,)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("out")
    p.add_argument("--center-x", type=float, default=0.0)
    p.add_argument("--center-y", type=float, default=0.0)
    t = sub.add_parser("tiles")
    t.add_argument("--center-x", type=float, default=0.0)
    t.add_argument("--center-y", type=float, default=0.0)
    t.add_argument("--radius-um", type=float, default=6000.0)
    t.add_argument("--fov-um", type=float, required=True)
    t.add_argument("--overlap", type=float, default=0.1)
    a = ap.parse_args()
    if a.cmd == "plan":
        Path(a.out).write_text(
            dish_plan((a.center_x, a.center_y)).model_dump_json(), encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        tiles = tile_centers((a.center_x, a.center_y), a.radius_um, a.fov_um, a.overlap)
        print(f"{len(tiles)} tiles")
        for x, y in tiles:
            print(f"{x:.1f}, {y:.1f}")


if __name__ == "__main__":
    main()
