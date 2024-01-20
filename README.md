# Fake-Web-IRC-Python
This is the dumbest IRC known to man, not recommended for use in anything serious.  Functionality still being built out.

Recommended Usage:
Don't

However if you really want, set up chat.html to run in an iframe and then use the irc_chat.py to render it.  You might run into problems if trying to run this locally, since flask sets up a virtual server and most browsers don't allow cross-origin frames.

the users.json is all encrypted with sha256, and it uses a token to save user data which gets passed between html renders so that the password is never exposed in plaintext.
