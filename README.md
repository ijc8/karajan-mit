What is this?
===

This is a (very) modest score visualizer built during the Karajan/MIT classical music hackathon, Oct. 2016.

Though it was made in well under 24 hours, it took me well over 8 months to get around to making it available somewhere.

Disclaimer: I've left the code completely as it was when presented; I even resisted the urge to remove the inexplicable trailing whitespace.

Who made this?
===
Ian C., Lisa K., Josie T., Alice

How can I use this?
===
- Install [pygame](https://www.pygame.org/) and [music21](http://web.mit.edu/music21/).
- Get a score in MusicXML format from somewhere. The [MuseScore site](https://musescore.com) is a good resource.
- Run like `python visual.py sonata.xml 124 -0.5`. The second arg is the tempo (in bpm); the third is an offset (in seconds) that you'll probably need to tweak to sync the visuals with the audio. (This invocation works well for [this score](https://musescore.com/user/7075436/scores/2297561).)
