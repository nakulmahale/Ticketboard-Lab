#!/bin/bash
set -e

echo "Installing SKYNET L1 Ticket Board + Practice Lab v2..."

# RHEL 10 may not have python3-flask available if system is not registered.
# This installer uses python venv + pip, and also supports local/offline wheelhouse.
dnf install -y python3 python3-pip sqlite firewalld httpd policycoreutils-python-utils || true

mkdir -p /opt/skynet-l1lab/templates /opt/skynet-l1lab/static /var/lib/skynet-l1lab
cp app.py /opt/skynet-l1lab/app.py
cp templates/*.html /opt/skynet-l1lab/templates/
cp static/style.css /opt/skynet-l1lab/static/

python3 -m venv /opt/skynet-l1lab/venv

if [ -d "wheelhouse" ] && ls wheelhouse/*.whl >/dev/null 2>&1; then
  echo "Installing Python packages from local wheelhouse..."
  /opt/skynet-l1lab/venv/bin/pip install --no-index --find-links=wheelhouse flask psutil || true
else
  echo "Installing Python packages from internet using pip..."
  /opt/skynet-l1lab/venv/bin/pip install flask psutil || true
fi

# Final check
/opt/skynet-l1lab/venv/bin/python - <<'PY'
try:
    import flask
    print('Flask OK')
except Exception as e:
    print('ERROR: Flask not installed:', e)
    print('If internet is not available, copy Flask wheels into wheelhouse/ or register RHEL repo.')
    raise SystemExit(1)
PY

cat >/etc/systemd/system/skynet-l1lab.service <<'EOF'
[Unit]
Description=SKYNET L1 Linux Ticket Board Practice Lab v2
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/skynet-l1lab
ExecStart=/opt/skynet-l1lab/venv/bin/python /opt/skynet-l1lab/app.py
Restart=always
RestartSec=3
Environment=SKYNET_ADMIN_PASSWORD=Skynet@123
Environment=SKYNET_STUDENT_COUNT=10
Environment=SKYNET_PORT_BASE=9000

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now skynet-l1lab

systemctl enable --now firewalld || true
firewall-cmd --permanent --add-port=8085/tcp || true
firewall-cmd --permanent --add-port=8080/tcp || true
firewall-cmd --reload || true
semanage port -a -t http_port_t -p tcp 8085 2>/dev/null || semanage port -m -t http_port_t -p tcp 8085 2>/dev/null || true

echo
echo "Installation completed."
echo "Open: http://$(hostname -I | awk '{print $1}'):8085"
echo "Admin Login: admin / Skynet@123"
echo "Student Login: student01 to student10 / Skynet@123"
