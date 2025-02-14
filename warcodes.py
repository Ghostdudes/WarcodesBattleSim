import tkinter as tk
from tkinter import ttk
import random
import json
import os
from PIL import Image, ImageTk

ITEM_MODIFIERS = {
    "Large Eyestone": {"primary_accuracy_modifier": 1},
    "Eagle Stone": {"accuracy_roll_extra": True, "defender_agility_modifier": -1},
    "Large Shard": {"primary_dice_increase": 1, "primary_damage_reduction": -3},
    "Flareheart": {"primary_dice_increase": 1},
    "Wrathstone": {"primary_weakness_dice_increase_ifattack": 1},
    "Vitaflare": {"primary_damage_reduction": -2},
    "Small Eyestone": {"secondary_accuracy_modifier": 1},
    "Sword Amulet": {"secondary_accuracy_modifier": 2},
    "Small Shard": {"secondary_dice_increase": 1, "secondary_damage_reduction": -3},
    "Earthbane": {"weakness_dice_increase_ifdefend": 1},
    "Aegis Stone": {"resistance_dice_reduction_ifdefend": 1},
    "Heartstone": {"defender_agility_modifier": -1}
}

def roll_die(sides):
    return random.randint(1, sides)

def apply_item_effects(creature: dict, is_attacker: bool) -> dict:
    """Applies item effects and returns modifiers."""
    modifiers = {
        "primary_accuracy_modifier": 0,
        "secondary_accuracy_modifier": 0,
        "primary_dice_increase": 0,
        "secondary_dice_increase": 0,
        "primary_damage_reduction": 0,
        "secondary_damage_reduction": 0,
        "primary_weakness_dice_increase_ifattack": 0,  
        "weakness_dice_increase_ifdefend": 0,
        "resistance_dice_reduction_ifdefend": 0,
        "defender_agility_modifier": 0,
        "accuracy_roll_extra": False  
    }

    for item, equipped in creature.items():  
        if equipped and item in ITEM_MODIFIERS:
            item_effects = ITEM_MODIFIERS[item]
            for effect, value in item_effects.items():
                if effect in modifiers:
                    modifiers[effect] += value  
                elif effect == "accuracy_roll_extra": 
                    modifiers[effect] = modifiers[effect] or value
    return modifiers

def calculate_primary_damage(attacker: dict, defender: dict, attacker_modifiers: dict, defender_modifiers: dict) -> int:
    """Calculates damage for the primary attack."""
    attack_types = attacker["Primary Attack Type"]
    defender_agility_roll = roll_die(defender["Agility"]) + defender_modifiers.get("defender_agility_modifier", 0)

    accuracy_rolls = [roll_die(attacker["Primary Accuracy"])]
    if attacker_modifiers.get("accuracy_roll_extra", False):
        accuracy_rolls.append(roll_die(attacker["Primary Accuracy"]))
    final_accuracy_roll = max(accuracy_rolls) + attacker_modifiers["primary_accuracy_modifier"]

    if final_accuracy_roll < defender_agility_roll:
        return 0  # Attack missed

    dice_count = 0
    for attack_type in attack_types:
        if attack_type != "NA":
            dice_count = 2 + attacker_modifiers["primary_dice_increase"]
            if attack_type in defender.get("Weakness", []):
                dice_count += 1
                dice_count += attacker_modifiers.get("primary_weakness_dice_increase_ifattack", 0) #wrathstone
                dice_count += defender_modifiers.get("weakness_dice_increase_ifdefend", 0)  # earthbane
            elif attack_type in defender.get("Resistance", []):
                dice_count -= 1
                dice_count -= defender_modifiers.get("resistance_dice_reduction_ifdefend", 0)  # aegis
            break

    dice_count = max(1, dice_count)
    damage = sum(roll_die(attacker["Primary Damage"]) for _ in range(dice_count))
    damage += attacker_modifiers["primary_damage_reduction"]

    return max(0, damage)  
def calculate_secondary_damage(attacker: dict, defender: dict, attacker_modifiers: dict, defender_modifiers: dict)-> int:
    """Calculates damage for the secondary attack"""
    attack_types = attacker["Secondary Attack Type"]
    defender_agility_roll = roll_die(defender["Agility"]) + defender_modifiers.get("defender_agility_modifier", 0)

    accuracy_rolls = [roll_die(attacker["Secondary Accuracy"])]
    if attacker_modifiers.get("accuracy_roll_extra", False):
        accuracy_rolls.append(roll_die(attacker["Secondary Accuracy"]))

    final_accuracy_roll = max(accuracy_rolls) + attacker_modifiers["secondary_accuracy_modifier"]

    if final_accuracy_roll < defender_agility_roll:
        return 0

    dice_count = 0
    for attack_type in attack_types:
        if attack_type != "NA":
            dice_count = 2 + attacker_modifiers["secondary_dice_increase"]
            if attack_type in defender.get("Weakness",[]):
                dice_count += 1
                dice_count += defender_modifiers.get("weakness_dice_increase_ifdefend", 0)
            elif attack_type in defender.get("Resistance", []):
                dice_count -= 1
                dice_count -= defender_modifiers.get("resistance_dice_reduction_ifdefend", 0)
            break

    dice_count = max(1, dice_count)
    damage = sum(roll_die(attacker["Secondary Damage"]) for _ in range(dice_count))
    damage += attacker_modifiers["secondary_damage_reduction"]

    return max(0, damage)

def perform_attack(attacker, defender, defender_hp):
    """Performs a single attack round (both primary and secondary)"""

    attacker_modifiers = apply_item_effects(attacker, True)
    defender_modifiers = apply_item_effects(defender, False)

    primary_damage = calculate_primary_damage(attacker, defender, attacker_modifiers, defender_modifiers)
    defender_hp -= primary_damage

    if defender_hp <= 0:
        return 0

    secondary_damage = calculate_secondary_damage(attacker, defender, attacker_modifiers, defender_modifiers)
    defender_hp -= secondary_damage

    return defender_hp

def simulate_battle(creature1, creature2):
    results = {creature1['Name']: 0, creature2['Name']: 0}  #################actual sim code

    if creature1['Name'] == creature2['Name']:
      results = {creature1['Name']: 0, creature2['Name'] + "again": 0}

    for _ in range(25000): #25k sims, used this for the bot
        temp_creature1 = creature1.copy() 
        temp_creature2 = creature2.copy()
        creature1_hp = temp_creature1['HP']
        creature2_hp = temp_creature2['HP']

        while creature1_hp > 0 and creature2_hp > 0:

            creature2_hp = perform_attack(temp_creature1, temp_creature2, creature2_hp)

            if creature2_hp <= 0:
                results[creature1['Name']] += 1 ###just as in game, defender goes first, when hp hits 0, opponent gets 1 pt, 10000x then find percentage of points
                break


            creature1_hp = perform_attack(temp_creature2, temp_creature1, creature1_hp)

            if creature1_hp <= 0:
              if creature1['Name'] == creature2['Name']:
                results[creature2['Name'] + "again"] += 1
              else:
                results[creature2['Name']] += 1
              break

    return results
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

        
        try:
            hp = int(fields["HP"].get())
        except ValueError:
            hp = 0  

        try:
            primary_damage = int(fields["Primary Damage"].get()[1:])  # Remove "d" prefix
        except (ValueError, IndexError):
            primary_damage = 8 

        try:
            secondary_damage = int(fields["Secondary Damage"].get()[1:])
        except (ValueError, IndexError):
            secondary_damage = 4 
        
        return {
            "Name": fields["Name"].get(),
            "HP": hp,
            "Agility": agility_mapping[fields["Agility"].get()],
            "Primary Damage": primary_damage,
            "Primary Accuracy": accuracy_mapping[fields["Primary Accuracy"].get()],
            "Secondary Damage": secondary_damage,
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
            json.dump(self.saved_creatures, file, indent=4)  

    def load_saved_creatures(self):
        try:
            with open("saved_creatures.json", "r") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    return data
                else:
                    print("Warning: Loaded data is not a dictionary.  Returning empty dictionary.")
                    return {}
        except (FileNotFoundError, json.JSONDecodeError):
            print("No saved creatures found or JSON error.  Returning empty dictionary.")
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
                    del self.creature1["Image Label"]
                elif image_label2:
                    self.creature1["Image Label"] = image_label2
                    image_label2.grid_forget()
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
