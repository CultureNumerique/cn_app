#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import os
import shlex
import subprocess
import sys


from django.utils import timezone

# see in cn_app.settings.py logger declaration
logger = logging.getLogger(__name__)


def run_shell_command(command_line):
    """ Utility to run shell commands """
    command_line_args = shlex.split(command_line)
    logger.warn('%s | Subprocess: %s ' % (timezone.now(), command_line))
    try:
        command_line_process = subprocess.Popen(
            command_line_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env={'PYTHONPATH': os.pathsep.join(sys.path)},
        )
        process_output, _ = command_line_process.communicate()
        logger.warn(process_output)
        returncode = command_line_process.returncode
    except (OSError, ValueError) as exception:
        logger.warn('%s | Subprocess failed' % timezone.now())
        logger.warn('Exception occured: ' + str(exception))
        return False, 'no output'
    else:
        logger.warn('%s | Subprocess finished' % timezone.now())
    if returncode == 0:
        return True, process_output
    else:
        return False, process_output


def cnrmtree(path):
    """ custom rmtree func to overcome unicode files bug """
    for root, dirs, files in os.walk(path.encode('utf-8'), topdown=False):
        for f in files:
            os.remove(os.path.join(root, f).decode('utf-8'))
        for d in dirs:
            os.rmdir(os.path.join(root, d).decode('utf-8'))
