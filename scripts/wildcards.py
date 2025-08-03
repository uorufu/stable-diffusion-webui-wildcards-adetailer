import os
import random
import sys
import gradio as gr
from modules import scripts, script_callbacks, shared, ui
from modules.ui_components import InputAccordion

wc_dir = shared.cmd_opts.wildcards_dir or os.path.join(scripts.basedir(), "wildcards")

class bcolors:
    OK = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    RED = "\033[91m"
    PURPLE = "\033[35m"
    CYAN = "\033[36m"

class WildcardsScript(scripts.Script):
    def title(self):
        return "Wildcards with Adetailer Support"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        elem = 'wildcard_'+("img2img_" if is_img2img else "txt2img_")
        with gr.Row(elem_id=elem+"wildcard_adetailer_row"):
            with gr.Accordion("Wildcards for Adetailer", open=False, elem_id=elem+"wildcard_adetailer_accordion"):
                with gr.Row():
                    wca_enabled = gr.Checkbox(scale=1, label="Enable Lock", value=False, interactive=True, elem_id=elem+"enabled")
                    wca_seed = gr.Number(scale=9, precision=0, label="Seed:", interactive=False, elem_id=elem+"seed")
                with gr.Row():
                    wca_osep = gr.Textbox(label="Outer Separator:", value="__", interactive=True, elem_id=elem+"osep")
                    wca_isep = gr.Textbox(label="Inner Separator:", value="_", interactive=True, elem_id=elem+"isep")
                with gr.Accordion('More info about Wildcards for Adetailer', open=False, elem_id=elem+'help'):
                    gr.Markdown('''
#Wildcards for Adetailer:

## Methods:

- Vanilla wildcard:   (Depreciated, but still functional. Completely random even when generating the same seed multiple times)
    `__wildcard__`
- Tiered wildcard:   (Preferred method): 
    `__0_wildcard__` up to `__99_wildcard__`
- Iterative wildcard: (iterates each line of a wildcard txt file when making a batch
    `__$_wildcard__`
- Specific line lock:
    `__wildcard_12__` or `__0_wildcard_12__` or `__$_wildcard_12__` (12 = line of wildcard txt file to lock)

## Supports:
- Normal prompts (pos+neg), HR prompts (pos+neg) and Adetailer prompts (pos+neg)
- Nesting wildcards inside wildcards
- Ability to change inner `_` and outer `__` separators in the menu. (Inner can conflict with filenames and outer can conflict with prompt text.)

## Incompatibility:
- Do not use `_`character in wildcard txt file names. (or whichever INNER separator you input in the menu)
- Does not work properly with Batch Size. Use Batch Count instead when making batches.
- Do not use `__` anywhere else in the prompt. (or whichever OUTER separator you input in the menu)



## Detailed explanation of methods:

- Tiered use is a great way to split wildcards into parts or match wildcards with wildcards in adetailer. If you need to use only parts in adetailer prompt or want to seperate lora's. If you have three txt files with 20 lines each and put them all in the same tier, let's say `__4_lora__` `__4_body__` in main prompt and `__4_face__` in adetailer prompt, then every time the same line number will be chosen for each of these wildcards.
  You can use up to 100 different tiers `(0 - 99)` which each having their own random generation seeding.
  Tiered wildcards are not order sensative. everything on the same tier shares the same random generation no matter what prompt it is in.
  Remember if you try to match multiple txt files in one tier and match them up, the txt files naturally have to have the same number of lines.

- Iterative wildcard is a way to have a wildcard go through the lines one by one instead of randomly choosing one. This can be great for making large batches and you want one result for each line in your wildcard txt file.

- Specific line lock is used to lock the wildcard to a specific line in your wildcard txt file, it ignores all randomization automatically and always chooses that specific line. `__wildcard_12__` will choose the 12th line from the txt file.

## Random generation method:

The random generation method just uses a seeding method based on the generation seed. Which means that every seed number will always have the same random results. A float between 0-1 will be randomly generated and that will be multiplied by the length of your txt file in order to decide which line to choose. 

## Seed locking:

The seed locking feature is for if you have a particular result and want to generate more of the same image with that result using other seeds. You can manually input the seed you want to lock (`Lock seed`) and then generate images in other seeds based on the random generation of the seed you locked. (Will not lock iterative wildcards. You can lock them manually using the 'specific line lock' feature (`__$_wildcard_2__`) 

## CMD Flags:

If you want to change the directory of your wildcards from the wildcards folder inside extension folder add this to your cmd flags and change the directory (or symlink externally):

- --wildcards-dir "c:\path\to\wildcards"
                    ''')
        wca_enabled.change(fn=lambda value:gr.update(interactive=value),inputs=wca_enabled,outputs=wca_seed)
        return [wca_enabled, wca_seed, wca_osep, wca_isep]

    def filecheck(self, file):
        if not os.path.exists(os.path.join(wc_dir, f"{file}.txt")):
            return False
        else:
            return True

    def wc_error(self, wc_sl, wc_errortype, wca_osep):
        if wc_errortype == 1:
            print (bcolors.RED + "[*] Wildcard missing: " + repr(wc_sl)[1:-1] + ".txt is not found." + bcolors.RESET)
        if wc_errortype == 2:
            print (bcolors.RED + "[*] Illegal wildcard found: " + wca_osep + repr(wc_sl)[1:-1] + wca_osep + " is not valid." + bcolors.RESET)
        return "e"

    def replace_wildcard(self, wc_file, wc_rand, wc_lock, wc_cseed, wc_ptype, wc_mode):
            wc_path = os.path.join(wc_dir, f"{wc_file}.txt")
            with open(wc_path, encoding="utf8") as f:
                wc_lines = f.read().splitlines()
                if wc_lock > 0:
                    wc_line = wc_lock
                    if wc_line > len(wc_lines):
                        wc_line = wc_line % len(wc_lines)
                    wc_lock = 0
                else:
                    if wc_rand >= 1:
                        wc_line = wc_rand
                        if wc_line > len(wc_lines):
                            wc_line = wc_line % len(wc_lines)
                    if 0 < wc_rand < 1:
                        wc_line = (len(wc_lines) * wc_rand).__ceil__()
                wc_prl = "Line " + str(wc_line) + " from " + str(wc_file) + ".txt (seed:" + str(wc_cseed) + ")"
                if len(wc_prl)<20:
                    tabs = "\t\t\t\t\t"
                elif len(wc_prl)<28:
                    tabs = "\t\t\t\t"
                elif len(wc_prl)<36:
                    tabs = "\t\t\t"
                elif len(wc_prl)<44:
                    tabs = "\t\t"
                else:
                    tabs = "\t"
                if wc_ptype == 1:
                    print(bcolors.OK, end='')
                if wc_ptype == 2:
                    print(bcolors.RED, end='')
                if wc_ptype == 3:
                    print(bcolors.CYAN, end='')
                if wc_ptype == 4:
                    print(bcolors.PURPLE, end='')
                print(f"[{wc_mode}] " + bcolors.RESET + bcolors.YELLOW + wc_prl + tabs + "►" + f"{wc_lines[wc_line-1][:100]}" + bcolors.RESET)
            return wc_lines[wc_line-1]

    def process(self, p, wca_enabled, wca_seed, wca_osep, wca_isep):
        o_prompt = p.all_prompts[0]
        o_negprompt = p.all_negative_prompts[0]
        wc_iter = 1
        if getattr(p, 'all_hr_prompts', None) is not None:
            inc_hrpos = True
            o_hrprompt = p.all_hr_prompts[0]
        else:
            inc_hrpos = False
        if getattr(p, 'all_hr_negative_prompts', None) is not None:
            inc_hrneg = True
            o_hrnegprompt = p.all_hr_negative_prompts[0]
        else:
            inc_hrneg = False
        global o_seed
        try:
            o_seed
        except NameError:
            o_seed = p.all_seeds[0]
        if len(p.all_seeds) > 1 and ( wca_osep in str(p.all_prompts) or wca_osep in str(p.all_negative_prompts) or (inc_hrpos == True and wca_osep in str(p.all_hr_prompts)) or (inc_hrneg == True and wca_osep in str(p.all_hr_negative_prompts))):
            o_seed = p.all_seeds[0]
            batchsize = p.n_iter * p.batch_size
            print (bcolors.YELLOW + f"[*] Batchsize {batchsize}" + bcolors.RESET)
            print (bcolors.YELLOW + f"[*] Starting Seed: {o_seed}" + bcolors.RESET)
        if wca_osep in str(p.all_prompts) or wca_osep in str(p.all_negative_prompts) or (inc_hrpos == True and wca_osep in str(p.all_hr_prompts)) or (inc_hrneg == True and wca_osep in str(p.all_hr_negative_prompts)):
            print(bcolors.OK + "[*] " + bcolors.RESET + bcolors.YELLOW + "Positive Prompt " + bcolors.RESET + bcolors.RED + "[*] " + bcolors.RESET + bcolors.YELLOW + "Negative Prompt " + bcolors.RESET + bcolors.CYAN + "[*] " + bcolors.RESET + bcolors.YELLOW + "HR Positive Prompt " + bcolors.RESET + bcolors.PURPLE + "[*] " + bcolors.RESET + bcolors.YELLOW + "HR Negative Prompt " + bcolors.RESET)
        if len(p.all_seeds) == 1 and o_seed != p.all_seeds[0]:
            wc_iter = abs(p.all_seeds[0] - o_seed) + 1
            if not o_seed <= p.all_seeds[0] <= (o_seed + wc_iter):
               o_seed = p.all_seeds[0]
               wc_iter = 1
        for wc_ptype in range(1,5):
            if wc_ptype == 1:
                wc_prompts = p.all_prompts
            if wc_ptype == 2:
                wc_prompts = p.all_negative_prompts
            if wc_ptype == 3:
                if inc_hrpos:
                    wc_prompts = p.all_hr_prompts
                else:
                    wc_prompts = ""
            if wc_ptype == 4:
                if inc_hrneg:
                    wc_prompts = p.all_hr_negative_prompts
                else:
                    wc_prompts = ""
                    break
            for j, wc_prompt in enumerate(wc_prompts):
                random.seed(wca_seed if wca_enabled == True else p.all_seeds[j])
                wc_rl = []
                for i in range(100):
                    wc_rl.append(random.random())
                if len(p.all_seeds) > 1 and o_seed <= p.all_seeds[j] <= (p.all_seeds[j] + len(p.all_seeds)):
                    wc_iter = p.all_seeds[j] - o_seed + 1
                wc_pl = wc_prompt.split(wca_osep)
                i = 0
                e = len(wc_pl)
                while i < e:
                    wc_sl = wc_pl[i]
                    if " " not in wc_sl and len(wc_sl) > 0 and i % 2 == 1:
                        wc_split = wc_sl.split(wca_isep)
                        if wca_isep not in wc_sl:
                            if self.filecheck(wc_sl) == True:
                                wc_mode = "N"
                                wc_pos = 0
                            else:
                                wc_mode = self.wc_error(wc_split[1], 1, wca_osep)
                        if wca_isep in wc_sl:
                            if len(wc_split) == 2:
                                if wc_split[0].isdigit():
                                    if self.filecheck(wc_split[1]) == True:
                                        if int(wc_split[0]) in range (0,99):
                                            wc_mode = "T"
                                            wc_pos = 1
                                    else:
                                        wc_mode = self.wc_error(wc_split[1], 1, wca_osep)
                                if wc_split[0] == "$":
                                    if self.filecheck(wc_split[1]) == True:
                                        wc_mode = "I"
                                        wc_pos = 1
                                    else:
                                        wc_mode = self.wc_error(wc_split[1], 1, wca_osep)
                            if 2 <= len(wc_split) <= 3:
                                if wc_split[-1].isdigit():
                                    if self.filecheck(wc_split[-2]) == True:
                                        if int(wc_split[-1]) > 0:
                                            wc_mode = "L"
                                    else:
                                        wc_mode = self.wc_error(wc_split[-2], 1, wca_osep)
                        try:
                            wc_mode
                        except NameError:
                            wc_mode = self.wc_error(wc_sl, 2, wca_osep)
                        if wc_mode == "N":
                            wc_pl[i] = self.replace_wildcard(wc_split[0], wc_rl[random.randint(0,99)], 0, p.all_seeds[j], wc_ptype, wc_mode)
                        if wc_mode == "I":
                            wc_pl[i] = self.replace_wildcard(wc_split[1], wc_iter, 0, p.all_seeds[j], wc_ptype, wc_mode)
                        if wc_mode == "T":
                            wc_pl[i] = self.replace_wildcard(wc_split[1], wc_rl[int(wc_split[0])], 0, p.all_seeds[j], wc_ptype, wc_mode)
                        if wc_mode == "L":
                            wc_lock = wc_split[-1]
                            wc_pl[i] = self.replace_wildcard(wc_split[-2], 0, int(wc_lock), p.all_seeds[j], wc_ptype, wc_mode)
                        if wca_osep in wc_pl[i]:
                            wc_nest = wc_pl[i].split(wca_osep)
                            e += (len(wc_nest) - 1)
                            wc_pl[i:i+1] = [""]
                            wc_pl[i+1:i+2] = wc_nest
                        if wc_ptype == 1:
                            if p.n_iter > 1 or p.batch_size > 1:
                                p.all_prompts[j] = ''.join(wc_pl)
                            else:
                                p.all_prompts[0] = ''.join(wc_pl)
                        if wc_ptype == 2:
                            if p.n_iter > 1 or p.batch_size > 1:
                                p.all_negative_prompts[j] = ''.join(wc_pl)
                            else:
                                p.all_negative_prompts[0] = ''.join(wc_pl)
                        if wc_ptype == 3:
                            if p.n_iter > 1 or p.batch_size > 1:
                                p.all_hr_prompts[j] = ''.join(wc_pl)
                            else:
                                p.all_hr_prompts[0] = ''.join(wc_pl)
                        if wc_ptype == 4:
                            if p.n_iter > 1 or p.batch_size > 1:
                                p.all_hr_negative_prompts[j] = ''.join(wc_pl)
                            else:
                                p.all_hr_negative_prompts[0] = ''.join(wc_pl)
                    i += 1
            if o_prompt != p.all_prompts[0]:
                p.extra_generation_params["Wildcard prompt"] = o_prompt
            if o_negprompt != p.all_negative_prompts[0]:
                p.extra_generation_params["Wildcard neg prompt"] = o_negprompt
            if inc_hrpos:
                if o_hrprompt != p.all_hr_prompts[0]:
                    p.extra_generation_params["Wildcard HR prompt"] = o_hrprompt
            if inc_hrneg:
                if o_hrnegprompt != p.all_hr_negative_prompts[0]:
                    p.extra_generation_params["Wildcard HR neg prompt"] = o_hrnegprompt
