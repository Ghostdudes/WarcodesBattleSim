import tkinter as tk
from tkinter import ttk
import random
import json
import os
from PIL import Image, ImageTk

def roll_die(sides):
    return random.randint(1, sides)

def simulate_battle(creature1, creature2):
    results = {creature1['Name']: 0, creature2['Name']: 0}   #################actual sim code

    for _ in range(25000): #25k sims, used this for the bot
        creature1_hp = creature1['HP']
        creature2_hp = creature2['HP']

        while creature1_hp > 0 and creature2_hp > 0:
           
            creature2_hp = perform_attack(creature1, creature2, creature2_hp)

            if creature2_hp <= 0:
                results[creature1['Name']] += 1 ###just as in game, defender goes first, when hp hits 0, opponent gets 1 pt, 10000x then find percentage of points
                break  

            
            creature1_hp = perform_attack(creature2, creature1, creature1_hp)

            if creature1_hp <= 0:
                results[creature2['Name']] += 1
                break 

    return results

def perform_attack(attacker, defender, defender_hp):
    attacker_primary_accuracy = attacker["Primary Accuracy"]
    attacker_secondary_accuracy = attacker["Secondary Accuracy"]
    defender_agility = defender["Agility"]

    defender_agility_roll = roll_die(defender_agility)
    if defender["Heartstone"]:
        defender_agility_roll -= 1
    if defender.get("Eagle Stone", False): 
        defender_agility_roll -= 1  

    primary_accuracy_roll = roll_die(attacker_primary_accuracy)
    
    
    if attacker.get("Eagle Stone", False):
        primary_accuracy_roll_2 = roll_die(attacker_primary_accuracy)
        primary_accuracy_roll = max(primary_accuracy_roll, primary_accuracy_roll_2)

    primary_accuracy_roll += (1 if attacker["Large Eyestone"] else 0)

    if primary_accuracy_roll >= defender_agility_roll:
        primary_dice = 0
        for attack_type in attacker["Primary Attack Type"]:
            if attack_type != "NA":
                primary_dice = 2
                primary_dice += attacker["Large Shard"] + attacker["Flareheart"]

                if attack_type in defender["Weakness"]:
                    primary_dice += 1 + defender.get("Earthbane", False) + attacker.get("Wrathstone", False)
                elif attack_type in defender["Resistance"]:
                    primary_dice += -1 - defender.get("Aegis Stone", False)

        if primary_dice > 0:
            primary_dice = max(1, primary_dice)
            primary_damage = sum(roll_die(attacker["Primary Damage"]) for _ in range(primary_dice))

            if attacker["Large Shard"]:
                primary_damage -= 3
            if attacker["Vitaflare"]:
                primary_damage -= 2

            defender_hp -= max(0, primary_damage)

    secondary_accuracy_roll = roll_die(attacker_secondary_accuracy)

    
    defender_agility_roll_secondary = roll_die(defender_agility)
        if defender["Heartstone"]:
            defender_agility_roll_secondary -= 1
        if defender.get("Eagle Stone", False):
            defender_agility_roll_secondary -= 1
    
    
        secondary_accuracy_roll = roll_die(attacker_secondary_accuracy)
    
        if attacker.get("Eagle Stone", False):
            secondary_accuracy_roll_2 = roll_die(attacker_secondary_accuracy)
            secondary_accuracy_roll = max(secondary_accuracy_roll, secondary_accuracy_roll_2)
    
        secondary_accuracy_roll += (1 if attacker["Small Eyestone"] else 0) + (2 if attacker["Sword Amulet"] else 0)
    
        if secondary_accuracy_roll >= defender_agility_roll_secondary:
            secondary_dice = 0
            for attack_type in attacker["Secondary Attack Type"]:
                if attack_type != "NA":
                    secondary_dice = 1
                    secondary_dice += attacker["Small Shard"]
    
                    if attack_type in defender["Weakness"]:
                        secondary_dice += 1 + defender.get("Earthbane", False)
                    elif attack_type in defender["Resistance"]:
                        secondary_dice += -1 - defender.get("Aegis Stone", False)
    
            if secondary_dice > 0:
                secondary_dice = max(1, secondary_dice)
                secondary_damage = sum(roll_die(attacker["Secondary Damage"]) for _ in range(secondary_dice))
    
                if attacker["Small Shard"]:
                    secondary_damage -= 3
    
                defender_hp -= max(0, secondary_damage)
    
        return defender_hp

    #######################################secondary
    if roll_die(attacker_secondary_accuracy) >= roll_die(defender_agility):
        secondary_dice = 0
        for attack_type in attacker["Secondary Attack Type"]:
            if attack_type != "NA":
                secondary_dice = 2
                secondary_dice += attacker["Small Shard"]

                if attack_type in defender["Weakness"]:
                    secondary_dice += 1
                elif attack_type in defender["Resistance"]:
                    secondary_dice -= 1 + int(defender.get("Aegis Stone", False))

        if secondary_dice > 0:
            secondary_dice = max(1, secondary_dice)
            secondary_damage = sum(roll_die(attacker["Secondary Damage"]) for _ in range(secondary_dice))

            if attacker["Small Shard"]:
                secondary_damage -= 3

            defender_hp -= max(0, secondary_damage)

    return defender_hp
####################################################end of attack phase#########################################################
class MultiSelectPopup(tk.Toplevel):
    def __init__(self, parent, options, current_selections, callback):
        super().__init__(parent)
        self.title("Select Options")
        self.geometry("80x400")
        self.options = options
        self.current_selections = current_selections
        self.callback = callback
        self.vars = {}
        for option in options:
            self.vars[option] = tk.BooleanVar(value=option in current_selections)  ########################checkboxes for type resist/weakness etc
            frame = tk.Frame(self)
            frame.pack(fill="x")
            label = tk.Label(frame, text=option)
            label.pack(side="left", expand=True)
            cb = tk.Checkbutton(frame, variable=self.vars[option])
            cb.pack(side="right")
        tk.Button(self, text="Done", command=self.on_done).pack()
        self.center_window(parent)
    def on_done(self):
        selected_items = [option for option, var in self.vars.items() if var.get()]
        self.callback(selected_items)
        self.destroy()

    def center_window(self, parent):
        self.update_idletasks()  
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        popup_width = self.winfo_width()
        popup_height = self.winfo_height()
        x = parent_x + (parent_width - popup_width) // 2
        y = parent_y + (parent_height - popup_height) // 2
        self.geometry(f"+{x}+{y}")
############################################################checkboxes for types^##########Actual gui window sttings V#############################################################
class BattleSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Does my monster beat Heavylon?" if random.random() < 0.1 else "Warcodes Battle Simulator")
        for col, text in enumerate(["Defender", "Attacker"], start=0):
            frame = tk.LabelFrame(self.root, text=text, font=("Arial", 12, "bold"))
            frame.grid(row=0, column=col * 2, padx=10, pady=10, sticky="nsew")
            setattr(self, f"creature{col+1}_frame", frame)
            setattr(self, f"creature{col+1}", self.create_input_fields(frame, f"Creature {col+1}"))
        self.button_frame = tk.Frame(self.root)
        self.button_frame.grid(row=0, column=1, sticky="nsew")
        for row, (text, cmd) in enumerate([("Simulate Battle", self.simulate_battle), ("🔁 Swap", self.switch_creatures)]):  ##############################GUI elements here
            tk.Button(self.button_frame, text=text, command=cmd).grid(row=row, column=0, pady=5, sticky="nsew")
        self.result_label = tk.Label(self.root, text="")
        self.result_label.grid(row=1, column=0, columnspan=3, pady=10)
        for i in range(3):
            self.root.grid_columnconfigure(i, weight=1)
        for i in range(2):
            self.root.grid_rowconfigure(i, weight=1)
            self.button_frame.grid_rowconfigure(i, weight=1)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.saved_creatures = self.load_saved_creatures()
        self.update_name_dropdowns()
        self.root.mainloop()
    def create_input_fields(self, frame, creature_label):
        fields = {}
        placeholder_image_path = os.path.join("Monster Images", "nan.png")  ####monster image folder in same dir as main script
        try:
            placeholder_image = Image.open(placeholder_image_path)
            placeholder_image.thumbnail((150, 150))
            placeholder_photo = ImageTk.PhotoImage(placeholder_image)
        except FileNotFoundError:
            print(f"Error: Placeholder image not found at {placeholder_image_path}")
            placeholder_photo = None
        if placeholder_photo:
            image_label = tk.Label(frame, image=placeholder_photo)
            image_label.image = placeholder_photo  #####something to load if no mon photo 
            image_label.grid(row=25, column=0, columnspan=2, pady=5)
            fields["Image Label"] = image_label
        def add_field(label, row, field_type="entry", options=None):
            tk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
            if field_type == "entry":
                entry = tk.Entry(frame, width=20)
                entry.grid(row=row, column=1)
                fields[label] = entry
            elif field_type == "combobox":
                combobox = ttk.Combobox(frame, values=options, width=17)
                combobox.grid(row=row, column=1)
                combobox.set(options[0])
                fields[label] = combobox
            elif field_type == "checkbox":
                var = tk.BooleanVar()
                checkbutton = tk.Checkbutton(frame, variable=var)
                checkbutton.grid(row=row, column=1, sticky="w")
                fields[label] = var
            elif field_type == "text":
                text_box = tk.Text(frame, height=4, width=20)
                text_box.grid(row=row, column=1)
                fields[label] = text_box

        def add_multi_select_field(label, row, options):
            tk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
            current_selections = []

  
            selections_var = tk.StringVar(value=", ".join(current_selections))
            entry = tk.Entry(frame, textvariable=selections_var, state="readonly", width=20)
            entry.grid(row=row, column=1)
            
 
            fields[label + "_var"] = selections_var

            def open_popup():
                nonlocal current_selections
                ####opens window next to button pressed
                MultiSelectPopup(frame, options, current_selections, lambda selections: update_selections(selections, label))

            def update_selections(selections, label):
                nonlocal current_selections
                current_selections = selections
                selections_var.set(", ".join(selections))
                fields[label] = current_selections  

            button = tk.Button(frame, text="Select", command=open_popup)
            button.grid(row=row, column=2)
            fields[label] = current_selections 

        def save_creature():
            creature_data = self.parse_fields(fields)
            creature_data['Notes'] = fields["Notes"].get("1.0", "end-1c")
            self.saved_creatures[creature_data['Name']] = creature_data
            self.save_creatures_to_file()
            self.update_name_dropdowns()

        def load_creature(*args):
            name = fields["Name"].get()
            if name in self.saved_creatures:
                creature_data = self.saved_creatures[name]
            
                ################################Agility/accuracy needs to be conveted to be read V#############################################################
                reverse_agility_mapping = {4: "★", 6: "★★", 8: "★★★"}
                reverse_accuracy_mapping = {6: "low", 8: "medium", 10: "high"}

   
                for key, widget in fields.items():
                    if key == "Agility" and isinstance(widget, ttk.Combobox):
                        widget.set(reverse_agility_mapping.get(creature_data.get(key, 4), "★"))
                    elif key in ["Primary Accuracy", "Secondary Accuracy"] and isinstance(widget, ttk.Combobox):
                        widget.set(reverse_accuracy_mapping.get(creature_data.get(key, 6), "low"))
                    elif key in ["Primary Damage", "Secondary Damage"] and isinstance(widget, ttk.Combobox):
                        widget.set(f"d{creature_data.get(key, 8)}")
                    elif isinstance(widget, tk.Entry) and not key.endswith("_var") and key not in ["Primary Attack Type", "Secondary Attack Type", "Weakness", "Resistance"]:
                        widget.delete(0, tk.END)
                        widget.insert(0, creature_data.get(key, ""))
                    elif isinstance(widget, ttk.Combobox):
                        widget.set(creature_data.get(key, ""))
                    elif isinstance(widget, tk.BooleanVar):
                        widget.set(creature_data.get(key, False))
                    elif isinstance(widget, tk.Text):
                        widget.delete(1.0, tk.END)
                        widget.insert(tk.END, creature_data.get("Notes", ""))
                    elif key in ["Primary Attack Type", "Secondary Attack Type", "Weakness", "Resistance"]:
                        fields[key] = creature_data.get(key, [])
                        if key + "_var" in fields:
                            fields[key + "_var"].set(", ".join(fields[key]))
                image_extensions = [".png", ".jpg"]
                for ext in image_extensions:
                    image_path = os.path.join("Monster Images", f"{name}{ext}")  ######same image dir, images with same name as mosnter are loaded with it
                    if os.path.exists(image_path):
                        try:
                            image = Image.open(image_path)
                            image.thumbnail((150, 150))
                            photo = ImageTk.PhotoImage(image)

                            fields["Image Label"].config(image=photo)
                            fields["Image Label"].image = photo
                        except Exception as e:
                            print(f"Error loading image {image_path}: {e}")
                        break 
            else:
                if "Image Label" in fields:
                    fields["Image Label"].config(image=placeholder_photo)
                    fields["Image Label"].image = placeholder_photo

        add_field("Name", 0)
        fields["Name"] = ttk.Combobox(frame, width=17, values=[])
        fields["Name"].grid(row=0, column=1)
        fields["Name"].bind("<<ComboboxSelected>>", load_creature)

        add_field("HP", 1)
        add_field("Agility", 2, "combobox", ["★", "★★", "★★★"])
        add_field("Primary Damage", 3, "combobox", ["d8", "d10", "d12"])
        add_field("Primary Accuracy", 4, "combobox", ["low", "medium", "high"])
        add_field("Secondary Damage", 5, "combobox", ["d4", "d6"])
        add_field("Secondary Accuracy", 6, "combobox", ["low", "medium", "high"])
        add_multi_select_field("Primary Attack Type", 7, ["NA", "Water", "Fire", "Electric", "Earth", "Wind", "Ice", "Radiation", "Poison", "Metal", "Magic", "Light", "Dark", "Spirit", "Psychic"])
        add_multi_select_field("Secondary Attack Type", 8, ["NA", "Water", "Fire", "Electric", "Earth", "Wind", "Ice", "Radiation", "Poison", "Metal", "Magic", "Light", "Dark", "Spirit", "Psychic"])
        add_multi_select_field("Weakness", 9, ["NA", "Water", "Fire", "Electric", "Earth", "Wind", "Ice", "Radiation", "Poison", "Metal", "Magic", "Light", "Dark", "Spirit", "Psychic"])
        add_multi_select_field("Resistance", 10, ["NA", "Water", "Fire", "Electric", "Earth", "Wind", "Ice", "Radiation", "Poison", "Metal", "Magic", "Light", "Dark", "Spirit", "Psychic"])
        add_field("Heartstone", 11, "checkbox")
        add_field("Earthbane", 12, "checkbox")
        add_field("Large Shard", 13, "checkbox")
        add_field("Small Shard", 14, "checkbox")
        add_field("Large Eyestone", 15, "checkbox")
        add_field("Small Eyestone", 16, "checkbox")
        add_field("Sword Amulet", 17, "checkbox")
        add_field("Vitaflare", 18, "checkbox")
        add_field("Flareheart", 19, "checkbox")
        add_field("Wrathstone", 20, "checkbox")
        add_field("Aegis Stone", 21, "checkbox")
        add_field("Eagle Stone", 22, "checkbox")
        add_field("Notes", 23, "text")  ###################################################################if adding new items, make sure to move save button: save_button.grid(row=23 <----- ######## and make sure image is the last thing image_label1.grid(row=25 <---- must change image placement for both mons

        save_button = tk.Button(frame, text=f"Save 💾", command=save_creature)
        save_button.grid(row=24, column=0, columnspan=2, pady=5)

        return fields

    def parse_fields(self, fields):
        agility_mapping = {"★": 4, "★★": 6, "★★★": 8}
        accuracy_mapping = {"low": 6, "medium": 8, "high": 10}

        return {
            "Name": fields["Name"].get(),
            "HP": int(fields["HP"].get()),
            "Agility": agility_mapping[fields["Agility"].get()],
            "Primary Damage": int(fields["Primary Damage"].get()[1:]),
            "Primary Accuracy": accuracy_mapping[fields["Primary Accuracy"].get()],
            "Secondary Damage": int(fields["Secondary Damage"].get()[1:]),
            "Secondary Accuracy": accuracy_mapping[fields["Secondary Accuracy"].get()],
            "Primary Attack Type": fields["Primary Attack Type"],
            "Secondary Attack Type": fields["Secondary Attack Type"],
            "Weakness": fields["Weakness"],
            "Resistance": fields["Resistance"],
            "Heartstone": fields["Heartstone"].get(),
            "Earthbane": fields["Earthbane"].get(),
            "Large Shard": fields["Large Shard"].get(),
            "Small Shard": fields["Small Shard"].get(),
            "Large Eyestone": fields["Large Eyestone"].get(),
            "Small Eyestone": fields["Small Eyestone"].get(),
            "Sword Amulet": fields["Sword Amulet"].get(),
            "Vitaflare": fields["Vitaflare"].get(),
            "Flareheart": fields["Flareheart"].get(),
            "Wrathstone": fields["Wrathstone"].get(),
            "Aegis Stone": fields["Aegis Stone"].get(),
            "Eagle Stone": fields["Eagle Stone"].get(),
        }

    def save_creatures_to_file(self):
        with open("saved_creatures.json", "w") as file:
            json.dump(self.saved_creatures, file)

    def load_saved_creatures(self):
        if os.path.exists("saved_creatures.json"):
            with open("saved_creatures.json", "r") as file:
                return json.load(file)
        return {}

    def update_name_dropdowns(self):
        creature_names = list(self.saved_creatures.keys())
        self.creature1["Name"]["values"] = creature_names
        self.creature2["Name"]["values"] = creature_names

    def switch_creatures(self):
        for field in list(self.creature1.keys()):
            if isinstance(self.creature1[field], tk.Entry) and not field.endswith("_var"):
                if field not in ["Primary Attack Type", "Secondary Attack Type", "Weakness", "Resistance"]:
                    value1 = self.creature1[field].get()
                    value2 = self.creature2[field].get()
                    self.creature1[field].delete(0, tk.END)
                    self.creature1[field].insert(0, value2)
                    self.creature2[field].delete(0, tk.END)
                    self.creature2[field].insert(0, value1)
            elif isinstance(self.creature1[field], ttk.Combobox):
                value1 = self.creature1[field].get()
                value2 = self.creature2[field].get()
                self.creature1[field].set(value2)
                self.creature2[field].set(value1)
            elif isinstance(self.creature1[field], tk.BooleanVar):
                value1 = self.creature1[field].get()
                value2 = self.creature2[field].get()
                self.creature1[field].set(value2)
                self.creature2[field].set(value1)
            elif isinstance(self.creature1[field], tk.Text): 
                value1 = self.creature1[field].get("1.0", tk.END)
                value2 = self.creature2[field].get("1.0", tk.END)
                self.creature1[field].delete("1.0", tk.END)
                self.creature1[field].insert(tk.END, value2)
                self.creature2[field].delete("1.0", tk.END)
                self.creature2[field].insert(tk.END, value1)
            elif field == "Image Label": 
                image_label1 = self.creature1.get("Image Label")
                image_label2 = self.creature2.get("Image Label")

                if image_label1 and image_label2:
                    photo1 = image_label1.image
                    photo2 = image_label2.image
                    image_label1.config(image=photo2)
                    image_label1.image = photo2
                    image_label2.config(image=photo1)
                    image_label2.image = photo1
                elif image_label1: 
                    self.creature2["Image Label"] = image_label1
                    image_label1.grid_forget()
                    image_label1.grid(row=25, column=0, columnspan=2, pady=5)  #######################################################################
                    del self.creature1["Image Label"]                          #
                elif image_label2:                                             #  IMAGE NEEDS TO BE LOWEST OR WILL OVERWRITE BOXES, I kept forgeting to move them down
                    self.creature1["Image Label"] = image_label2               #
                    image_label2.grid_forget()                                 #
                    image_label2.grid(row=25, column=0, columnspan=2, pady=5)  ######################################################################
                    del self.creature2["Image Label"]
            elif field in ["Primary Attack Type", "Secondary Attack Type", "Weakness", "Resistance"]:
                value1 = self.creature1[field]
                value2 = self.creature2[field]
                self.creature1[field] = value2
                self.creature2[field] = value1
                if field + "_var" in self.creature1:
                    self.creature1[field + "_var"].set(", ".join(value2))
                if field + "_var" in self.creature2:
                    self.creature2[field + "_var"].set(", ".join(value1))

    def simulate_battle(self):
        creature1 = self.parse_fields(self.creature1)
        creature2 = self.parse_fields(self.creature2)

        results = simulate_battle(creature1, creature2)

        win_rate1 = results[creature1['Name']] / 25000 * 100
        win_rate2 = results[creature2['Name']] / 25000 * 100

        self.result_label.config(
            text=f"{creature1['Name']}: {win_rate1:.2f}% wins vs {creature2['Name']}: {win_rate2:.2f}% wins",
            font=("Arial", 20, "bold")
        )

if __name__ == "__main__":
    BattleSimulator()
