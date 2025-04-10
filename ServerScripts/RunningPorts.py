import subprocess

def list_working_ports():
    """List all the ports on which services are currently running."""
    result = subprocess.run(["lsof", "-i", "-P", "-n"], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    ports = set()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) > 8 and ':' in parts[8]:
            port = parts[8].split(':')[-1]
            if port.isdigit():
                ports.add(int(port))
    return sorted(ports)

working_ports = list_working_ports()
print("Working Ports: ", working_ports)
