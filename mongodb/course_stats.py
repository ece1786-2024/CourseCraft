import pandas as pd
import matplotlib.pyplot as plt
import json

# Load the transformed data
with open("transformed_data.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Extract course data
courses = data["courses"]

# Create a DataFrame for analysis
df = pd.DataFrame(courses)

# Count courses by division
division_counts = df["division"].value_counts()

# Plot the barplot
plt.figure(figsize=(10, 6))
bars = plt.bar(division_counts.index, division_counts.values)

# Add exact numbers on top of each bar
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{int(height)}",
        ha="center",
        va="bottom",
        fontsize=10
    )

# Customize the plot
plt.title("Number of Courses by Division", fontsize=14)
plt.xlabel("Division", fontsize=12)
plt.ylabel("Number of Courses", fontsize=12)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

# Show the plot
plt.show()
