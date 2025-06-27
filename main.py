from downloader import download_pdfs_eps, download_pdfs_informatika
from extractor import extract
from cache import *
import os, sys
from dotenv import load_dotenv


# to activate venv
# $ source venv/bin/activate 

if __name__ == "__main__":
    print("#START")
    load_dotenv()
    username = os.getenv("USERNAME")
    info_pass = os.getenv("INFO_PASSWORD")
    eps_pass = os.getenv("EPS_PASSWORD")

    if not all([username, info_pass, eps_pass]):
        print("❌ Missing one or more required environment variables: USERNAME, INFO_PASSWORD, EPS_PASSWORD")
        sys.exit(1)

    cache = initialize_download_cache()
    save_download_cache(cache)

    #download_pdfs_informatika(username, info_pass, cache)
    download_pdfs_eps(username, eps_pass, cache)

    if is_all_true():
        extract(cache)
    print("#ENDE")

