import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def load_data(path="netflix_titles.csv"):
    df = pd.read_csv(path)
    df['combined'] = (
        df['title'] + " " + 
        df['director'].fillna('') + " " + 
        df['cast'].fillna('') + " " + 
        df['listed_in']
    )
    return df

def build_model(df):
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    return cosine_sim

def recommend(title, df, cosine_sim):
    try:
        idx = df[df['title'].str.lower() == title.lower()].index[0]
    except IndexError:
        return ["❌ Title not found. Try another."]
    
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    movie_indices = [i[0] for i in sim_scores[1:6]]
    return df['title'].iloc[movie_indices].tolist()
