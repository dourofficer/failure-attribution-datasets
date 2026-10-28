#!/bin/bash
# Resume a byte-range download (HF resolve URL) until the local file reaches MAX bytes or 8 attempts.
# usage: resume_range.sh <url> <file> <max_bytes>
url="$1"; file="$2"; max="$3"
for i in $(seq 1 8); do
  size=$(stat -c%s "$file" 2>/dev/null || echo 0)
  if [ "$size" -ge "$max" ]; then echo "done at $size"; exit 0; fi
  echo "attempt $i from $size"
  curl -sL -r "${size}-$((max-1))" "$url" >> "$file"
  echo "curl exit $?"
  sleep 3
done
echo "final size $(stat -c%s "$file")"
