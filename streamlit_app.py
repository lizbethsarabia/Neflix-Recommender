import streamlit as st
import pandas as pd
from recommender_core import load_data, build_model, recommend
import matplotlib.pyplot as plt
import os
import streamlit as st
import requests
import difflib
from typing import Optional

# Try to load from Streamlit Cloud secrets first
if "TMDB_API_KEY" in st.secrets:
    TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
else:
    # Fallback: load from .env for local dev
    from dotenv import load_dotenv
    load_dotenv()
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Quick check (optional, but good for debugging locally)
if not TMDB_API_KEY:
    st.error("⚠️ TMDB_API_KEY not found! Please set it in .env or Streamlit secrets.")


# ------------------------
# Load & cache data
# ------------------------
@st.cache_data
def setup():
    df = load_data("netflix_titles.csv")
    cosine_sim = build_model(df)
    
    # Extract year from "release_year"
    if "release_year" in df.columns:
        df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce')
    return df, cosine_sim

df, cosine_sim = setup()

# ------------------------
# Sidebar: Extra Insights
# ------------------------
st.sidebar.header("📊 Dataset Insights")

# Top genres chart
genres = df['listed_in'].dropna().str.split(',').explode().str.strip()
top_genres = genres.value_counts().head(10)

fig, ax = plt.subplots()
top_genres.plot(kind='bar', ax=ax, color="skyblue")
ax.set_title("Top 10 Genres")
ax.set_ylabel("Count")
st.sidebar.pyplot(fig)

# ------------------------
# Main App
# ------------------------
st.markdown(
    """
    <style>
    .hero {
        background-color: #141414; /* Netflix dark background */
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
    }
    .hero h1 {
        color: white;
        font-size: 2.5em;
        margin: 10px 0 0 0;
    }
    </style>

    <div class="hero">
        <img src="https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg" 
             alt="Netflix" width="200">
        <h1>Movie & TV Show Recommender</h1>
    </div>
    """,
    unsafe_allow_html=True
)

#get posters
@st.cache_data(show_spinner=False)
def get_tmdb_poster(title: str, year: Optional[int] = None, media_type: str = "movie") -> Optional[str]:
    """
    Robust TMDb poster fetcher:
      - media_type: "movie" or "tv"
      - uses title similarity + year match + popularity to pick the best result
      - returns full image URL or None
    """
    title = (title or "").strip()
    if not title:
        return None

    media_type = media_type.lower()
    if media_type == "tv":
        search_url = "https://api.themoviedb.org/3/search/tv"
    else:
        search_url = "https://api.themoviedb.org/3/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US",
        "include_adult": False,
        "page": 1
    }
    # for movies, TMDb supports a 'year' param — pass it to narrow results
    if media_type == "movie" and year:
        params["year"] = year

    try:
        resp = requests.get(search_url, params=params, timeout=6)
        if resp.status_code != 200:
            return None
        results = resp.json().get("results", [])
        if not results:
            return None
    except Exception:
        return None

    # normalize popularity for scoring
    pops = [float(r.get("popularity") or 0) for r in results]
    max_pop = max(pops) if pops else 1.0

    best = None
    best_score = -1.0

    for r in results:
        # TMDb uses 'title' for movies, 'name' for TV shows
        candidate_title = r.get("title") or r.get("name") or ""
        candidate_title = candidate_title.strip()

        # Title similarity (0..1)
        title_sim = difflib.SequenceMatcher(None, title.lower(), candidate_title.lower()).ratio()

        # Year match score (0..1)
        rd = r.get("release_date") or r.get("first_air_date") or ""
        year_score = 0.0
        if year and rd:
            try:
                r_year = int(rd[:4])
                diff = abs(r_year - year)
                if diff == 0:
                    year_score = 1.0
                elif diff <= 1:
                    year_score = 0.7
                elif diff <= 3:
                    year_score = 0.4
                else:
                    year_score = 0.0
            except Exception:
                year_score = 0.0

        # popularity normalized 0..1
        pop = float(r.get("popularity") or 0)
        pop_norm = pop / max_pop if max_pop > 0 else 0.0

        # scoring: prefer title similarity, but boost by year & popularity
        if year:
            score = 0.6 * title_sim + 0.3 * year_score + 0.1 * pop_norm
        else:
            score = 0.85 * title_sim + 0.15 * pop_norm

        if score > best_score:
            best_score = score
            best = r

    # require a minimum similarity to avoid returning wrong posters
    # tweak thresholds if needed:
    if best is None:
        return None

    # thresholds:
    if year:
        threshold = 0.30   # with year provided we can be more lenient
    else:
        threshold = 0.60   # without year require a stronger title match

    if best_score < threshold:
        return None

    poster_path = best.get("poster_path")
    if poster_path:
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return None


# Filters
st.subheader("Filters")
genre_filter = st.multiselect("Select genre(s):", sorted(genres.unique()))
year_range = st.slider("Select release year range:",
                       int(df['release_year'].min()),
                       int(df['release_year'].max()),
                       (2000, 2020))
type_filter = st.radio("Select type:", ["All", "Movie", "TV Show"])

# Dropdown for movie selection
movie_name = st.selectbox(
    "Pick a movie/show:",
    [""] + sorted(df['title'].unique()),  # add an empty first option
    format_func=lambda x: "Type to search..." if x == "" else x
)



# ------------------------
# Recommendations
# ------------------------

# Detect if user interacted (movie chosen OR filters changed)
default_year_range = (int(df['release_year'].min()), int(df['release_year'].max()))
user_did_something = movie_name or genre_filter or type_filter != "All" or year_range != default_year_range

if user_did_something:
    # Case 1: movie-based recommendations
    if movie_name:
        results = recommend(movie_name, df, cosine_sim)
        results_df = df[df['title'].isin(results)]
    else:  # Case 2: filter-only recommendations
        results_df = df.copy()

    # Apply filters
    if genre_filter:
        results_df = results_df[results_df['listed_in'].apply(
            lambda g: any(f in g for f in genre_filter)
        )]

    results_df = results_df[
        (results_df['release_year'] >= year_range[0]) &
        (results_df['release_year'] <= year_range[1])
    ]

    if type_filter != "All":
        results_df = results_df[results_df['type'] == type_filter]

# Display results
if not results_df.empty:
    st.markdown("🍿 **Here are some great picks for you:**")

    cols = st.columns(3)  # 3 posters per row

    for i, (_, row) in enumerate(results_df.head(9).iterrows()):
        with cols[i % 3]:
            # Get poster
            media_type = "tv" if row["type"].lower() == "tv show" else "movie"
            poster_url = get_tmdb_poster(row['title'], int(row['release_year']) if pd.notna(row['release_year']) else None, media_type)

            
            # Poster or fallback
            if poster_url:
                st.image(poster_url, use_container_width=True)
            else:
                st.image(
                    "https://via.placeholder.com/300x450?text=No+Poster",
                    use_container_width=True
                )

            # Title + Year
            st.markdown(
                f"<h4 style='margin:5px 0; color:#E50914;'>{row['title']}</h4>",
                unsafe_allow_html=True
            )
            st.caption(f"{int(row['release_year']) if pd.notna(row['release_year']) else 'N/A'} • {row['type']}")

            # Expander for description
            with st.expander("📖 Description"):
                st.write(row['description'] if pd.notna(row['description']) else "No description available.")
else:
    st.warning("🚫 No recommendations match your filters. Try adjusting them!")



