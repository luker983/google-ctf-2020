# <img src="/media/cat_reversing_icon.svg" width="48" height="48"/> BEGINNER

## Prompt

Dust off the cobwebs, let's reverse!

[Attachment](https://storage.googleapis.com/gctf-2020-attachments-project/f0c3f1cbf2b64f69f07995ebf34aa10aed3299038b4a006b2776c9c14b0c762024bc5056b977d9161e033f80ff4517556d79af101088b651b397a27d4a89f2a1)

## Files

* [provided.zip](provided.zip) - Attachment provided in the prompt
  - [a.out](a.out) - Executable to reverse contained in zip
* [helper.py](helper.py) - Script to aid in the reversing process
* [flag.txt](flag.txt) - Flag revealed by reversing the executable

## Solution

### File Analysis

Unzipping the provided attachment reveals an `a.out` file. Just to confirm that it's an ELF, let's check it with `file`:

```
$ file a.out
a.out: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=e3a5d8dc3eee0e960c602b9b2207150c91dc9dff, for GNU/Linux 3.2.0, not stripped
```

It's an ELF, so we should be able to `chmod 766 a.out` and then run it:

```
$ ./a.out
Flag: p@$$w0rd
FAILURE
```

Let's throw this into Ghidra to see how this password is evaluated.

After opening the executable, running the analysis, and hopping down to the main function, we see this:

<div align="center"><img src="/media/reversing/beginner/main.png"></div>

It seems like a pretty small function, thank goodness. It reads in user input, performs a few operations on the input string, then compares the original input string with the modified string? That's pretty strange:

```
strncmp(local_38, (char *)&local_28, 0x10);
```

This tells us that the flag should probably be 16 characters long (null character counts as the 16th) and after the modifications made in the middle, it should end up being identical to the original input. The next comparison is also interesting:

```
strncmp((char *)&local_28, EXPECTED_PREFIX, 4);
```

Clicking on `EXPECTED_PREFIX` shows us that the first four characters need to be `CTF{`.

Okay, time to look the operations that happen in the middle. In this case the disassembled view is easier to understand than the decompiled view:

```
PSHUFB  XMM0,xmmword ptr[SHUFFLE]
PADDD   XMM0,xmmword ptr[ADD32]
PXOR    XMM0,xmmword ptr[XOR]
```

Now we have a pretty good idea of how the program works:

1. Input string is read in, placed into floating point register `XMM0`
2. Register is shuffled using `SHUFFLE` constant
2. Register is added with `ADD32` constant
3. Register is xord with `XOR` constant
4. Original input string is compared with the new shuffled/added/xord string
5. If previous values are equal, first four characters are compared with `CTF{`
6. If previous values are equal, flag is correct

### Understanding Floating Point Operations

Floating point operations can be confusing, it's important to really understand how they work to prevent mistakes in the reversing process. And when in doubt, we can test things out with dynamic analysis tools such as GDB.

The PSHUFB instruction is the most confusing operation here, and documentation didn't help my understanding much. So I input 15 unique characters (16th is null) into the provided program and then monitored the `XMM0` register before and after the PSHUFB instruction using the `i r xmm0` command in GDB. The `SHUFFLE` value is passed into the instruction to determine the mapping:

```
Flag:               abcdefghijklmno
XMM0 Pre-Shuffle:   61 62 63 64 65 66 67 68 69 6a 6b 6c 6d 6e 6f 00
SHUFFLE:            02 06 07 01 05 0b 09 0e 03 0f 04 08 0a 0c 0d 00
XMM0 Post-Shuffle:  63 67 68 62 66 6c 6a 6f 64 00 65 69 6b 6d 6e 61
```

Okay, so like it sounds, the bytes get shuffled around. The pseudo-code looks something like this:

```
Post-Shuffle[i] = Pre-Shuffle[SHUFFLE[i]]
```

The next instruction is PADDD, this adds up doublewords (32bits) at a time. We have 16 bytes, so we need to break that into 4, 32-bit chunks. After some testing with GDB, it seems that these chunks are formed in reverse endianness, so `01 02 03 04` would become `0x04030201`. Also, if overflow occurs, the carry bit is ignored. 

```
XMM0 Pre-Add:   63 67 68 62 66 6c 6a 6f 64 00 65 69 6b 6d 6e 61
ADD32:          ef be ad de ad de e1 fe 37 13 37 13 66 74 63 67

XMM0 Pre-Add:   0x62686763  0x6f6a6c66  0x69650064  0x616e6d6b
ADD32:          0xdeadbeef  0xfee1dead  0x13371337  0x67637466
XMM0 Post-Add:  0x41162652  0x6e4c4b13  0x7c9c139b  0xc8d1e1d1  

XMM0 Post-Add:  52 26 16 41 13 4b 4c 6e 9b 13 9c 7c d1 e1 d1 c8
```

That's step 2! All that's left is the XOR, which works exactly like you'd expect.

```
XMM0 Pre-Xor:   52 26 16 41 13 4b 4c 6e 9b 13 9c 7c d1 e1 d1 c8
XOR:            76 58 b4 49 8d 1a 5f 38 d4 23 f8 34 eb 86 f9 aa
XMM0 Post-Xor:  24 7e a2 08 9e 51 13 56 4f 30 64 48 3a 67 28 62
```

That's the final value. And you might notice, it looks nothing like the original string... How is it even possible to figure out flag bytes if the final string is compared with a modified version of itself?? It doesn't seem to make any sense at first. But think about it. Our input string contains `CTF{...}`, gets operated on, and outputs to `CTF{...}` even though that shuffle operation is there. The input character `C` changes to different letter of the flag in the output string. A different letter ends up forming the first `C`. If we start by reversing the known values (we have 5 so far, `C T F { } \0`), we can hopefully start forming the flag! Let's test this theory.

### Deriving The Flag

The flags tend to follow a theme, so if we did this byte-by-byte we could probably figure out the result despite off by one errors caused by the addition. But since we have the full first 4 byte chunk, we might as well start it off right. Our 4 byte chunk won't be consecutive after the shuffle, so we need to do this in reverse.

```
XMM0 Post-Xor:  CTF{
XMM0 Post-Xor:  43 54 46 7b
XMM0 XOR:       76 58 b4 49
XMM0 Pre-Xor:   35 0c f2 32

XMM0 Post-Add:  0x32f20c35
ADD32:          0xdeadbeef
XMM0 Pre-Add:   0x54444d46

XMM0 Post-Shuffle:  46 4d 44 54
SHUFFLE:            02 06 07 01
XMM0 Pre-Shuffle:   ?? 54 46 ?? ?? ?? 4d 44 ?? ?? ?? ?? ?? ?? ??
                        T  F           M  D                          
```

That's awesome!! We found two characters of the flag this way! Slowly filling in the solution:

```
CTF{__MD_____}\0
```

Except, now we don't have another 4 byte chunk to work with. Maybe we would if we look at the data after the shuffle? It should work just as well:

```
C T F { _ _ M D _ _ _ _ _ _ } \0
        Shuffling...
F M D T _ _ _ } { \0 _ _ _ _ _ C
```

Nope, just the 4 we already figured out... Guess we can start doing it one by one. Addition errors won't occur everyhwere. It's impossible for there to be an error on the least significant byte, because there is no carry possible from a lower byte. For example:

```
  0xeeeeeeee
+ 0xdeadbeef
____________
  0xcd9caddd (carry bit ignored)
```

Calculating the least significant byte depends on no other bytes in the number. There is no possibility of a carry bit being sent from a less significant byte. This is not the case for higher order bytes. So, for now, we can safely reverse least significant bytes. In our flag, there are 4 'least significant bytes'.

We already sent the first one, `C`, through the algorithm in reverse. But we also know that `{` is a least significant byte after the shuffle and before the add. So that's our next target.  Scripting this would make it a lot easier, so I whipped up something in python to help out: [helper.py](helper.py). It takes in the hex value of a known item in the flag (`{ = 0x7b`) and its index (`{ = 3`). Then it follows that element through the algorithm to figure out how it transforms.  

```
$ helper.py 0x7b 3
0x66 f 8
```

This tells us that `f` is at the 8th index of our flag string!

```
C T F { _ _ M D f _ _ _ _ _ } \0
```

But now we've run into the same issue. No new least significant bytes are available. But, since `{` was a least significant byte, we can find out if its addition resulted in a carry or not and then find out if the next byte over needs to get an extra bit! When we shuffled what we know so far, we found out that the next byte over is the null byte.

```
XMM0 Pre-Add:   0x????007b
ADD32:          0x13371337         
XMM0 Post-Add:  0x????13b2
```

No carry happens because `7b + 37 < 256`. This means we can plug in the null byte to our script!

```
$ helper.py 0x00 15
0x30 0 9 
```
```
C T F { _ _ M D f 0 _ _ _ _ } \0
```

I'm starting to get impatient, does it really matter if we don't know for sure if the addition results in a carry? It's only off by one. We have enough safe characters by now that we can probably deduce the right string. Let's try it. Without accounting for any possible carries, I ran each known character through the helper script and got this:

```
C S E { _ _ N C f 0 _ M _ _ } \0
```

That looks terrible. And it got a lot of our original string wrong, let's fix it up, but leave the new characters alone. 

```
C T F { _ _ M D f 0 _ M _ _ } \0
```

Hmmm, we only got one new character, let's pass it through the helper script and see what happens, and if we get a new character, keep following it.

```
C T F { S 1 M D f 0 r M 3 ! } \0
```

Wow! That looks like something. *SIMD for me!*
SIMD stands for Single Instruction, Multiple Data. The floating point instructions in this problem are SIMD instructions!
Submitting that into the program results in a `SUCCESS`!

```
CTF{S1MDf0rM3!}
```

<div align="center"><img src="/media/flag_submitted_compressed.gif"></div>

## Resources

* PSHUFB Documentation: https://www.felixcloutier.com/x86/pshufb
* PADDD Documentation: https://www.felixcloutier.com/x86/paddb:paddw:paddd:paddq
* PXOR Documentation: https://www.felixcloutier.com/x86/pxor
