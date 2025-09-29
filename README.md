# Netflix-Style Movie & TV Show Recommender

A sleek, interactive movie and TV show recommender built with **Streamlit**, **Python**, and the **TMDb API**.
Designed to showcase **data science, API integration, and web app development skills** in a polished, Netflix-like interface.

---

## Project Structure

```bash
my_project/
├─ streamlit_app.py                       # Main Streamlit app
├─ netflix_recommendations.ipynb          # exploration notebook
├─ recommender_core.py                    # Recommendation engine
├─ netflix_titles.csv                     # Dataset
├─ requirements.txt                       # Python dependencies
├─ .gitignore                             # Ignore .env and cache files
└─ README.md                              # Project description
```
--- 

## Project Highlights

- **Search & Recommendation Engine:**  
  - Enter a movie or TV show to receive content-based recommendations using a similarity model.  
  - Optionally filter by genre, type (Movie/TV Show), and release year range.

- **Interactive UI:**  
  - Dark, Netflix-inspired theme with red accents.  
  - Responsive poster grid with zoom effects.  
  - Clickable description expanders for each poster.  

- **Data Insights:**  
  - Sidebar chart visualizing top genres in the dataset.  
  - Shows ability to handle and visualize real-world datasets.  

- **API Integration:**  
  - Fetches movie and TV show posters dynamically from **TMDb API**.  
  - Caches API calls to optimize performance.

---

## Technologies & Skills

- **Languages & Libraries:** Python, Pandas, Matplotlib, Requests, Streamlit  
- **APIs:** TMDb API for poster images  
- **Data Science Concepts:** Content-based recommendation, filtering, caching  
- **Web App / UI Skills:** Streamlit, CSS styling for interactive layout  

---

## How to Run

### Clone the Repository
```bash
git clone https://github.com/lizbethsarabia/Netflix-Recommender.git
cd Netflix-Recommender

pip install -r requirements.txt

```

###Set up TMDb API Key
Locally: Create .env in project root:

```bash
TMDB_API_KEY=your_api_key_here
```
Streamlit Cloud: Add TMDB_API_KEY in Settings → Secrets.

###Run app locally

```bash
streamlit run streamlit_app.py
```



