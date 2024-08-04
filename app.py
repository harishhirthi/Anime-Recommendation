import pickle
import gradio as gr
from bs4 import BeautifulSoup
import requests
import pandas as pd

hdr = {'User-Agent': 'Mozilla/5.0'}
cosine_property = pickle.load(open('similarity.pkl', 'rb')) # Load similarity matrix
data = pickle.load(open('anime.pkl', 'rb')) # Load anime data
indices = pd.Series(data.index, index = data['Name']).drop_duplicates() # Creating indices of anime title

"""_____________________________________________________________________________________________________________________________"""
# Function to recommend the anime for the given title.
def get_recommendations(title):
    try:
        idx = indices[title]
    except KeyError:
        raise ValueError(f"Anime {title} not found in list.")

    return get_recommendations_by_id(idx)


def get_recommendations_by_id(idx):
    
     # Extracting the respective anime similarity scores
    sim_scores = list(enumerate(cosine_property[idx]))
     # Sorting the similarity scores
    sim_scores = sorted(sim_scores, key = lambda x: x[1], reverse = True)

    suggest_amount = 15

    sim_scores = sim_scores[1 : suggest_amount + 1]

    # Get the anime indices
    anime_indices = [i[0] for i in sim_scores]

    # Map indices to anime_id
    anime_ids = data.iloc[anime_indices]['anime_id'].values    

    out = []
    for id in anime_ids:
        title = data[data['anime_id'] == id]['Name'].values[0]
        title = f"{title}" # Title of Anime
        out.append(title)
        an_name = title.replace(" ", '_')
        anime_link = f"https://myanimelist.net/anime/{id}/{an_name}" # Creating MyAnimeList link
        url_data = requests.get(anime_link, headers = hdr).text
        s_data = BeautifulSoup(url_data, 'html.parser')
        mal_dp = s_data.find("meta", property = "og:image")
        anime_poster_link = mal_dp.attrs['content'] # Extracting anime poster link from the above MAL link [1]
        # Creating Markdown content to display anime poster and anime url
        anime_img = f"""
        [MAL]({anime_link})
        <img src='{anime_poster_link}' alt='{an_name}' style='width:250px;height:300px;'>"""
        out.append(anime_img)
        synopsis = data[data['anime_id'] == id]['Synopsis'].values[0] # To display the summary of anime
        out.append(f"{synopsis}")

    return out

"""_____________________________________________________________________________________________________________________________"""
# Creating Gradio app for recommendation
theme = gr.themes.Soft(primary_hue = "orange").set(body_background_fill = '#e3e3e3')

with gr.Blocks(theme = theme) as app:
    with gr.Row(): # This row shows the title and toggle button to change the screen mode
        gr.Markdown("<h1><span style='color:orange'>Anime Recommendation 🐱‍👤🐱‍🏍🤖</span><h1>")
        with gr.Column(scale = 0):
            dark_btn = gr.Button("Toggle mode")
    
    with gr.Row(): # This row shows the dropdown list to select the anime, submit button to recommend and clear button to clear dropdown content
        with gr.Column(scale = 4):
            anime_title = gr.Dropdown(sorted(data['Name'].values.tolist()), label = "Anime", info = "Select the Anime from the list for recommendation.") 
        with gr.Column(scale = 1, min_width = 50):
            submit_btn = gr.Button("Submit", variant = "primary", interactive = False) # Initially, disabled and gets enabled once anime is selected in dropdown
            clear_ip = gr.ClearButton([anime_title])
   
    with gr.Row(): 
        gr.Markdown("<h5><span style='color:orange'>Recommended Anime will be displayed here !!!!</span></h5>")

    # This row will be visible once submit button is clicked
    with gr.Row(visible = False) as row_1: # This row indicates first 6 recommended anime with anime name, anime URL, anime poster and anime summary, each 3 in column
        outputs = []
        for i in range(1, 7):
            with gr.Column():
                with gr.Row(equal_height = True):
                    output_0 = gr.Textbox(label = "Name", lines = 2, max_lines = 2, show_copy_button = True) # Textbox for anime title
                    outputs.append(output_0)
                with gr.Row(equal_height = True):
                    output_1 = gr.Markdown(label = "Link and picture") # Markdown for anime URL and anime poster
                    outputs.append(output_1)
                with gr.Row(equal_height = True):
                    with gr.Accordion('Summary', open = False):
                        output_2 = gr.TextArea(label = "Summary", min_width = 250, show_label = False) # TextArea for anime summary
                        outputs.append(output_2)
        
    show_more_btn_1 = gr.Button("Show more ......", visible = False, interactive = True) # Button to show the next 6 anime

    # This row will be visible once show_more_btn_1 is clicked 
    with gr.Row(visible = False) as row_2: # This row indicates next 6 recommended anime with anime name, anime URL, anime image and anime summary, each 3 in column
        for i in range(7, 13):
            with gr.Column():
                with gr.Row(equal_height = True):
                    output_0 = gr.Textbox(label = "Name", lines = 2, max_lines = 2, show_copy_button = True)
                    outputs.append(output_0)
                with gr.Row(equal_height = True):
                    output_1 = gr.Markdown(label = "Link and picture")
                    outputs.append(output_1)
                with gr.Row(equal_height = True):
                    with gr.Accordion('Summary', open = False, visible = True) as accord:
                        output_2 = gr.TextArea(label = "Summary", min_width = 250, show_label = False)
                        outputs.append(output_2)

    show_more_btn_2 = gr.Button("Show more ...", visible = False, interactive = True) # Button to show the next 3 anime

    # This row will be visible once show_more_btn_2 is clicked
    with gr.Row(visible = False) as row_3: # This row indicates next 3 recommended anime with anime name, anime URL, anime image and anime summary, each 3 in column
        for i in range(13, 16):
            with gr.Column():
                with gr.Row(equal_height = True):
                    output_0 = gr.Textbox(label = "Name", lines = 2, max_lines = 2, show_copy_button = True)
                    outputs.append(output_0)
                with gr.Row(equal_height = True):
                    output_1 = gr.Markdown(label = "Link and picture")
                    outputs.append(output_1)
                with gr.Row(equal_height = True):
                    with gr.Accordion('Summary', open = False) as accord1:
                        output_2 = gr.TextArea(label = "Summary", min_width = 250, show_label=False)
                        outputs.append(output_2)

    submit_btn.click(fn = get_recommendations, inputs = [anime_title], outputs = outputs) # Function for submit button
    dark_btn.click(
        None,
        js="""
        () => {
            document.body.classList.toggle('dark');    
        }
        """)
    clear_btn = gr.ClearButton([anime_title] + outputs, visible = False) # Clear the entire contents

    # To enable submit button once anime is selected
    def enable(anime_title):
        if anime_title:
            return gr.Button(interactive = True)
        elif anime_title == None:
            return gr.Button(interactive = False)
    anime_title.change(fn = enable, inputs = anime_title, outputs = submit_btn)

    # To reset submit button when clear is clicked
    @gr.on(triggers = [clear_ip.click, clear_btn.click], inputs = None, outputs = submit_btn)
    def disable():
        return gr.Button(interactive = False)

    # To make first 6 anime to get displayed   
    @gr.on(triggers = [submit_btn.click], inputs = None, outputs = [row_1, show_more_btn_1, clear_btn])
    def show():
        return gr.update(visible = True), gr.update(visible = True), gr.update(visible = True)

    # To reset the screen layout when clear button is clicked
    @gr.on(triggers = [clear_btn.click], inputs = None, outputs = [row_1, row_2, show_more_btn_1, show_more_btn_2, row_3, clear_btn])
    def reset():
        return [gr.update(visible = False), gr.update(visible = False), gr.update(visible = False), gr.update(visible = False), gr.update(visible = False), gr.update(visible = False]
    
    # To show next 6 anime
    @gr.on(triggers = [show_more_btn_1.click], inputs = None, outputs = [row_2, show_more_btn_2, show_more_btn_1])
    def visible():
            return [gr.update(visible = True), gr.update(visible = True), gr.update(visible = False)]
    
    # To show next 3 anime
    @gr.on(triggers = [show_more_btn_2.click], inputs = None, outputs = [row_3, show_more_btn_2])
    def visible_2():
            return [gr.update(visible = True), gr.update(visible = False)]

gr.close_all() # To close all gradio instances

if __name__ == '__main__':

    app.launch(share = True)
    app.close()


"""
Reference:
1. https://github.com/Spidy20/Movie_Recommender_App

"""
