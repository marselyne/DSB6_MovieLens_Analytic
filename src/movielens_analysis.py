import re
from collections import Counter, OrderedDict



class Tags:
    """
    Класс для анализа данных из файла tags.csv из набора данных MovieLens.
    Автоматически загружает данные из CSV-файла при инициализации.

    Attributes:
        path (str): Путь к файлу tags.csv
        num_rows (int): Максимальное количество строк для загрузки (по умолчанию 1000)
        tags_data (list): Список словарей с информацией о тегах после загрузки
    """
    def __init__(self, path_to_the_file: str, num_rows: int = 1000) -> None:
        """
        Инициализирует объект Tags и загружает данные из указанного файла.

        Args:
            path_to_the_file (str): Путь к CSV-файлу tags.csv
            num_rows (int): Максимальное количество строк для загрузки.
                           По умолчанию 1000. Используется для ограничения объема
                           данных при тестировании или отладке.

        Raises:
            Exception: Если возникает ошибка при чтении файла

        Note:
            После инициализации поле tags_data будет содержать список словарей с ключами:
            - user_id: int - идентификатор пользователя, добавившего тег
            - movie_id: int - идентификатор фильма, к которому добавлен тег
            - tag: str - текст тега (пользовательская метка)
            - timestamp: int - временная метка в секундах с 1 января 1970 года
        """
        self.path = path_to_the_file
        self.num_rows = num_rows
        self.tags_data = []
        self._load_tags()

    def most_words(self, n: int) -> OrderedDict:
        """
        Возвращает топ-N тегов с наибольшим количеством слов.

        Args:
            n (int): Количество тегов для возврата (размер топа)

        Returns:
            OrderedDict: Упорядоченный словарь, где:
                - Ключи: текст тега (str)
                - Значения: количество слов в теге (int)
        """
        tag_word_counter = Counter()
        seen_tags = set()
        for tag_info in self.tags_data:
            tag = tag_info['tag']
            if tag in seen_tags or tag == "":
                continue
            seen_tags.add(tag_info['tag'])
            tag_word_counter[tag] = len(tag.split())

        big_tags = OrderedDict(
            sorted(tag_word_counter.items(), key=lambda x: x[1], reverse=True)[:n]
        )

        return big_tags

    def longest(self, n: int) -> list:
        """
        Возвращает топ-N самых длинных тегов по количеству символов.

        Args:
            n (int): Количество тегов для возврата (размер топа)

        Returns:
            list: Список строк, содержащий n самых длинных уникальных тегов
        """
        tag_lengths = list()
        seen_tags = set()
        for tag_info in self.tags_data:
            tag = tag_info['tag']
            if tag in seen_tags or tag == "":
                continue
            seen_tags.add(tag_info['tag'])
            tag_lengths.append((tag, len(tag)))

        tag_lengths.sort(key=lambda x: x[1], reverse=True)

        big_tags = [tag for tag, _ in tag_lengths[:n]]

        return big_tags

    def most_words_and_longest(self, n: int) -> list:
        """
        Возвращает пересечение топ-N тегов по количеству слов и топ-N самых длинных тегов.

        Args:
            n (int): Размер топа для обеих категорий (используется одинаковый n)

        Returns:
            list: Отсортированный по алфавиту список тегов, которые входят в оба топа
        """
        top_words_tags = set(self.most_words(n).keys())
        top_longest_tags = set(self.longest(n))

        set_interseection = top_words_tags.intersection(top_longest_tags)

        big_tags = sorted(list(set_interseection))

        return big_tags

    def most_popular(self, n: int) -> OrderedDict:
        """
        Возвращает самые популярные теги по частоте использования.

        Args:
            n (int): Количество тегов для возврата (размер топа)

        Returns:
            OrderedDict: Упорядоченный словарь, где:
                - Ключи: текст тега (str)
                - Значения: количество использований тега (int)
        """
        tag_counter = Counter()
        for tag_info in self.tags_data:
            tag = tag_info['tag']
            if tag:
                tag_counter[tag] += 1

        popular_tags = OrderedDict(
            sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)[:n]
        )
        return popular_tags

    def tags_with(self, word: str) -> list:
        """
        Возвращает все уникальные теги, содержащие указанное слово.

        Args:
            word (str): Слово для поиска в тегах

        Returns:
            list: Отсортированный по алфавиту список уникальных тегов,
                  содержащих указанное слово
        """
        word_lower = word.lower()
        matching_tags = set()
        for tag_info in self.tags_data:
            tag = tag_info['tag']
            if tag in matching_tags:
                continue
            if tag and word_lower in tag.lower():
                matching_tags.add(tag)

        tags_with_word = sorted(list(matching_tags))

        return tags_with_word

    def _load_tags(self) -> None:
        """
        Приватный метод для загрузки и парсинга данных из CSV-файла тегов.

        Raises:
            Exception: Если возникает ошибка при чтении файла
                      (обрабатывается в методе _file_reader)
        """
        reader = self._file_reader()
        num = 0
        for line in reader:
            if line == "":
                continue

            parts = self._parse_csv_line(line)
            if len(parts) < 4 or parts[0] == 'userId':
                continue

            try:
                user_id = int(parts[0])
                movie_id = int(parts[1])
                tag = parts[2]
                timestamp = int(parts[3])

                tag_info = {
                    'user_id': user_id,
                    'movie_id': movie_id,
                    'tag': tag,
                    'timestamp': timestamp
                }
                self.tags_data.append(tag_info)

            except ValueError:
                continue

            num += 1
            if num >= self.num_rows:
                break

    def _file_reader(self):
        """
        Приватный генератор для построчного чтения CSV-файла.

        Yields:
            str: Очередная строка из файла (без завершающего символа перевода строки)

        Raises:
            Exception: Если файл не найден или произошла ошибка ввода-вывода
        """
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                for line in file:
                    yield line.strip()
        except Exception as e:
            raise Exception(f"Error in reading file: {e}")

    def _parse_csv_line(self, line) -> list:
        """
        Приватный метод для парсинга строки в формате CSV с учетом кавычек.

        Args:
            line (str): Строка CSV для парсинга

        Returns:
            list: Список значений из строки
        """
        result = ""
        in_quote = False
        for symbol in line:
            if symbol == '"':
                in_quote = not in_quote
            elif symbol == ',' and not in_quote:
                result += '\t'
            else:
                result += symbol
        return result.split(sep='\t')


if __name__ == "__main__":
    tags = Tags(path_to_the_file='tags.csv')