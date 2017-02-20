# MTG Website

A draft of a new website for the MIT Musical Theatre Guild.  Currently hosted at:

http://mattputnam.org/MTGWebsite/site

_(disclaimer: may not be synced with this repo at any given time)_

Driven by a custom template system written in Python.  Here's how you do common tasks (note that there's an implicit
"run `make.py`" at the end of each):

##### Selection happened, new future shows need a placeholder page

Create the \<year>/\<season> directory and drop in a skeletal `show.yaml` with just the name, credits info, show dates
(can be "TBD"), and venue.

##### Prodstaff/Cast/Orchestra have been picked

Add them to `show.yaml`.

##### The Publicity Designer created the show graphic and a banner image for Facebook

Add them to the show directory as `graphic.[whatever]` and `banner.[whatever]`.  All file types accepted, it's your
responsibility to make sure it's a real image.

##### Oh no, the show graphic is super big and it looks dumb.  And the banner doesn't look good with the default black margin.  And...

Add a custom css override to the directory.  It can be named anything, all CSS files found are automatically linked.

##### Guild Day happened and we have a new Board

Modify `main.yaml`.

---

Todos:

* Support production photos
* General announcements for current show page
* Do something for reservations, probably a switch in `main.yaml` that creates a link to our existing system
* Decouple HTML from Python.  Goal is to have an engine where all modifications can be done by tweaking htmpl files and
adding yaml and custom CSS.  **Update**: complete except for tables.
* Link people across shows like the G&S website?
* Add hook to automatically run `make.py`.
