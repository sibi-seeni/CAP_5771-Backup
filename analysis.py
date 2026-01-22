import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def load_data():
    # Connecting to SQLite database
    conn = sqlite3.connect('arc_raiders_sentiment.db')
    
    # Joining comments with video metadata to get the video titles and published dates
    query = """
    SELECT 
        c.text, 
        c.published_at as comment_date, 
        v.title as video_title,
        v.published_at as video_date
    FROM comments c
    JOIN videos v ON c.video_id = v.video_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert dates to datetime objects
    df['comment_date'] = pd.to_datetime(df['comment_date'])
    return df

def analyze_sentiment(df):
    analyzer = SentimentIntensityAnalyzer()
    
    print("Calculating sentiment scores...")
    # Apply VADER to each comment
    df['scores'] = df['text'].apply(lambda x: analyzer.polarity_scores(x))
    
    # Extract the 'compound' score (-1 is very negative, +1 is very positive)
    df['compound'] = df['scores'].apply(lambda score_dict: score_dict['compound'])
    
    # Categorize based on standard VADER thresholds
    df['sentiment'] = df['compound'].apply(
        lambda c: 'Positive' if c >= 0.05 else ('Negative' if c <= -0.05 else 'Neutral')
    )
    return df

def plot_sentiment_over_time(df):
    # Resample by week to see trends
    df.set_index('comment_date', inplace=True)
    weekly_sentiment = df['compound'].resample('W').mean()

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=weekly_sentiment, marker='o', color='royalblue')
    
    plt.title('Arc Raiders: Weekly Average Sentiment (2025-2026)')
    plt.xlabel('Date')
    plt.ylabel('Average Compound Sentiment Score')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Highlighting key events for report
    plt.axvline(pd.Timestamp('2025-10-30'), color='red', linestyle='--', label='Game Launch')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('sentiment_trend.png')
    print("Plot saved as sentiment_trend.png")

if __name__ == "__main__":
    data = load_data()
    if not data.empty:
        analyzed_data = analyze_sentiment(data)
        plot_sentiment_over_time(analyzed_data)

        # Exporting to CSV for your final submission
        analyzed_data.to_csv('arc_raiders_final_analysis.csv')
        print("Analysis complete. CSV exported.")
    else:
        print("No data found in database. Run the collector first!")