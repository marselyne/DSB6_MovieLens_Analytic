from collections import OrderedDict

import pytest

from movielens_analysis import Tags

class Tests:
    @pytest.fixture
    def sample_tags_data(self):
        """
        Фикстура с тестовыми данными для таблицы тегов.
        Возвращает список списков, имитирующий содержимое CSV-файла tags.csv.
        Первая строка содержит заголовки колонок, последующие - данные.

        Returns:
            list: Список строк с данными о фильмах в формате CSV
        """
        return [
            ["userId", "movieId", "tag", "timestamp"],
            ["2", "60756", "funny", "1445714994"],
            ["2", "60756", "Highly quotable", "1445714996"],
            ["2", "60756", "will ferrell", "1445714992"],
            ["2", "89774", "Boxing story", "1445715207"],
            ["2", "89774", "MMA", "1445715200"],
            ["2", "89774", "Tom Hardy", "1445715205"],
            ["2", "106782", "drugs", "1445715054"],
            ["2", "106782", "Leonardo DiCaprio", "1445715051"],
            ["2", "106782", "Martin Scorsese", "1445715056"],
            ["7", "48516", "way too long", "1169687325"],
            ["18", "431", "Al Pacino", "1462138765"],
            ["18", "431", "gangster", "1462138749"],
            ["18", "431", "mafia", "1462138755"],
            ["18", "1221", "Al Pacino", "1461699306"],
            ["18", "1221", "Mafia", "1461699303"],
            ["18", "5995", "holocaust", "1455735472"],
            ["18", "5995", "true story", "1455735479"],
            ["18", "44665", "twist ending", "1456948283"],
            ["18", "52604", "Anthony Hopkins", "1457650696"],
            ["18", "88094", "indie record label", "1457444592"],
            ["106", "4896", "Everything you want is here", "1467566944"]
        ]

    @pytest.fixture
    def tags_instance(self, tmp_path, sample_tags_data):
        """
        Фикстура, создающая тестовый файл 'tags.csv', на основе которого создается экземпляр класса Tags.
        Args:
            tmp_path: Временная директория, предоставляемая pytest
            sample_tags_data: Тестовые данные из фикстуры sample_tags_data

        Returns:
            Tags: Экземпляр класса Tags, инициализированный с тестовыми данными
        """
        tags_path = tmp_path / "tags.csv"
        with open(tags_path, 'w', encoding='utf-8') as f:
            for row in sample_tags_data:
                f.write(','.join(row) + '\n')

        return Tags(str(tags_path))

    def test_tags_init(self, tags_instance):
        """
        Тест инициализации класса Tags.

        Args:
            tags_instance: Экземпляр класса Tags с тестовыми данными
        """
        assert len(tags_instance.tags_data) > 0

        for tag_info in tags_instance.tags_data:
            row = tag_info
            assert isinstance(row, dict)
            assert len(row.keys()) == 4
            assert ('user_id' in row and 'movie_id' in row and 'tag' in row and 'timestamp' in row)
            assert isinstance(row['user_id'], int)
            assert isinstance(row['movie_id'], int)
            assert isinstance(row['tag'], str)
            assert isinstance(row['timestamp'], int)

    def test_tags_most_words(self, tags_instance):
        """
        Тест метода most_words класса Tags.

        Args:
            tags_instance: Экземпляр класса Tags с тестовыми данными
        """
        n = 4
        result = tags_instance.most_words(n)
        assert isinstance(result, OrderedDict)
        assert len(result.keys()) == n

        keys = list(result.keys())
        values = list(result.values())
        assert all(isinstance(key, str) for key in keys), "Not all keys are strings"
        assert all(isinstance(value, int) for value in values), "Not all values are integer"

        for i in range(len(values) - 1):
            assert values[i] >= values[i + 1], "Incorrect sorting, not in descending order"

        assert "Everything you want is here" in result
        assert "indie record label" in result
        assert "MMA" not in result

    def test_tags_longest(self, tags_instance):
        """
        Тест метода longest класса Tags.

        Args:
            tags_instance: Экземпляр класса Tags с тестовыми данными
        """
        n = 5
        result = tags_instance.longest(n)
        assert isinstance(result, list)
        assert len(result) == n
        assert all(isinstance(row, str) for row in result), "Elements are not all string"

        for i in range(len(result) - 1):
            assert len(result[i]) >= len(result[i + 1]), "Incorrect sorting, not in descending order"

        assert len(result) == len(set(result)), "There are duplicates in the list"

        assert "Everything you want is here" in result
        assert "MMA" not in result

    def test_tags_most_words_and_longest(self, tags_instance):
        """
        Тест метода most_words_and_longest класса Tags.

        Args:
            tags_instance: Экземпляр класса Tags с тестовыми данными
        """
        n = 5
        result = tags_instance.most_words_and_longest(n)
        assert isinstance(result, list)
        assert len(result) <= n
        assert all(isinstance(row, str) for row in result), "Elements are not all string"

        for i in range(len(result) - 1):
            assert result[i] <= result[i + 1], "Incorrect sorting, not in alphabetical order"

        assert len(result) == len(set(result)), "There are duplicates in the list"

        assert "Everything you want is here" in result
        assert "MMA" not in result

    def test_tags_most_popular(self, tags_instance):
        """
        Тест метода most_popular класса Tags.

        Args:
            tags_instance: Экземпляр класса Tags с тестовыми данными
        """
        # test 1
        n = 1
        result = tags_instance.most_popular(n)
        assert isinstance(result, OrderedDict)
        assert len(result.keys()) == n

        keys = list(result.keys())
        values = list(result.values())
        assert all(isinstance(key, str) for key in keys), "Not all keys are strings"
        assert all(isinstance(value, int) for value in values), "Not all values are integer"

        for i in range(len(values) - 1):
            assert values[i] >= values[i + 1], "Incorrect sorting, not in descending order"

        assert "Al Pacino" in result.keys()
        assert "MMA" not in result.keys()

        # test 2
        n = 1000
        result = tags_instance.most_popular(n)
        assert isinstance(result, OrderedDict)
        assert len(result.keys()) <= n

        keys = list(result.keys())
        values = list(result.values())
        assert all(isinstance(key, str) for key in keys), "Not all keys are strings"
        assert all(isinstance(value, int) for value in values), "Not all values are integer"

        for i in range(len(values) - 1):
            assert values[i] >= values[i + 1], "Incorrect sorting, not in descending order"

        assert "Al Pacino" in result.keys()
        assert "MMA" in result.keys()
        assert "Non existed tag" not in result.keys()

    def test_tags_tags_with(self, tags_instance):
        """
        Тест метода tags_with класса Tags.

        Args:
            tags_instance: Экземпляр класса Tags с тестовыми данными
        """
        word = "mafia"
        result = tags_instance.tags_with(word)
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(row, str) for row in result), "Elements are not all string"

        for i in range(len(result) - 1):
            assert len(result[i]) >= len(result[i + 1]), "Incorrect sorting, not in descending order"

        assert len(result) == len(set(result)), "There are duplicates in the list"
        assert "Mafia" in result
        assert "MMMafia" not in result