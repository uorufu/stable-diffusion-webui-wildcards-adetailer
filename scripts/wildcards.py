import os
import random
import sys
import gradio as gr

from modules import scripts, script_callbacks, shared

warned_about_files = {}
repo_dir = scripts.basedir()

class bcolors:
    OK = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    RED = "\033[91m"
    PURPLE = "\033[35m"
    CYAN = "\033[36m"

class WildcardsScript(scripts.Script):
    def title(self):
        return "Simple wildcards for adetailer"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        elem = 'wildcard_'+("img2img_" if is_img2img else "txt2img_")
        with gr.Row(elem_id=elem+"wildcard_adetailer_row"):
            with gr.Accordion("Wildcards for adetailer", open=False, elem_id=elem+"wildcard_adetailer_accordion"):
                with gr.Row():
                    wca_enable = gr.Checkbox(label="Enable locking of wildcards randomization to a specific seed", value=False, elem_id=elem+"enable", interactive=True)
                with gr.Row():
                    wca_seed = gr.Number(precision=0, label="Which seed to lock", interactive=False, elem_id=elem+"seed")
                with gr.Row():
                    wca_linelock = gr.Number(value=1, precision=0, label="Specific iterative line number to lock", interactive=False, elem_id=elem+"linelock")
                with gr.Row():
                    wca_iterative_unlock = gr.Checkbox(label="Don't lock iterative wildcards", value=False, elem_id=elem+"iterativeunlock", interactive=False)
                with gr.Accordion('More info about Wildcards for adetailer',open=False,elem_id=elem+'help'):
                    gr.Markdown('''

# Methods:

- Depriciated use: `__wildcard__`
- Tiered wildcards: `__0_wildcard__` up to `__99_wildcard__`
- Iterative wildcard: `__$_wildcard__`
- Specific line lock: `__wildcard_12__` or `__0_wildcard_12__` or `__$_wildcard_12__` (12 can be any number)


## Random generation method:

The random generation method just uses a seeding method based on the generation seed. Which means that every seed number will always have the same random results. A float between 0-1 will be randomly generated and that will be multiplied by the length of your txt file in order to decide which line to choose. 


## Explanation of methods:

- Normal use is only really still here because people might be used to it. Personally I recommend using tiered wildcards only. The random generation for normal wildcards use a total of 100 unshared random seeds. So if you use more than 100 wildcards (lol), seeds will get reused.
  Note however that normal wildcards are order sensative when it comes to adetailer, unlike tiered wildcards. (first normal wildcard in mainprompt shares same random generation as first normal wildcard in adetailer.)
  It's really better to just use tiered wildcards.

- Tiered use is a great way to split wildcards into parts or match wildcards with wildcards in adetailer. If you need to use only parts in adetailer prompt or want to seperate lora's. If you have three text files with 20 lines each and put them all in the same tier, let's say `__4_lora__` `__4_body__` in main prompt and `__4_face__` in adetailer prompt, then every time the same line number will be chosen for each of these wildcards.
  You can use up to 100 different tiers `(0 - 99)` which each having their own random generation seeding.
  Tiered wildcards are not order sensative. everything on the same tier shares the same random generation no matter what prompt it is in.
  Remember if you try to match multiple txt files in one tier and match them up, the txt files naturally have to have the same number of lines.

- Iterative wildcard is a way to have a wildcard go through the lines one by one instead of randomly choosing one. This can be great for making large batches and you want one result for each line in your wildcard text file.

- Specific line lock is used to lock the wildcard to a specific line in your wildcard txt file, it ignores all randomization automatically and always chooses that specific line. `__wildcard_12__` will choose the 12th line from the txt file.

## Seed locking:

The seed locking feature is for if you have a particular result and want to generate more of the same image with that result using other seeds. You can manually input the seed you want to lock (`Which seed to lock`) and then generate images in other seeds based on the random generation of the seed you locked. Don't forget to manually lock the iterative wildcards to the proper line as well as otherwise they'll get locked to line 1 (`Specific iterative line number to lock`).

You can enable iterative wildcards to work while locking the random generation by selecing `Don't lock iterative wildcards`.

Save your wildcards in the wildcards folder. To avoid issues, use only a-z in your txt filename.

If you want to change the directory of your wildcards add this to your cmd flags and change the directory:
--wildcards-dir "c:\path\to\wildcards"
                    ''')
        outs = [wca_seed,wca_iterative_unlock,wca_linelock]
        wca_enable.change(fn=lambda value:[gr.update(interactive=value) for _ in outs],inputs=[wca_enable],outputs=outs, queue=False)
        return [wca_enable, wca_seed, wca_iterative_unlock, wca_linelock]

    def replace_wildcard(self, text, rlist, replacement_file, lock, currentseed, prompttype):
        with open(replacement_file, encoding="utf8") as f:
            textarray = []
            textarray = f.read().splitlines()
            if lock > 0:
                nline = lock
                if nline > len(textarray):
                    nline = nline % len(textarray)
                    if nline == 0:
                        nline = len(textarray)
                lock = 0
            else:  
                nline = round(len(textarray) * rlist)
                if rlist >= 1:
                    nline = rlist
                    if rlist > len(textarray):
                        nline = rlist % len(textarray)
                        if nline == 0:
                            nline = len(textarray)
            printtext = "Seed:" + str(currentseed) + " Line:" + str(nline) + " File:" + str(text) + ".txt"
            if len(printtext)<20:
                tabs = "\t\t\t\t\t"
            elif len(printtext)<28:
                tabs = "\t\t\t\t"
            elif len(printtext)<36:
                tabs = "\t\t\t"
            elif len(printtext)<44:
                tabs = "\t\t"
            else:
                tabs = "\t"
            if prompttype == 1:
                print(bcolors.OK + "[*] " + bcolors.RESET + bcolors.YELLOW + printtext + tabs + "►" + f"{textarray[nline-1][:100]}" + bcolors.RESET)
            if prompttype == 2:
                print(bcolors.RED + "[*] " + bcolors.RESET + bcolors.YELLOW + printtext + tabs + "►" + f"{textarray[nline-1][:100]}" + bcolors.RESET)
            if prompttype == 3:
                print(bcolors.CYAN + "[*] " + bcolors.RESET + bcolors.YELLOW + printtext + tabs + "►" + f"{textarray[nline-1][:100]}" + bcolors.RESET)
            if prompttype == 4:
                print(bcolors.PURPLE + "[*] " + bcolors.RESET + bcolors.YELLOW + printtext + tabs + "►" + f"{textarray[nline-1][:100]}" + bcolors.RESET)
        return textarray[nline-1]

    def process(self, p, wca_enable, wca_lock_seed, wca_iterative_unlock, wca_linelock):
        original_prompt = p.all_prompts[0]
        original_negative_prompt = p.all_negative_prompts[0]
        if getattr(p, 'all_hr_prompts', None) is not None:
            original_hr_prompt = p.all_hr_prompts[0]
        if getattr(p, 'all_hr_negative_prompts', None) is not None:
            original_hr_negative_prompt = p.all_hr_negative_prompts[0]
        global original_seed
        try:
            original_seed
        except NameError:
            original_seed = p.all_seeds[0]
        global original_batchsize
        try:
            original_batchsize
        except NameError:
            original_batchsize = p.n_iter * p.batch_size
        global current_seed
        try:
            current_seed
        except NameError:
            current_seed = p.all_seeds[0]
        wildcards_dir = shared.cmd_opts.wildcards_dir or os.path.join(repo_dir, "wildcards")
        linearray = []
        text = []
        useprompts = []
        if len(p.all_seeds) > 1 and ( "__" in str(p.all_prompts) or "__" in str(p.all_negative_prompts) ):
            original_batchsize = p.n_iter * p.batch_size
            original_seed = p.all_seeds[0]
            print (bcolors.YELLOW + f"[*] Batchsize {original_batchsize}" + bcolors.RESET)
            print (bcolors.YELLOW + f"[*] Starting Seed: {original_seed}" + bcolors.RESET)
        if "__" in str(p.all_prompts) or "__" in str(p.all_negative_prompts):
            print(bcolors.OK + "[*] " + bcolors.RESET + bcolors.YELLOW + "Positive Prompt " + bcolors.RESET + bcolors.RED + "[*] " + bcolors.RESET + bcolors.YELLOW + "Negative Prompt " + bcolors.RESET + bcolors.CYAN + "[*] " + bcolors.RESET + bcolors.YELLOW + "HR Positive Prompt " + bcolors.RESET + bcolors.PURPLE + "[*] " + bcolors.RESET + bcolors.YELLOW + "HR Negative Prompt " + bcolors.RESET)
        if len(p.all_seeds) == 1 and original_seed != p.all_seeds[0]:
            lastseed = original_seed + original_batchsize - 1
            if not original_seed < p.all_seeds[0] <= lastseed:
               original_seed = p.all_seeds[0]
               del original_batchsize
        for k in range(4):
            if k == 0:
                useprompts = p.all_prompts
                prompt_type = 1
            if k == 1:
                useprompts = p.all_negative_prompts
                prompt_type = 2
            if k == 2:
                if getattr(p, 'all_hr_prompts', None) is not None:
                    useprompts = p.all_hr_prompts
                    prompt_type = 3
                else:
                    continue
            if k == 3:
                if getattr(p, 'all_hr_negative_prompts', None) is not None:
                    useprompts = p.all_hr_negative_prompts
                    prompt_type = 4
                else:
                    break
            for j, text in enumerate(useprompts):
                current_seed = p.all_seeds[j]
                random.seed(wca_lock_seed if wca_enable == True and wca_lock_seed > 0 else p.all_seeds[j])
                rand_list_tiers = []
                rand_list = []
                for i in range(100):
                    rand_list_tiers.append(random.random())
                    rand_list.append(random.random())
                fixedline = 1
                if wca_enable == True and wca_iterative_unlock == True or wca_enable == False:
                    if len(p.all_seeds) > 1 and p.all_seeds[j] > original_seed:
                        fixedline = p.all_seeds[j] - original_seed + 1
                    if p.all_seeds[0] > original_seed:
                        fixedline = p.all_seeds[0] - original_seed + 1
                if wca_enable == True and wca_iterative_unlock == False:
                    fixedline = wca_linelock
                text = " " + text + " "
                text = text.split("__")
                lockedline = 0
                i = 0
                n = 0
                while i < len(text):
                    line = str(text[i])
                    if " " not in line and len(line) > 0 and (i % 2) != 0:
                        linearray = line.split("_")
                        if len(linearray) == 1:
                            if not os.path.exists(os.path.join(wildcards_dir, f"{linearray[0]}.txt")):
                                noline = str(linearray[0])
                                print (bcolors.RED + "[*] Wildcard txt file not found: " + noline + ".txt" + bcolors.RESET)
                            else:                 
                                replacement_file = os.path.join(wildcards_dir, f"{linearray[0]}.txt")
                                if os.path.exists(replacement_file):
                                    if n > 99:
                                        n = n % 99
                                    text[i] = self.replace_wildcard(linearray[0], rand_list[n], replacement_file, lockedline, current_seed, prompt_type)
                                    n = n + 1
                        if len(linearray) == 2:
                            if os.path.exists(os.path.join(wildcards_dir, f"{linearray[0]}.txt")):
                                replacement_file = os.path.join(wildcards_dir, f"{linearray[0]}.txt")
                                lockedline = int(linearray[1])
                                if n > 99:
                                        n = n % 99
                                text[i] = self.replace_wildcard(linearray[0], rand_list[n], replacement_file, lockedline, current_seed, prompt_type)
                                lockedline = 0
                                n = n + 1
                            elif os.path.exists(os.path.join(wildcards_dir, f"{linearray[1]}.txt")):
                                replacement_file = os.path.join(wildcards_dir, f"{linearray[1]}.txt")
                                if linearray[0] == "$":
                                    text[i] = self.replace_wildcard(linearray[1], fixedline, replacement_file, lockedline, current_seed, prompt_type)
                                else:
                                    text[i] = self.replace_wildcard(linearray[1], rand_list_tiers[int(linearray[0])], replacement_file, lockedline, current_seed, prompt_type)
                            else:
                                noline = str(linearray[0])
                                noline2 = str(linearray[1])
                                if noline2.isdigit():
                                    print (bcolors.RED + "[*] Wildcard txt file not found: " + noline + ".txt" + bcolors.RESET)
                                else:
                                    print (bcolors.RED + "[*] Wildcard txt file not found: " + noline2 + ".txt" + bcolors.RESET)
                        if len(linearray) == 3:
                            if os.path.exists(os.path.join(wildcards_dir, f"{linearray[1]}.txt")):
                                replacement_file = os.path.join(wildcards_dir, f"{linearray[1]}.txt")
                                lockedline = int(linearray[2])
                                if linearray[0] == "$":
                                    text[i] = self.replace_wildcard(linearray[1], fixedline, replacement_file, lockedline, current_seed, prompt_type)
                                else:
                                    text[i] = self.replace_wildcard(linearray[1], rand_list_tiers[int(linearray[0])], replacement_file, lockedline, current_seed, prompt_type)
                                lockedline = 0
                            else:
                                noline = str(linearray[1])
                                print (bcolors.RED + "[*] Wildcard txt file not found: " + noline + ".txt" + bcolors.RESET)
                        if k == 0:
                            if p.n_iter > 1 or p.batch_size > 1:
                                p.all_prompts[j] = ''.join(text)
                            else:
                                p.all_prompts[0] = ''.join(text)
                        if k == 1:
                            if p.n_iter > 1 or p.batch_size > 1:
                                p.all_negative_prompts[j] = ''.join(text)
                            else:
                                p.all_negative_prompts[0] = ''.join(text)
                        if k == 2:
                            if p.n_iter > 1 or p.batch_size > 1:
                                p.all_hr_prompts[j] = ''.join(text)
                            else:
                                p.all_hr_prompts[0] = ''.join(text)
                        if k == 3:
                            if p.n_iter > 1 or p.batch_size > 1:
                                p.all_hr_negative_prompts[j] = ''.join(text)
                            else:
                                p.all_hr_negative_prompts[0] = ''.join(text)
                    i = i + 1
        if original_prompt != p.all_prompts[0]:
            p.extra_generation_params["Wildcard prompt"] = original_prompt
        if original_negative_prompt != p.all_negative_prompts[0]:
            p.extra_generation_params["Wildcard neg prompt"] = original_negative_prompt
        if getattr(p, 'all_hr_prompts', None) is not None:
            if original_hr_prompt != p.all_hr_prompts[0]:
                p.extra_generation_params["Wildcard HR prompt"] = original_hr_prompt
        if getattr(p, 'all_hr_negative_prompts', None) is not None:
            if original_hr_negative_prompt != p.all_hr_negative_prompts[0]:
                p.extra_generation_params["Wildcard HR neg prompt"] = original_hr_negative_prompt
