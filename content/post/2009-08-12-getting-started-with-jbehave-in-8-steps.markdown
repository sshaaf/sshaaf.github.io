---
title: Getting started with JBehave in 8 steps.
tags: [java, jbehave, unit-testing]
date: 2009-08-12 16:13:30 +02:00
categories: ["Java"]
layout: post
type: post
---


This post is about JBehave and how to quickly get started with it. If you would like to know about BDD please use the following link.
[What is Behavioral Driven Development?](http://en.wikipedia.org/wiki/Behavior_Driven_Development)

Today I have used JBehave for the first time. It does have some convincing factors for instance diving requirements into scenarios which map pretty nicely to the tests that are written with in the Steps. Thus it seems like it would be easier for Stakeholder/s to use it as a good guideline for the initial requirements. Its always quite usual to come up to some disagreements about the development however the tool does help to bring forth the ease for stake holders who really dont have to get into writing code but will have a technical jargon to communicate through to the developers in shape of scenarios.

So the first things come up.
1. Create a Java project in Eclipse.
2. Download the JBehave latest version from the [website](http://jbehave.org/software/download/) and add the jar files to your project build classpath
3. Create a scenario file and name it as user_wants_to_shop.scenario

Add the following text to the file


	Given user Shaaf is logged in
	Check if user shaaf is Allowed to shop
	Then show shaaf his shopping cart


The lines above simply state the rules for the scenario we are about to create.

4. Now we will create a java file mapping to it.

Create a new class with the name corresponding to the same as the .scenario file
UserWantsToShop.java

Add the following code to it

```
	import org.jbehave.scenario.PropertyBasedConfiguration;
	import org.jbehave.scenario.Scenario;
	import org.jbehave.scenario.parser.ClasspathScenarioDefiner;
	import org.jbehave.scenario.parser.PatternScenarioParser;
	import org.jbehave.scenario.parser.ScenarioDefiner;
	import org.jbehave.scenario.parser.UnderscoredCamelCaseResolver;

	public class UserWantsToShop extends Scenario {

        // The usual constructor with default Configurations.

	public UserWantsToShop(){
		super(new ShoppingSteps());
	}

	// Mapping .scenario files to the scenario. This is not by default.
	public UserWantsToShop(final ClassLoader classLoader) {
        	super(new PropertyBasedConfiguration() {
            	public ScenarioDefiner forDefiningScenarios() {
                	return new ClasspathScenarioDefiner(
                    	new UnderscoredCamelCaseResolver(".scenario"),
                    	new PatternScenarioParser(this), classLoader);
            		}
        	}, new ShoppingSteps());
    	}

	}
```

5. Just that we now have steps we need some place to put the logic for the Steps in the Scenarios. So we create a new Steps class ShoppingSteps.java

```
	import org.jbehave.scenario.annotations.Given;
	import org.jbehave.scenario.annotations.Then;
	import org.jbehave.scenario.annotations.When;
	import org.jbehave.scenario.steps.Steps;

	public class ShoppingSteps extends Steps {}
```

6. Now you can run the Scenario by running it as a Junit Test.

Following should be the output

	Scenario:

	Given I am not logged in (PENDING)
	When I log in as Shaaf with a password JBehaver (PENDING)
	Then I should see my "Shopping Cart" (PENDING)


This means that none of the scenario requirements have been implemented as yet. But the test result should be green to show there are no problems with our setup.

Now lets add the implementation to the tests.

7. Add the body to the ShoppingSteps. I have added the comments with the methods.

```
        // Given that a user(param) is loggen in
	@ Given("user $username is logged in")
	public void logIn(String userName){
		checkInSession(userName);
	}

        // Check if the user is allowed on the server
	@ When("if user $username is $permission to shop")
	public void isUserAllowed(String userName, String permission){
		getUser(userName).isUserAllowed().equals(permission);
	}

       // finally then let him use the shopping cart.
	@ Then("show $username his Shopping cart")
	public void getMyCart(String userName, String cart){
		getUserCart(userName);
	}
```


8. Now you should try to run the scenario again. And all of the test should be green. I have not implemented the actual methods so they will be red. :-)
