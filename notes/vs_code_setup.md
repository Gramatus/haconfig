# Preparing SSH login

Please take a look at the awesome [documentation created by GitHub](https://help.github.com/articles/connecting-to-github-with-ssh/) about using public/private key pairs and how to create them, specifically: [Generating a new SSH key and adding it to the ssh-agent](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent).

# Setup HA
* Install add-on "Advanced SSH & Web Terminal"
* Configure as follows at main config:
```
ssh:
  username: root
  password: ""
  authorized_keys:
    - >-
      ssh-rsa
      <public key of generated SSH key pair>
  sftp: false
  compatibility_mode: false
  allow_agent_forwarding: false
  allow_remote_port_forwarding: true
  allow_tcp_forwarding: true
zsh: true
share_sessions: false
packages:
  - gcompat
  - libstdc++
  - curl
  - procps
init_commands: []
```
* Set port to 2222

# Setup VS Code
* Install extension `ms-vscode-remote.remote-ssh`
* Make sure this is present in `%userprofile%\.ssh\config`:
```
Host homeassistant.local
  HostName homeassistant.local
  User root
  Port 2222
  MACs hmac-sha2-512-etm@openssh.com
```
* `>Remote-SSH: Connect to Host...`
* Select `homeassistant.local` (name from `.ssh\config`)

> Note: if stuff changes in HA or some other reasons, you might need to remove everything concerned with `homeassistant.local` from `%userprofile%\.ssh\config` (can also be commented out by starting lines with #)
