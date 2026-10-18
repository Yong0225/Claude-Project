#!/bin/sh
# Full build: voiceover → soundtrack → frames → mux. usage: ./build.sh <workdir> <kokoro model dir>
set -e
W="$1"; M="$2"; cd "$(dirname "$0")"
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p "$W/vo"; cp script.json "$W/"
[ -f "$W/vo/cues.json" ] || python3 tts.py "$W" "$M"
for v in plain logo; do
  if [ $v = logo ]; then D=68.5; Q='?logo=1'; else D=65; Q=''; fi
  python3 audio.py "$W" $D && mv "$W/mix.wav" "$W/mix_$v.wav"
  NODE_PATH=$(npm root -g) node render.js "$W/video_$v.mp4" "$FF" $D "$Q"
  "$FF" -y -loglevel error -i "$W/video_$v.mp4" -i "$W/mix_$v.wav" -c:v copy \
    -af "loudnorm=I=-14:TP=-1.5,aresample=48000" -c:a aac -b:a 192k -shortest -movflags +faststart "$W/insights_$v.mp4"
  echo "built $W/insights_$v.mp4"
done
