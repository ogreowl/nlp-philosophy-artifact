# helpers.py

# Import Libraries
import pandas as pd
import numpy as np
from matplotlib.patches import FancyArrowPatch
from ipywidgets import Dropdown, SelectMultiple, IntSlider

# check if a row matches any of the selected categories
def row_matches_categories(row, selected_categories):
    if "All" in selected_categories:
        return True
    row_categories = {cat.strip() for cat in row.split(",")}
    return bool(row_categories & set(selected_categories))

# get philosophers to display and their top references/referenced-by philosophers.
def get_display_philosophers(df_filtered, philosopher, top_references, top_referenced_by):
    df_philosopher = df_filtered[df_filtered['author_of_book'] == philosopher]
    top_referenced = df_philosopher['full_author_referenced'].value_counts().head(top_references).index
    top_referenced_by_philosophers = df_filtered[df_filtered['full_author_referenced'] == philosopher]['author_of_book'].value_counts().head(top_referenced_by).index
    display_philosophers = list(set(top_referenced).union(set(top_referenced_by_philosophers), {philosopher}))
    return display_philosophers, top_referenced, top_referenced_by_philosophers

# calculate coordinates (birth year, reference count) for each philosopher
def calculate_coordinates(df_filtered, display_philosophers, reference_counts):
    coordinates = {}
    for philosopher_name in display_philosophers:
        philosopher_rows = df_filtered[df_filtered['author_of_book'] == philosopher_name]
        if not philosopher_rows.empty:
            birth_year = philosopher_rows['birth_year'].iloc[0]
            num_references_made = reference_counts.get(philosopher_name, 0)
            if pd.notna(birth_year) and np.isfinite(num_references_made):
                coordinates[philosopher_name] = (birth_year, num_references_made)
    return coordinates

# determine the color for each philosopher
def get_philosopher_color(philosopher_name, main_philosopher, top_referenced, top_referenced_by):
    if philosopher_name == main_philosopher:
        return '#1E88E5'
    elif philosopher_name in top_referenced and philosopher_name in top_referenced_by:
        return '#7B1FA2' 
    elif philosopher_name in top_referenced_by:
        return '#D81B60'
    return '#00ACC1'     

# draw arrow connections between philosophers based on reference data
def draw_connections(ax, df_display, coordinates, threshold, arrow_alpha, arrow_width):
    unique_connections = set()
    reference_counts_pairs = df_display.groupby(['author_of_book', 'full_author_referenced']).size()
    
    for (source, target), count in reference_counts_pairs.items():
        if source != target and count >= threshold and (source, target) not in unique_connections:
            unique_connections.add((source, target))
            if source in coordinates and target in coordinates:
                arrow = FancyArrowPatch(
                    posA=coordinates[source],
                    posB=coordinates[target],
                    connectionstyle="arc3,rad=0.2",
                    arrowstyle=f"->,head_length=2,head_width=0.8",
                    color='gray',
                    alpha=arrow_alpha,
                    linewidth=arrow_width
                )
                ax.add_patch(arrow)

# filter the dataframe based on selected categories and philosopher             
def filter_dataframe(df, categories_to_include, philosopher):
    if categories_to_include is None:
        categories_to_include = df['predicted_category'].unique()
    df_filtered = df[df['predicted_category'].apply(lambda row: row_matches_categories(row, categories_to_include))]
    return df_filtered
   
# plot scatter points for philosophers with size and color based on references   
def plot_scatter(ax, coordinates, restricted_referenced_counts, philosopher_name, top_referenced, top_referenced_by, main_philosopher, point_size, font_size, bubble_scale):
    for philosopher_name, (x, y) in coordinates.items():
        first_name = philosopher_name.split()[0].rstrip(',')
        color = get_philosopher_color(philosopher_name, main_philosopher, top_referenced, top_referenced_by)

        ax.scatter(x, y, s=point_size, c=color, edgecolor='k', alpha=0.7)
        ax.text(x + 5, y, first_name, fontsize=font_size)

        if philosopher_name in restricted_referenced_counts:
            bubble_size = restricted_referenced_counts[philosopher_name] * bubble_scale
            ax.scatter(x, y, s=bubble_size, c=color, alpha=0.3, edgecolor='none')
      
# axes, labels, & title for the visualization
def configure_axes(ax, philosopher, font_size, title_font_size):
    ax.tick_params(axis='both', labelsize=font_size)
    ax.set_xlabel("Birth Year", fontsize=font_size)
    ax.set_ylabel("Number of References Made", fontsize=font_size)
    ax.set_title(f"Top References for {philosopher}", fontsize=title_font_size)
    
# widgets for interactive selection
def create_widgets(sorted_philosophers, category_options):
    philosopher_dropdown = Dropdown(
        options=sorted_philosophers, 
        description="Philosopher:",
        layout={'width': '500px'}
    )

    categories_select = SelectMultiple(
        options=category_options,
        value=["All"],
        description="Categories:",
        layout={'width': '500px'}
    )

    top_references_slider = IntSlider(
        value=10, min=1, max=50,
        description="Outgoing References:",
        style={'description_width': '150px'},
        layout={'width': '500px'}
    )

    top_referenced_by_slider = IntSlider(
        value=10, min=1, max=50,
        description="Incoming References:",
        style={'description_width': '150px'},
        layout={'width': '500px'}
    )

    threshold_slider = IntSlider(
        value=1, min=1, max=20,
        description="Line Threshold:",
        style={'description_width': '150px'},
        layout={'width': '500px'}
    )

    return (philosopher_dropdown, categories_select, top_references_slider, top_referenced_by_slider, threshold_slider)