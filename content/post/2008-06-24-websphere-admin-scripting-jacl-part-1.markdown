---
title: Creating the MQQueueConnectionFactory with wsadmin scripting  - JACL Part 1.
tags: [howto, java, programming, websphere, wsadmin, jacl, mq, administrator, scripting, sysadmin, ibm]
category: Configuration
date: 2008-06-24 15:44:31 +02:00
---



While working my way in some piece of long java code I came across this huge pile of sand that just shattered me off every bit of patience I was left with. The dilemma all of us face every second day. *CONFIGURATIONS!!*

While my sarcastic mind was just saying Congratulations to me instead. And just how the - would you expect me to start configuring now.

So what exactly is my problem? I have a list of MQs, Factories, datasource, providers etc.. that I need to configure. And every time I create a new profile on my RAD (Rational Application Developer) I have to manually goto the Admin console and configure them.

With the very useless bit of linux I am acquainted too I cant live with clicks at least while programming.

As I am working with websphere and its a biggy in all those names I thought the guys would be smart and would at least have something in the box for people like me. Well guess what I was right.

IBM has provided two languages for scripting.

1. JACL
2. Jython

If I am not wrong JACL will be deprecated out in future releases and Jython would be the tool for our scripting bit.
[Here](http://publib.boulder.ibm.com/infocenter/wasinfo/v6r1/index.jsp?topic=/com.ibm.websphere.nd.doc/info/ae/ae/rmig_deprecationlist.html)

In this article I will just go briefly with JACL and move to Jython in the next version where we will be able to configure the data sources in the websphere.

So what exactly is JACL. or pronounced as "JACKAL"

Jacl, Java Command Language, is much like/version of the tcl scripting language for the Java. It runs on the JVM much like we hear about JRuby and the interpreter is written completely in Java.

For more details on the language itself you could go [Here](http://publib.boulder.ibm.com/infocenter/imshelp1/v3r0/index.jsp?topic=/com.ibm.sif.doc/jaclabout.html)

Lets get down to business: *How to create a Webspehere MQ Connection Factory with wsamdin using JACL.*
You would already have some of the details of the queues but some you will need to extract.

*Step 1.
*Identify the Provider for your Factory. By default this is the name for it. If you have created a new provider with a different name then specify it here.

'''
	set tmp1 "WebSphere MQ JMS Provider"
'''

*Step 2.*
Now you would need to find the CELL NAME and the NODE NAME of your server
A typical location to my websphere profile's Node configuration file is as follows
C:\Programs\IBM\Rational\SDP\6.0\runtimes\base_v6\profiles\test_wsp\config\cells\BNode05Cell\nodes\BNode05
The cell name in this location is after \cells\ i.e. BNode05Cell
And the node name is at the end after \nodes\ i.e. BNode05

'''
	set newjmsp [$AdminConfig getid /Cell:CELLNAMECell/Node:NODENAME/JMSProvider:$tmp1/]
'''

*Step 3.*
Now you need to specify the Factories properties.

The properties I plan to setup are as follows.
	Name, jndiName,QueueManager, sname, port, channel, ttype, xaenabled

To check what are the required parameters for the Factory you can run the following command on the wsadmin console.

'''
	$AdminConfig required WASQueueConnectionFactory
	Example output:
	wsadmin $AdminConfig required WASQueueConnectionFactory
	Attribute                       Type
	name                            String
	jndiName                        String

'''

*Where will I find the wsadmin?*
It is typically placed in the bin directory of your server.
In my case its lying in my RAD installation directory as
../Rational/SDP/6.0/runtimes/base_v6/bin

To invoke the wasadmin, just open your terminal and move to the bin dir where you can simply call it by typing wsadmin.  By doing so you would be invoking the default profile. if you want to specify the profile then use the switch -profileName YOURPROFILENAME

To see the all parameters required and optional write the following command on the console.

'''
	$AdminConfig attributes WASQueueConnectionFactory
	Example output:
	wsadmin $AdminConfig attributes WASQueueConnectionFactory
	"XAEnabled boolean"
	"authDataAlias String"
	"authMechanismPreference ENUM(BASIC_PASSWORD, KERBEROS)"
	"category String"
	"connectionPool ConnectionPool"
	"description String"
	"jndiName String"
	"logMissingTransactionContext boolean"
	"manageCachedHandles boolean"
	"mapping MappingModule"
	"name String"
	"node String"
	"preTestConfig ConnectionTest"
	"propertySet J2EEResourcePropertySet"
	"provider J2EEResourceProvider@"
	"providerType String"
	"serverName String"
	"sessionPool ConnectionPool"
	"xaRecoveryAuthAlias String"
'''

I have added some extra optional parameters for those of us who are using extra options.

'''
	set name [list name NAME]

	set jndi [list jndiName jms/JNDINAME]

	set qManager [list queueManager QMANAGER]

	set sname [list host HOSTNAME]

	set port [list port 1414]

	set channel [list channel CHANNEL]

	set ttype [list transportType CLIENT]

	set xa [list XAEnabled True|false]
'''

*Step 4.*
Now set all parameters in one string so that they can be passed to the command as one.

'''
	set mqcfAttrs [list $name $jndi $qManager $sname $port $channel $ttype $xa]
'''

*Step 5.*
Now to create the Factory use the following command. This will add the factory to the node and cell mentioned earlier in step 2.

'''
	$AdminConfig create MQQueueConnectionFactory $newjmsp $mqcfAttrs
'''

Once it is created it is not saved and only stays in the current session. So to save it run the following command. And you should be all set.

'''
	$AdminConfig save
'''

You can alternatively also save this script in a file on your local system. And run it by passing it to the wasadmin. Follwing is a sample command.

'''
	wsadmin -profileName test_wsp -f $SCRIPT_FILENAME_LOCATION$
'''

Complete code listing is as follows.

'''
	set tmp1 "WebSphere MQ JMS Provider"

	set newjmsp [$AdminConfig getid /Cell:CELLNAMECell/Node:NODENAME/JMSProvider:$tmp1/]

	set name [list name NAME]

	set jndi [list jndiName jms/JNDINAME]

	set qManager [list queueManager QMANAGER]

	set sname [list host HOSTNAME]

	set port [list port 1414]

	set channel [list channel CHANNEL]

	set ttype [list transportType CLIENT]

	set xa [list XAEnabled false]

	set mqcfAttrs [list $name $jndi $qManager $sname $port $channel $ttype $xa]

	$AdminConfig create MQQueueConnectionFactory $newjmsp $mqcfAttrs

	$AdminConfig save
'''

 
