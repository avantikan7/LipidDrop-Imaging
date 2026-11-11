<p align="center">
  <img src="assets/lipid-droplet-icon.png" width="140" alt="Lipid droplet imaging icon">
</p>

# Lipid drop imaging workspace

**Adaptive image-guided Raman acquisition and lipid-droplet tracking in adipocytes.**

Launch `launch_cellpose4_napari.bat` using the existing conda environment
`confocal_control_gui_cellpose4` (Cellpose 4.2.1.1). The launcher selects this
workspace's four component folders through PYTHONPATH without modifying shared
editable installations. It invokes conda through base Python because this machine's
standalone conda executable fails. The launcher contains this machine's conda path.

## Git layout

This parent repository and all four components use branch `lipid-drop-imaging`.
The components are submodules: cns-control, napari-raman-widget, raman-control,
and raman-mda-engine. Their complete existing histories remain intact.
The parent tracks launch files, environment inventories, supporting files, and
exact component commits. Commit changes inside a component first, then run
`git add <component>` and commit in this parent to record its new revision.
Use `git submodule status` to inspect the pinned revisions.

On this machine, the submodules are also linked worktrees of the original
confocal_control_gui repositories. Original checkouts remain on main. Keep the
original repositories in place while using these linked worktrees. Do not run
`git submodule absorbgitdirs` on this layout. The original parent's empty .git
folder had no history; all existing history was in the four components.

GitHub URLs in .gitmodules describe upstream repositories. The new local commits
and branches have not been pushed, so a remote recursive clone cannot yet restore
this exact snapshot. Use the supplied offline bundles and restore.ps1 instead.
The restored copy has independent Git metadata and needs no original worktrees.

## Environment and package

cellpose4-conda-explicit.txt records conda packages; cellpose4-pip-freeze.txt
records pip packages excluding editable installs. These are inventories, not a
tested clean installation recipe. requirements.txt is retained legacy metadata.
Hardware drivers, Micro-Manager configuration, and saved application settings
remain machine-local. The existing environment is reused without package changes.

The backup ZIP contains a source snapshot, five Git bundles (parent plus four
components), a revision manifest, SHA-256 checksums, and an offline restore script.
Acquisition data, calibration outputs, caches, and temporary backups remain in the
original workspace and are excluded. Existing tracked history is preserved in full.

After extracting the package, run:
`powershell -ExecutionPolicy Bypass -File .\restore.ps1 -Destination C:\path\lipid-drop-imaging`
Choose a new destination. The script restores all pinned component revisions from
the local bundles and places each component on lipid-drop-imaging.
