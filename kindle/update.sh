#!/bin/sh
# 保存到 Kindle 后先修改 DEST 为你原显示脚本读取的图片位置。
set -eu
URL='https://279838089.github.io/screen.png'
DEST='/mnt/us/kindle-screen/screen.png'
mkdir -p "$(dirname "$DEST")"
TMP="$DEST.tmp.$$"
trap 'rm -f "$TMP"' 0 1 2 3 15
FETCH_URL="$URL?v=$(date +%s)"
if command -v curl >/dev/null 2>&1; then
  curl -fL -sS --connect-timeout 15 --max-time 60 -o "$TMP" "$FETCH_URL"
elif command -v wget >/dev/null 2>&1; then
  wget -q -O "$TMP" "$FETCH_URL"
else
  echo "No curl or wget" >&2; exit 1
fi
SIZE=$(wc -c < "$TMP")
test "$SIZE" -ge 300 || { echo "Download incomplete" >&2; exit 1; }
if command -v od >/dev/null 2>&1; then
  MAGIC=$(dd if="$TMP" bs=8 count=1 2>/dev/null | od -An -tx1 | tr -d ' \n')
  test "$MAGIC" = 89504e470d0a1a0a || { echo "Not PNG" >&2; exit 1; }
fi
mv -f "$TMP" "$DEST"
echo "Updated $DEST ($SIZE bytes)"
