import os
import requests
import csv

def sanitize_filename(filename, max_length=100):
    sanitized = "".join(c for c in filename if c.isalnum() or c in (' ', '_')).rstrip()
    return sanitized[:max_length]

def format_birth_death_years(birth_year, death_year):
    if birth_year and death_year:
        return f"{birth_year} - {death_year}"
    elif birth_year:
        return f"{birth_year} - Unknown"
    elif death_year:
        return f"Unknown - {death_year}"
    else:
        return "Unknown - Unknown"

def fetch_books_from_gutendex(url, params=None):
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch books. Status code: {response.status_code}")
        return None

def download_books_from_gutendex(books, download_folder="books", csv_writer=None, start_index=1):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    index = start_index

    for book in books:
        title = book.get("title")
        authors = book.get("authors", [{"name": "Unknown", "birth_year": None, "death_year": None}])
        author_name = authors[0].get("name", "Unknown")
        birth_year = authors[0].get("birth_year")
        death_year = authors[0].get("death_year")
        
        birth_death_years = format_birth_death_years(birth_year, death_year)

        formats = book.get("formats", {})
        year_written = book.get("author_year") or "Unknown"

        download_url = formats.get("text/plain; charset=us-ascii")

        if download_url:
            file_name = f"{download_folder}/{index}.txt"

            if os.path.exists(file_name):
                print(f"Skipping {title} - Already downloaded.")
                index += 1
                continue

            try:
                response = requests.get(download_url)
                if response.status_code == 200:
                    with open(file_name, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded: {title}")

                    csv_writer.writerow([index, author_name, file_name, birth_death_years])
                else:
                    print(f"Failed to download {title}.")
            except OSError as e:
                print(f"Error downloading {title}: {e}")
        else:
            print(f"No text/plain format available for {title}.")

        index += 1

    return index

def main():
    params = {
        'topic': 'philosophy',
        'languages': 'en',
        'author_year_end': 1990,
        'mime_type': 'text/plain',
    }
    
    base_url = "https://gutendex.com/books/"
    next_url = base_url
    downloaded_books = 0
    total_books_to_download = 2500
    index = 1

    with open('books_metadata.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Index', 'Author', 'Filename', 'Birth - Death'])

        while next_url and downloaded_books < total_books_to_download:
            result = fetch_books_from_gutendex(next_url, params)

            if result and result.get('results'):
                books = result['results']
                print(f"Found {len(books)} books.")
                index = download_books_from_gutendex(books, start_index=index, csv_writer=csv_writer)
                downloaded_books += len(books)

                next_url = result.get('next')
                if next_url:
                    print(f"Fetching more books from: {next_url}")
            else:
                print("No more books found.")
                break

    print(f"Downloaded {downloaded_books} books.")

if __name__ == "__main__":
    main()