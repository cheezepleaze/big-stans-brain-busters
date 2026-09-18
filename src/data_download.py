# imports

from pathlib import Path
import logging

import urllib.request
import shutil

# configs

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s"
)

IMDB_BASE_URL = "https://datasets.imdbws.com"
DATASETS = [
    "name.basics.tsv.gz",
    "title.basics.tsv.gz",
    "title.principals.tsv.gz",
    "title.ratings.tsv.gz"
]


def download_imdb_data(url: str, output_path: Path) -> None:
    """
    Downloads movies data from IMDB to local data path (streamed).
    """

    if output_path.exists():
        logging.info(f"File already exists, skipping: {output_path.name}")
        return

    logging.info(f"Starting download: {url}")
    
    try:
        # stream the request to save memory
        with urllib.request.urlopen(url) as response:
            with open(output_path, "wb") as out_file:
                # shutil.copyfileobj reads and writes in chunks automatically
                shutil.copyfileobj(response, out_file)
        logging.info(f"Successfully downloaded: {output_path.name}")
        
    except Exception as e:
        logging.error(f"Failed to download {url}. Error: {e}")
        # clean up partial files if the download fails halfway
        if output_path.exists():
            output_path.unlink()

def main():
    project_root = Path(__file__).resolve().parents[1]
    raw_data_dir = project_root / "data" / "raw"
    
    raw_data_dir.mkdir(parents = True, exist_ok = True)
    
    for filename in DATASETS:
        url = f"{IMDB_BASE_URL}/{filename}"
        output_path = raw_data_dir / filename
        download_imdb_data(url, output_path)

if __name__ == "__main__":
    main()