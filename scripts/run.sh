#!/usr/bin/env bash
#
# Novus OS - QEMU runner
#
# Boots the generated FAT ESP (out/esp.img) under QEMU with OVMF.  Unlike a
# partial vvfat staging tree, this image includes the live SYSTEM.IMG, the
# installer ESP.IMG, the signed TEST.NKM, applications and wallpapers.
# Serial output (COM1) is connected to this terminal's stdio.
#
# Usage: scripts/run.sh [MEM]    (guest memory size, defaults to 4G)

set -euo pipefail

MEM="${1:-4G}"

# Always run from the repository root so relative paths are stable.
cd "$(dirname "$0")/.."

if [ ! -f out/esp.img ]; then
    echo "out/esp.img not found. Run 'make esp' first." >&2
    exit 1
fi

# Copy pristine OVMF non-volatile variables on first use only, so boot
# entries and firmware state persist across runs.
if [ ! -f out/OVMF_VARS.fd ]; then
    cp /usr/share/OVMF/OVMF_VARS_4M.fd out/OVMF_VARS.fd
fi

# Show a window when a display is available; otherwise run headless.
# Serial output on stdio is fully functional either way.
if [ -n "${DISPLAY:-}" ]; then
    DISPLAY_ARGS="-display gtk"
else
    DISPLAY_ARGS="-display none"
fi

# Boot from the complete generated ESP. QEMU's per-drive snapshot mode
# prevents the guest from modifying out/esp.img, preserving build results
# across runs. Unlike fat:rw:esp, this has the same FAT layout as the ISO.
#
# Networking: QEMU's user-mode stack gives the guest DHCP (10.0.2.2), DNS
# (10.0.2.3) and NAT to the real internet, which is what the NCSI probe in
# kernel/net_ncsi.c needs to reach ncsi.novus-os.ryzn.pro.
#
# NIC models the kernel drives: e1000, e1000e, virtio-net-pci, rtl8139.
# Pick one with NOVUS_NIC, e.g.  NOVUS_NIC=virtio-net-pci make run
NIC="${NOVUS_NIC:-e1000}"
exec qemu-system-x86_64 -machine q35 -smp 2 -m "$MEM" \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,file=out/OVMF_VARS.fd \
    -drive if=ide,format=raw,file=out/esp.img,snapshot=on \
    -serial stdio -no-reboot $DISPLAY_ARGS \
    -netdev user,id=novusnet -device "$NIC",netdev=novusnet
