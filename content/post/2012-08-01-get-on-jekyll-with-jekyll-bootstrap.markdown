---
title: Get on Jekyll with Jekyll bootstrap
tags: [blog, static-sites, ruby, jekyll, jekyll-bootstrap, wordpress]
date: 2012-08-01
Description: "Jekyll-Bootstrap makes it easy to get started with Jekyll, if you are looking for a static site generator then you are at the right place"
---




There has been an era, where we have thought about and implemented blog engines such as wordpress and the like, but then one asks why did we do that in the first place.
Good things that come to mind, rich text editing, comments, dynamic content. The last one is a bit of an over kill though , at least in my case. I just host a personal blog, have enough technical knowledge to use tools as git, ruby etc. So yes knowledge is there and perhaps that makes me itchy a bit when I have to think that

* I write content that goes into a database.
* The server retrieves content on every server call (almost) to get that dynamic content in shape of an sql and do some magic and show my page in html. Which was the idea in the first place.
* Then the server has to be dynamic module aware etc etc.


Well where some would argue about other tactics to make life simpler, like caching etc.

So the use case is simple.

One important feature that has made me stuck to something like wordpress for a long while has been commenting. I was happy to recieve comments on what I had wrote/said, sometimes not so happy with the spam and could moderate them etc. So yes I rememmber that as one of the useful features otherwise I was typically quite *screwed*.

But then again, something like Disqus changes the likes compeletely. Now you had the power of having a comment anywhere, it didnt matter if you had a dynamic hosting server or not. plain and simple write an html, add a script and there you go. moderation, migrations, yes! actually double yes!! it can migrate your wordpress comments. wola!

With that issue out of the window nothing stopped me in pursuing my goal of a static engine that would just spit out html based on something as simple as markdown.

So there you go, I said it. I turned to [jekyll] (www.jekyllrb.com)

A simple blog aware static site generator, takes simple input of markdown or textile and spits out your site.

One of the tools that I used was jekyll-bootstrap, it uses the twitter-bootstrap theme, and preconfigures the entire directory structure to get started.

So running as simple as jekyll on the command line renders a complete static site for you.

There is a good tutorial for begniner on the [jekyll-bootstrap] (http://www.jekyllbootstrap.com)

So if you would like to host your site on github jekyll-bootstrap has the goods for you.

So if we were supposed to do this step by step.

Step by Step
+ Migrate comments to Disqus
+ Install jekyll and Jekyll-bootstrap (instructions are on the site)
+ Migrate from the current tool e.g. wordpress
+ Make configuration changes in \_config.yml
+ Deploy your site

To migrate, you could just simply run the following

	ruby -rubygems -e 'require "jekyll/migrators/wordpress"; Jekyll::WordPress.process("database", "user", "pass")'


And there you will have all your posts from Wordpress into a markdown format.
Just be aware that the migration can do posts, slugs, categories etc. but if you have any links or files that will need to be taken care of. So its not simple, for me it was something I thought was not hard to live with. If you happen to be a code junkie like some, I could suggest forking the projects on github and adding valuables to them.

[https://github.com/mojombo/jekyll] (https://github.com/mojombo/jekyll)

[https://github.com/plusjade/jekyll-bootstrap] (https://github.com/plusjade/jekyll-bootstrap)

Once done migrating, simply make the changes to your \_config.yml, that takes care of disqus, page configs etc.

And run

	jekyll or jekyll --server


The second one will spawn a webrick listening on 4000

And thats it. review, deploy and redeploy, whatever you like.
