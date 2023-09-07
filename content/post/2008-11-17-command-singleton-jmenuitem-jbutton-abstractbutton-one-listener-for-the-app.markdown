---
date: 2008-11-17 21:17:24 +01:00
title: Command, Singleton, JMenuItem, JButton, AbstractButton - One Listener for the app
tags: [computers, design, patterns, gof, howto, java, patterns, programming, singleton, software, command, jmenuitem, jbutton, abstractbutton, swing]
---


Here I would like to demonstrate a simple use of JMenuItems being used with Single Listener for the entire system.
A simple sample of use would probably be SingleInstance Desktop Application.

Lets see how that is done here.

1. First lets create a OneListener class that should be able to listen to ActionEvents and also be able to add Commands to itself. Please refer to my previous post on Command,Singleton if you would like to see more about this patterns and there usage.

```
	package com.shaafshah.jmenus;

	import java.awt.event.ActionEvent;
	import java.awt.event.ActionListener;
	import java.util.ArrayList;
	import javax.swing.AbstractButton;

	// Implements the ActionListener and is a Singleton also.

	public class OneListener implements ActionListener{

		private static OneListener oneListener = null;

		// Holds the list of all commands registered to this listener
		private ArrayList<Command> commandList = null;

		// A private constructor
		private OneListener(){
			commandList = new ArrayList<Command>();
		}

		// Ensuring one instance.
		public static OneListener getInstance(){
			if(oneListener != null)
				return oneListener;
			else return oneListener = new OneListener();
		}

		// Add the command and add myself as the listener
		public void addCommand(Command command){
			commandList.add(command);
		    ((AbstractButton)command).addActionListener(this);
		}


		// All Events hit here.
		@Override
		public void actionPerformed(ActionEvent e) {
			((Command)e.getSource()).execute();
		}

	}
```


In the above code, the addCommand method adds the command Object and adds a listener to it.
Now how is that possible.
Basically because I am categorizing my UI objects as Commands with in the system having some UI. And I am also assuming that these commands are Currently AbstractButton i.e. JMenuItem, JButton. Lets have a look at the Command Interface and its Implementation.

```
	public interface Command {
		public void execute();
	}
```

And the implementation, note that the Command is an interface where as the class is still extending a UI object.

```
	import javax.swing.JMenuItem;

	public class TestCmd extends JMenuItem implements Command{

	public TestCmd() {
		super("Test");
		OneListener.getInstance().addCommand(this);
		}

	@Override
	public void execute() {
		System.out.println("HelloWorld");
		}
	}
```

Personally don't like calling the OneListener in the constructor of the class but just for the sake of simplicity of this post I have left it that way. There are many different ways to omit it.

So the TestCmd is a JMenuItem but is also a Command and thats what the OneListener understands.
As this commads Listener is also OneListener all ActionEvents are thrown there and from there only the Command.execute is called on.

So now you dont have to worry about what listeners are you in. The only thing you know is that when execute is called you need to do your stuff.

You can download the code from
[Here](images/2008/11/jmenus.zip)

Hope this helps.
