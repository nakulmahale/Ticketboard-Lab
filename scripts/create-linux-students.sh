#!/bin/bash
# Optional helper: create student Linux users
for i in $(seq -w 1 10); do
  useradd -m student$i 2>/dev/null || true
  echo "student$i:Skynet@123" | chpasswd
done
echo "Student Linux users created: student01-student10"
