# Copyright (C) Yamaha Corporation.
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import re

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import Connection, ConnectionError

_DEVICE_CONFIGS = {}

def get_connection(module):
    if hasattr(module, '_rtx_connection'):
        return module._rtx_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module._rtx_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._rtx_connection


def get_capabilities(module):
    if hasattr(module, '_rtx_capabilities'):
        return module._rtx_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module._rtx_capabilities = json.loads(capabilities)
    return module._rtx_capabilities


def check_args(module, warnings):
    pass


def get_config(module, flags=None):
    flags = to_list(flags)

    section_filter = False
    if flags and 'section' in flags[-1]:
        section_filter = True

    flag_str = ' '.join(flags)

    try:
        return _DEVICE_CONFIGS[flag_str]
    except KeyError:
        connection = get_connection(module)
        try:
            out = connection.get_config(flags=flags)
        except ConnectionError as exc:
            if section_filter:
                module.warn("section %s" % section_filter)
                out = get_config(module, flags=flags[:-1])
            else:
                module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS[flag_str] = cfg
        return cfg


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)
    try:
        return connection.run_commands(commands=commands, check_rc=check_rc)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def load_config(module, commands):
    connection = get_connection(module)

    try:
        resp = connection.edit_config(commands)
        return resp.get('response')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def get_console_info(module):
    console_info = {
        'character': 'no console character',
        'lines': 'no console lines',
        'columns': 'no console columns'
    }

    config = run_commands(module, 'show config | grep console')
    config_txt = config[0]

    config_txt_match = re.search(r'(console character (.+))', config_txt)
    if config_txt_match:
        console_info['character'] = config_txt_match.group(1)

    config_txt_match = re.search(r'(console lines (.+))', config_txt)
    if config_txt_match:
        console_info['lines'] = config_txt_match.group(1)

    config_txt_match = re.search(r'(console columns (\d{2,}))', config_txt)
    if config_txt_match:
        console_info['columns'] = config_txt_match.group(1)

    return console_info


def set_console_info(module, console_info=None):
    try:
        if console_info:
            run_commands(module, console_info['character'])
        else:
            run_commands(module, 'console character ascii')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='unable to set console character'))

    try:
        if console_info:
            run_commands(module, console_info['lines'])
        else:
            run_commands(module, 'console lines infinity')
    except ConnectionError as exshc:
        module.fail_json(msg=to_text(exc, errors='unable to set console lines'))

    try:
        if console_info:
            run_commands(module, console_info['columns'])
        else:
            run_commands(module, 'console columns 200')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='unable to set console columns'))


def update_console_info(commands, console_info):

    character = [c_char for c_char in commands if 'console character' in c_char]
    if character:
        console_info['character'] = character[0]

    lines = [c_lines for c_lines in commands if 'console lines' in c_lines]
    if lines:
        console_info['lines'] = lines[0]

    columns = [c_columns for c_columns in commands if 'console columns' in c_columns]
    if columns:
        console_info['columns'] = columns[0]

    return console_info
