#!/usr/bin/env bash

mkdir -p ~/.config/qBittorrent
cat <<EOF > ~/.config/qBittorrent/qBittorrent.conf
[LegalNotice]
Accepted=true

[Preferences]
WebUI\LocalHostAuth=false
EOF

qbittorrent-nox -d

python3 frontal.py &
python3 -m bot
