import pexpect
import sys
import time

password = "Taksha@22062023"
host = "root@62.72.13.196"
print(f"Connecting to {host}...")

# Use ssh-copy-id first
child = pexpect.spawn(f"ssh-copy-id -o StrictHostKeyChecking=no {host}", encoding='utf-8')

idx = child.expect(['(?i)password:', '(?i)passphrase', pexpect.EOF, pexpect.TIMEOUT])
if idx == 0:
    print("Found password prompt for ssh-copy-id. Sending password...")
    child.sendline(password)
    child.expect(pexpect.EOF)
    print(child.before)
else:
    print("ssh-copy-id output:", child.before)

# Now test normal SSH
child = pexpect.spawn(f"ssh -o StrictHostKeyChecking=no {host} 'echo Connection Successful'", encoding='utf-8')
idx = child.expect(['(?i)password:', 'Connection Successful', pexpect.EOF, pexpect.TIMEOUT])
if idx == 0:
    print("Found password prompt for ssh. Sending password...")
    child.sendline(password)
    child.expect(pexpect.EOF)
    print(child.before)
elif idx == 1:
    print("Connection Successful (Passwordless)")
else:
    print("SSH test output:", child.before)
