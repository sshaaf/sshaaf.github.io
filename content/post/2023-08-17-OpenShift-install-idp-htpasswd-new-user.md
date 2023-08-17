---
title: How-to configure your first user with OpenShift IDP - htpasswd
tags: [kubernetes, openshift, configuration, htpasswd]
Category: Java
date: 2023-08-17 09:15:22 +02:00
image: /images/2023/08/17/brett-jordan-D44kHt8Ex14-unsplash.jpg
---

There are multiple options to configure OpenShift integration with an IDP. Usually one would use something like an LDAP, AD (Active Directory) for use in a production cluster or a corporate environment. This guide is a basic how-to in configuring using the htpasswd file which is one of the IDP integration options in Openshift 4.x. 

**htpasswd** is a tool used to create and update the flat-files used to store usernames and password for basic authentication of HTTP users. These flat-files are commonly used by the Apache HTTP Server, as well as some other server software, to provide password protection for web content.

Okay lets do this. 

You want to run the following command on your linux/unix box. This command should create a new .htpasswd file (because of -c), use bcrypt encryption for the password (because of -B), and take the password directly from the command line (because of -b).

```
htpasswd -c -B -b myhttpasswdfile.htpasswd mydesireduser mypassword
```

- `httpasswd` - the cli to generate the file
- `-c` - This option is used to create a new password file. If the specified password file already exists, using this option will overwrite it. Be cautious when using -c to ensure you don't unintentionally erase existing files.
- `B` - This option tells htpasswd to use the bcrypt encryption for the password. Bcrypt is a strong method for hashing passwords, and it's recommended over the older methods like MD5 or SHA because of its resistance to brute-force attacks.
- `b` - This option allows you to specify the password on the command line rather than being prompted for it. This can be helpful in scripting but is considered less secure because the password can be viewed in the command history or by other users using commands like ps on UNIX-based systems.

Okay now that we have a simple htpasswd file with one user. Lets add it to OpenShift. 

Login to your OpenShift Console and hit this URL:\
 `<Your OpenShift Console>/k8s/cluster/config.openshift.io~v1~OAuth/cluster`

Or Goto `Adminsitration > Cluster Settings >` Tab "Configuration" and Select OAuth. like the following screenshot

![alt_text](/images/2023/08/17/OpenShift-ClusterSettings-Config-OAuth.png "OpenShift Cluster Settings, Config OAuth")

Okay perfect once at the OAuth Config screen, click add under `Identity providers`, you should be able to see the dropdown list as follows. Select htpasswd from it. 

![alt_text](/images/2023/08/17/OpenShift-OAuth-htpasswd-select.png "OpenShift OAuth types")

And then lets just browse to the htpasswd file created and press add. This will take a couple of secs and should be ready as the CR is submitted. What OpenShift will do in the backgroud is create the htpasswd OAuth provider and it will sync to all the master nodes under `/etc/origin/master/`. 

![alt_text](/images/2023/08/17/OpenShift-OAuth-htpasswd-config.png "OpenShift Config")

You should now be able to login via `oc login` or via the OpenShift console. 
Incase of any issues check the tips [here for diagnostics](https://access.redhat.com/solutions/4110561) or [docs](https://docs.openshift.com/container-platform/4.13/authentication/identity_providers/configuring-htpasswd-identity-provider.html)


Header background image by [Brett Jordan](https://unsplash.com/@brett_jordan?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText)
  