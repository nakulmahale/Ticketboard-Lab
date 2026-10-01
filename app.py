#!/usr/bin/env python3
"""
SKYNET L1 Linux Ticket Board + Practice Lab
Author: Kishor Ahire
Institute: Skynet Linux Training Centre

Purpose:
- Real company style L1 ticket board for students/employees
- Auto ticket creation
- Ticket pickup locking: once one student picks a ticket, it disappears for others
- Built-in Linux L1 troubleshooting tasks
- Test-machine break/fix setup
- Auto grading/checking
"""

from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import sqlite3, os, subprocess, random, json, time
from datetime import datetime

APP_NAME = "SKYNET L1 Linux Ticket Board"
DB = "/var/lib/skynet-l1lab/l1lab.db"
ADMIN_PASSWORD = os.getenv("SKYNET_ADMIN_PASSWORD", "Skynet@123")
PORT_BASE = int(os.getenv("SKYNET_PORT_BASE", "9000"))
STUDENT_COUNT = int(os.getenv("SKYNET_STUDENT_COUNT", "10"))

app = Flask(__name__)
app.secret_key = os.getenv("SKYNET_SECRET_KEY", "change-this-key-skynet-l1lab")

TICKET_POOL = [
    {
        "title": "SSH service down on practice server",
        "priority": "High",
        "category": "Service",
        "description": "User reports SSH access is not working. Check sshd service and restore access.",
        "break_cmd": "systemctl stop sshd",
        "check_cmd": "systemctl is-active sshd | grep -q active",
        "hint": "Use systemctl status sshd and systemctl start sshd."
    },
    {
        "title": "Apache web service not responding",
        "priority": "High",
        "category": "Web",
        "description": "Company internal web page is down. Restore httpd service.",
        "break_cmd": "systemctl stop httpd || true",
        "check_cmd": "systemctl is-active httpd | grep -q active",
        "hint": "Check httpd package, service status, and firewall."
    },
    {
        "title": "Firewall blocks web application port 8080",
        "priority": "Medium",
        "category": "Firewall",
        "description": "Web application is running but users cannot access port 8080.",
        "break_cmd": "firewall-cmd --permanent --remove-port=8080/tcp || true; firewall-cmd --reload || true",
        "check_cmd": "firewall-cmd --list-ports | grep -q '8080/tcp'",
        "hint": "Open 8080/tcp using firewall-cmd."
    },
    {
        "title": "Disk usage alert due to unwanted big file",
        "priority": "High",
        "category": "Storage",
        "description": "Monitoring shows /tmp usage increased because of an unwanted big file. Find and clean it.",
        "break_cmd": "fallocate -l 700M /tmp/skynet_bigfile_alert.log || dd if=/dev/zero of=/tmp/skynet_bigfile_alert.log bs=1M count=200",
        "check_cmd": "test ! -f /tmp/skynet_bigfile_alert.log",
        "hint": "Use du -sh /tmp/* and remove unwanted file."
    },
    {
        "title": "Wrong permission on shared directory",
        "priority": "Medium",
        "category": "Permission",
        "description": "/srv/shared should be accessible by group skynetstudents with 770 permission.",
        "break_cmd": "mkdir -p /srv/shared; groupadd -f skynetstudents; chown root:root /srv/shared; chmod 700 /srv/shared",
        "check_cmd": "stat -c '%a %G' /srv/shared | grep -q '770 skynetstudents'",
        "hint": "Use chgrp and chmod."
    },
    {
        "title": "User account locked",
        "priority": "Medium",
        "category": "User Management",
        "description": "User demo1 cannot login because account is locked. Unlock the account.",
        "break_cmd": "useradd -m demo1 2>/dev/null || true; echo 'demo1:Skynet@123' | chpasswd; passwd -l demo1",
        "check_cmd": "passwd -S demo1 | awk '{print $2}' | grep -qv '^L$'",
        "hint": "Use passwd -u demo1 or usermod -U demo1."
    },
    {
        "title": "Cron service stopped",
        "priority": "Low",
        "category": "Service",
        "description": "Scheduled jobs are not running. Check and start crond service.",
        "break_cmd": "systemctl stop crond",
        "check_cmd": "systemctl is-active crond | grep -q active",
        "hint": "Use systemctl enable --now crond."
    },
    {
        "title": "SELinux context issue on web file",
        "priority": "High",
        "category": "SELinux",
        "description": "Web file exists but httpd cannot serve it due to wrong SELinux context. Restore context.",
        "break_cmd": "mkdir -p /var/www/html; echo 'SKYNET L1 LAB' > /var/www/html/index.html; chcon -t user_home_t /var/www/html/index.html || true",
        "check_cmd": "ls -Z /var/www/html/index.html | grep -q httpd_sys_content_t",
        "hint": "Use restorecon -Rv /var/www/html."
    },
    {
        "title": "NetworkManager service inactive",
        "priority": "High",
        "category": "Network",
        "description": "NetworkManager service is inactive. Start and enable it.",
        "break_cmd": "systemctl stop NetworkManager || true",
        "check_cmd": "systemctl is-active NetworkManager | grep -q active",
        "hint": "Use systemctl enable --now NetworkManager."
    },
    {
        "title": "Failed login report investigation",
        "priority": "Medium",
        "category": "Security",
        "description": "Check failed SSH login attempts and write root-cause note in ticket resolution.",
        "break_cmd": "logger 'SKYNET-L1LAB simulated failed password for invalid user testuser from 192.168.1.100 port 55222 ssh2'",
        "check_cmd": "journalctl --no-pager -n 200 | grep -q 'SKYNET-L1LAB simulated failed password'",
        "hint": "Use journalctl and /var/log/secure."
    },
    {
        "title": "Wrong owner on application directory",
        "priority": "Medium",
        "category": "Permission",
        "description": "/opt/companyapp should be owned by appuser:appuser.",
        "break_cmd": "useradd -m appuser 2>/dev/null || true; mkdir -p /opt/companyapp; chown root:root /opt/companyapp",
        "check_cmd": "stat -c '%U:%G' /opt/companyapp | grep -q 'appuser:appuser'",
        "hint": "Use chown appuser:appuser /opt/companyapp."
    },
    {
        "title": "Package missing: tar",
        "priority": "Low",
        "category": "Package",
        "description": "Backup script failed because tar package is missing. Install tar package.",
        "break_cmd": "dnf remove -y tar || true",
        "check_cmd": "rpm -q tar >/dev/null 2>&1",
        "hint": "Use dnf install -y tar."
    },
    {
        "title": "Root filesystem inode pressure from many temp files",
        "priority": "Medium",
        "category": "Storage",
        "description": "Application created many temporary files in /tmp/skynet_inode_issue. Clean that directory.",
        "break_cmd": "mkdir -p /tmp/skynet_inode_issue; for i in $(seq 1 300); do touch /tmp/skynet_inode_issue/file_$i.tmp; done",
        "check_cmd": "test ! -d /tmp/skynet_inode_issue || test $(find /tmp/skynet_inode_issue -type f | wc -l) -eq 0",
        "hint": "Use find /tmp/skynet_inode_issue -type f and rm."
    },
    {
        "title": "SUID permission missing on /usr/bin/passwd",
        "priority": "High",
        "category": "Permission",
        "description": "Normal users cannot change their password because SUID bit is missing on /usr/bin/passwd.",
        "break_cmd": "chmod u-s /usr/bin/passwd",
        "check_cmd": "stat -c '%a' /usr/bin/passwd | grep -q '^4'",
        "hint": "Use chmod u+s /usr/bin/passwd."
    },
    {
        "title": "Sticky bit missing on /tmp",
        "priority": "High",
        "category": "Permission",
        "description": "Temporary directory permission is insecure. Restore /tmp permission to 1777.",
        "break_cmd": "chmod 0777 /tmp",
        "check_cmd": "stat -c '%a' /tmp | grep -q '1777'",
        "hint": "Use chmod 1777 /tmp."
    },
    {
        "title": "DNS resolution not working",
        "priority": "High",
        "category": "Network",
        "description": "Server cannot resolve domain names because resolv.conf is empty/wrong. Configure working DNS.",
        "break_cmd": "cp -a /etc/resolv.conf /etc/resolv.conf.skynetbak 2>/dev/null || true; echo '' > /etc/resolv.conf",
        "check_cmd": "grep -Eq 'nameserver[[:space:]]+([0-9]{1,3}\.){3}[0-9]{1,3}' /etc/resolv.conf",
        "hint": "Add nameserver 8.8.8.8 or your local DNS in /etc/resolv.conf."
    },
    {
        "title": "Hostname changed incorrectly",
        "priority": "Low",
        "category": "System",
        "description": "Hostname must be server.skynet.com. Correct the hostname.",
        "break_cmd": "hostnamectl set-hostname wronghost.local",
        "check_cmd": "hostnamectl --static | grep -q '^server.skynet.com$'",
        "hint": "Use hostnamectl set-hostname server.skynet.com."
    },
    {
        "title": "Important log file missing",
        "priority": "Low",
        "category": "Logs",
        "description": "/var/log/skynet-app.log is missing. Recreate it with correct owner root:root and permission 640.",
        "break_cmd": "rm -f /var/log/skynet-app.log",
        "check_cmd": "test -f /var/log/skynet-app.log && stat -c '%a %U:%G' /var/log/skynet-app.log | grep -q '640 root:root'",
        "hint": "Use touch, chown and chmod."
    },
    {
        "title": "Custom application service disabled",
        "priority": "Medium",
        "category": "Service",
        "description": "skynet-app service should be enabled and active. Restore service state.",
        "break_cmd": "cat >/etc/systemd/system/skynet-app.service <<'EOF'\n[Unit]\nDescription=Skynet Demo App\n[Service]\nType=simple\nExecStart=/bin/bash -c 'while true; do sleep 60; done'\n[Install]\nWantedBy=multi-user.target\nEOF\nsystemctl daemon-reload; systemctl disable --now skynet-app || true",
        "check_cmd": "systemctl is-active skynet-app | grep -q active && systemctl is-enabled skynet-app | grep -q enabled",
        "hint": "Use systemctl enable --now skynet-app."
    },
    {
        "title": "Wrong firewall service rule for HTTP",
        "priority": "Medium",
        "category": "Firewall",
        "description": "HTTP service should be allowed in firewalld, but it is removed. Add http service permanently.",
        "break_cmd": "firewall-cmd --permanent --remove-service=http || true; firewall-cmd --reload || true",
        "check_cmd": "firewall-cmd --list-services | tr ' ' '\n' | grep -q '^http$'",
        "hint": "Use firewall-cmd --permanent --add-service=http; firewall-cmd --reload."
    },
    {
        "title": "Group membership missing for developer user",
        "priority": "Medium",
        "category": "User Management",
        "description": "User dev1 must be member of group developers.",
        "break_cmd": "groupadd -f developers; useradd -m dev1 2>/dev/null || true; gpasswd -d dev1 developers 2>/dev/null || true",
        "check_cmd": "id -nG dev1 | tr ' ' '\n' | grep -q '^developers$'",
        "hint": "Use usermod -aG developers dev1."
    },
    {
        "title": "LVM mount entry missing in fstab",
        "priority": "High",
        "category": "Storage",
        "description": "/orders directory must have an fstab entry. For lab, add a tmpfs fstab entry for /orders and mount it.",
        "break_cmd": "mkdir -p /orders; sed -i '\#/orders#d' /etc/fstab; umount /orders 2>/dev/null || true",
        "check_cmd": "grep -q '[[:space:]]/orders[[:space:]]' /etc/fstab && mountpoint -q /orders",
        "hint": "Add: tmpfs /orders tmpfs defaults 0 0, then mount /orders."
    },
    {
        "title": "Web index page content wrong",
        "priority": "Low",
        "category": "Web",
        "description": "/var/www/html/index.html must contain text SKYNET PRODUCTION OK.",
        "break_cmd": "mkdir -p /var/www/html; echo 'WRONG PAGE' > /var/www/html/index.html",
        "check_cmd": "grep -q 'SKYNET PRODUCTION OK' /var/www/html/index.html",
        "hint": "Edit /var/www/html/index.html with correct content."
    },
    {
        "title": "NTP/Chrony service stopped",
        "priority": "Medium",
        "category": "Service",
        "description": "Time sync is not working because chronyd is stopped. Start and enable chronyd.",
        "break_cmd": "systemctl stop chronyd || true",
        "check_cmd": "systemctl is-active chronyd | grep -q active",
        "hint": "Use systemctl enable --now chronyd."
    },
    {
        "title": "Logrotate configuration missing for application log",
        "priority": "Low",
        "category": "Logs",
        "description": "Create logrotate config /etc/logrotate.d/skynet-app for /var/log/skynet-app.log.",
        "break_cmd": "rm -f /etc/logrotate.d/skynet-app; touch /var/log/skynet-app.log",
        "check_cmd": "test -f /etc/logrotate.d/skynet-app && grep -q '/var/log/skynet-app.log' /etc/logrotate.d/skynet-app",
        "hint": "Create /etc/logrotate.d/skynet-app with rotate policy."
    }
]

def run(cmd):
    try:
        return subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
    except Exception as e:
        class R: pass
        r = R(); r.returncode = 1; r.stdout = str(e)
        return r

def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        fullname TEXT,
        role TEXT DEFAULT 'student',
        active INTEGER DEFAULT 1
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS tickets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        priority TEXT,
        category TEXT,
        status TEXT DEFAULT 'open',
        assigned_to TEXT DEFAULT '',
        created_at TEXT,
        picked_at TEXT DEFAULT '',
        resolved_at TEXT DEFAULT '',
        break_cmd TEXT,
        check_cmd TEXT,
        hint TEXT,
        resolution_note TEXT DEFAULT '',
        score INTEGER DEFAULT 0,
        check_output TEXT DEFAULT ''
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        at TEXT,
        username TEXT,
        action TEXT,
        details TEXT
    )""")
    cur.execute("INSERT OR IGNORE INTO students(username,password,fullname,role) VALUES('admin',?,?, 'admin')", (ADMIN_PASSWORD, "Trainer Admin"))
    for i in range(1, STUDENT_COUNT+1):
        u = f"student{i:02d}"
        cur.execute("INSERT OR IGNORE INTO students(username,password,fullname,role) VALUES(?,?,?, 'student')",
                    (u, "Skynet@123", f"Student {i:02d}"))
    con.commit()
    con.close()

def audit(action, details=""):
    con = db()
    con.execute("INSERT INTO audit(at,username,action,details) VALUES(?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session.get("user","system"), action, details))
    con.commit()
    con.close()

def current_user():
    return session.get("user")

def is_admin():
    return session.get("role") == "admin"

@app.before_request
def setup():
    init_db()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"].strip()
        pw = request.form["password"].strip()
        con = db()
        row = con.execute("SELECT * FROM students WHERE username=? AND password=? AND active=1", (user,pw)).fetchone()
        con.close()
        if row:
            session["user"] = row["username"]
            session["role"] = row["role"]
            audit("LOGIN", "Login success")
            return redirect("/dashboard")
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html", error="")

@app.route("/logout")
def logout():
    audit("LOGOUT", "Logout")
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if not current_user(): return redirect("/")
    con = db()
    if is_admin():
        stats = {
            "open": con.execute("SELECT count(*) c FROM tickets WHERE status='open'").fetchone()["c"],
            "assigned": con.execute("SELECT count(*) c FROM tickets WHERE status='assigned'").fetchone()["c"],
            "resolved": con.execute("SELECT count(*) c FROM tickets WHERE status='resolved'").fetchone()["c"],
            "students": con.execute("SELECT count(*) c FROM students WHERE role='student'").fetchone()["c"]
        }
        tickets = con.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 100").fetchall()
        users = con.execute("SELECT * FROM students ORDER BY username").fetchall()
        con.close()
        return render_template("admin.html", app_name=APP_NAME, stats=stats, tickets=tickets, users=users)
    else:
        user = current_user()
        my = con.execute("SELECT * FROM tickets WHERE assigned_to=? ORDER BY id DESC", (user,)).fetchall()
        available = con.execute("SELECT id,title,priority,category,created_at FROM tickets WHERE status='open' ORDER BY id DESC LIMIT 50").fetchall()
        leaderboard = con.execute("SELECT assigned_to, sum(score) total, count(*) solved FROM tickets WHERE status='resolved' GROUP BY assigned_to ORDER BY total DESC").fetchall()
        con.close()
        return render_template("student.html", app_name=APP_NAME, my=my, available=available, leaderboard=leaderboard)

@app.route("/admin/create-ticket", methods=["POST"])
def create_ticket():
    if not is_admin(): return redirect("/")
    idx = int(request.form.get("ticket_id", random.randint(0, len(TICKET_POOL)-1)))
    t = TICKET_POOL[idx]
    con = db()
    con.execute("""INSERT INTO tickets(title,description,priority,category,created_at,break_cmd,check_cmd,hint)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (t["title"], t["description"], t["priority"], t["category"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 t["break_cmd"], t["check_cmd"], t["hint"]))
    con.commit(); con.close()
    audit("CREATE_TICKET", t["title"])
    return redirect("/dashboard")

@app.route("/admin/auto-generate", methods=["POST"])
def auto_generate():
    if not is_admin(): return redirect("/")
    count = int(request.form.get("count", 10))
    con = db()
    for _ in range(count):
        t = random.choice(TICKET_POOL)
        con.execute("""INSERT INTO tickets(title,description,priority,category,created_at,break_cmd,check_cmd,hint)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (t["title"], t["description"], t["priority"], t["category"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     t["break_cmd"], t["check_cmd"], t["hint"]))
    con.commit(); con.close()
    audit("AUTO_GENERATE", f"{count} tickets")
    return redirect("/dashboard")

@app.route("/admin/break/<int:ticket_id>")
def break_ticket(ticket_id):
    if not is_admin(): return redirect("/")
    con = db()
    t = con.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    con.close()
    if t:
        r = run(t["break_cmd"])
        audit("BREAK_MACHINE", f"ticket={ticket_id}, rc={r.returncode}")
    return redirect("/dashboard")

@app.route("/admin/reset")
def reset_lab():
    if not is_admin(): return redirect("/")
    con = db()
    con.execute("DELETE FROM tickets")
    con.execute("DELETE FROM audit")
    con.commit(); con.close()
    audit("RESET_LAB", "All tickets and audit deleted")
    return redirect("/dashboard")

@app.route("/ticket/<int:ticket_id>")
def ticket_detail(ticket_id):
    if not current_user(): return redirect("/")
    con = db()
    t = con.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    con.close()
    if not t: return "Ticket not found", 404
    if not is_admin() and t["assigned_to"] not in ("", current_user()):
        return "This ticket is not available for you.", 403
    return render_template("ticket.html", t=t, admin=is_admin())

@app.route("/pick/<int:ticket_id>")
def pick(ticket_id):
    if not current_user() or is_admin(): return redirect("/")
    con = db()
    cur = con.cursor()
    # Lock rule: only open ticket can be picked
    cur.execute("""UPDATE tickets SET status='assigned', assigned_to=?, picked_at=?
                   WHERE id=? AND status='open' AND assigned_to=''""",
                (current_user(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ticket_id))
    con.commit()
    changed = cur.rowcount
    con.close()
    audit("PICK_TICKET", f"ticket={ticket_id}, success={changed}")
    return redirect("/dashboard")

@app.route("/resolve/<int:ticket_id>", methods=["POST"])
def resolve(ticket_id):
    if not current_user() or is_admin(): return redirect("/")
    note = request.form.get("note","").strip()
    con = db()
    t = con.execute("SELECT * FROM tickets WHERE id=? AND assigned_to=?", (ticket_id,current_user())).fetchone()
    if not t:
        con.close()
        return "Ticket not assigned to you", 403
    r = run(t["check_cmd"])
    score = 100 if r.returncode == 0 else 0
    status = "resolved" if score == 100 else "assigned"
    con.execute("""UPDATE tickets SET status=?, resolved_at=?, resolution_note=?, score=?, check_output=?
                   WHERE id=?""",
                (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S") if score else "", note, score, r.stdout[-1000:], ticket_id))
    con.commit(); con.close()
    audit("RESOLVE_CHECK", f"ticket={ticket_id}, score={score}")
    return redirect(f"/ticket/{ticket_id}")

@app.route("/admin/ticket-pool")
def ticket_pool():
    if not is_admin(): return redirect("/")
    return render_template("pool.html", pool=list(enumerate(TICKET_POOL)))

@app.route("/api/stats")
def api_stats():
    con = db()
    rows = con.execute("SELECT status, count(*) c FROM tickets GROUP BY status").fetchall()
    data = {r["status"]: r["c"] for r in rows}
    con.close()
    return jsonify(data)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8085)
