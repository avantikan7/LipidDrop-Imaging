# Workspace instructions
Use conda environment confocal_control_gui_cellpose4.
The parent repository pins four Git submodules, all on neuron_imaging.
On this machine they are linked worktrees; preserve their original repositories.
Never create a Git commit without the user's explicit permission. A request to implement, fix, or test changes does not authorize committing them. Leave changes uncommitted unless the user explicitly authorizes a commit.
Only after the user explicitly authorizes committing, commit component edits first, then commit the updated gitlink in the parent.
Use launch_cellpose4_napari.bat so imports resolve to this workspace.
Do not redirect shared editable installs; the launcher handles source paths.
