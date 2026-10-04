#!/bin/sh
# Export the three printable parts (already in print orientation) to stl/.
# Can be run from anywhere:  fan-housing/export_stl.sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HERE/stl"
for p in tray lid guide; do
    openscad -q -o "$HERE/stl/fan-housing-$p.stl" -D "part=\"$p\"" "$HERE/fan-housing.scad"
    echo "stl/fan-housing-$p.stl"
done
