# ScrapeFOMC

This repository contains python codes to scrape FOMC meeting dates including selected documents.

## Scrape History
With the following code the history (up to 2016 at the moment) can be downloaded:
```python
dirname = "/path/to/repository"

# Which documents to download
documentTypes = ["Record of Policy Actions", "Minutes", "Beige Book", "Tealbook A", "Tealbook B", "Greenbook",
                 "Bluebook", "Redbook", "Longer-Run Goals", "Memoranda", "Statement", "Supplement", "Transcript",
                 "Individual Projections"]

startyear = 1936
endyear = 2016
df1 = get_fomc_archive(dirname, startyear, endyear, documentTypes)
```

## Scrape last 5 years
Some documents are only released after 5 years. With the following code the the last five years of meeting dates and available documents can be downloaded:
```python
# Which documents to download
documentTypes = ["Minutes", "Longer-Run Goals", "Statement", "Projection"]

df2 = get_fomc_current(dirname, documentTypes)
```

Note: The program uses the selenium package with geckodriver. See here for more information: ![https://github.com/mozilla/geckodriver](https://github.com/mozilla/geckodriver)