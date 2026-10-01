# SKYNET L1 Linux Ticket Board - 25 Ticket Answers

Author: Kishor Ahire  
Institute: Skynet Linux Training Centre

> Use these answers only for trainer verification or after students complete practice.

---

## 1. SSH service down on practice server

```bash
systemctl status sshd
systemctl enable --now sshd
systemctl restart sshd
systemctl is-active sshd
```

Resolution note:
```text
Root cause: sshd service was stopped.
Action: Started and enabled sshd.
Verification: systemctl is-active sshd shows active.
```

---

## 2. Apache web service not responding

```bash
systemctl status httpd
systemctl enable --now httpd
systemctl restart httpd
systemctl is-active httpd
```

---

## 3. Firewall blocks web application port 8080

```bash
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload
firewall-cmd --list-ports
```

---

## 4. Disk usage alert due to unwanted big file

```bash
du -sh /tmp/*
ls -lh /tmp/skynet_bigfile_alert.log
rm -f /tmp/skynet_bigfile_alert.log
df -h
```

---

## 5. Wrong permission on shared directory

Requirement: `/srv/shared` group `skynetstudents`, permission `770`.

```bash
groupadd -f skynetstudents
mkdir -p /srv/shared
chgrp skynetstudents /srv/shared
chmod 770 /srv/shared
stat -c '%a %G' /srv/shared
```

---

## 6. User account locked

```bash
passwd -S demo1
passwd -u demo1
passwd -S demo1
```

Alternative:

```bash
usermod -U demo1
```

---

## 7. Cron service stopped

```bash
systemctl status crond
systemctl enable --now crond
systemctl is-active crond
```

---

## 8. SELinux context issue on web file

```bash
ls -Z /var/www/html/index.html
restorecon -Rv /var/www/html
ls -Z /var/www/html/index.html
```

If still not fixed:

```bash
semanage fcontext -a -t httpd_sys_content_t "/var/www/html(/.*)?"
restorecon -Rv /var/www/html
```

---

## 9. NetworkManager service inactive

```bash
systemctl status NetworkManager
systemctl enable --now NetworkManager
systemctl is-active NetworkManager
```

---

## 10. Failed login report investigation

```bash
journalctl --no-pager -n 200 | grep -i 'failed\|invalid\|authentication'
grep -i 'failed\|invalid\|authentication' /var/log/secure 2>/dev/null
```

Resolution note:

```text
Checked authentication logs using journalctl and /var/log/secure. Found simulated failed login attempt. No service outage found.
```

---

## 11. Wrong owner on application directory

Requirement: `/opt/companyapp` owner `appuser:appuser`.

```bash
useradd -m appuser 2>/dev/null || true
mkdir -p /opt/companyapp
chown appuser:appuser /opt/companyapp
stat -c '%U:%G' /opt/companyapp
```

---

## 12. Package missing: tar

```bash
dnf install -y tar
rpm -q tar
```

---

## 13. Root filesystem inode pressure from many temp files

```bash
find /tmp/skynet_inode_issue -type f | wc -l
rm -f /tmp/skynet_inode_issue/*
find /tmp/skynet_inode_issue -type f | wc -l
```

Optional remove directory:

```bash
rm -rf /tmp/skynet_inode_issue
```

---

## 14. SUID permission missing on /usr/bin/passwd

```bash
ls -l /usr/bin/passwd
chmod u+s /usr/bin/passwd
stat -c '%a %n' /usr/bin/passwd
```

Expected permission starts with `4`, commonly `4755`.

---

## 15. Sticky bit missing on /tmp

```bash
ls -ld /tmp
chmod 1777 /tmp
stat -c '%a %n' /tmp
```

---

## 16. DNS resolution not working

```bash
cat /etc/resolv.conf
vi /etc/resolv.conf
```

Add DNS:

```text
nameserver 8.8.8.8
nameserver 1.1.1.1
```

Test:

```bash
ping -c 2 google.com
```

For classroom local DNS, use your institute DNS/server IP instead of public DNS.

---

## 17. Hostname changed incorrectly

Requirement: hostname must be `server.skynet.com`.

```bash
hostnamectl set-hostname server.skynet.com
hostnamectl --static
```

---

## 18. Important log file missing

Requirement: `/var/log/skynet-app.log`, owner `root:root`, permission `640`.

```bash
touch /var/log/skynet-app.log
chown root:root /var/log/skynet-app.log
chmod 640 /var/log/skynet-app.log
stat -c '%a %U:%G' /var/log/skynet-app.log
```

---

## 19. Custom application service disabled

```bash
systemctl daemon-reload
systemctl enable --now skynet-app
systemctl is-active skynet-app
systemctl is-enabled skynet-app
```

---

## 20. Wrong firewall service rule for HTTP

```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --reload
firewall-cmd --list-services
```

---

## 21. Group membership missing for developer user

Requirement: user `dev1` must be member of `developers` group.

```bash
groupadd -f developers
useradd -m dev1 2>/dev/null || true
usermod -aG developers dev1
id dev1
```

---

## 22. LVM mount entry missing in fstab

For this lab checker, use tmpfs entry for `/orders`.

```bash
mkdir -p /orders
cp /etc/fstab /etc/fstab.bak
sed -i '\#/orders#d' /etc/fstab
echo 'tmpfs /orders tmpfs defaults 0 0' >> /etc/fstab
mount /orders
mountpoint /orders
grep /orders /etc/fstab
```

---

## 23. Web index page content wrong

Requirement: `/var/www/html/index.html` must contain `SKYNET PRODUCTION OK`.

```bash
echo 'SKYNET PRODUCTION OK' > /var/www/html/index.html
cat /var/www/html/index.html
```

---

## 24. NTP/Chrony service stopped

```bash
systemctl status chronyd
systemctl enable --now chronyd
systemctl is-active chronyd
```

Optional check:

```bash
chronyc tracking
```

---

## 25. Logrotate configuration missing for application log

```bash
cat > /etc/logrotate.d/skynet-app <<'EOF'
/var/log/skynet-app.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    create 0640 root root
}
EOF

logrotate -d /etc/logrotate.d/skynet-app
```

---

# Student resolution note format

```text
Root cause: <what was wrong>
Action taken: <commands used>
Verification: <command output/check result>
```
