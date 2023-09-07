---
title: Creating the MQQueues with wsadmin scripting - JACL Part 2
tags: [howto, java, programming, websphere, wsadmin, jacl, mq, administrator, scripting, sysadmin, ibm, mqqueue]
category: Configuration
date: 2008-06-25 14:40:47 +02:00
---



Yesterday I wrote an article about creating and configuring the MQQueueConnectionFactory with the JACL on the wsadmin console. The other half of the article that was left out was to create the queues also.

The world looks pretty much the same today and my /etc/profile doesnt seemed to have been sourced again. Good we dont need a restart.

You would find some of the steps to be similar and that is because we are running on the same configs.

*Step 1.*
Identify the Provider for your Queue. By default this is the name for it. If you have created a new provider with a different name then specify it here.
```
	set tmp1 "WebSphere MQ JMS Provider"
```

*Step 2.*
Now you would need to find the CELL NAME and the NODE NAME of your server
A typical location to my websphere profile’s Node configuration file is as follows
C:\Programs\IBM\Rational\SDP\6.0\runtimes\base_v6\profiles\test_wsp\config\cells\BNode05Cell\nodes\BNode05
The cell name in this location is after \cells\ i.e. BNode05Cell
And the node name is at the end after \nodes\ i.e. BNode05

	```
	set newjmsp [$AdminConfig getid /Cell:CELLNAMECell/Node:NODENAME/JMSProvider:$tmp1/]
	```

*Step 3.*
You would now need to set the attributes that go into the queue.

To see all the attributes you can simply run the following command

```
	$AdminConfig [required|attributes] MQQueue
```

i.e. required or attributes

The attributes that I will be setting in the following commands are

```
	name, jndiName, baseQueueName, targetclient
	set name [list name NAME]
	set jndi [list jndiName jms/jndiName]
	set baseQN [list baseQueueName BASEQUEUENAME]
	set targetclient [list targetclient MQ]
```

You can see in the above example the target client is set to MQ it can be JMS based on your configuration.

*Step 4.*

Now set all parameters in one string so that they can be passed to the command as one.

```
	set mqqAttrs [list $name $jndi $baseQN $targetclient]
```

*Step 5.*
Now to create the MQQueue use the following command. This will add the Queue to the node and cell mentioned earlier in step 2.

```
	$AdminConfig create MQQueue $newjmsp $mqqAttrs
```

Once it is created it is not saved and only stays in the current session. So to save it run the following command. And you should be all set.

```
	$AdminConfig save
```

You can alternatively also save this script in a file on your local system. And run it by passing it to the wasadmin. Follwing is a sample command.

```
	wsadmin -profileName test_wsp -f $SCRIPT_FILENAME_LOCATION$
```

Complete code listing is as follows.

```
	set tmp1 "WebSphere MQ JMS Provider"

	set newjmsp [$AdminConfig getid /Cell:HOSTNAMENode04Cell/Node:HOSTNAMENode04/JMSProvider:$tmp1/]

	set name [list name Q.REPLY]
	set jndi [list jndiName jms/Q.REPLY]
	set baseQN [list baseQueueName Q.SYSTEM]
	set targetclient [list targetclient MQ]
	set mqqAttrs [list $name $jndi $baseQN $targetclient]

	$AdminConfig create MQQueue $newjmsp $mqqAttrs

	$AdminConfig save
```
