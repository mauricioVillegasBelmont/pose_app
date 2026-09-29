```Powershell
usbipd list
usbipd attach --wsl --busid <BUSID>
```


pythest
`pytest `<path>` -v`

````
GAME_TYPE=particles POSE_PROVIDER=mock RENDER_PROVIDER=mock python -m app.main
# Ctrl+C para cerrar, sin traceback feo

GAME_TYPE=color POSE_PROVIDER=mock RENDER_PROVIDER=mock python -m app.main
# Ctrl+C

curl http://localhost:8000/api/v1/state

curl -X POST http://localhost:8000/api/v1/commands/change-palette \
  -H "Content-Type: application/json" \
  -d '{"palette": "ocean"}'
```