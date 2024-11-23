import os
import requests
import csv

def sanitize_filename(filename, max_length=100):
    """Sanitize the filename to avoid illegal characters and limit the filename length."""
    sanitized = "".join(c for c in filename if c.isalnum() or c in (' ', '_')).rstrip()
    return sanitized[:max_length]  # Truncate to a maximum length

def format_birth_death_years(birth_year, death_year):
    """Format birth and death years as 'YYYY - YYYY' or handle missing years gracefully."""
    if birth_year and death_year:
        return f"{birth_year} - {death_year}"
    elif birth_year:
        return f"{birth_year} - Unknown"
    elif death_year:
        return f"Unknown - {death_year}"
    else:
        return "Unknown - Unknown"

def fetch_books_from_gutendex(url, params=None):
    """Fetch books from the Gutendex API with the given parameters."""
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch books. Status code: {response.status_code}")
        return None

def download_books_from_gutendex(books, download_folder="books", csv_writer=None, start_index=1):
    """Download books in text/plain format, skipping already downloaded files, and logging data to a CSV."""
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    index = start_index

    for book in books:
        title = book.get("title")
        authors = book.get("authors", [{"name": "Unknown", "birth_year": None, "death_year": None}])  # Default to "Unknown" if no authors found
        author_name = authors[0].get("name", "Unknown")
        birth_year = authors[0].get("birth_year")
        death_year = authors[0].get("death_year")
        
        # Format birth and death years in 'YYYY - YYYY' format
        birth_death_years = format_birth_death_years(birth_year, death_year)

        formats = book.get("formats", {})
        year_written = book.get("author_year") or "Unknown"  # Assuming author_year contains the year written

        # Only download if the book has a text/plain format
        download_url = formats.get("text/plain; charset=us-ascii")

        if download_url:
            file_name = f"{download_folder}/{index}.txt"

            # Check if the file already exists before downloading
            if os.path.exists(file_name):
                print(f"Skipping {title} - Already downloaded.")
                index += 1
                continue

            # Download the file
            try:
                response = requests.get(download_url)
                if response.status_code == 200:
                    with open(file_name, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded: {title}")

                    # Write data to CSV with author birth and death years
                    csv_writer.writerow([index, author_name, file_name, birth_death_years])
                else:
                    print(f"Failed to download {title}.")
            except OSError as e:
                print(f"Error downloading {title}: {e}")
        else:
            print(f"No text/plain format available for {title}.")

        index += 1

    return index  # Return the next index to keep track across multiple batches

def main():
    # Parameters for fetching philosophy books in English before 1950
    params = {
        'topic': 'philosophy',
        'languages': 'en',
        'author_year_end': 1990,
        'mime_type': 'text/plain',
    }
    
    base_url = "https://gutendex.com/books/"
    next_url = base_url
    downloaded_books = 0
    total_books_to_download = 2500  # Set this to the desired number of books to download
    index = 1  # Start index for book numbering

    # Open CSV file to log book data
    with open('books_metadata.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        # Write the header for the CSV
        csv_writer.writerow(['Index', 'Author', 'Filename', 'Birth - Death'])

        while next_url and downloaded_books < total_books_to_download:
            result = fetch_books_from_gutendex(next_url, params)

            if result and result.get('results'):
                books = result['results']
                print(f"Found {len(books)} books.")
                index = download_books_from_gutendex(books, start_index=index, csv_writer=csv_writer)
                downloaded_books += len(books)

                # Follow pagination link
                next_url = result.get('next')
                if next_url:
                    print(f"Fetching more books from: {next_url}")
            else:
                print("No more books found.")
                break

    print(f"Downloaded {downloaded_books} books.")

if __name__ == "__main__":
    main()