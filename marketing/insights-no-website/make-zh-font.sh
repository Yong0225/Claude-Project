#!/bin/sh
# Rebuilds fonts/NotoSansSC-subset.woff2 with every non-ASCII character used in the *-zh.html slides.
cd "$(dirname "$0")"
TXT=$(python3 -c "
import re,glob,urllib.parse
t=''.join(open(f).read() for f in glob.glob('*zh*.html'))
print(urllib.parse.quote(''.join(sorted(set(c for c in re.sub(r'<[^>]+>','',t) if ord(c)>127)))))")
URL=$(curl -sS -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36" \
  "https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@100..900&text=$TXT" | grep -o 'https://[^)]*' | head -1)
curl -sS -o fonts/NotoSansSC-subset.woff2 "$URL"
