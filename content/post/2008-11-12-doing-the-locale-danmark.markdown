---
title: Doing the Locale - Danmark
tags: [howto, java, programming, software, software-development, utils, tips, locale, internationalization]
date: 2008-11-12 14:52:08 +01:00
categories: ["Java"]
layout: post
type: post
---


The following illustrates how to get the Number format working with a danish locale.

```
	import java.text.NumberFormat;
	import java.util.Currency;
	import java.util.Locale;


	public class TestLocale {

	public static void main(String args[]){
		// Create a Locale for Danmark
		Locale DANMARK = new Locale("da","DK");

 		// get the currency instance for this locale.
 		Currency krone = Currency.getInstance(DANMARK);

 		// Get a Number format for the locale.
 		NumberFormat krFormat = NumberFormat.getCurrencyInstance(DANMARK);
 		// A symbol for the currency
 		String symbol = krFormat.getCurrency().getSymbol();
 		// A double amount
 		double amount = 10000.25;
		// print it out after formatting.
 		System.out.println(krFormat.format(amount));
 		}
	}
```
