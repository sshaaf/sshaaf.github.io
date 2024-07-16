---
title: Abstract Factory pattern
tags: [homputers, design, design-patterns, gof, howto, java, patterns, programming, singleton, singleton-pattern, software, software-development]
date: 2008-10-10 10:20:10 +02:00
categories: ["Java"]
---



Factories have been a key pattern in building applications, its fascinatingly simple, effective and to the point. When starting to learn a design oriented approach to applications or API, I would always recommend a factory pattern as one of the key starting notes of highlight in your design.

So today I am talking about the Abstract Factory pattern. Its not an "abstract" class or object that you call a pattern. But its a Factory of facotries and that is what exactly makes it so much wordingly abstract. Having "abstract" classes is there but just some other side of the coin.

When should I use an Abstract Factory:
+ Independence of how products are created, composed or represented
+ You need enforcable constraints for the products used as a group
+ You need to reveal only the interfaces of products and not thier implementation as part of a bigger picture.

So lets begin with the fun.

This is how I plan to implement it:
Has A:
+ Product has a Specification
+ Factory has a Product
+ FactoryManager has FactoryConstants
+ FactoryManager has ComputerFactory

Is A:
+ BFactory is a ComputerFactory
+ AFactory is a ComputerFactory

Not shown.
+ ProductA is a Product
+ ProductB is a Product

Diagram
![Alt text](/images/2008/10/abstractfactory.jpeg)

Creating a simple factory that returns products.

```
	public abstract class ComputerFactory {
		public abstract String getName();
		public abstract Product[] getProducts();
		public abstract Product getProduct(int ProductID);
	}
```

Implementation of the ComputerFactory

```
	public class AFactory extends ComputerFactory {

		public String getName(){
			return "A";
		}

		public Product[] getProducts(){
			return null;
		}

		public Product getProduct(int productID){
			switch(productID){
		case 1:
			return new ProductA();

		case 2:
			return new ProductB();

		default:
			throw new IllegalArgumentException("Sorry you hit the wrong factory, we closed down in 1600 BC");
			}
		}
	}
```

A register base for factories. Refer to the main method for use later in this post.

```
	public interface FactoryConstants {
		public int A = 1;
 		public int B = 2;
	}
```

The main Entrant class. the Factory Manager that will give the ComputerFactory resultant. Its assumed to be a Singleton as it registers as a Creator in the system (assumption).

```
	public class FactoryManager{
		private static FactoryManager factoryManager = null;
		private FactoryManager(){}
 		public static FactoryManager getInstance(){
  			if(factoryManager != null){
   				return factoryManager;
  			}
  			else return factoryManager = new FactoryManager();
 		}
 
		public ComputerFactory getFactory(int factory) throws IllegalArgumentException{
  			switch(factory){
   				case FactoryConstants.A:
   					return new IBMFactory();
   				case FactoryConstants.B:
   					return new SUNFactory();
   				default:
   					throw new IllegalArgumentException("Sorry you hit the wrong factory, we closed down in 1600 BC");
  			} 
 	     	}
	}
```

A main method to test the AbstractFactory

```
	public static void main(String args[]){
  		System.out.println(FactoryManager.getInstance().getFactory(FactoryConstants.A).getName());
  		System.out.println(FactoryManager.getInstance().getFactory(FactoryConstants.B).getName());
  		System.out.println(FactoryManager.getInstance().getFactory(3).getName());
	}
```


You can find the complete code listing
[here](/images/2008/10/abstractfactory.zip)
