import subprocess
import os


def exec_cmd(cmd: str | list[str],
             *,
             encoding: str = 'utf-8') -> str:
    default_shell = os.getenv('SHELL', '/bin/bash')

    stdout, stderr = subprocess.Popen(cmd,
                                      shell=True,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      executable=default_shell).communicate()
    if stderr:
        raise Exception(stderr.decode(encoding))
    return stdout.decode(encoding)
