import os
import pytest
from unittest.mock import patch

from links import Links  # если класс Links лежит в links.py


class Tests:
    """Тесты для класса Links"""

    @pytest.fixture
    def sample_movies_data(self):
        return [
            ["movieId", "title", "genres"],
            ["1", "Toy Story (1995)", "Adventure|Animation|Children|Comedy|Fantasy"],
            ["2", "Jumanji (1995)", "Adventure|Children|Fantasy"],
            ["3", "Grumpier Old Men (1995)", "Comedy|Romance"],
            ["4", "Waiting to Exhale (1995)", "Comedy|Drama|Romance"],
            ["5", "Father of the Bride Part II (1995)", "Comedy"],
            ["6", "Heat (1995)", "Action|Crime|Thriller"],
            ["7", "Inception (2010)", "Action|Sci-Fi"],
            ["8", "Old Movie (1985)", "Drama"],
            ["9", "No Year Title", "Drama"],
        ]

    @pytest.fixture
    def sample_links_data(self):
        return [
            ["movieId", "imdbId", "tmdbId"],
            ["1", "0114709", "862"],
            ["2", "0113497", "8844"],
            ["3", "0113228", "15602"],
            ["4", "0114885", ""],
            ["5", "", "11862"],
            ["6", "0113277", "949"],
            ["7", "1375666", "27205"],
        ]

    @pytest.fixture
    def links_instance(self, tmp_path, sample_movies_data, sample_links_data):
        movies_path = tmp_path / "movies.csv"
        links_path = tmp_path / "links.csv"

        with open(movies_path, "w", encoding="utf-8") as f:
            for row in sample_movies_data:
                f.write(",".join(row) + "\n")

        with open(links_path, "w", encoding="utf-8") as f:
            for row in sample_links_data:
                f.write(",".join(row) + "\n")

        return Links(str(links_path), cache_file=str(tmp_path / "cache.json"), limit=100)

    @pytest.fixture
    def links_with_imdb_data(self, links_instance):
        links_instance.imdb_data = {
            "0114709": {
                "Director": "John Lasseter",
                "Budget": "$30 million",
                "Cumulative Worldwide Gross": "$373 million",
                "Runtime": "81 min",
            },
            "0113497": {
                "Director": "Joe Johnston",
                "Budget": "$65,000,000",
                "Cumulative Worldwide Gross": "$262,797,249",
                "Runtime": "104 min",
            },
            "0113228": {
                "Director": "Howard Deutch",
                "Budget": "$25,000,000",
                "Cumulative Worldwide Gross": "$71,518,000",
                "Runtime": "101 min",
            },
        }
        return links_instance

    def test_init_limit(self, tmp_path, sample_movies_data, sample_links_data):
        movies_path = tmp_path / "movies.csv"
        links_path = tmp_path / "links.csv"

        with open(movies_path, "w", encoding="utf-8") as f:
            for row in sample_movies_data:
                f.write(",".join(row) + "\n")

        with open(links_path, "w", encoding="utf-8") as f:
            for row in sample_links_data:
                f.write(",".join(row) + "\n")

        links = Links(str(links_path), limit=3)
        assert len(links.links) <= 3
        assert len(links.movie_titles) <= 3

    def test_get_movie_links_and_ids(self, links_instance):
        links = links_instance
        assert links.get_imdb_id(1) == "0114709"
        assert links.get_tmdb_id(1) == "862"
        assert links.get_imdb_id(999) is None

    def test_get_movies_without_links(self, links_instance):
        result = links_instance.get_movies_without_links()
        assert any("Old Movie" in t for t in result)
        assert any("No Year Title" in t for t in result)

    def test_get_top_linked_movies_sorted(self, links_instance):
        top = links_instance.get_top_linked_movies(5)
        counts = [c for _, c in top]
        assert counts == sorted(counts, reverse=True)

    def test_analyze_link_coverage(self, links_instance):
        result = links_instance.analyze_link_coverage()
        assert result["total_movies"] == len(links_instance.movie_titles)
        assert result["movies_with_links"] == len(links_instance.links)

    def test_get_movies_with_missing_ids(self, links_instance):
        missing_imdb = links_instance.get_movies_with_missing_ids("imdb")
        missing_tmdb = links_instance.get_movies_with_missing_ids("tmdb")

        assert any("Father of the Bride Part II" in t for t in missing_imdb)
        assert any("Waiting to Exhale" in t for t in missing_tmdb)

    def test_year_distribution(self, links_instance):
        dist = links_instance.dist_by_year()
        year, count = links_instance.get_year_with_most_links()
        assert count == max(dist.values())

    def test_title_pattern(self, links_instance):
        result = links_instance.get_movies_by_title_pattern("story")
        assert any("Toy Story" in t for t in result)

    def test_get_imdb_table(self, links_with_imdb_data):
        rows = links_with_imdb_data.get_imdb([1, 2, 3], ["Director", "Runtime"])
        titles = [r[0] for r in rows]
        assert titles == sorted(titles)

    def test_parse_money_and_runtime(self, links_with_imdb_data):
        links = links_with_imdb_data
        assert links._parse_money("$30 million") == 30_000_000
        assert links._parse_money("N/A") == 0
        assert links._parse_runtime("2h 30min") == 150
        assert links._parse_runtime("N/A") == 0

    def test_collect_all_imdb_data_mock(self, tmp_path, sample_movies_data, sample_links_data):
        movies_path = tmp_path / "movies.csv"
        links_path = tmp_path / "links.csv"
        cache_path = tmp_path / "cache.json"

        with open(movies_path, "w", encoding="utf-8") as f:
            for row in sample_movies_data:
                f.write(",".join(row) + "\n")

        with open(links_path, "w", encoding="utf-8") as f:
            for row in sample_links_data:
                f.write(",".join(row) + "\n")

        links = Links(str(links_path), cache_file=str(cache_path), limit=3)

        with patch.object(Links, "_extract_fields", return_value=["Some Director", "$10"]):
            links.collect_all_imdb_data(["Director", "Budget"])

        assert len(links.imdb_data) == len(links.movie_links)
        assert os.path.exists(cache_path)
