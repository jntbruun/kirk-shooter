# Kirk Shooter

A pygame-ce space shooter, built for the browser and mobile with [pygbag](https://pygame-web.github.io/).

**Play:** https://jntbruun.github.io/kirk-shooter/

## Controls

| Action | Keyboard | Touch |
| --- | --- | --- |
| Move | `WASD` | left on-screen joystick |
| Fire | `Space` | `FIRE` button |
| Ultimate | `E` | `ULT` button |
| Restart after game over | `R` | tap anywhere |

## Project layout

```
main.py            game source (async main loop for pygbag)
images/            sprites, fonts, explosion frames
audio/             sound effects and music (desktop only)
highscore.txt      persisted best score
docs/              pygbag web build — this is what GitHub Pages serves
build/web/         raw pygbag build output
```

## Browser audio

`pygame.mixer` is skipped entirely when `sys.platform == "emscripten"`. In the
browser, `pygame.init()` blocks forever on the audio-permission handshake, so the
web build runs silent and only desktop loads sound. This is intentional — do not
"restore" mixer init for the web path.

## Rebuilding the web version

```bash
python3 -m pygbag --build .
cp build/web/* docs/
```

Then commit `docs/`. GitHub Pages is configured to serve from `/docs` on `main`.

## Running on desktop

```bash
pip install pygame-ce
python3 main.py
```
