Plutonium
---------

This is an experimental web framework ["Meteor like"](https://www.meteor.com/), i.e, reactive, based on Python3 and [Brython](http://www.brython.info/index.html).

That means that you can subscribe to a filter like 'the patients waiting in emergency". Then, when an user introduces in the system a new patient in emergencies, every running application that is subscribed to that filter will receive the data and update its HTML.

It's a declarative way of programing. You declare what you want to see and every time the system changes and your view is affected, then data is sent to you.

Examples given that you are subscribed to "the patients waiting in emergency": If a patient that is hospitalized goes to home, you are not informed, but if a patient in emergency is hospitalized you are informed.

This is the next step on web applications. And we can say that it's not a future step but a today reality thanks to Meteor and [Volt](http://voltframework.com/).


