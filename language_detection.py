"""
Language Detection for YouTube Comments
========================================
Detects language of comments and visualizes distribution.
"""

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from langdetect import detect, LangDetectException
from collections import Counter

def detect_and_visualize_languages(db_path='arc_raiders_sentiment.db', sample_size=None):
    """
    Detect languages in comments and create visualization.
    
    Args:
        db_path (str): Path to the SQLite database
        sample_size (int): If provided, only analyze a random sample of comments
    
    Returns:
        pd.DataFrame: DataFrame with added 'language' column
    """
    print("="*80)
    print("🌍 LANGUAGE DETECTION ANALYSIS")
    print("="*80 + "\n")
    
    # Load data
    print("Loading comments from database...")
    conn = sqlite3.connect(db_path)
    query = "SELECT comment_id, text FROM comments"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"✅ Loaded {len(df):,} comments\n")
    
    # Sample if requested
    if sample_size and sample_size < len(df):
        print(f"📊 Using random sample of {sample_size:,} comments for faster processing\n")
        df = df.sample(n=sample_size, random_state=42)
    
    # Detect language for each comment
    print("🔍 Detecting languages... (this may take a moment)")
    
    def safe_detect(text):
        """Safely detect language, return 'unknown' on error"""
        try:
            if pd.isna(text) or len(str(text).strip()) < 3:
                return 'unknown'
            return detect(str(text))
        except LangDetectException:
            return 'unknown'
        except Exception:
            return 'unknown'
    
    df['language'] = df['text'].apply(safe_detect)
    
    # Count languages
    lang_counts = Counter(df['language'])
    
    print(f"\n✅ Language detection complete!\n")
    print("="*80)
    print("📊 LANGUAGE DISTRIBUTION")
    print("="*80 + "\n")
    
    # Display statistics
    total = len(df)
    english_count = lang_counts.get('en', 0)
    
    print(f"{'Total comments analyzed:':<40} {total:>10,}")
    print(f"{'English comments:':<40} {english_count:>10,} ({english_count/total*100:>5.1f}%)")
    print(f"{'Non-English comments:':<40} {total - english_count:>10,} ({(total-english_count)/total*100:>5.1f}%)")
    print(f"{'Unique languages detected:':<40} {len(lang_counts):>10,}")
    
    print(f"\n{'Top 15 Languages:':^80}")
    print("-"*80)
    for i, (lang, count) in enumerate(lang_counts.most_common(15), 1):
        # Language code to name mapping for common languages
        lang_names = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch', 'ru': 'Russian',
            'ja': 'Japanese', 'ko': 'Korean', 'zh-cn': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)', 'ar': 'Arabic', 'hi': 'Hindi',
            'tr': 'Turkish', 'pl': 'Polish', 'sv': 'Swedish', 'no': 'Norwegian',
            'da': 'Danish', 'fi': 'Finnish', 'unknown': 'Unknown/Too Short'
        }
        lang_name = lang_names.get(lang, lang.upper())
        bar = '█' * int(count / lang_counts.most_common(1)[0][1] * 50)
        print(f"{i:>2}. {lang_name:<30} {count:>7,} ({count/total*100:>5.1f}%) {bar}")
    
    # Create visualization
    print(f"\n{'Creating visualization...':^80}")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Top 15 languages bar chart
    top_15 = dict(lang_counts.most_common(15))
    lang_names_map = {
        'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
        'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch', 'ru': 'Russian',
        'ja': 'Japanese', 'ko': 'Korean', 'zh-cn': 'Chinese (S)', 'zh-tw': 'Chinese (T)',
        'ar': 'Arabic', 'hi': 'Hindi', 'tr': 'Turkish', 'pl': 'Polish',
        'sv': 'Swedish', 'no': 'Norwegian', 'da': 'Danish', 'fi': 'Finnish',
        'unknown': 'Unknown'
    }
    
    languages = [lang_names_map.get(k, k.upper()) for k in top_15.keys()]
    counts = list(top_15.values())
    colors = ['#2ecc71' if 'English' in lang else '#e74c3c' if lang == 'Unknown' else '#3498db' 
              for lang in languages]
    
    axes[0, 0].barh(range(len(languages)), counts, color=colors, edgecolor='black', alpha=0.8)
    axes[0, 0].set_yticks(range(len(languages)))
    axes[0, 0].set_yticklabels(languages)
    axes[0, 0].set_xlabel('Number of Comments')
    axes[0, 0].set_title('Top 15 Languages Detected', fontsize=14, fontweight='bold')
    axes[0, 0].invert_yaxis()
    axes[0, 0].grid(True, alpha=0.3, axis='x')
    
    # Add count labels
    for i, (count, lang) in enumerate(zip(counts, languages)):
        axes[0, 0].text(count + max(counts)*0.01, i, f'{count:,}', va='center', fontsize=9)
    
    # 2. English vs Non-English pie chart
    english_vs_other = {
        'English': english_count,
        'Non-English': total - english_count
    }
    colors_pie = ['#2ecc71', '#e74c3c']
    explode = (0.05, 0)
    
    axes[0, 1].pie(english_vs_other.values(), labels=english_vs_other.keys(),
                   autopct='%1.1f%%', startangle=90, colors=colors_pie,
                   explode=explode, textprops={'fontsize': 12, 'fontweight': 'bold'})
    axes[0, 1].set_title('English vs Non-English Comments', fontsize=14, fontweight='bold')
    
    # 3. All languages (for reference)
    all_langs_sorted = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
    all_lang_names = [lang_names_map.get(k, k.upper()) for k, v in all_langs_sorted[:30]]
    all_counts = [v for k, v in all_langs_sorted[:30]]
    
    axes[1, 0].bar(range(len(all_lang_names)), all_counts, 
                   color=['#2ecc71' if name == 'English' else '#95a5a6' for name in all_lang_names],
                   edgecolor='black', alpha=0.7)
    axes[1, 0].set_xticks(range(len(all_lang_names)))
    axes[1, 0].set_xticklabels(all_lang_names, rotation=45, ha='right', fontsize=8)
    axes[1, 0].set_ylabel('Number of Comments')
    axes[1, 0].set_title('Top 30 Languages Distribution', fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # 4. Language diversity metrics
    metrics_text = f"""
LANGUAGE STATISTICS

Total Comments: {total:,}

English: {english_count:,} ({english_count/total*100:.1f}%)
Non-English: {total - english_count:,} ({(total-english_count)/total*100:.1f}%)

Unique Languages: {len(lang_counts)}

Top 5 Non-English Languages:
"""
    
    non_english = [(k, v) for k, v in lang_counts.most_common() if k != 'en'][:5]
    for lang, count in non_english:
        lang_name = lang_names_map.get(lang, lang.upper())
        metrics_text += f"\n  • {lang_name}: {count:,} ({count/total*100:.1f}%)"
    
    metrics_text += f"""

RECOMMENDATION:
"""
    if english_count / total >= 0.9:
        metrics_text += "\n✅ Dataset is predominantly English (≥90%)\n   Safe to filter for English-only analysis."
    elif english_count / total >= 0.7:
        metrics_text += "\n⚠️  Dataset has significant non-English content\n   Consider filtering, but note data loss."
    else:
        metrics_text += "\n❌ Dataset is very multilingual (<70% English)\n   Filtering may remove too much data.\n   Consider multilingual sentiment models."
    
    axes[1, 1].text(0.1, 0.9, metrics_text, transform=axes[1, 1].transAxes,
                    fontsize=11, verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.savefig('figures/language_distribution.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: figures/language_distribution.png\n")
    
    # Save results to CSV
    lang_summary = pd.DataFrame([
        {'language': k, 
         'language_name': lang_names_map.get(k, k.upper()),
         'count': v, 
         'percentage': v/total*100}
        for k, v in lang_counts.most_common()
    ])
    lang_summary.to_csv('language_distribution.csv', index=False)
    print(f"✅ Saved: language_distribution.csv\n")
    
    # Return dataframe with language column for further processing
    print("="*80)
    print("💡 NEXT STEPS")
    print("="*80 + "\n")
    print("To filter for English-only comments in your analysis:")
    print("")
    print("Option 1: Add to database (recommended)")
    print("```python")
    print("# Run this once to add language column to database")
    print("import sqlite3")
    print("conn = sqlite3.connect('arc_raiders_sentiment.db')")
    print("# Add language column")
    print("conn.execute('ALTER TABLE comments ADD COLUMN language TEXT')")
    print("# Update with detected languages")
    print("for idx, row in df.iterrows():")
    print("    conn.execute('UPDATE comments SET language = ? WHERE comment_id = ?',")
    print("                 (row['language'], row['comment_id']))")
    print("conn.commit()")
    print("conn.close()")
    print("```")
    print("")
    print("Option 2: Filter during analysis")
    print("```python")
    print("# In your analysis.py, after loading data:")
    print("df_english = df[df['language'] == 'en']")
    print("# Then proceed with sentiment analysis on df_english")
    print("```")
    print("")
    print("="*80 + "\n")
    
    return df


if __name__ == "__main__":
    import sys
    import os
    
    # Check if database exists
    if not os.path.exists('arc_raiders_sentiment.db'):
        print("❌ Error: Database 'arc_raiders_sentiment.db' not found!")
        print("Please run your data collection script first.")
        sys.exit(1)
    
    # Check if figures directory exists
    os.makedirs('figures', exist_ok=True)
    
    # Run language detection
    # Use sample_size=5000 for faster testing on large datasets
    # Remove sample_size parameter to analyze all comments
    df_with_languages = detect_and_visualize_languages(
        db_path='arc_raiders_sentiment.db',
        sample_size=None  # Set to e.g., 5000 for testing
    )
    
    print(f"🎉 Analysis complete! Detected languages for {len(df_with_languages):,} comments.")
