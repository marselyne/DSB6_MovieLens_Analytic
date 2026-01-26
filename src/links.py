#!/usr/bin/env python3
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
        self.data_imdb = self.file_reader('../datasets/data_imdb.csv')
    
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
                    arr_of_links = split_lines[:1000]
            else:
                return "Incorrect path."
        except Exception as e:
            return f"Error: {e}"
        return arr_of_links

    
    # ORIGINAL METHODS
    
    def get_data(self):
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'text/html',
        }
        
        with open('../datasets/data_imdb.csv', 'a', encoding='utf-8') as data:
            for line in self.arr_of_links:
                imdb_id = line[1]
                url = f"https://www.imdb.com/title/tt{imdb_id}/"
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'lxml')

                title_tag = soup.find('span', {'data-testid': 'hero__primary-text'})
                movie_title = title_tag.get_text(strip=True).replace(',', '') if title_tag else "None"

                director_item = soup.find('li', {'data-testid': 'title-pc-principal-credit'})
                director = director_item.find('a').get_text(strip=True) if director_item else None

                data.write(f"{imdb_id},{movie_title},{director},None,None,None\n")

    @staticmethod
    def get_imdb(list_of_movies, list_of_fields):
        imdb_info = []
        try:
            with open('../datasets/data_imdb.csv', 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
                header = lines[0].split(',')
                indices = [header.index('movieId')]
                for field in list_of_fields:
                    if field in header:
                        indices.append(header.index(field))

                for line in lines[1:]:
                    row = line.split(',')
                    if row[0] in list_of_movies:
                        imdb_info.append([row[i] for i in indices])
        except FileNotFoundError:
            return []
        return sorted(imdb_info, key=lambda x: x[0], reverse=True)

    def top_directors(self, n):
        d = defaultdict(int)
        for el in self.data_imdb:
            d[el[2]] += 1
        return dict(sorted(d.items(), key=lambda x: -x[1])[:n])

    def most_expensive(self, n):
        d = {}
        for el in self.data_imdb:
            if el[3] != "None":
                d[el[1]] = int(el[3])
        return dict(sorted(d.items(), key=lambda x: -x[1])[:n])

    def most_profitable(self, n):
        d = {}
        for el in self.data_imdb:
            if el[3] != "None" and el[4] != "None":
                d[el[1]] = int(el[4]) - int(el[3])
        return dict(sorted(d.items(), key=lambda x: -x[1])[:n])

    def longest(self, n):
        d = {}
        for el in self.data_imdb:
            if el[5] != "None":
                d[el[1]] = int(el[5])
        return dict(sorted(d.items(), key=lambda x: -x[1])[:n])

    def top_cost_per_minute(self, n):
        d = {}
        for el in self.data_imdb:
            if el[3] != "None" and el[5] != "None":
                d[el[1]] = round(int(el[3]) / int(el[5]), 2)
        return dict(sorted(d.items(), key=lambda x: -x[1])[:n])

    
    # BONUS METHOD 

    def enrich_movies(self, movie_ids, movies_titles=None):
        """
        BONUS:
        Join links.csv + data_imdb.csv (+ optional movie titles).

        Returns rows:
        [movieId, imdbId, tmdbId, title?, director, budget, gross, runtime]
        Sorted by movieId descending.
        """
        wanted = {int(mid) for mid in movie_ids if str(mid).isdigit()}

        link_map = {}
        for row in self.arr_of_links:
            try:
                mid = int(row[0])
                if mid in wanted:
                    link_map[mid] = (row[1], row[2])
            except:
                continue

        imdb_map = {}
        for row in self.data_imdb:
            imdb_map[row[0]] = row[2:6]

        result = []
        for mid in wanted:
            if mid not in link_map:
                continue

            imdb_id, tmdb_id = link_map[mid]
            director, budget, gross, runtime = imdb_map.get(imdb_id, [None]*4)

            row = [mid, imdb_id, tmdb_id]
            if isinstance(movies_titles, dict):
                row.append(movies_titles.get(mid))
            row.extend([director, budget, gross, runtime])
            result.append(row)

        return sorted(result, key=lambda x: x[0], reverse=True)


def main():
    links = Links('../datasets/links.csv')
    print(links.enrich_movies([1, 2, 3]))


if __name__ == '__main__':
    main()
