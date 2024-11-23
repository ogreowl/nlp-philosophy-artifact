import csv
import os
import re
import pandas as pd
import concurrent.futures

# Step 1: Load author references and book metadata from the CSV
def load_author_references_and_books(csv_file):
    author_references = {}
    book_metadata = {}
    valid_indexes = set()  # Set to store valid indexes (books listed in the CSV)

    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            author = row['Author']
            reference = row['Reference'].strip()  # Get the reference
            author_references[author] = [reference]  # Store the reference in a list
            
            # Store metadata for each book (index, book title, and author)
            book_metadata[row['Index']] = {
                'filename': row['Filename'],
                'author_of_book': row['Author'],
                'birth_death': row['Birth - Death']
            }

            # Add the index to the valid indexes set
            valid_indexes.add(row['Index'])

    return author_references, book_metadata, valid_indexes

# Step 2: Clean the context (remove large spaces and paragraph breaks)
def clean_context(text):
    # Replace multiple spaces or newlines with a single space
    return re.sub(r'\s+', ' ', text).strip()

# Step 3: Find references in the text and collect 200-character context
def find_references_with_context(book_text, ref_name, book_filename, author_of_book, birth_death, full_author_referenced, context_size=100):
    snippets = []
    pattern = re.compile(r'\b' + re.escape(ref_name) + r'\b', re.IGNORECASE)  # Word boundary match

    for match in pattern.finditer(book_text):
        start, end = match.start(), match.end()

        # Get the context around the match (100 characters before and after)
        before = clean_context(book_text[max(0, start - context_size):start])
        after = clean_context(book_text[end:end + context_size])

        # Collect the full snippet (200 characters total)
        snippet = before + book_text[start:end] + after

        # Store the reference, book filename, author, birth/death info, and snippet
        snippets.append({
            'book_filename': book_filename,
            'author_of_book': author_of_book,
            'birth_death': birth_death,
            'reference': ref_name,
            'full_author_referenced': full_author_referenced,
            'context': snippet
        })

    return snippets

# Step 4: Process a batch of books and save snippets for each reference
def process_batch(batch_books, author_references, book_metadata, context_size=100):
    all_snippets = []

    # Process each book in the batch
    for book_file in batch_books:
        book_index = os.path.splitext(book_file)[0]  # Extract index from the book file name (e.g., '10.txt' -> '10')
        book_path = os.path.join('books', book_file)

        if os.path.exists(book_path):
            with open(book_path, 'r', encoding='utf-8', errors='ignore') as f:
                book_text = f.read().lower()  # Convert to lowercase for case-insensitive search

                # Get the book title and author from metadata
                book_info = book_metadata.get(book_index, {})
                book_filename = book_info.get('filename', 'Unknown Book')
                author_of_book = book_info.get('author_of_book', 'Unknown Author')
                birth_death = book_info.get('birth_death', 'Unknown')

                # Iterate over authors and their reference names
                for full_author_referenced, ref_names in author_references.items():
                    for ref_name in ref_names:
                        snippets = find_references_with_context(
                            book_text, ref_name.lower(), book_filename, author_of_book, birth_death, full_author_referenced, context_size
                        )
                        all_snippets.extend(snippets)  # Collect all snippets

    return all_snippets

# Step 5: Save each batch of snippets to a separate CSV
def save_snippets_to_file(snippets, batch_index):
    df = pd.DataFrame(snippets)
    output_file = f'batch_{batch_index}.csv'
    df.to_csv(output_file, index=False)
    print(f"Saved batch {batch_index} to {output_file}")

# Step 6: Combine all batches into a single file
def combine_batches(num_batches, output_file):
    combined_df = pd.concat([pd.read_csv(f'batch_{i}.csv') for i in range(num_batches)])
    combined_df.to_csv(output_file, index=False)
    print(f"Combined all batches into {output_file}")

# Step 7: Parallelized batch processing
def collect_reference_snippets_parallel(book_folder, author_references, book_metadata, valid_indexes, batch_size=50, num_workers=4, context_size=100):
    # Get all the book files from the folder and filter only the ones listed in the CSV
    book_files = [f for f in sorted(os.listdir(book_folder)) if os.path.splitext(f)[0] in valid_indexes]
    total_books = len(book_files)

    # Split the books into batches
    batch_chunks = [book_files[i:i + batch_size] for i in range(0, total_books, batch_size)]

    # Process the batches in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(process_batch, batch, author_references, book_metadata, context_size) 
            for batch in batch_chunks
        ]

        for batch_index, future in enumerate(concurrent.futures.as_completed(futures)):
            snippets = future.result()
            save_snippets_to_file(snippets, batch_index)

    return len(batch_chunks)

# Main function to run the process in parallel and then combine batches
def main():
    csv_file = 'newest.csv'  # The CSV file containing the author references
    book_folder = 'books'  # The folder containing the books (as text files)
    output_file = 'references.csv'  # Output file for the final combined result
    context_size = 250  # Number of characters before and after the reference
    batch_size = 50  # Number of books per batch
    num_workers = 4  # Number of parallel workers

    # Load author references and book metadata
    author_references, book_metadata, valid_indexes = load_author_references_and_books(csv_file)

    # Collect reference snippets in parallel and save them to intermediate files
    num_batches = collect_reference_snippets_parallel(book_folder, author_references, book_metadata, valid_indexes, batch_size, num_workers, context_size)

    # Combine the intermediate batch files into a final CSV
    combine_batches(num_batches, output_file)

if __name__ == "__main__":
    main()