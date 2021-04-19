import subprocess

cmd = ["ps", "aux"]

out = subprocess.run(cmd, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, shell=False, cwd=None,
                     timeout=None, env=None,
                     universal_newlines=None)
print(out.stdout)
print(out.stderr)
print(out.returncode)
