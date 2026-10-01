# Linux Ticket Board + Practice Lab v2

## New in v2

- Total 25 real L1 Linux practice tickets
- Permission issues
- Service issues
- Disk/full-file issues
- Firewall issues
- SELinux issue
- DNS/network issue
- User/group issues
- Log and logrotate issues
- Web/httpd issues
- Auto checker
- Leaderboard
- Ticket pickup lock

## Install

```bash
unzip skynet-l1-ticket-lab-pro-v2.zip
cd skynet-l1-ticket-lab-pro-v2
chmod +x install.sh
sudo ./install.sh
```

Open:

```text
http://SERVER-IP:8085
```

## Login

```text
Admin: admin / Skynet@123
Students: student01 to student10 / Skynet@123
```

## Admin workflow

1. Login as admin.
2. Generate tickets.
3. Click **Break Test Machine** for selected ticket.
4. Student picks ticket.
5. Student fixes issue on RHEL machine.
6. Student submits resolution note.
7. Auto checker gives score.

## Student workflow

1. Login as student.
2. Pick available ticket.
3. Solve on same RHEL lab machine.
4. Open ticket.
5. Write resolution note.
6. Submit for auto check.

## Service commands

```bash
systemctl status skynet-l1lab
systemctl restart skynet-l1lab
systemctl stop skynet-l1lab
journalctl -u skynet-l1lab -f
```

## If Flask install fails

Check DNS/internet:

```bash
ping -c 2 8.8.8.8
ping -c 2 google.com
```

Add DNS:

```bash
echo 'nameserver 8.8.8.8' > /etc/resolv.conf
```

Then run:

```bash
/opt/skynet-l1lab/venv/bin/pip install flask psutil
systemctl restart skynet-l1lab
```

## Trainer answer file

See:

```text
TICKET_ANSWERS.md
```

Do not share answer file with students before practice.
