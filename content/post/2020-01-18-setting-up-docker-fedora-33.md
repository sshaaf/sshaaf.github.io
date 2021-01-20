---
title: "Setup docker on Fedora 33"
images:
tags: [config, docker, fedora, install]
date: 2020-01-18
---

Here is a quick list of things that worked for me to setup docker on Fedora 33.
I followed the guidelines [here](https://docs.docker.com/engine/install/fedora/).
Plus some more to config the firewall and user access.

```
# Adding the docker repo to install.
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager \
    --add-repo \
    https://download.docker.com/linux/fedora/docker-ce.repo

# Install the packages
sudo dnf install docker-ce docker-ce-cli containerd.io

# Enable and start docker
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl status docker


# Adding rules to the firewall
sudo firewall-cmd --permanent --zone=FedoraWorkstation --add-masquerade
sudo firewall-cmd --permanent --zone=trusted --add-interface=docker0


# Create and add your user to the group
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Test if its working
docker run hello-world
```

The last command should print a nice standard output from the hello-world container. 
