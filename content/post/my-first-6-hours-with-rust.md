---
title: "My first 6 hours with Rust"
date: 2025-09-01
image: "/images/2025/09/learning-rust.jpg"
tags: ["java", "rust", ]
categories: ["Java", "rust"]
layout: post
type: post
---

**TLDR**; I took a day off from work today, although still most of my time I ended up doing my travel expenses. Talk about priorities. I am the one to blame here totally. 😄

So come around lunch time, thats when all the fluids are ready to do something different. I ended up exploring some basics about Rust. I heard a friend once said, if a prominent person (wonder who that is..) says billions over and over again, somehow people just start believing in billions. Anyways I am totally sold by my youtube feed to explore this a bit. What is this rust thing? And before I go any further, just to let you know I like programming languages and problem solving. I am not hung up on one language. I appreciate them all. Except MS access (oops)

Installation:
Just like you would use something like sdkman for Java. Rust-up is a great library to get started. 
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# to start a new project
cargo new rust_example

# to run
cd rust_example && cargo run

```

## Ownership!
In Java objects are managed by the GC (Garbage collector), we all have a need and dislike relationship with somewhat (my opnion offcourse). And this also means that we primarily deal with references. The cool thing about references is that its easy to build up this amazing object model. The not so very cool thing it managing it and its use of memory. Hence the "Garbage collector 👽". While Java brings a particular reference/object for more accessibility, Rust takes a rather different approach and dictates that there is only one owner at a time. Take an example of the following code which takes a `String` similar to a `StringBuilder`:

```rust
let s1 = String::from("hello"); // s1 owns the String data
let s2 = s1;                 // Ownership MOVES from s1 to s2.
println!("s1: {}", s1);    // Compile-time error: `s1`'s value was moved.
println!("s2: {}", s2);     // s2 is now the valid owner.
```
In Java both s1 and s2 would point to the same reference. However in Rust you cannot do that once the reference has a new `owner`.

To sum up: in Java, when you pass an object, you're passing a reference. Multiple parts of your code can hold references to the same object. In Rust, things are different.
Each value in Rust has an owner. There can only be one owner at a time. When the owner goes out of scope, the value will be dropped (memory is freed).

> This is an interesting concept, I can see how this makes sense.Something I probably have to learn when I implement a complex project.


## References and borrowing
Okay, so at this point everything is owned. Fair enough, but in projects, defining ones own data types etc or helper functions, one does need to share the reference. A reference in Rust is like a pointer but also a guarantee to point to valid data, in other words I think, "it has an owner". By default all references are immutable unless explicitly defined. Furthermore since there can only be one owner at a time, there can only be one mutable reference (`&mut T`) at a time and many immutable references (`&T`).
For example:

```rust
// This function takes an immutable reference to a String.
// It does not take ownership.
fn calculate_length(some_string: &String) -> usize {
    some_string.len()
} // `some_string` goes out of scope, but the data it refers to is NOT dropped.

// This function takes a mutable reference.
fn change(some_string: &mut String) {
    some_string.push_str(", world");
}
``` 
> You can have either one mutable reference `(&mut T)` OR any number of immutable references `(&T)`, but not both at the same time. This is one of Rust's key safety guarantees.

## Structs and Enums
Most applications require some sort of logic and data types. In Rust one can define a Struct for example: 

```rust
struct User {
    username: String,
    email: String,
    sign_in_count: u64,
    active: bool,
}
```
This is just like a Java class with only fields. In essence a struct is like a key-value pairs. 
The values can be used or assigned like this

```rust
fn main() {
    let mut user1 = User {
        email: String::from("someone@example.com"),
        username: String::from("someusername123"),
        active: true,
        sign_in_count: 1,
    };

    user1.email = String::from("anotheremail@example.com");
    println!("User email: {}", user1.email);
}
```

Rust also has Enum but quite different than Java. An enum is a type that can be of several possible variants. The most important `enum` is likely the `Option<T>`, which handles the concept of nullability. While in Java Enum has a fixed set of constants Rust is a little more flexible about it with more complex data structures. This also enables it for pattern matching. For example take a look at the following code. Enum has two types in it Car, Bicycle. `match` is checking the `available_transport`. In Java 21 pattern matching was also introduced as a standard feature and Java 25 has further enhancements to it as well. 

```rust
enum Transport {
    Car(String),
    Bicycle(String),
}

/// Checks the garage and determines which form of transport is available.
fn check_garage() -> Transport {
    let car_model = String::from("Tesla Model Y");
    Transport::Car(car_model)
}

fn main() {
    let available_transport = check_garage();

    // The `match` statement is the standard way in Rust to handle enums.
    // It ensures you handle every possible variant, making your code safer.
    match available_transport {
        Transport::Car(model) => {
            println!("You're taking the car today! It's a {}.", model);
        }
        Transport::Bicycle(brand) => {
            println!("Looks like you're biking today on your {}.", brand);
        }
    }
}
```

## The concept of Self
`self` is analogous to `this` in Java. In Rust its obviously is treated or worked with differently. For example its is a special first parameter in a method that represents the specific instance of the `struct`, `enum` or `trait object` the method is being called on. The key difference is the ownership. 

### 1> &self as An Immutable Borrow
In this case the method can read the data of the instance, but it cannot modify it. This also means the caller retains the full ownership of the instance. After the call is made the instance can be used as before. In the example below the struct can not be assigned a value. 

```rust
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    // This method borrows the Rectangle immutably.
    fn area(&self) -> u32 {
        self.width = 5; // This would cause a compile error! Cannot modify borrowed data.
        self.width * self.height
    }
}
``` 
### 2> &mut self as A Mutable Borrow
In this case the method can both read and modify the data of the instance. The caller retains the ownership, 
Here if you would like to have setters like in Java, you would add the `&mut` for ownership. In the following example I create a Stack<T> using the growable array type from the Rust standard library Vec<T>. For write operations like push and pop I use the `&mut` but for read operations like `is_empty` I do not need ownership hence just `&self` will suffice. 

```rust
struct Stack<T> {
    items: Vec<T>,
}

impl<T> Stack<T> {
    // A "static method" to create a new, empty stack.
    // In Rust, these are called associated functions.
    fn new() -> Self {
        Stack { items: Vec::new() }
    }

    // A method to push an item onto the stack.
    // `&mut self` is a mutable borrow of the instance, like `this` in Java.
    fn push(&mut self, item: T) {
        self.items.push(item);
    }

    // A method to pop an item.
    // It returns an Option<T> because the stack might be empty!
    fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }

    // An immutable borrow to peek at the top item.
    fn peek(&self) -> Option<&T> {
        self.items.last()
    }

    // Check if the stack is empty.
    fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
}

fn main() {
    let mut my_stack = Stack::new();

    my_stack.push(1);
    my_stack.push(2);
    my_stack.push(3);

    println!("Top item is: {:?}", my_stack.peek()); // Some(3)

    let popped = my_stack.pop();
    println!("Popped item: {:?}", popped); // Some(3)

    println!("Is stack empty? {}", my_stack.is_empty()); // false

    my_stack.pop();
    my_stack.pop();
    let last_pop = my_stack.pop();
    println!("Last pop: {:?}", last_pop); // None

    println!("Is stack empty? {}", my_stack.is_empty()); // true
}
``` 

Another interesting thing was the line `let popped = my_stack.pop()` I would have thought for safety I should write something like `let popped: Option<i32> = my_stack.pop();` 
but thats not the case. The compiler looks at the signature of the pop method for `Stack<i32>: fn pop(&mut self) -> Option<T>`. Since it knows T is i32, it knows that this specific call to `pop()` will return a value of type `Option<i32>`. Therefore, it automatically infers that the variable popped must also be of type `Option<i32>`. Okay so thats great, but the compiler is not always going to figure this out. 

**When Do You Need to Add Types?**
**Function Signatures**: Rust requires you to declare the types of all function arguments and the function's return value. This is a deliberate design choice to ensure interfaces are stable and clear.
```rust
fn process_popped_item(item: Option<i32>) {
    match item {
        Some(number) => println!("Processing the number: {}", number),
        None => println!("There was nothing on the stack to process."),
    }
}
```

Same rule will also apply if the entire `Stack<T>` was passed to a function.
```rust
// A function that just inspects the top of the stack
fn inspect_stack(stack: &Stack<i32>) {
    match stack.peek() {
        Some(top_item) => println!("The top item is {}.", top_item),
        None => println!("The stack is empty."),
    }
    // `stack` is just a reference. The original `my_stack` in `main` is untouched.
}

// In main:
// let mut my_stack = ...;
inspect_stack(&my_stack); // We pass a reference using '&'
``` 

**When a Type is Ambiguous**: Sometimes, the compiler can't figure it out on its own. A very common example is the collect() method on iterators, which can create many different kinds of collections.

```rust
let numbers = (0..10); // An iterator of numbers

// This will NOT compile. What kind of collection should this be?
let collected = numbers.collect();

// This is correct. We tell the compiler we want a Vec<i32>.
let collected: Vec<i32> = numbers.collect();
```
**Clarity for Human Readers**: Especially with complex types or long function chains, adding a type annotation can help other developers (or your future self 😄) understand the code more quickly, even if the compiler doesn't need it.

### 3> Taking full ownership with self
This form of self takes full ownership of the instance. The instance is moved into the method. After the method call, the original instance can no longer be used by the caller because it has been moved. Let's say you would like to create a builder pattern. 

```rust
fn build(self) -> Result<Pizza, String> {
        if self.size.is_empty() {
            return Err("Size is a required field.".to_string());
        }

        // Create the final Pizza using the builder's state
        Ok(Pizza {
            size: self.size,
            // Use `unwrap_or` to provide default values for optional fields
            has_stuffed_crust: self.has_stuffed_crust.unwrap_or(false),
            toppings: self.toppings.unwrap_or_else(Vec::new), // Default to an empty vec
        })
    }

    // Example usage
    let cheese_pizza = PizzaBuilder::new("Large").build().unwrap();

```

> Self with a capital `S` is not a variable but a type alias. 

## Public and private
By now I was itching to understand how to make my own datatype outside of main.rs. To do that, first I need to put my types in another file. That file for example is named as bank_account.rs

```rust
    pub struct BankAccount {
        owner: String,
        balance: f64,
    }

    impl BankAccount {
        pub fn new(owner: String) -> Self {
            BankAccount {
                owner, 
                balance: 0.0,
            }
        }

    pub fn deposit(&mut self, amount: f64) {
        if amount > 0.0 {
            self.balance += amount;
            println!("Deposited: ${}", amount);
        } 
    }

    pub fn balance(&self) -> f64 {
        self.balance
    }
}
``` 
At this point if I do not add `pub` keyword to any of the functions then I wont be able to use them. so by default everything is private here. I can then add the following lines to where I want to use this module. 

```rust
mod bank_account;
use bank_account::BankAccount;
```
See a difference here. bank_account.rs is the same as the mod name, however the type that resides in it is BankAccount. Theres probably conventions one can use, but rust doesn't really restrict you with type names. So a little different when defining public classes in Java. 

## Summary
I am sure, there is a lot more, but hey! couple of hours to learn is not bad for a start. I can say I like some semantics here. It also sort of re-wires my brain a bit. At the end a langauge should be the right tool used for the right job. Here are some of my takeaways from today. 

**Memory Management through Ownership**: Unlike Java's Garbage Collector (GC), Rust manages memory using an ownership system. Each value has a single owner, and when the owner goes out of scope, the memory is freed. Assigning a value to a new variable moves ownership, invalidating the original variable.

**Borrowing and References**: To access data without transferring ownership, Rust uses references, a concept known as "borrowing." The compiler enforces a key rule: at any given time, you can have either one mutable reference `&mut T` or any number of immutable references `&T`, but not both simultaneously.

**Data Structuring with Structs and Enums**: Rust uses structs to create custom data types with named fields, similar to a Java class with only member variables. Its enums are more powerful than Java's, as variants can hold data. This enables robust pattern matching with the match statement and is fundamental to features like the `Option<T>` enum for handling nullability.

**Method Receiver Types and self**: The self parameter in a method, analogous to this in Java, explicitly defines how the method interacts with the instance's data. It can be an immutable borrow `&self`, a mutable borrow `&mut self`, or it can take full ownership `self`, which moves the instance into the method.

**Modularity and Default Privacy**: Code is organized into modules, declared with the mod keyword. By default, all items (structs, functions, fields, etc.) within a module are private. The pub keyword must be used to make them public and accessible from outside the module.