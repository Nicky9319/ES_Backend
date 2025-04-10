#!/bin/bash

# Update and upgrade system
echo "Updating and upgrading the system..."
sudo apt-get update && sudo apt-get upgrade -y

# Install necessary packages for VNC server
echo "Installing VNC server and required packages..."
sudo apt-get install -y tightvncserver xfce4 xfce4-goodies

# Install desktop environment (XFCE)
echo "Installing XFCE desktop environment..."
sudo apt-get install -y xfce4 xfce4-goodies

# Install and configure VNC server
echo "Installing and configuring VNC server..."
sudo apt-get install -y tightvncserver

# Set up a VNC password
echo "Setting up VNC password..."
vncserver

# Set up VNC configuration to start XFCE
echo "Configuring VNC to start XFCE..."
mkdir -p ~/.vnc
echo -e "#!/bin/bash\n\nxrdb $HOME/.Xresources\nstartxfce4 &" > ~/.vnc/xstartup
chmod +x ~/.vnc/xstartup

# Restart VNC server to apply changes
echo "Restarting VNC server..."
vncserver -kill :1
vncserver :1

# Install a tool to manage VNC as a service (optional)
echo "Setting up VNC as a service..."
sudo apt-get install -y vnc4server

# Allow VNC through firewall (if applicable)
echo "Allowing VNC through the firewall..."
sudo ufw allow 5901/tcp

# Optional: Enable VNC server to start on boot
echo "Enabling VNC server to start on boot..."
echo -e "[Unit]\nDescription=VNC Server\nAfter=multi-user.target\n\n[Service]\nExecStart=/usr/bin/vncserver :1\n\n[Install]\nWantedBy=multi-user.target" | sudo tee /etc/systemd/system/vncserver@.service
sudo systemctl enable vncserver@1.service

# Done
echo "VNC server setup is complete. You can now connect using your VNC client to <server-ip>:5901"

# Finish
echo "Setup complete!"
