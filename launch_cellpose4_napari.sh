#!/bin/bash
# macOS launcher: same effect as launch_cellpose4_napari.bat
W="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$W/napari-raman-widget:$W/raman-control:$W/raman-mda-engine:$W/cns-control/src"
cd "$W/napari-raman-widget"
exec "$HOME/miniconda3/envs/confocal_control_gui_cellpose4/bin/python" run_napari.py
