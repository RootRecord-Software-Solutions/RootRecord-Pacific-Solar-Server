# Security

Security subsystem ownership: cameras, access surfaces, and related desk security tooling.

## Runtime

Camera runtime is implemented under `Security/Cameras/` in the Pacific server repository.

## Persistent data

- Camera images: `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Images/`
- Timelapse outputs: `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Timelapses/`
- Security logs: `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Security/`

Runtime camera credentials remain outside Git in the operator environment. Never commit `CONNECTION.json` or public UI credentials.

## Migration status

The former G2 camera implementation was initially staged as `A-Eyes/`. It has now been moved into the canonical `Security/Cameras/` domain. Runtime verification remains required before legacy retirement.

*Updated 2026-09-28 HST.*
