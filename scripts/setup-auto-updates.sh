#!/usr/bin/env bash
# Configure unattended apt updates on Ubuntu/Debian.
# Run once: sudo ./scripts/setup-auto-updates.sh
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run with sudo:"
  echo "  sudo $0"
  exit 1
fi

echo "==> Installing unattended-upgrades (if needed)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y unattended-upgrades apt-listchanges

echo "==> Daily apt update + unattended upgrade"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

echo "==> Enable normal -updates pocket (not just -security)"
if grep -q '^//.*"${distro_id}:${distro_codename}-updates"' /etc/apt/apt.conf.d/50unattended-upgrades; then
  sed -i 's|^//\(\s*"\${distro_id}:\${distro_codename}-updates";\)|\1|' \
    /etc/apt/apt.conf.d/50unattended-upgrades
fi

echo "==> Extra unattended-upgrade options"
cat > /etc/apt/apt.conf.d/99nova-autoupgrade <<'EOF'
// Keep the system tidy and apply updates without prompting.
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";
Unattended-Upgrade::Automatic-Reboot-WithUsers "false";
EOF

echo "==> Enabling systemd timers"
systemctl enable --now apt-daily.timer apt-daily-upgrade.timer unattended-upgrades.service

echo "==> Dry run (what would be upgraded)"
unattended-upgrades --dry-run --debug 2>&1 | tail -20 || true

echo
echo "Done. Your system will now:"
echo "  - run apt update daily"
echo "  - install security + normal updates automatically"
echo "  - reboot at 04:00 when a kernel/libc update requires it"
echo
echo "Logs: /var/log/unattended-upgrades/unattended-upgrades.log"
echo "This is safer than raw 'apt upgrade' (skips proposed/backports)."
