#### Wildcards Adetailer fix

A personal fork I made to make wildcards extension work better with Adetailer.

# Final update (probably)

Added negative and hires prompt support




# Update

locking a wildcard: `__0_wildcard_12__` will lock to the 12th line of the wildcard.txt file.

Cleaned up code a bit as it was a bit of a mess.

# Upate:

-Added the functionality back to use normal wildcards `__wildcard__` next to tiered wild cards `__0_wildcard__` upto `__19_wildcard__`.

-Added functionality for iterative wildcards that go through text files line by line. `__$_wildcard__`

-Fixed a bunch of bugs and made it work a lot better, also added settings to txt2img UI instead of inside settings menu for seed locking.

## Changes from main extension:

1. Now, order does not matter and you can add any wildcard to adetailer prompt without it generating a different item. 

2. Also, I have made it so there can be tiers. So you can link certain wildcard txt files to each other so all of them will grab the same line number in the TXT.
    The proper use for this fork is by using `__0_name__` up to `__9_name__` to pull from **name.txt** in the wildcards directory. (the leading number **should not** be on the txt filename.)
    Every wildcard using the same leading number will use the same random generation (and if the txt files have an equal amount of lines, will pick the same line number.

This is great when you want to add a lengthy bit of prompt into the main prompt but only want a small part of the same prompt in adetailer prompt (Or you want to seperate lora's. Now you can just seperate them into two txt files and use the same leading number like `__0_partone__ __0_parttwo__` in your main prompt and only `__0_partone__` in adetailer. If both partone.txt and parttwo.txt have the same number of lines, they will both get the same linenumber.

3. For the best randomization, unless you need to use the same tier, it is best to use as many tiers as possible. So `__0_name__ __1_name__ __2_name__` etc. Right now the maximum amount of tiers is 20 (0 to 19), I think that is a nice amount.
    

Just like the main extension, make sure you use spaces at the beginning and end of newlines.


## Install
To install from webui, go to `Extensions -> Install from URL`, paste `https://github.com/uorufu/stable-diffusion-webui-wildcards-adetailer`
into URL field, and press Install.
