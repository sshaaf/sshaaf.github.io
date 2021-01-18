---
title: FedUp and Fedora 18
tags: [fedora, fc17, fc18, upgrade]
date: 2013-04-19 07:07:22 +02:00
---


Just now I made the update from Fedora 17 to 18. I didnt know that fedora 18 has a new update util called fedUp.
If you are interested you could read here: https://fedoraproject.org/wiki/FedUp

Just do the following


	yum --enablerepo=updates-testing install fedup


And then


	fedup --network 18


It should ask for a reboot after some downloads, and that should just do the trick. atleast it did for me.
