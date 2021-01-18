---
title: Install log; fedora 23, Virtualbox and windows 10
tags : [ virtualization, beginner, admin, tutorial ]
category : How-to
date: 2016-04-06
---



I have been using Linux for quite some time now, and jumping from windows xp to windows 10 was a huge change for me.
Not just that I had completely forgotten what windows was all about, configs, screens, services. Anyways, I made a quick compilation of how you could run Fedora 23 and on VirtualBox running on windows 10.


**Software versions**
- Windows: 10
- VirtualBox: 5.0.16.x
- Fedora: 23


Sidetrack tip: Even though the installer was in English , it changed my language to Danish.
To change it goto indstillinger/sprog and change the options to English. that worked.

And another thing with the surface pro keyboard I have is that it doesnt have the right ctrl key, which was important for VirtualBox host key to switch between guest and host etc. Following helped with that. To change that you could goto preferences and then input. Change the host key there. I chose left ctrl not the optimal since whenever I want to do a ctrl+c in the guest is switches back to host. So beaware of what you would like to choose.


After I installed Fedora, the screen size was very small. I changed the default screen settings for VirtualBox but didnt help. It was quite evident I need the guest additions.

Fixing that meant the right guest addtions should be installed. Not so surprising as the guest additions are not available for Fedora 23 or rightly put not for the version of Xorg.


So first you would need to downgrade your xorg.
If you are root, something like this should help

	dnf –showduplicates –allowerasing –releasever=22 downgrade xorg-x11-server-Xorg


Then you would need to install kernel-devel and gcc, to make sure the installer doesnt fail

	dnf -y install kernel-devel gcc

Plus a few kernel headers that the installer *might depend on. It said might in the log so stating it direct from the source.

	dnf -y install kernel-devel-4.2.3-300.fc23.x86_64

I tried unmounting the guest addtions and then try to install via menu but didnt work. So I just unmounted and rebooted the guest. And press install then, just worked fine for me.

And now I can run my Fedora on a surface pro4, in a full screen mode and use the touch aswell.

Install node.js and azure-cli coming up next.




**References:**

A nice page on how to downgrade Xorg
http://gamblisfx.com/install-virtualbox-guest-additions-on-fedora-23/

A nice video explainig how to install guest additions for fc23.
https://www.youtube.com/watch?v=k6vsycIoho0
