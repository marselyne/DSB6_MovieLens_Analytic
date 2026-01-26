import os, requests
from collections import defaultdict
from bs4 import BeautifulSoup

class Links:
    """
    Analyzing data from links.csv
    """
    def __init__(self, path_to_the_file):
        """
        Put here any fields that you think you will need.
        """
        self.path_to_the_file = path_to_the_file
        self.arr_of_links = self.file_reader(path_to_the_file)
        self.data_imdb = self.file_reader('datasets/data_imdb.csv')
    
    def file_reader(self, path_to_the_file, has_header=True):
        """
        Reads the content of the file and returns the array of lines.
        """ 
        try:
            if os.path.exists(path_to_the_file):
                with open(path_to_the_file, "r", encoding='utf-8') as data:
                    header = data.readline().strip().split(",")
                    data.seek(0)

                    if header[0].isdigit():
                        has_header = False

                    if has_header:
                        next(data)

                    lines = data.readlines()
                    split_lines = []
                    for line in lines:
                        if "\"" in line:
                            parts = line.split("\"")
                            res = [parts[0].rstrip(','), parts[1], parts[2].lstrip(',')]
                        else:
                            res = line.strip().split(',')
                        split_lines.append(res)
                    arr_of_movies = split_lines[:1000]
            else:
                return("Incorrect path.")
        except Exception as e:
            return(f"Error: {e}")
        return arr_of_movies

    def get_data(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'text/html',
        }
        
        with open('datasets/data_imdb.csv', 'a', encoding='utf-8') as data:
            num = 1
            
            for line in self.arr_of_links:
                imdb_id = line[1]
                url = f"https://www.imdb.com/title/tt{imdb_id}/"
                
                try:
                    response = requests.get(url, headers=headers)
                    text = response.text
                except:
                    print("Error loading page")
                    break
                
                soup = BeautifulSoup(text, 'lxml')
                print(num, response.status_code)
                num += 1
                
                title_tag = soup.find('span', {'data-testid': 'hero__primary-text'})
                movie_title = title_tag.get_text(strip=True).replace(',', '') if title_tag else "None"
                
                director_item = soup.find('li', {'data-testid': 'title-pc-principal-credit'})
                if director_item:
                    director_name = director_item.find('a').get_text(strip=True).replace(',', '')
                else:
                    director_name = None
                
                budget_li = soup.find('li', {'data-testid': 'title-boxoffice-budget'})
                if budget_li:
                    budget_value = budget_li.find('span', class_='ipc-metadata-list-item__list-content-item').get_text(strip=True)
                    clean_budget = ''.join(filter(str.isdigit, budget_value.split('(')[0]))
                    if not clean_budget:
                        clean_budget = None
                else:
                    clean_budget = None
                
                gross_li = soup.find('li', {'data-testid': 'title-boxoffice-cumulativeworldwidegross'})
                if gross_li:
                    gross_value = gross_li.find('span', class_='ipc-metadata-list-item__list-content-item').get_text(strip=True)
                    clean_gross = ''.join(filter(str.isdigit, gross_value))
                    if not clean_gross:
                        clean_gross = None
                else:
                    clean_gross = None
                
                runtime_li = soup.find('li', {'data-testid': 'title-techspec_runtime'})
                if runtime_li:
                    subtext_span = runtime_li.find('span', class_='ipc-metadata-list-item__list-content-item--subText')
                    runtime_text = subtext_span.get_text(strip=True) if subtext_span else runtime_li.get_text(strip=True)
                    minutes = ''.join(filter(str.isdigit, runtime_text))
                    if not minutes:
                        minutes = None
                else:
                    minutes = None
                
                data.write(f"{imdb_id},{movie_title},{director_name},{clean_budget},{clean_gross},{minutes}\n")      

    @staticmethod
    def get_imdb(list_of_movies, list_of_fields):
        """
        The method returns a list of lists [movieId, field1, field2, field3, ...] for the list of movies given as the argument (movieId).
        For example, [movieId, Director, Budget, Cumulative Worldwide Gross, Runtime].
        The values should be parsed from the IMDB webpages of the movies.
        Sort it by movieId descendingly.
        """
        imdb_info = []
    
        try:
            with open('datasets/data_imdb.csv', 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
                header = lines[0].split(',')
                
                indices = [header.index('movieId')]
                for field in list_of_fields:
                    if field in header and field != 'movieId':
                        indices.append(header.index(field))
                
                for line in lines[1:]:
                    row = line.split(',')
                    if row[0] in list_of_movies:
                        item = [row[i].strip() for i in indices]
                        imdb_info.append(item)
                        
        except FileNotFoundError:
            return("The input file is not found!")

        imdb_info.sort(key=lambda x: x[0], reverse=True) 
        return imdb_info
        
    def top_directors(self, n):
        """
        The method returns a dict with top-n directors where the keys are directors and 
        the values are numbers of movies created by them. Sort it by numbers descendingly.
        """
        dict_of_directors = defaultdict(int)
        for el in self.data_imdb:
            director = el[2]
            dict_of_directors[director] += 1
        directors = dict(sorted(dict_of_directors.items(), key=lambda x: -x[1])[:n])
        
        return directors
        
    def most_expensive(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are their budgets. Sort it by budgets descendingly.
        """
        
        budgets_dict = defaultdict(int)
        for el in self.data_imdb:
            title, budget = el[1], el[3]
            if budget != "None":
                budgets_dict[title] = int(budget)
        
        budgets = dict(sorted(budgets_dict.items(), key=lambda x: -x[1])[:n])
    
        return budgets
        
    def most_profitable(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are the difference between cumulative worldwide gross and budget.
        Sort it by the difference descendingly.
        """
        
        profits_dict = defaultdict(int)
        for el in self.data_imdb:
            title, budget, gross = el[1], el[3], el[4]
            if budget != "None" and gross != "None":
                profits_dict[title] = int(gross) - int(budget)
        
        profits = dict(sorted(profits_dict.items(), key=lambda x: -x[1])[:n])
        
        return profits
        
    def longest(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are their runtime. If there are more than one version – choose any.
        Sort it by runtime descendingly.
        """
        runtimes_dict = defaultdict(int)
        for el in self.data_imdb:
            title, runtime = el[1], el[5]
            if runtime != "None":
                runtimes_dict[title] = int(runtime)
        
        runtimes = dict(sorted(runtimes_dict.items(), key=lambda x: -x[1])[:n])
    
        return runtimes
        
    def top_cost_per_minute(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are the budgets divided by their runtime. The budgets can be in different currencies – do not pay attention to it. 
        The values should be rounded to 2 decimals. Sort it by the division descendingly.
        """
        costs_dict = defaultdict(int)
        for el in self.data_imdb:
            title, budget, runtime = el[1], el[3], el[5]
            if budget != "None" and runtime != "None":
                costs_dict[title] = round(int(budget) * 1.0 / int(runtime), 2)
        
        costs = dict(sorted(costs_dict.items(), key=lambda x: -x[1])[:n])
        
        return costs

  
    # BONUS METHOD 
    
    def enrich_movies(self, movie_ids, movies_titles=None):
        """
        Bonus:
        Returns list of lists:
        [movieId, imdbId, tmdbId, title(optional), director, budget, gross, runtime]

        - movie_ids: iterable of movieId (int/str)
        - movies_titles: optional dict {movieId: title}
        Sort: by movieId descending.
        """
       
        wanted = set()
        for mid in movie_ids:
            try:
                wanted.add(int(mid))
            except (TypeError, ValueError):
                continue

        link_map = {}
        for row in self.arr_of_links:
            try:
                mid = int(row[0])
                if mid in wanted:
                    imdbId = str(row[1]).strip()
                    tmdbId = str(row[2]).strip() if len(row) > 2 else ""
                    link_map[mid] = (imdbId, tmdbId)
            except (ValueError, IndexError, TypeError):
                continue

    
        imdb_map = {}
        for row in self.data_imdb:
           
            try:
                imdb_id = str(row[0]).strip()
            except (IndexError, TypeError):
                continue

            director = row[2].strip() if len(row) > 2 and isinstance(row[2], str) else row[2] if len(row) > 2 else None
            budget = row[3].strip() if len(row) > 3 and isinstance(row[3], str) else row[3] if len(row) > 3 else None
            gross = row[4].strip() if len(row) > 4 and isinstance(row[4], str) else row[4] if len(row) > 4 else None
            runtime = row[5].strip() if len(row) > 5 and isinstance(row[5], str) else row[5] if len(row) > 5 else None

            imdb_map[imdb_id] = [director, budget, gross, runtime]

        enriched = []
        for mid in wanted:
            if mid not in link_map:
                continue

            imdb_id, tmdb_id = link_map[mid]
            director, budget, gross, runtime = imdb_map.get(imdb_id, [None, None, None, None])

            row = [mid, imdb_id, tmdb_id]
            if isinstance(movies_titles, dict):
                row.append(movies_titles.get(mid))
            row.extend([director, budget, gross, runtime])
            enriched.append(row)

        enriched.sort(key=lambda x: x[0], reverse=True)
        return enriched


def main():
    links = Links('datasets/links.csv')
    print(links.top_cost_per_minute(10))
    print(links.enrich_movies([1, 10, 100]))
    
if __name__ == '__main__':
    main()
