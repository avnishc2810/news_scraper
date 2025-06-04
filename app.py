from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import asyncio
from scrape import scrape_articles 
from datetime import datetime
import os 

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form['query']
        domains_input = request.form['domains']
        valid_domains = [d.strip() for d in domains_input.split(',') if d.strip()]
        
        # Run the async scrape
        articles = asyncio.run(scrape_articles(query, valid_domains))
        
        # Create filename and save path
        filename = f"{query[:50].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        output_dir = "output"
        filepath = os.path.join(output_dir, filename)
        os.makedirs(output_dir, exist_ok=True)

        # Write articles to the file
        with open(filepath, "w", encoding="utf-8") as f:
            for idx, article in enumerate(articles, 1):
                f.write(f"Article {idx}\n")
                f.write(f"Title: {article['Title']}\n")
                f.write(f"URL: {article['URL']}\n")
                f.write(f"Content:\n{article['Content']}\n")
                f.write("="*100 + "\n\n")

        # Redirect user to download link
        return redirect(url_for('download_file', filename=filename))

    return render_template('index.html')


@app.route('/download/<filename>')
def download_file(filename):
    output_dir = os.path.abspath("output")
    return send_from_directory(output_dir, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
