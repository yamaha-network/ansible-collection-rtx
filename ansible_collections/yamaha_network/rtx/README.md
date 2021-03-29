# Ansible collection for Yamaha RTX/NVR/FWX/vRX series

## Modules
The following Ansible modules are part of this collection.

- rtx_command.py - Run commands on remote Yamaha RTX/NVR/FWX/vRX devices
- rtx_config.py - Manage the configuration of Yamaha RTX/NVR/FWX/vRX devices

## Installation
To install the latest version of this collection, please use the following command:

`ansible-galaxy collection install yamaha_network.rtx`

## Requirements
- Ansible 2.10

## Sample playbook 

```
---
- hosts: RTX1210
  connection: network_cli

  tasks:
  - name: get configuration
    yamaha_network.rtx.rtx_command:
      commands: 
        - show config
    register: result

  - name: debug
    debug:
      msg: "{{ result.stdout_lines[0] }}"

  - name: set description
    yamaha_network.rtx.rtx_config:
      lines: 
        - description 1 yamaha

  vars:
    ansible_network_os: yamaha_network.rtx.rtx
    ansible_user: username
    ansible_ssh_pass: password
    ansible_become: true
    ansible_become_password: become_password
```

## Licence

See the LICENSE file.