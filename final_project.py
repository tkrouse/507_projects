import json, plotly.graph_objects as go, requests, sqlite3, csv

##GLOBAL CONSTANTS##
NEWSAPI_KEY = "757b2d20f65c4443b3680b6cbc1a97d9"
CACHE_FILE_NAME = 'cache.json'
#TODO: build table in SQLlite and then load data. See lecture notes. 

CONN = sqlite3.connect('covid_final_project.db')



#conn = sqlite3.connect('covid_final_project.db')

class NewsArticle:
    def __init__(self,author, title, description, url):
        self.author = author
        self.title = title
        self.description = description
        self.url = url
    def __str__(self):
        return f'{self.title} by {self.author}\n\n{self.description}\n\n{self.url}'

def start_interactive_prompt():
    print("starting interactive prompt...")
    cache = load_cache()
    response = input('Please enter a US state')
    while not state_is_valid(response):
        print('ERROR. Please enter one of the 50 United States of America.')
        response = input('Please enter a US state')
    create_viz(response)
    new_lists = get_news(response, cache)
    for article in new_lists:
        print('===================================')
        print(article)

def state_is_valid(response):
    cursor = CONN.cursor()
    results = cursor.execute('SELECT State FROM Covid GROUP BY(State)').fetchall()
    #returns a list of tuples
    for i in results:
        if response in i:
            return True
    return False

def create_db():
    cur = CONN.cursor()

    drop_covid_sql = 'DROP TABLE IF EXISTS "Covid"'
    drop_diseases_sql = 'DROP TABLE IF EXISTS "Diseases"'
    drop_population_sql = 'DROP TABLE IF EXISTS "Population"'
    
    create_covid_sql = '''
        CREATE TABLE IF NOT EXISTS "Covid" (
            "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Date" TEXT NOT NULL, 
            "State" TEXT NOT NULL,
            "Fips" INTEGER NOT NULL, 
            "Cases" INTEGER NOT NULL,
            "Deaths" INTEGER NOT NULL
        )
    '''

    create_diseases_sql = '''
        CREATE TABLE IF NOT EXISTS 'Diseases'(
            "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
            'Year' INTEGER NOT NULL,
            'Cause of Death' TEXT NOT NULL,
            'State' TEXT NOT NULL,
            'Age Range' TEXT NOT NULL,
            'Benchmark' TEXT NOT NULL,
            'Locality' TEXT NOT NULL,
            'Observed Deaths' INTEGER NOT NULL
        )
    '''

    create_population_sql = '''
        CREATE TABLE IF NOT EXISTS 'Population'(
            'State Key' INTEGER PRIMARY KEY,
            'State' TEXT NOT NULL,
            'Population' INTEGER NOT NULL
        )
    '''
    cur.execute(drop_covid_sql)
    cur.execute(drop_diseases_sql)
    cur.execute(drop_population_sql)
    cur.execute(create_covid_sql)
    cur.execute(create_diseases_sql)
    cur.execute(create_population_sql)
    CONN.commit()

def fill_db():
    cur = CONN.cursor()

    file_contents = open('us_states_covid.csv', 'r')
    file_reader = csv.reader(file_contents)
    next(file_reader) # skip header row

    for row in file_reader:
        cur.execute('INSERT INTO Covid VALUES (null, ?, ?, ?, ?, ?)', row)


    file_contents = open('nchs_chronic_disease_deaths2015.csv', 'r')
    file_reader = csv.reader(file_contents)
    next(file_reader) # skip header row

    for row in file_reader:
        cur.execute('INSERT INTO Diseases VALUES (null, ?, ?, ?, ?, ?, ?, ?)', row)

    file_contents = open('population_by_state.csv', 'r')
    file_reader = csv.reader(file_contents)
    next(file_reader) # skip header row

    for row in file_reader:
        cur.execute('INSERT INTO Population VALUES (?, ?, ?)', row)
    
    CONN.commit()

def get_covid_deaths_state(response):
    cursor=CONN.cursor()
    results=cursor.execute('''SELECT State, max(Deaths) 
    FROM (SELECT * FROM Covid WHERE State = ?) GROUP BY State''', [response]).fetchone()
    return results[1]

def get_covid_confirmed_state(response):
    cursor=CONN.cursor()
    results=cursor.execute('''SELECT State, max(Cases) FROM Covid 
        WHERE State = ?
        GROUP BY State''', [response]).fetchone()
    return results[1]

def get_cancer_disease_state(response):
    cursor = CONN.cursor()
    results = cursor.execute('''SELECT "Cause of Death", max("Observed Deaths")
    FROM Diseases
    WHERE State = ? AND Year = "2015" AND "Cause of Death" = "Cancer"''', [response]).fetchone()
    return results[1]

def get_heart_disease_state(response):
    cursor = CONN.cursor()
    results = cursor.execute('''SELECT "Cause of Death", max("Observed Deaths")
    FROM Diseases
    WHERE state = ? AND Year = "2015" AND "Cause of Death" = "Heart Disease"''', [response]).fetchone()
    return results[1]

def create_viz(response):
    x =['Covid19 Deaths 2020', 'Cancer Deaths 2015']
    y =[get_covid_deaths_state(response), get_cancer_disease_state(response)]
    print("x=",x)
    print("y=",y)
    fig = go.Figure([go.Bar(x=x, y=y)])
    fig.show()

def load_cache(): # called only once, when we run the program
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache): # called whenever the cache is changed
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, params, key, cache):
    if (key in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[key]     # we already have it, so return it
    else:
        print("Fetching")
        response = requests.get(url, params) # gotta go get it
        cache[key] = response.json() # add the TEXT of the web page to the cache
        save_cache(cache)          # write the cache to disk
        return cache[key]          # return the text, which is now in the cache

def get_news(response, cache):
    url = 'https://newsapi.org/v2/everything'
    params= {'lanugages': "en", 'q': '(Coronavirus OR COVID OR COVID-19) AND ' + response,'apiKey' : NEWSAPI_KEY, }
    response = make_url_request_using_cache(url, params, response, cache)
    return [NewsArticle(a['author'], a['title'], a['description'], a['url']) for a in response['articles'][:5]]


if __name__ == '__main__':
    create_db()
    fill_db()
    print("final project starting....")
    start_interactive_prompt()

    CONN.close()
