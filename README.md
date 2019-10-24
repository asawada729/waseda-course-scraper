# waseda-course-scraper

1. Create python3 virtual environment and activate it.

2. Download dependencies:
pip install -r requirements.txt

3. In src/scraper.py, at the end of the file:
Uncomment the function call write_to_local() if you want to save a json file of scraped data locally.
Uncomment the function call post_to_api() if you want to post the scraped data to api.

4. Run:
python scraper.py

5. (Optional) To export json data of courses into csv, run:
python json_to_pandas.py