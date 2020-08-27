# <img src="/media/cat_reversing_icon.svg" width="48" height="48"/> ANDROID

## Prompt
Can you find the correct key to unlock this app?

[Attachment](https://storage.googleapis.com/gctf-2020-attachments-project/91b17683f3f2b06b679d729a5b5279cdbdfea7607546ac34c1f7114add7e4a0970410d22d359d09055f8fa7d6efe20b4b3f4be67ed5d7a5257fc4117175848c8)

## Files

* [provided.zip](provided.zip) - Provided attachment
    - [reverse.apk](reverse.apk) - Android app that needs to be reversed
* [reverse/](reverse/) - APK decompiled with `apktool`
* [replaced.apk](replaced.apk) - APK with the `ő` character removed
* [replaced-aligned-debugSigned.apk](replaced-aligned-debugSigned.apk) - Signed/debug version of [replaced.apk](replaced.apk)
* [brute_force.py](brute_force.py) - Script to brute force the flag
* [flag.txt](flag.txt) - Solution to this challenge, makes the 🚩 icon appear in the app

## Solution

### Trying It Out

The provided zip file contains an APK that I loaded into Android Studio. The app does not have debugging enabled, but we can still get an idea of what it does.

<div align="center">
<img src="/media/reversing/android/home.png" width="480"><img src="/media/reversing/android/fail.png" width="480">
</div>

The source code wasn't provided with the APK, but Android Studio will still disassemble the `classes.dex` file without it. There are some weird looking classes in here...

<div align="center"><img src="/media/reversing/android/studio.png" width="640"></div>


### Decompilation Attempts

We could totally solve this challenge by just looking at this bytecode, but that would be a nightmare. So let's see if we can get a higher-level view of this code. There are plenty of tools out there that will decompile `.dex` files for us. I tried [Luyten](https://github.com/deathmarine/Luyten), [JADX](https://github.com/skylot/jadx), and [JD-GUI](http://java-decompiler.github.io/). Really really popular decompilers. All resulted in the same sort of error:

```
Lcom/google/ctf/sandbox/ő;.<init>()V
java.lang.NullPointerException
    at java.base/java.lang.String.rangeCheck(String.java:289)
    at java.base/java.lang.String.<init>(String.java:285)
    at org.objectweb.asm.Type.getInternalName(Type.java:580)
    at com.googlecode.d2j.converter.IR2JConverter.toInternal(IR2JConverter.java:97)
    at com.googlecode.d2j.converter.IR2JConverter.reBuildTryCatchBlocks(IR2JConverter.java:89)
    at com.googlecode.d2j.converter.IR2JConverter.convert(IR2JConverter.java:57)
    at com.googlecode.d2j.dex.Dex2jar$2.ir2j(Dex2jar.java:173)
    at com.googlecode.d2j.dex.Dex2Asm.convertCode(Dex2Asm.java:453)
    at com.googlecode.d2j.dex.ExDex2Asm.convertCode(ExDex2Asm.java:40)
    at com.googlecode.d2j.dex.Dex2jar$2.convertCode(Dex2jar.java:132)
    at com.googlecode.d2j.dex.Dex2Asm.convertMethod(Dex2Asm.java:596)
    at com.googlecode.d2j.dex.Dex2Asm.convertClass(Dex2Asm.java:444)
    at com.googlecode.d2j.dex.Dex2Asm.convertClass(Dex2Asm.java:357)
    at com.googlecode.d2j.dex.Dex2Asm.convertDex(Dex2Asm.java:460)
    at com.googlecode.d2j.dex.Dex2jar.doTranslate(Dex2jar.java:175)
    at com.googlecode.d2j.dex.Dex2jar.to(Dex2jar.java:275)
    at com.googlecode.dex2jar.tools.Dex2jarCmd.doCommandLine(Dex2jarCmd.java:112)
    at com.googlecode.dex2jar.tools.BaseCmd.doMain(BaseCmd.java:290)
    at com.googlecode.dex2jar.tools.Dex2jarCmd.main(Dex2jarCmd.java:33)
```

I couldn't figure out how to resolve the error, so I tried throwing it into Ghidra and was surprised to find out that it will decompile DEX files and seemed to do a great job without any errors!! The most interesting function is `ő$1.onClick()` and Ghidra lays out the password comparison logic plain as day.

<div align="center"><img src="/media/reversing/android/onclick.png" width="320"></div>

Those hex values are Integers that get cast to Characters, appended to a string, and then compared with the input string! Should be super easy to get the flag back!

```
41 70 70 61 72 65 6e 74 6c 79 20 74 68 69 73 20 69 73 20 6e 6f 74 20 74 68 65 20 66 6c 61 67 2e 20 57 68 61 74 27 73 20 67 6f 69 6e 67 20 6f 6e 3f
Apparently this is not the flag. What's going on?
```

Wow, I was so hopeful. Looks like this is not the correct input to the app. I even tried copy/pasting this string into the app just to make sure. No luck. So what is going on? I looked around for other information in the the other classes, and all I could find was another suspicious function called `ő()`:

```
long [] ő(long a, long b)
{
    long[] plVar1;
    long[] plVar2;
    
    if (a == 0) {
        plVar1 = new long[2];
        return plVar1;
    }
    plVar1 = R.ő(b % a, a);
    plVar2 = new long[2];
    plVar2[0] = plVar1[1] - (b / a) * plVar1[0];
    plVar2[1] = plVar1[0];
    return plVar2;
}
```

Ghidra listed 4 references to this function. Entry Point, the recursive call within the function itself, some other section that lists all functions, and then another section of code where the Decompile view showed an exception:

```
org.xml.sax.SAXParseException; lineNumber: 50; columnNumber: 15; Invalid byte 2 of 2-byte UTF-8 sequence. 
```

Aw man, Ghidra finally broke too. But I was able to go through the disassembled view to figure out where this code segment is. It's right underneath the `onClick()` function! Upon further inspection, `onClick()` sets up a try/catch block and there is quite a bit of code in the catch segment. Maybe some exception gets triggered and starts execution somewhere else?? I copied the decompiled code from the `onClick()` function into an online Java compiler and touched it up to make it run. The error occurs in the cast from Integer to Character. This is not an allowed cast, so an exception is triggered! 

So we know where to find the new execution path, Ghidra just has trouble decompiling it. After quite a bit of troubleshooting, I found the solution to this error: https://stackoverflow.com/a/4294792

> Most commonly it's due to feeding ISO-8859-x (Latin-x, like Latin-1) but parser thinking it is getting UTF-8. Certain sequences of Latin-1 characters (two consecutive characters with accents or umlauts) form something that is invalid as UTF-8, and specifically such that based on first byte, second byte has unexpected high-order bits.
>
> This can easily occur when some process dumps out XML using Latin-1, but either forgets to output XML declaration (in which case XML parser must default to UTF-8, as per XML specs), or claims it's UTF-8 even when it isn't.

Hmmm, the `ő` character might be causing problems. Ghidra didn't seem to have trouble decompiling other portions of the code with the `ő`, but I finally resolved to try it anyway by replacing that character in the APK and then reimporting into Ghidra. After disassembling with `apktool`, `AndroidManifest.xml` and everything in the `smali` directory need to have that character replaced: 

1. `apktool d reverse.apk`
2. `find reverse/AndroidManifest.xml -type f | xargs gsed -i 's/ő/o/g'` from https://stackoverflow.com/a/1585189
3. `find reverse/smali/ -type -f | xargs gsed -i 's/ő/o/g'` from https://stackoverflow.com/a/1585189
4. `find reverse/ -name "*ő*" -exec rename 's/ő/o/g' {} ";"` from https://stackoverflow.com/a/9394874
5. `apktool b reverse -o replaced.apk`

Android Studio won't accept this new APK because it's not signed or anything, and we may not need to import it into Android Studio again, but just for fun we can use [Uber Apk Signer](https://github.com/patrickfav/uber-apk-signer) to automatically do all of that stuff for us. 

```
java -jar uber-apk-signer-1.1.0.jar --apks ./
```

Now Ghidra should have no trouble decompiling the exception block. 

<div align="center"><img src="/media/reversing/android/exception.png" width="480"></div>

### The Real Problem Appears

This makes it much easier to understand. Although some of the variables are not shown as initialized here, they are initialized in the `onClick()` function. It checks the input string to make sure it's `0x30 (48)` characters, then divides the characters up 4 at a time into an array with 12 elements. Here's an example:

```
Input String:   CTF{abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ}
Hex:            43 54 46 7b 61 62 63 64 65 66 67 68 69 6a 6b 6c 6d 6e 6f 70 71 72 73 74 75 76 77 78 79 7a 41 42 43 44 45 46 47 48 49 4a 4b 4c 4d 4e 4f 50 51 7d
Array:
        [0]:    0x7b465443
        [1]:    0x64636261
        [2]:    0x68676665
                   ...
        [11]:   0x7d51504f
```

The next part isn't quite as clear. The `R.o()` function is invoked and checked. But it is difficult to read what's getting compared and with what. So, let's go back to Studio and see if we can figure out what's happening using dynamic analysis. We don't have source code, so it's not super easy to set breakpoints, but Studio has an option to set a breakpoint at every exception, which just so happens to be how our secret password check gets executed:

<div align="center"><img src="/media/reversing/android/breakpoint.png" width="480"></div>

A breakpoint is set, now we just need to click the *CHECK* button in the app to trigger an exception. It works! We hit an exception and we can see several variables with their original names!

<div align="center"><img src="/media/reversing/android/var.png" width="480"></div>

`key` and `keyString` and `chr` are related to our input string. But the really interesting variables are `this$0.class` and `this$0.o.o`. Both are twelve element arrays, one populated and one not. 

```
this$0
    class
        0 = 40999019
        1 = 2789358025
        2 = 656272715
        3 = 18374979
        4 = 3237618335
        5 = 1762529471
        6 = 685548119
        7 = 382114257
        8 = 1436905469
        9 = 2126016673
        10 = 3318315423
        11 = 797150821
```

It looks like the input string is going to have to match this pre-populated array once it gets placed in the other array. To test this theory, let's try a random flag and see if the first elements match up since `CTF{` is a safe bet:

```
comparison array:
    0 = 40999019
    
our flag's array:
    0 = 2068206659
```

Well that didn't work... But let's think about it. The array gets populated *before* it goes through the `R.o()` function. Maybe if we pass this number through the `R.o()` function they'll equal each other? Thankfully the logic of that function is pretty similar, so I transposed it to python and pass in `2068206659` and `0x100000000` as parameters and got back:

```
[40999019, -19742745]
```

That's the same!! I have no clue what the second element means, but it doesn't seem to be important. Now all we need to do is reverse the pre-populated array to figure out what the original input string was, right? Well yeah, but that would be a lot of work. Instead, since we only need 4 bytes at a time, we can brute force it. The input characters are likely to be between `0x32` and `0x128`. Easy.

[brute_force.py](brute_force.py) contains the code used to break the flag and only takes a few minutes to run. When it finishes, it prints out the flag!

```
CTF{y0u_c4n_k3ep_y0u?_m4gic_1_h4Ue_laser_b3ams!}
```

At this point the competition had ended, so I had to verify my flag a different way. Through the app! 

<div align="center"><img src="/media/reversing/android/solved.png" width="480"></div>

<div align="center"><img src="/media/flag_submitted_compressed.gif"></div>

## Resources

* Uber APK Signer: https://github.com/patrickfav/uber-apk-signer/releases/tag/v1.1.0
* Stack Overflow - Ghidra Decompilation Solution: https://stackoverflow.com/a/4294792
* Stack Overflow - File Search and Replace: https://stackoverflow.com/a/1585189
* Stack Overflow - Filename Search and Replace: https://stackoverflow.com/a/9394874
