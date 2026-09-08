# Kirk Shooter

A pygame-ce space shooter, built for the browser and mobile with [pygbag](https://pygame-web.github.io/).

**Play:** https://jntbruun.github.io/kirk-shooter/

## Controls

| Action | Keyboard | Touch |
| --- | --- | --- |
| Move | `WASD` | left on-screen joystick |
| Fire | `Space` | `FIRE` button |
| Ultimate | `E` | `ULT` button |
| Fullscreen | `F` | top-right button |
| Restart after game over | `R` | tap anywhere |

**Fullscreen on mobile:** works in Android Chrome/Firefox and iPadOS Safari.
iPhone Safari has no Fullscreen API — the button shows a hint instead. For a
chromeless view there, use Share → Add to Home Screen and launch from the icon
(pygbag ships the `apple-mobile-web-app-capable` meta for this).

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
export SSL_CERT_FILE=$(python3 -c "import certifi;print(certifi.where())")
python3 -m pygbag --build --ume_block 0 --title "Kirk Shooter" --app_name "Kirk Shooter" .
cp build/web/* docs/ && touch docs/.nojekyll
```

Then commit `docs/`. GitHub Pages serves from `/docs` on `main`.

- `SSL_CERT_FILE` — without it pygbag can't fetch its CDN template on a
  python.org Python that has no CA bundle, and hangs.
- `--ume_block 0` — the build has no audio, so skip the "click to unlock media"
  gate and boot straight to the game.

### pygbag / WASM constraints

`pygame.time.set_timer` is not implemented on WASM. Meteors spawn from a `dt`
accumulator in the async loop instead. Frame `dt` is clamped to 0.1s so a
backgrounded tab doesn't teleport sprites on the frame it regains focus.

## Running on desktop

```bash
pip install pygame-ce
python3 main.py
```
