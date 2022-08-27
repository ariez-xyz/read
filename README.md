# Todo

* Custom CSS: Add a callback for *finishing* downloading a stylesheet, after which you can inject custom CSS.
* Better handling of page loads.
* Prettier interface.


# Bugs list

In Action Bronsons book:

```html
<!-- kobo-style -->
<link xmlns="http://www.w3.org/1999/xhtml" rel="stylesheet" type="text/css" href="../../css/kobo.css"/>
<script xmlns="http://www.w3.org/1999/xhtml" type="text/javascript" src="../../js/kobo.js"/>
<style xmlns="http://www.w3.org/1999/xhtml" type="text/css" id="kobostylehacks">div#book-inner p, div#book-inner div { font-size: 1.0em; } a { color: black; } a:link, a:visited, a:hover, a:active { color: blue; } div#book-inner * { margin-top: 0 !important; margin-bottom: 0 !important;}</style>
```

Breaks the HTML view (also in Firefox) - issue is with the script tag.
