import os
import re
import yaml
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta

# Global variables
recipes_folder = r"C:\Users\wardv\iCloudDrive\[4]Obsidian\2 Areas\Koken"

def get_lunch_salad_recipes():
    lunch_salad_recipes = {}
    for root, dirs, files in os.walk(recipes_folder):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '#LunchSalad' in content:
                        title = os.path.splitext(file)[0]
                        ingredients, portions = extract_ingredients(content)
                        # Default portion is 1 if not specified
                        lunch_salad_recipes[title] = {
                            'path': file_path,
                            'ingredients': ingredients,
                            'portions': portions if portions else 1
                        }
    return lunch_salad_recipes

def extract_ingredients(content):
    ingredients = []

    # First try to find a 'portions' line
    portions = None
    portions_match = re.search(r'portions:\s*(\d+)', content, re.IGNORECASE)
    if portions_match:
        portions = int(portions_match.group(1))

    # If ingredients not in YAML, fallback to Markdown section
    # (We assume ingredients are listed under "## Ingredients")
    ingredients_match = re.search(r'## Ingredients\s*(.*?)\n(##|\Z)', content, re.DOTALL)
    if ingredients_match:
        ingredients_text = ingredients_match.group(1)
        ingredients = re.findall(r'-\s*(.+)', ingredients_text)

    return ingredients, portions

def normalize_fractions(text):
    fractions_map = {
        '½': '0.5',
        '¼': '0.25',
        '¾': '0.75'
    }
    for frac_char, decimal_str in fractions_map.items():
        text = text.replace(frac_char, decimal_str)
    return text

def scale_ingredient(ingredient, factor):
    ingredient = normalize_fractions(ingredient)
    match = re.match(r"^(\d+(?:\.\d+)?)(.*)$", ingredient.strip())
    if match:
        quantity_str = match.group(1)
        rest = match.group(2).strip()
        quantity = float(quantity_str)
        scaled_quantity = quantity * factor
        if scaled_quantity.is_integer():
            scaled_quantity = int(scaled_quantity)
        return f"{scaled_quantity} {rest}".strip()
    else:
        # No numeric prefix found, return as is
        return ingredient

def parse_ingredient_line(line):
    match = re.match(r'^(\d+(?:\.\d+)?)(.*)$', line.strip())
    if match:
        quantity_str = match.group(1)
        description = match.group(2).strip()
        quantity = float(quantity_str)
        return quantity, description
    else:
        # No numeric quantity
        return None, line.strip()

def save_to_obsidian(meal_plan, shopping_list):
    week_number = datetime.now().isocalendar()[1]
    date_range = f"{(datetime.now()).strftime('%B %d')} - {(datetime.now() + timedelta(days=4)).strftime('%B %d')}"
    meal_plan_content = f"# Weekly Meal Plan for Week {week_number}\n\n"
    meal_plan_content += f"### Date Range: {date_range}\n\n"
    meal_plan_content += "## Meals\n\n"
    for day, recipe_title in meal_plan.items():
        meal_plan_content += f"### {day}\n- Lunch: [[{recipe_title}]]\n\n"

    meal_plan_content += "## Shopping List\n\n"
    for item in shopping_list:
        meal_plan_content += f"- {item}\n"

    meal_plan_filename = f"Meal Plan Week {week_number}.md"
    meal_plan_path = os.path.join(recipes_folder, meal_plan_filename)
    with open(meal_plan_path, 'w', encoding='utf-8') as f:
        f.write(meal_plan_content)
    messagebox.showinfo("Success", f"Meal plan saved to {meal_plan_path}")

class ToolTip:
    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind('<Enter>', self.enter)
        widget.bind('<Leave>', self.leave)

    def enter(self, event=None):
        self.showtip()

    def leave(self, event=None):
        self.hidetip()

    def showtip(self):
        if not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)  # Remove window decorations
        tw.configure(bg="#ffffe0", padx=5, pady=5, relief="solid", borderwidth=1)
        label = tk.Label(tw, text=self.text, bg="#ffffe0", wraplength=300)
        label.pack()

        tw.wm_geometry(f"+{x}+{y}")

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
        self.tipwindow = None

    def update_text(self, new_text):
        self.text = new_text

class MealPlannerApp:
    def __init__(self, master):
        self.master = master
        master.title("Obsidian Meal Planner")

        master.minsize(600, 400)
        master.configure(bg="#d4f1c5", padx=30, pady=20)

        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Define custom styles
        self.style.configure("Green.TFrame", background="#d4f1c5")
        self.style.configure("Header.TFrame", background="#a5d6a7")
        self.style.configure("Header.TLabel", background="#a5d6a7", foreground="#1b5e20", font=("Helvetica", 18, "bold"))
        self.style.configure("Subtitle.TLabel", background="#a5d6a7", foreground="#2e7d32", font=("Helvetica", 10))
        self.style.configure("Title.TLabel", background="#d4f1c5", foreground="#1b5e20", font=("Helvetica", 14))
        self.style.configure("Bold.TLabel", background="#d4f1c5", foreground="#1b5e20", font=("Helvetica", 12, "bold"))
        self.style.configure("Regular.TLabel", background="#d4f1c5", foreground="#1b5e20", font=("Helvetica", 12))
        self.style.configure("Green.TButton", background="#4caf50", foreground="white", font=("Helvetica", 10))
        self.style.map("Green.TButton",
                       background=[("active", "#43a047")],
                       foreground=[("active", "white")])
        self.style.configure("TCombobox", fieldbackground="#ffffff")

        # Load recipes
        self.lunch_salad_recipes = get_lunch_salad_recipes()
        self.recipe_titles = list(self.lunch_salad_recipes.keys())

        # Meal plan dictionary
        self.meal_plan = {}
        self.selected_recipes = {}
        self.day_portions = {}
        self.tooltips = {}
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        # Create widgets
        self.create_widgets()

    def create_widgets(self):
        # Header Frame
        header_frame = ttk.Frame(self.master, style="Header.TFrame", padding=(0, 0, 0, 20))
        header_frame.pack(fill='x')

        title_label = ttk.Label(header_frame, text="Obsidian Meal Planner", style="Header.TLabel")
        title_label.pack()
        subtitle_label = ttk.Label(header_frame, text="Generate weekly meal plans and shopping lists", style="Subtitle.TLabel")
        subtitle_label.pack()

        # Instructions
        instructions_label = ttk.Label(self.master, text="Select recipes and portions for each workday:", style="Title.TLabel")
        instructions_label.pack(pady=10)

        # Separator
        separator = ttk.Separator(self.master, orient='horizontal')
        separator.pack(fill='x', pady=10)

        # Main selection frame (using grid)
        selection_frame = ttk.Frame(self.master, style="Green.TFrame")
        selection_frame.pack(fill=tk.BOTH, expand=True)

        # Add column headers
        ttk.Label(selection_frame, text="Day", style="Bold.TLabel").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        ttk.Label(selection_frame, text="Recipe", style="Bold.TLabel").grid(row=0, column=1, padx=5, pady=5, sticky='w')
        ttk.Label(selection_frame, text="Portions", style="Bold.TLabel").grid(row=0, column=2, padx=5, pady=5, sticky='w')

        for idx, day in enumerate(self.days, start=1):
            ttk.Label(selection_frame, text=day, style="Regular.TLabel").grid(row=idx, column=0, padx=5, pady=5, sticky='e')
            var = tk.StringVar(value=self.recipe_titles[0] if self.recipe_titles else '')
            self.selected_recipes[day] = var
            option_menu = ttk.Combobox(selection_frame, textvariable=var, values=self.recipe_titles, state="readonly", width=40)
            option_menu.grid(row=idx, column=1, padx=5, pady=5, sticky='w')

            # Create a tooltip for the combobox
            tooltip = ToolTip(option_menu, text=var.get())
            self.tooltips[day] = tooltip
            var.trace_add("write", lambda *args, v=var, t=tooltip: t.update_text(v.get()))

            # Portion spinbox with default = 1
            portion_var = tk.IntVar(value=1)
            self.day_portions[day] = portion_var
            portions_spin = ttk.Spinbox(selection_frame, from_=1, to=100, textvariable=portion_var, width=5)
            portions_spin.grid(row=idx, column=2, padx=5, pady=5, sticky='w')

        # Button frame at the bottom, aligned to the right
        button_frame = ttk.Frame(self.master, style="Green.TFrame")
        button_frame.pack(fill='x', pady=20)

        button_frame.columnconfigure(0, weight=1)

        self.generate_button = ttk.Button(button_frame, text="Generate Meal Plan", style="Green.TButton", command=self.generate_meal_plan)
        self.generate_button.grid(row=0, column=1, padx=10, sticky='e')

        self.exit_button = ttk.Button(button_frame, text="Exit", style="Green.TButton", command=self.master.quit)
        self.exit_button.grid(row=0, column=2, padx=(10, 20), sticky='e')

    def generate_meal_plan(self):
        # Build meal plan dictionary
        self.meal_plan = {}
        for day in self.days:
            recipe_title = self.selected_recipes[day].get()
            if recipe_title:
                self.meal_plan[day] = recipe_title

        # Collect selected recipes info
        selected_recipes_info = {title: self.lunch_salad_recipes[title] for title in self.meal_plan.values()}

        # Dictionary to accumulate all ingredients: {description: total_quantity}
        ingredient_totals = {}

        for day, recipe_title in self.meal_plan.items():
            recipe_data = selected_recipes_info[recipe_title]
            default_portions = recipe_data.get('portions', 1)  # default to 1 if not found
            desired_portions = self.day_portions[day].get()
            factor = desired_portions / default_portions if default_portions else 1

            for ingredient in recipe_data['ingredients']:
                scaled_ingredient = scale_ingredient(ingredient, factor)
                qty, desc = parse_ingredient_line(scaled_ingredient)

                if desc not in ingredient_totals:
                    ingredient_totals[desc] = qty
                else:
                    # If both are numeric, sum them
                    if ingredient_totals[desc] is not None and qty is not None:
                        ingredient_totals[desc] += qty
                    else:
                        # If one has no numeric value, we can't sum
                        ingredient_totals[desc] = None

        # Convert ingredient_totals back to a list of strings
        final_shopping_list = []
        for desc, total_qty in ingredient_totals.items():
            if total_qty is not None:
                # Format total qty (as int if whole number)
                if float(total_qty).is_integer():
                    total_qty = int(total_qty)
                final_shopping_list.append(f"{total_qty} {desc}")
            else:
                # No numeric quantity
                final_shopping_list.append(desc)

        # Sort the list
        final_shopping_list.sort()

        # Confirm and save
        confirm = messagebox.askyesno("Confirm", "Do you want to save the meal plan and shopping list to Obsidian?")
        if confirm:
            save_to_obsidian(self.meal_plan, final_shopping_list)


def main():
    root = tk.Tk()
    app = MealPlannerApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()