---
title: Howto setup ssh with selinux and firewalld
tags: [how-to, fedora, ssh, firewalld, firewall, selinux, yum]
date: 2013-07-20 14:40:47 +02:00
---




While running fedora, if you want to change the port for your ssh, just changing the firewall rules will not make a difference.
If you are running selinux its important that you change the policy to allow a different port as well. I did learn it the hard way though, hopefully the following guide should be helpful.

Lets start by an introduction to semanage.

From man

**Description**

semanage is used to configure certain elements of SELinux policy without requiring modification to or recompilation from policy sources. This includes the mapping from Linux usernames to SELinux user identities (which controls the initial security context assigned to Linux users when they login and bounds their authorized role set) as well as security context mappings for various kinds of objects, such as network ports, interfaces, and nodes (hosts) as well as the file context mapping. See the EXAMPLES section below for some examples of common usage. Note that the semanage login command deals with the mapping from Linux usernames (logins) to SELinux user identities, while the semanage user command deals with the mapping from SELinux user identities to authorized role sets. In most cases, only the former mapping needs to be adjusted by the administrator; the latter is principally defined by the base policy and usually does not require modification.


Which package provides semanage? I use fedora so yum in this case should help.


	dnf provides semanage


I have the following package that provides semanage so lets install that.


	dnf install policycoreutils-python-utils


Additionally if you would like to check the ports in the semanage policy you could do the following


	semanage port --list



So before I even make any changes to my sshd_config lets add the port config into the selinux policy.


	semanage port -a -t ssh_port_t -p tcp 52022


And if I take the listing again I should get something like this
ssh_port_t                     tcp      52022, 22

The output above means that there are two ports allowed here for ssh both 52022 and 22. Which is fine, incase one wants to change back to 22.

Okay now all looks good, lets move on and add the rules into the firewall. If you dont use the --permanent the rule will not be saved on service restart so thats important. The following command adds the port 42 on tcp in zone public.


	firewall-cmd --permanent --zone=public --add-port=52022/tcp

To test out in the current session try without permanent.

This should be all set now. Now you can go ahead and change the port in the sshd_config to 52022


	vi /etc/ssh/sshd_config


If all of the above is done. restart the service

	systemctl restart sshd


Take the status which should look similar to the following

	systemctl status sshd


23:13:57 host.com systemd[1]: Started OpenSSH server daemon.

23:13:57 host.com sshd[795]: Server listening on X.X.X.X port 52022.
