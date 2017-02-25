# MTG Website

A draft of a new website for the MIT Musical Theatre Guild.  Currently hosted at:

http://mattputnam.org/MTGWebsite/site

_(disclaimer: may not be synced with this repo at any given time)_

Driven by a custom template system written in Python.  Here's how you do common tasks (note that there's an implicit
"run `make.py`" at the end of each):

##### Selection happened, new future shows need a placeholder page

Create the \<year>/\<season> directory and drop in a skeletal `show.yaml` with just the name, dates, and venue.  "TBD" or "Upcoming" are valid placeholders.  Example:

```yaml
Title: Cats
Credits: |
  Book, Music, and Lyrics by Andrew Lloyd Weber
  Based on Old Possum’s Book of Practical Cats by T.S. Eliot
Dates: TBA
Venue: KLT
```

##### Prodstaff/Cast/Orchestra have been picked

Add them to `show.yaml`.  Names must be "Production Staff", "Cast", and "Orchestra" exactly.  Example:

```yaml
Production Staff:
  Producer: John Smith '08
  Directors: |
    Jane Doe '15
    Bob Williams '17
```
etc.

##### The Publicity Designer created the show graphic and a banner image for Facebook

Add them to the show directory as `graphic.[whatever]` and `banner.[whatever]`.  All file types accepted, it's your
responsibility to make sure it's a real image.  Default behavior: If there's both, hide the graphic.

##### Oh no, the show graphic is super big and it looks dumb.  And the banner doesn't look good with the default black margin.  And...

Add a custom css override to the show directory.  It can be named anything, all CSS files found are automatically linked.

##### Someone took production photos

Drop them in the show directory, thumbnails in `photos/thumbnails`, full photos in `photos/full`.  To attribute them, add info to `show.yaml` like this:

```yaml
Photo Credits:
  Global: Joe Schmo '18
  IMG5773.jpg: Someone Else '19
```

##### Guild Day happened and we have a new Board

Modify `main.yaml`.

##### One show ended, and the next began

Change `Current Show:` in `main.yaml`.

---

Todos:

* General announcements/ticket reservations for current show page
* Do something for reservations, probably a switch in `main.yaml` that creates a link to our existing system
* Link people across shows like the G&S website?
* Add hook to automatically run `make.py`.
* Add parameters to `make.py` to build only certain pages
