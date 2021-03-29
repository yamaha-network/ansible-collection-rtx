#!/usr/bin/python
#
# Copyright (C) Yamaha Corporation.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <https://www.gnu.org/licenses/gpl-3.0.txt>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: rtx_config
version_added: "2.10"
authors:
  - Yamaha Corporation
short_description: Manage the configuration of Yamaha RTX/NVR/FWX/vRX devices.
description:
  - This module provides an implementation for manage the configuration
    of Yamaha RTX/NVR/FWX/vRX devices in a deterministic way.
notes:
  - Abbreviated commands are NOT idempotent, see
    L(Network FAQ,../network/user_guide/faq.html#why-do-the-config-modules-always-return-changed-true-with-abbreviated-commands).
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device config.  Be sure to note the configuration command
        syntax as some commands are automatically modified by the device
        config parser.
    type: list
    elements: str
    aliases: ['commands']
  parents:
    description:
      - The ordered set of parents that uniquely identify the section or hierarchy
        the commands should be checked against.  If the parents argument
        is omitted, the commands are checked against the set of top
        level.
    type: list
    elements: str
  src:
    description:
      - Specifies the source path to the file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory.  This argument is mutually
        exclusive with I(lines), I(parents).
    type: path
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made.  This allows the playbook designer
        the opportunity to perform commands prior to pushing any changes
        without affecting how the set of commands are matched against the
        system.
    type: list
    elements: str
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a change needs to be made.  Just like with I(before) this
        allows the playbook designer to append a set of commands to be
        executed after the command set.
    type: list
    elements: str
  match:
    description:
      - Instructs the module on the way to perform the matching of
        the set of commands against the current device config.  If
        match is set to I(line), commands are matched line by line.  If
        match is set to I(strict), command lines are matched with respect
        to position.  If match is set to I(exact), command lines
        must be an equal match.  Finally, if match is set to I(none), the
        module will not attempt to compare the source configuration with
        the running configuration on the remote device.
    choices: ['line', 'strict', 'exact', 'none']
    type: str
    default: line
  replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device. If the replace argument is set to I(line) then
        the modified lines are pushed to the device in configuration
        mode.  If the replace argument is set to I(block) then the entire
        command block is pushed to the device in configuration mode if any
        line is not correct.
    default: line
    choices: ['line', 'block']
    type: str
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the running C(config) from the remote device before any
        changes are made. If the C(backup_options) value is not given,
        the backup file is written to the C(backup) folder in the playbook
        root directory or role root directory, if playbook is part of an
        ansible role. If the directory does not exist, it is created.
    type: bool
    default: 'no'
  running_config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the running config to use as a base for comparing
        against the contents of source. There are times when it is not
        desirable to have the task get the running config for every
        task in a playbook.  The I(running_config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison.
    type: str
    aliases: ['config']
  save_when:
    description:
      - When changes are made to the device running config, the changes
        are not copied to non-volatile storage by default.  Using this
        argument will change that before.  If the argument is set to
        I(always), then the running config will always be copied to the
        default config.  If the argument is set to I(never), the running
        config will never be copied to the default config.  If the
        argument is set to I(changed), then the running config will only
        be copied to the default config if the task has made a change.
    default: never
    choices: ['always', 'never', 'changed']
    type: str
  diff_against:
    description:
      - When using the C(ansible-playbook --diff) command line argument
        the module can generate diffs against different sources.
      - When this option is configured as I(intended), the module will
        return the diff of the running config against the configuration
        provided in the C(intended_config) argument.
      - When th is option is configured as I(running), the module will
        return the before and after diff of the running configuration
        with respect to any changes made to the device configuration.
    type: str
    choices: ['running', 'intended']
  diff_ignore_lines:
    description:
      - Use this argument to specify one or more lines that should be
        ignored during the diff.  This is used for lines in the configuration
        that are automatically updated by the system.  This argument takes
        a list of regular expressions or exact line matches.
    type: list
    elements: str
  intended_config:
    description:
      - The C(intended_config) provides the master configuration that
        the node should conform to and is used to check the final running
        configuration against. This argument will not modify any settings
        on the remote device and is strictly used to check the compliance
        of the current device's configuration against.  When specifying this
        argument, the task should also modify the C(diff_against) value and
        set it to I(intended).
    type: str
  backup_options:
    description:
      - This is a dict object containing configurable options related to backup file path.
        The value of this option is read only when C(backup) is set to I(yes), if C(backup) is set
        to I(no) this option will be silently ignored.
    suboptions:
      filename:
        description:
          - The filename to be used to store the backup configuration. If the the filename
            is not given it will be generated based on the hostname, current time and date
            in format defined by <hostname>_config.<current-date>@<current-time>
        type: str
      dir_path:
        description:
          - This option provides the path ending with directory name in which the backup
            configuration file will be stored. If the directory does not exist it will be first
            created and the filename is either the value of C(filename) or default filename
            as described in C(filename) options description. If the path value is not given
            in that case a I(backup) directory will be created in the current working directory
            and backup configuration will be copied in C(filename) within I(backup) directory.
        type: path
    type: dict
"""

EXAMPLES = """
- name: configure hostname
  rtx_config:
    lines: console prompt {{ inventory_hostname }}

- name: configure lan1 interface settings
  rtx_config:
    lines:
      - description lan1 test
      - ip lan1 address 192.168.100.1/24

- name: configure description for pp
  rtx_config:
    lines:
      - description pp test
    parents:
      - pp select anonymous

- name: check the running config against master config
  rtx_config:
    diff_against: intended
    diff_ignore_lines:
      - administrator password
      - login
    intended_config: "{{ lookup('file', 'master.cfg') }}"

- name: configurable backup path
  rtx_config:
    src: rtx_template.j2
    backup: yes
    backup_options:
      filename: backup.cfg
      dir_path: /home/user
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['console prompt foo', 'ip lan2 address dhcp']
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['console prompt foo', 'ip lan2 address dhcp']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: str
  sample: /playbooks/ansible/backup/rtx_config.2020-02-04@12:24:48
filename:
  description: The name of the backup file
  returned: when backup is yes and filename is not specified in backup options
  type: str
  sample: rtx_config.2020-02-04@12:24:48
shortname:
  description: The full path to the backup file excluding the timestamp
  returned: when backup is yes and filename is not specified in backup options
  type: str
  sample: /playbooks/ansible/backup/rtx_config
date:
  description: The date extracted from the backup file name
  returned: when backup is yes
  type: str
  sample: "2020-02-04"
time:
  description: The time extracted from the backup file name
  returned: when backup is yes
  type: str
  sample: "12:24:48"
"""
import json

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible_collections.yamaha_network.rtx.plugins.module_utils.network.rtx.rtx import run_commands, get_config
from ansible_collections.yamaha_network.rtx.plugins.module_utils.network.rtx.rtx import get_connection
from ansible_collections.yamaha_network.rtx.plugins.module_utils.network.rtx.rtx import get_console_info, set_console_info
from ansible_collections.yamaha_network.rtx.plugins.module_utils.network.rtx.rtx import update_console_info
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import NetworkConfig, dumps


def edit_config_or_macro(connection, commands):
    # only catch the macro configuration command,
    # not negated 'no' variation.
    if commands[0].startswith("macro"):
        connection.edit_macro(candidate=commands)
    else:
        connection.edit_config(candidate=commands)


def get_candidate_config(module):
    candidate = ''
    if module.params['src']:
        candidate = module.params['src']

    elif module.params['lines']:
        candidate_obj = NetworkConfig(indent=1)
        parents = module.params['parents'] or list()
        candidate_obj.add(module.params['lines'], parents=parents)
        candidate = dumps(candidate_obj, 'raw')

    return candidate


def get_running_config(module, current_config=None, flags=None):
    running = module.params['running_config']
    if not running:
        if current_config:
            running = current_config
        else:
            running = get_config(module, flags=flags)

    return running


def save_config(module, result):
    result['changed'] = True
    if not module.check_mode:
        run_commands(module, 'save\r')
    else:
        module.warn('Skipping command `save` '
                    'due to check_mode.  Configuration not copied to '
                    'non-volatile storage')


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list', elements="str"),
        parents=dict(type='list', elements="str"),

        before=dict(type='list', elements="str"),
        after=dict(type='list', elements="str"),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),

        running_config=dict(aliases=['config']),
        intended_config=dict(),

        backup=dict(type='bool', default=False),
        backup_options=dict(type='dict', options=backup_spec),
        save_when=dict(choices=['always', 'never', 'changed'], default='never'),

        diff_against=dict(choices=['intended', 'running']),
        diff_ignore_lines=dict(type='list', elements="str"),
    )
    mutually_exclusive = [('lines', 'src'),
                          ('parents', 'src')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines']),
                   ('diff_against', 'intended', ['intended_config'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    result['warnings'] = warnings

    diff_ignore_lines = module.params['diff_ignore_lines']
    config = None
    contents = None
    flags = []
    connection = get_connection(module)

    console_info = get_console_info(module)
    set_console_info(module)

    if module.params['backup'] or (module._diff and module.params['diff_against'] == 'running'):
        contents = get_config(module, flags=flags)
        config = NetworkConfig(indent=1, contents=contents)
        if module.params['backup']:
            result['__backup__'] = contents

    if any((module.params['lines'], module.params['src'])):
        match = module.params['match']
        replace = module.params['replace']
        path = module.params['parents']

        candidate = get_candidate_config(module)
        running = get_running_config(module, contents, flags=flags)
        if module.params['lines']:
            console_info = update_console_info(module.params['lines'], console_info)
        elif module.params['src']:
            console_info = update_console_info(module.params['src'], console_info)

        try:
            response = connection.get_diff(candidate=candidate, running=running, diff_match=match, diff_ignore_lines=diff_ignore_lines, path=path,
                                           diff_replace=replace)
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

        config_diff = response['config_diff']

        if config_diff:
            commands = config_diff.split('\n')

            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

            result['commands'] = commands
            result['updates'] = commands

            # send the configuration commands to the device and merge
            # them with the current running config
            if not module.check_mode:
                if commands:
                    edit_config_or_macro(connection, commands)

            result['changed'] = True

    running_config = module.params['running_config']
    if not running_config:
        output = run_commands(module, 'show config')
        running_config = output[0]

    set_console_info(module, console_info)

    if module.params['save_when'] == 'always':
        save_config(module, result)

    elif module.params['save_when'] == 'changed' and result['changed']:
        save_config(module, result)

    if module._diff:
        contents = running_config

        # recreate the object in order to process diff_ignore_lines
        running_config = NetworkConfig(indent=1, contents=contents, ignore_lines=diff_ignore_lines)

        if module.params['diff_against'] == 'running':
            if module.check_mode:
                module.warn("unable to perform diff against running-config due to check mode")
                contents = None
            else:
                contents = config.config_text

        elif module.params['diff_against'] == 'intended':
            contents = module.params['intended_config']

        if contents is not None:
            base_config = NetworkConfig(indent=1, contents=contents, ignore_lines=diff_ignore_lines)

            if running_config.sha1 != base_config.sha1:
                result.update({
                    'changed': True,
                    'diff': {'before': str(base_config), 'after': str(running_config)}
                })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
