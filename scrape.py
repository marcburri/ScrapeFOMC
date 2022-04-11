import os
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By


def get_request_session(driver):
    import requests
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    return session


def greenbook_special_cases(doc, row, browser, year):
    try:
        p1 = doc.find_element(by=By.XPATH,
                              value=".//*[contains(text(), 'Part 1')]")
        p2 = doc.find_element(by=By.XPATH,
                              value=".//*[contains(text(), 'Part 2')]")

        link1 = p1.get_attribute("href")
        link2 = p2.get_attribute("href")

        folderpath = os.path.join(dirname, "Documents", "Greenbook", str(year))
        filepath1 = os.path.join(folderpath, os.path.basename(link1))
        filepath2 = os.path.join(folderpath, os.path.basename(link2))

        Path(folderpath).mkdir(parents=True, exist_ok=True)

        chunk_size = 2000
        session = get_request_session(browser)
        r = session.get(link1, stream=True)
        with open(filepath1, 'wb') as file:
            for chunk in r.iter_content(chunk_size):
                file.write(chunk)

        r = session.get(link1, stream=True)
        with open(filepath2, 'wb') as file:
            for chunk in r.iter_content(chunk_size):
                file.write(chunk)


        row["Greenbook"] = os.path.join("Documents", "Greenbook", str(year),
                                             os.path.basename(link1)) + ";" + \
                                os.path.join("Documents", documentType, str(year),
                                             os.path.basename(link2))
        return row
    except Exception as e:
        print(e)


def get_fomc_archive(dirname, startyear, endyear, documentTypes):
    # Operating in headless mode?
    opts = Options()
    opts.headless = False

    # Start Browser
    browser = webdriver.Firefox(options=opts, executable_path=os.path.join(dirname, "geckodriver"))

    # Initiate dataframe
    df = pd.DataFrame(columns=('Start', 'End', "Twoday", "Meeting", "Press Conference", "Record of Policy Actions", "Minutes", "Beige Book",
                           "Tealbook A", "Tealbook B", "Greenbook", "Bluebook", "Redbook", "Longer-Run Goals",
                           "Memoranda", "Statement", "Supplement", "Transcript", "Individual Projections"))

    # Choose daterange to scrape
    years = range(startyear, endyear)
    for year in years:
        url = "https://www.federalreserve.gov/monetarypolicy/fomchistorical" + str(year) + ".htm"
        browser.get(url)
        meetings = browser.find_elements(by=By.CLASS_NAME, value="panel-default")
        for meeting in meetings:
            docs = meeting.find_elements(by=By.CSS_SELECTOR, value="p")

            heading = meeting.find_element(by=By.CSS_SELECTOR, value="h5").text
            if heading.find("Meeting") != -1:
                meetingType = "Meeting"
            elif heading.find("Conference Call") != -1:
                meetingType = "Conference Call"
            elif heading.find("unscheduled") != -1:
                meetingType = "unscheduled"
            else:
                print("Is no Meeting or Conference Call! Then What?")

            date = heading.split(meetingType)[0].strip()
            if date.find("/") != -1:
                startmonth = date.split("/")[0]
                endmonth = date.split("/")[1].split(" ")[0]
                start = date.split(" ")[1].split("-")[0]
                end = date.split(" ")[1].split("-")[1]
            elif date.find("-") != -1:
                if len(date.split("-")[1]) > 4:
                    startmonth = date.split("-")[0].strip().split(" ")[0]
                    endmonth = date.split("-")[1].strip().split(" ")[0]
                    start = date.split("-")[0].strip().split(" ")[1]
                    end = date.split("-")[1].strip().split(" ")[1]
                else:
                    start = date.split(" ")[1].strip().split("-")[0]
                    end = date.split(" ")[1].strip().split("-")[1]
                    startmonth = endmonth = date.split("-")[0].strip().split(" ")[0]
            elif date.find("and") != -1:
                startmonth = endmonth = date.split(" ")[0]
                start = date.split(" ")[1].split(",")[0]
                end = date.split("and")[1].strip()
            else:
                startmonth = endmonth = date.split(" ")[0]
                start = end = date.split(" ")[1]

            if start == end:
                TwodayMeeting = 0
            else:
                TwodayMeeting = 1

            if "Press Conference" in meeting.text:
                PC = 1
            else:
                PC = 0

            row = pd.DataFrame({'Start': [pd.to_datetime(str(year) + startmonth + start, format='%Y%B%d')],
                                'End': [pd.to_datetime(str(year) + endmonth + end, format='%Y%B%d')],
                                'Twoday': [TwodayMeeting],
                                'Meeting': [meetingType],
                                'Press Conference': [PC]})
            for docT in documentTypes:
                row[docT] = None

            for doc in docs:
                for documentType in documentTypes:
                    try:  # Deal with some exceptions
                        if documentType in doc.text:
                            if documentType == "Greenbook" and "Part" in doc.text:
                                row = greenbook_special_cases(doc, row, browser, year)
                                continue
                            elif documentType == "Minutes" and "Intermeeting" in doc.text:
                                continue
                            elif "accessible materials" in doc.text or "ZIP" in doc.text:
                                continue
                            elif documentType == "Statement" and "Longer-Run" in doc.text:
                                continue
                            elif documentType == "Beige Book" and "PDF" in doc.text:
                                a = doc.find_element(by=By.XPATH, value=".//*[contains(text(), 'PDF')]")
                                link = a.get_attribute("href")
                            elif documentType == "Minutes" and "PDF" in doc.text:
                                a = doc.find_element(by=By.XPATH, value=".//*[contains(text(), 'PDF')]")
                                link = a.get_attribute("href")
                            elif documentType == "Beige Book" and "PDF" not in doc.text:
                                a = doc.find_element(by=By.XPATH, value=".//*[contains(text(), '" + documentType + "')]")
                                link = a.get_attribute("href")
                                link.replace("default", "FullReport")
                            else:
                                a = doc.find_element(by=By.XPATH, value=".//*[contains(text(), '" + documentType + "')]")
                                link = a.get_attribute("href")

                            folderpath = os.path.join(dirname, "Documents", documentType, str(year))
                            filepath = os.path.join(folderpath, os.path.basename(link))
                            Path(folderpath).mkdir(parents=True, exist_ok=True)

                            session = get_request_session(browser)
                            r = session.get(link, stream=True)
                            chunk_size = 2000
                            with open(filepath, 'wb') as file:
                                for chunk in r.iter_content(chunk_size):
                                    file.write(chunk)

                            if row[documentType].isnull()[0]:
                                row[documentType] = os.path.join("Documents", documentType, str(year),
                                                                 os.path.basename(link))
                            else:
                                row[documentType] = row[documentType] + ";" + \
                                                    os.path.join("Documents", documentType, str(year),
                                                                 os.path.basename(link))
                    except Exception as e:
                        print(e)
                        continue

            df = pd.concat([df, row], ignore_index=True)

        df.to_csv("FOMCData.csv")
        df.to_excel("FOMCData.xlsx", index=False)

    browser.close()
    return df


def get_fomc_current(dirname, documentTypes):
    # Operating in headless mode?
    opts = Options()
    opts.headless = False

    # Start Browser
    browser = webdriver.Firefox(options=opts, executable_path=os.path.join(dirname, "geckodriver"))

    # Initiate dataframe
    df = pd.DataFrame(columns=(
    'Start', 'End', "Twoday", "Meeting", "Press Conference", "Minutes", "Longer-Run Goals",
    "Statement", "Projection"))

    url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    browser.get(url)

    years = browser.find_elements(by=By.CLASS_NAME, value="panel-default")
    for yeardiv in years:
        year = yeardiv.text.split(" ")[0]
        meetings = yeardiv.find_elements(by=By.CLASS_NAME, value="fomc-meeting")
        for meeting in meetings:
            docs = meeting.find_elements(by=By.CLASS_NAME, value="col-xs-12")
            if "Press Conference" in meeting.text:
                PC = 1
            else:
                PC = 0
            month = meeting.find_element(by=By.CLASS_NAME, value="fomc-meeting__month").text
            if "/" in month:
                startmonth = month.split("/")[0]
                endmonth = month.split("/")[1]
            else:
                startmonth = endmonth = month

            date = meeting.find_element(by=By.CLASS_NAME, value="fomc-meeting__date").text
            if "(" in date:
                meetingType = date.split("(")[1].split(")")[0]
                date = date.split("(")[0]
            else:
                meetingType = "Meeting"
            if "-" in date:
                start = date.split("*")[0].split("-")[0].strip()
                end = date.split("*")[0].split("-")[1].strip()
            else:
                start = end = date.strip()

            if start == end:
                TwodayMeeting = 0
            else:
                TwodayMeeting = 1

            try:
                row = pd.DataFrame({'Start': [pd.to_datetime(str(year) + startmonth + start, format='%Y%B%d')],
                                    'End': [pd.to_datetime(str(year) + endmonth + end, format='%Y%B%d')],
                                    'Twoday': [TwodayMeeting],
                                    'Meeting': [meetingType],
                                    'Press Conference': [PC]})
            except Exception as e:
                print(e)
                try:
                    row = pd.DataFrame({'Start': [pd.to_datetime(str(year) + startmonth + start, format='%Y%b%d')],
                                        'End': [pd.to_datetime(str(year) + endmonth + end, format='%Y%b%d')],
                                        'Twoday': [TwodayMeeting],
                                        'Meeting': [meetingType],
                                        'Press Conference': [PC]})
                except Exception as e:
                    print(e)

            for docT in documentTypes:
                row[docT] = None

            for doc in docs:
                for documentType in documentTypes:
                    if documentType in doc.text:
                        if documentType == "Minutes" and "PDF" in doc.text:
                                    a = doc.find_element(by=By.XPATH, value=".//*[contains(text(), 'PDF')]")
                        elif documentType == "Projection" and "PDF" in doc.text:
                                    a = doc.find_element(by=By.XPATH, value=".//*[contains(text(), 'PDF')]")
                        elif documentType == "Statement" and "PDF" in doc.text:
                                    a = doc.find_element(by=By.XPATH, value=".//*[contains(text(), 'PDF')]")
                        elif documentType == "Longer-Run Goals" and "Longer-Run" in doc.text:
                                    a = doc.find_element(by=By.XPATH, value=".//*[contains(text(), 'Longer-Run')]")
                        else:
                            continue
                        link = a.get_attribute("href")
                    else:
                        continue

                    folderpath = os.path.join(dirname, "Current", documentType, str(year))
                    filepath = os.path.join(folderpath, os.path.basename(link))
                    Path(folderpath).mkdir(parents=True, exist_ok=True)

                    session = get_request_session(browser)
                    r = session.get(link, stream=True)
                    chunk_size = 2000
                    with open(filepath, 'wb') as file:
                        for chunk in r.iter_content(chunk_size):
                            file.write(chunk)

                    if row[documentType].isnull()[0]:
                        row[documentType] = os.path.join("Current", documentType, str(year),
                                                         os.path.basename(link))
                    else:
                        row[documentType] = row[documentType] + ";" + \
                                            os.path.join("Current", documentType, str(year),
                                                         os.path.basename(link))
            df = pd.concat([df, row], ignore_index=True)
        df.to_csv("FOMCDataCurrent.csv")
        df.to_excel("FOMCDataCurrent.xlsx", index=False)
    browser.close()
    return df




# Set basedir
dirname = "/Users/marcburri/Documents/GitHub/ScrapeFOMC"

# Which documents to download
documentTypes = ["Record of Policy Actions", "Minutes", "Beige Book", "Tealbook A", "Tealbook B", "Greenbook",
                 "Bluebook", "Redbook", "Longer-Run Goals", "Memoranda", "Statement", "Supplement", "Transcript",
                 "Individual Projections"]

startyear = 1936
endyear = 2007

df1 = get_fomc_archive(dirname, startyear, endyear, documentTypes)

# Which documents to download
documentTypes = ["Minutes", "Longer-Run Goals", "Statement", "Projection"]

df2 = get_fomc_current(dirname, documentTypes)
