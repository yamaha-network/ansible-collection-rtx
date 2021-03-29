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
module: rtx_command
version_added: "2.10"
authors:
  - Yamaha Corporation
short_description: Run commands on remote Yamaha RTX/NVR/FWX/vRX devices.
description:
  - Sends arbitrary commands to an Yamaha RTX/NVR/FWX/vRX device and
    returns the results read from the device. This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
options:
  commands:
    description:
      - List of commands to send to the remote RTX/NVR/FWX/vRX device.
        The resulting output from the command is returned. If the
        I(wait_for) argument is provided, the module is not returned
        until the condition is satisfied or the number of retries has
        expired. If a command sent to the device requires answering a
        prompt, it is possible to pass a dict containing I(command),
        I(answer) and I(prompt).
    required: true
    type: list
    elements: raw
  wait_for:
    description:
      - List of conditions to evaluate against the output of the
        command. The task will wait for each condition to be true
        before moving forward. If the conditional is not true
        within the configured number of retries, the task fails.
        See examples.
    aliases: ['waitfor']
    type: list
    elements: str
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy.  Valid
        values are C(all) or C(any).  If the value is set to C(all)
        then all conditionals in the wait_for must be satisfied.  If
        the value is set to C(any) then only one of the values must be
        satisfied.
    default: all
    choices: ['any', 'all']
    type: str
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the
        I(wait_for) conditions.
    default: 10
    type: int
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
        trying the command again.
    default: 1
    type: int
"""

EXAMPLES = r"""
tasks:
  - name: run show environment on remote devices
    rtx_command:
      commands: show environment

  - name: run show environment and check to see if output contains RTX
    rtx_command:
      commands: show environment
      wait_for: result[0] contains RTX

  - name: run multiple commands on remote nodes
    rtx_command:
      commands:
        - show environment
        - show config

  - name: run multiple commands and evaluate the output
    rtx_command:
      commands:
        - show environment
        - show config
      wait_for:
        - result[0] contains RTX
        - result[1] contains address

  - name: run commands that require answering a prompt
    rtx_command:
      commands:
        - command: 'administrator'
          prompt: 'Password: '
          answer: 'administrator_password'
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
import time

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.parsing import Conditional
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import transform_commands, to_lines
from ansible_collections.yamaha_network.rtx.plugins.module_utils.network.rtx.rtx import run_commands
from ansible_collections.yamaha_network.rtx.plugins.module_utils.network.rtx.rtx import check_args
from ansible_collections.yamaha_network.rtx.plugins.module_utils.network.rtx.rtx import get_console_info, set_console_info
from ansible_collections.yamaha_network.rtx.plugins.module_utils.network.rtx.rtx import update_console_info


def parse_commands(module, warnings):
    commands = transform_commands(module)

    if module.check_mode:
        for item in list(commands):
            if not item['command'].startswith('show'):
                warnings.append(
                    'Only show commands are supported when using check mode, not '
                    'executing %s' % item['command']
                )
                commands.remove(item)
    return commands


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list', elements="raw", required=True),
        wait_for=dict(type='list', elements="str", aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )
    module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )

    warnings = list()
    result = {'changed': False, 'warnings': warnings}
    check_args(module, warnings)
    commands = parse_commands(module, warnings)
    wait_for = module.params['wait_for'] or list()

    try:
        conditionals = [Conditional(c) for c in wait_for]
    except AttributeError as exc:
        module.fail_json(msg=to_text(exc))

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    console_info = get_console_info(module)
    set_console_info(module)

    while retries > 0:
        responses = run_commands(module, commands)

        for item in list(conditionals):
            if item(responses):
                if match == 'any':
                    conditionals = list()
                    break
                conditionals.remove(item)

        if not conditionals:
            break

        time.sleep(interval)
        retries -= 1

    console_info = update_console_info(module.params['commands'], console_info)
    set_console_info(module, console_info)

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result.update({
        'stdout': responses,
        'stdout_lines': list(to_lines(responses)),
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
