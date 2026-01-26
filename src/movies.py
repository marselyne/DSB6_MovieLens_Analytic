import os
from collections import Counter

class Movies:
    """
    Analyzing data from movies.csv
    """
    def __init__(self, path_to_the_file):
        """
        Initialization constructor.
        """ 
        self.path_to_the_file = path_to_the_file
        self.arr_of_movies = self.file_reader(path_to_the_file)
    
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
                            res = line.split(',')
                        split_lines.append(res)
                    arr_of_movies = split_lines[:1000]
            else:
                return("Incorrect path.")
        except Exception as e:
            return(f"Error: {e}")
        return arr_of_movies

    def dist_by_release(self):
        """
        The method returns a dict or an OrderedDict where the keys are years and the values are counts. 
        You need to extract years from the titles. Sort it by counts descendingly.
        """
        list_of_years = [int(el[1].split("(")[-1].strip(")")) for el in self.arr_of_movies]
        release_years = dict(Counter(list_of_years).most_common())
        return release_years
    

    def dist_by_genres(self):
        """
        The method returns a dict where the keys are genres and the values are counts.
        Sort it by counts descendingly.
        """
        list_of_genres = [el.strip() for arr in self.arr_of_movies for el in arr[2].split('|') ]
        genres = dict(Counter(list_of_genres).most_common())
        return genres

        
    def most_genres(self, n):
        """
        The method returns a dict with top-n movies where the keys are movie titles and 
        the values are the number of genres of the movie. Sort it by numbers descendingly.
        """
        lst = [[el[1], len(el[2].split('|'))] for el in self.arr_of_movies]
        sorted_lst = sorted(lst, key=lambda x: -x[1])
        movies = dict(sorted_lst[:n])
        return movies


    # BONUS METHOD 
   
    def genre_cooccurrence(self, top_k=10):
        """
        Bonus:
        Returns dict {("Genre1","Genre2"): count} for most common genre pairs.
        Example: ("Adventure","Children") -> 123
        """
        pair_counts = Counter()

        for row in self.arr_of_movies:
            try:
                genres_str = row[2].strip()
            except (IndexError, TypeError):
                continue

            genres = [g.strip() for g in genres_str.split("|") if g.strip()]
            genres = sorted(set(genres))
            if len(genres) < 2:
                continue

            for i in range(len(genres)):
                for j in range(i + 1, len(genres)):
                    pair_counts[(genres[i], genres[j])] += 1

        return dict(pair_counts.most_common(top_k))


def main():
    movies = Movies('datasets/movies.csv')
    print(movies.most_genres(10))
    print(movies.genre_cooccurrence(10))
    
if __name__ == '__main__':
    main()
