#!/bin/sh
# One-command rebuild: picture, sound, final mix. Needs the Lemo-Opuscar library and ffmpeg.
set -e
LIB=${LIB:-$HOME/lemo-opuscar}
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$LIB"
node core/render/events.mjs "$HERE"
node core/render/video.mjs "$HERE" --fps 30 --workers 4 --out "$HERE/out/video.mp4"
cd "$HERE"
LIB="$LIB" "$LIB/.venv/bin/python" mix.py
# two-pass loudness normalisation to -14 LUFS, then mux (works with ffmpeg 6 and newer)
M=$(ffmpeg -hide_banner -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$M" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -hide_banner -loglevel error -y -i out/video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" \
  -c:a aac -b:a 256k -shortest -movflags +faststart groovy-coop-ad.mp4
ffmpeg -loglevel error -y -ss 29.5 -i groovy-coop-ad.mp4 -frames:v 1 -q:v 2 poster.jpg
echo "done: $HERE/groovy-coop-ad.mp4"
