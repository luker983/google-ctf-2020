# <img src="/media/cat_hardware_icon.svg" width="48" height="48"/> BASICS

## Prompt

With all those CPU bugs I don't trust software anymore, so I came up with my custom TPM (trademark will be filed soon!). You can't break this, so don't even try.

[Attachment](https://storage.googleapis.com/gctf-2020-attachments-project/3da8bc17f534eec284ee0f7f0cb473218365fc189dec41931240c2a7dcd0fcea4968cd56561525e184a0043efaff7a5029bb581afbc6ce89491b8384db6d8b1a)  
`basics.2020.ctfcompetition.com 1337`

## Files

* [provided.zip](provided.zip) - Challenge attachment
  - [main.cpp](main.cpp) - Software component of password checker 
  - [check.sv](check.sv) - Verilog password checker called by main.cpp
* [helper.v](helper.v) - Modified Verilog for use with online compiler
* [pass.txt](pass.txt) - Derived password
* [flag.txt](flag.txt) - Flag retrieved from server after providing password

## Solution

### Walking Through The Code
I started off by downloading and unzipping the provided atachment and connecting to the server from the prompt. 

```
$ nc basics.2020.ctfcompetition.com 1337
Enter password:
p@$$w0rd
=(
$
```

This matches up with what we see in main.cpp. Characters are read in, and if the hardware component decides the password is incorrect we get a sad face. The only interesting part in main.cpp is that the top bit of each character gets cut off:

```
check->data = c & 0x7f;
```

And then at the end, it checks the value of `check->open_safe`. If this value is true, the flag will be revealed. It looks like the meat of this problem is going to be in `check.sv`. 

I don't have much verilog experience, so I find it helpful to list out each variable and the bit width of each:

* `[6:0] data` - 7-bit input, this is where each character from our password goes, with the top bit trimmed off to fit
* `open_safe` - Boolean that will be true if password at the end is correct
* `[6:0] memory [7:0]` - This is an 8-element array, where each element has 7 bits
* `[2:0] idx` - 3-bit wide index variable
* `[55:0] magic` - 56-bit wide value, notice that 7 * 8 == 56
* `[55:0] kittens` - Another 56-bit wide value

Now we can work our way through the file and see how the values are assigned. Let's start by finding out where our characters end up and follow it through the hardware.

```
always_ff @(posedge clk) begin
  memory[idx] <= data;
  idx <= idx + 5;
end
```

**NOTE:** `<=` in verilog is a nonblocking assignment, not a 'less than or equal' operator

`memory` values are being filled using `idx`. The `idx` increments by 5 each time starting with 0. We only have 8 memory slots, so at first I thought there would be an error after the third assignment. Something like this:

```
memory[0] = char_1
memory[5] = char_2
memory[10] = char_3
ERROR: Out of bounds
```

But it turns out that accessing arrays uses modular arithmetic, so instead of accessing `memory[10]`, it accesses `memory[10 % 8]`. This means that values will be assigned as follows:

```
memory[0] = char_1
memory[5] = char_2
memory[10 % 8] = memory[2] = char_3
memory[15 % 8] = memory[7] = char_4
memory[20 % 8] = memory[4] = char_5
memory[25 % 8] = memory[1] = char_6
memory[30 % 8] = memory[6] = char_7
memory[35 % 8] = memory[3] = char_8
```

All of the `memory` registers are filled! Just a little out of order... Now we need to find out where it goes!

```
wire [55:0] magic = {
    {memory[0], memory[5]},
    {memory[6], memory[2]},
    {memory[4], memory[3]},
    {memory[7], memory[1]}
};
```

It looks like the `memory` registers are concatenated, *sigh* even more out of order, and placed into the `magic` wires. So now `magic` should look like this:

```
magic = memory[0].memory[5].memory[6].memory[2].memory[4].memory[3].memory[7].memory[1]
```
And then `magic` gets shuffled when being assigned to the `kittens` variable!!

```
wire [55:0] kittens = { magic[9:0],  magic[41:22], magic[21:10], magic[55:42] };
```

In my first attempt at deciphering all of this, I misintepreted how slices of a variable are accessed. I thought that `magic[0]` would be the 'leftmost' or most significant bit. It's actually the opposite. If I have 8 bits, they are indexed as follows:

```
[7:0] test: 10101101
Index:      76543210
```
So, the 'rightmost' 10 bits of `magic` have been moved to the 'leftmost' bits of `kittens` and so on.

Finally, the value of kittens is compared with a 56-bit decimal value and the result of that comparison determines the value of `open_safe`:

```
assign open_safe = kittens == 56'd3008192072309708;
```

To solve this challenge, we need to figure out what 8 characters result in a final bit stream that equals `3008192072309708`. Let's start reversing!!

### Now Do It Backwards

To make it more manageable, lets convert the decimal value into hex and binary:

````
Decimal:  3008192072309708
Hex:      0A        AF        EF        4B        E2        DB        CC
Binary:   00001010  10101111  11101111  01001011  11100010  11011011  11001100
````

This should be the value of kittens, so let's do a reverse shuffle to derive the value of `magic`. The 'leftmost' 10 bits of kittens are the 'rightmost' bits of `magic`, the next bits of `magic` are in the `[21:10]` slice, and we can keep building up the string using that logic:

```
          |[9:0]      |[41:22]                |[21:10]        |[55:42]
kittens:  00001010  10101111  11101111  01001011  11100010  11011011  11001100
magic:                                                            00  00101010 [9:0]
                                                    111110  00101100  00101010 [21:0]
                          10  11111110  11110100  10111110  00101100  00101010 [41:0]
          01101111  00110010  11111110  11110100  10111110  00101100  00101010 [55:0]
````

We have `magic`! Time to get `memory`. Reminder, `memory` is made up of 8, 7-bit values. The assignment to `magic` looks like this:

```
magic = memory[0].memory[5].memory[6].memory[2].memory[4].memory[3].memory[7].memory[1]
```

The 'leftmost' 7 bits of magic form `memory[0]`, the next 7 form `memory[5]`, and so on. We can divide `magic` into 7 bit chunks to figure out how they fit into `memory`:

```
magic:  0110111 1001100 1011111 1101111 0100101 1111000 1011000 0101010
memory: 0       5       6       2       4       3       7       1
```

We have `memory`!!! Now we know enough information to figure out what characters form the password! Just remember that the top bit was shaved off, so it could be a 1 or 0 at the top. But we only need to be concerned about that if our result without that top bit is something we can't print or a newline or something like that:

```
memory[0] = 0110111 = '7' 
memory[1] = 0101010 = '*'
memory[2] = 1101111 = 'o'
memory[3] = 1111000 = 'x'
memory[4] = 0100101 = '%'
memory[5] = 1001100 = 'L'
memory[6] = 1011111 = '_'
memory[7] = 1011000 = 'X'
```

Exciting!! But, we aren't quite ready for submission yet. We still need to reararange them based on the weird indexing we worked out in the beginning. Memory is loaded in the following order:

```
memory[0] = char_1 = '7'
memory[5] = char_2 = 'L'
memory[2] = char_3 = 'o'
memory[7] = char_4 = 'X'
memory[4] = char_5 = '%'
memory[1] = char_6 = '*'
memory[6] = char_7 = '_'
memory[3] = char_8 = 'x'
```

Now we're ready! The password is **`7LoX%*_x`** and can be typed into the server for the flag:

```
$ nc basics.2020.ctfcompetition.com 1337
Enter password:
7LoX%*_x
CTF{W4sTh4tASan1tyCh3ck?}
```

<div align="center"><img src="/media/flag_submitted_compressed.gif"></div>

## Resources

* Online Verilog Compiler: https://www.tutorialspoint.com/compile_verilog_online.php
