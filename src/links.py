import os
import csv
import json
import re
import time
import random
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup



class Links:
    """
    Класс для работы с внешними ссылками (links.csv, movies.csv)
    и дополнительными данными с IMDb (через веб-скрапинг)
    """

    def __init__(self, path: str, cache_file: str = "imdb_data.json", limit: int = 1000):
        self.limit = limit

        self.links: Dict[int, Dict[str, Optional[str]]] = {}
        self.movie_titles: Dict[int, str] = {}

        self.movie_links: Dict[int, str] = {}
        self.imdb_data: Dict[str, Dict[str, str]] = {}
        self.cache_path = cache_file

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; MovieLensAnalytics/1.0; +https://example.com)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        self.delay = random.uniform(1.5, 3.0)

        self._load_links(path)
        base_dir = os.path.dirname(path) or "."
        movies_path = os.path.join(base_dir, "movies.csv")
        if os.path.exists(movies_path):
            self._load_movie_titles(movies_path)

        self._load_cache()

    def _load_links(self, path: str) -> None:
        """Загружает данные из links.csv в self.links и self.movie_links"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)

                for i, row in enumerate(reader):
                    if i >= self.limit:
                        break
                    if len(row) < 2:
                        continue

                    movie_id_str, imdb_id = row[0], row[1].strip()
                    tmdb_id = row[2].strip() if len(row) > 2 and row[2].strip() else None

                    try:
                        movie_id = int(movie_id_str)
                    except ValueError:
                        continue

                    imdb_id = imdb_id if imdb_id else None

                    self.links[movie_id] = {"imdb": imdb_id, "tmdb": tmdb_id}
                    if imdb_id:
                        self.movie_links[movie_id] = imdb_id

        except FileNotFoundError:
            raise FileNotFoundError(f"File {path} not found.")
        except Exception as e:
            raise IOError(f"Error reading {path}: {e}")

    def _load_movie_titles(self, movies_path: str) -> None:
        """Загружает названия фильмов из movies.csv в self.movie_titles"""
        try:
            with open(movies_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)

                for i, row in enumerate(reader):
                    if i >= self.limit:
                        break
                    if len(row) < 2:
                        continue

                    movie_id_str, title = row[0], row[1].strip()
                    try:
                        movie_id = int(movie_id_str)
                    except ValueError:
                        continue

                    self.movie_titles[movie_id] = title

        except FileNotFoundError:
            raise FileNotFoundError(f"File {movies_path} not found.")
        except Exception as e:
            raise IOError(f"Error reading {movies_path}: {e}")

    def get_movie_links(self, movie_id: int) -> Optional[Dict[str, Optional[str]]]:
        """Возвращает словарь с внешними ID фильма (imdb/tmdb) или None"""
        return self.links.get(movie_id)

    def get_imdb_id(self, movie_id: int) -> Optional[str]:
        """Возвращает IMDb-ID фильма (как строку без префикса tt) или None"""
        links = self.links.get(movie_id)
        return links.get("imdb") if links else None

    def get_tmdb_id(self, movie_id: int) -> Optional[str]:
        """Возвращает TMDb-ID фильма или None"""
        links = self.links.get(movie_id)
        return links.get("tmdb") if links else None

    def get_movies_without_links(self) -> List[str]:
        """Список фильмов, для которых вообще нет записей в links.csv"""
        result: List[str] = []
        for movie_id, title in self.movie_titles.items():
            if movie_id not in self.links:
                result.append(title)
        return sorted(result)

    def get_top_linked_movies(self, n: int = 10) -> List[Tuple[str, int]]:
        """
        Топ-N фильмов по числу внешних ссылок (imdb + tmdb).
        Возвращает список (title, count), отсортированный по count по убыванию, затем по title по возрастанию
        """
        if n <= 0:
            return []

        rows: List[Tuple[str, int]] = []
        for movie_id, link_info in self.links.items():
            count = sum(1 for v in link_info.values() if v)
            title = self.movie_titles.get(movie_id, f"Movie {movie_id}")
            rows.append((title, count))

        rows.sort(key=lambda x: (-x[1], x[0]))
        return rows[:n]

    def analyze_link_coverage(self) -> Dict[str, float]:
        """
        Аналитика покрытия ссылками:
         * total_movies – всего фильмов в movies.csv
         * movies_with_links – сколько из них имеют запись в links.csv
         * coverage_percentage – доля в процентах
         * movies_with_both_ids – есть и imdb, и tmdb
         * movies_with_imdb_only
         * movies_with_tmdb_only
         * both_ids_percentage – среди фильмов со ссылками, доля с обоими ID
        """
        total_movies = len(self.movie_titles)
        movies_with_links = len(self.links)

        movies_with_both = 0
        movies_with_imdb_only = 0
        movies_with_tmdb_only = 0

        for link_info in self.links.values():
            has_imdb = link_info.get("imdb") is not None
            has_tmdb = link_info.get("tmdb") is not None

            if has_imdb and has_tmdb:
                movies_with_both += 1
            elif has_imdb:
                movies_with_imdb_only += 1
            elif has_tmdb:
                movies_with_tmdb_only += 1

        return {
            "total_movies": total_movies,
            "movies_with_links": movies_with_links,
            "coverage_percentage": round(movies_with_links / total_movies * 100, 2)
            if total_movies
            else 0.0,
            "movies_with_both_ids": movies_with_both,
            "movies_with_imdb_only": movies_with_imdb_only,
            "movies_with_tmdb_only": movies_with_tmdb_only,
            "both_ids_percentage": round(movies_with_both / movies_with_links * 100, 2)
            if movies_with_links
            else 0.0,
        }

    def get_movies_with_missing_ids(self, id_type: str = "both") -> List[str]:
        """
        Фильмы с отсутствующими ID.
        'imdb' - отсутствует только IMDb-ID | 'tmdb' - отсутствует только TMDb-ID | 'both' - отсутствуют оба ID
        """
        result: List[str] = []

        for movie_id, link_info in self.links.items():
            has_imdb = link_info.get("imdb") is not None
            has_tmdb = link_info.get("tmdb") is not None
            title = self.movie_titles.get(movie_id, f"Movie {movie_id}")

            if id_type == "imdb" and not has_imdb:
                result.append(title)
            elif id_type == "tmdb" and not has_tmdb:
                result.append(title)
            elif id_type == "both" and (not has_imdb or not has_tmdb):
                result.append(title)

        return sorted(result)

    def get_imdb_id_distribution(self) -> Dict[str, int]:
        """Распределение IMDb-ID по длине строки (ключ – длина как строка)"""
        lengths: Counter = Counter()
        for link_info in self.links.values():
            imdb_id = link_info.get("imdb")
            if imdb_id:
                lengths[str(len(imdb_id))] += 1
        return dict(sorted(lengths.items()))

    def find_imdb_patterns(self) -> Dict[str, int]:
        """
        Наивная статистика по префиксам IMDb-ID.
        Возвращает словарь вида 'starts_with_01' -> count (топ-10 по убыванию)
        """
        counter: Counter = Counter()
        for link_info in self.links.values():
            imdb_id = link_info.get("imdb")
            if imdb_id and len(imdb_id) >= 2:
                prefix = imdb_id[:2]
                counter[f"starts_with_{prefix}"] += 1
        return dict(counter.most_common(10))

    def _extract_year_from_title(self, title: str) -> Optional[int]:
        """Извлекает год из названия вида 'Title (1995)'"""
        if "(" in title and ")" in title:
            year_part = title.split("(")[-1].split(")")[0]
            if year_part.isdigit() and len(year_part) == 4:
                return int(year_part)
        return None

    def dist_by_year(self) -> Dict[int, int]:
        """Количество фильмов со ссылками по годам"""
        year_count: Counter = Counter()
        for movie_id in self.links:
            title = self.movie_titles.get(movie_id, "")
            year = self._extract_year_from_title(title)
            if year:
                year_count[year] += 1
        return dict(sorted(year_count.items()))

    def get_movies_by_year_range(self, start_year: int, end_year: int) -> Dict[int, List[str]]:
        """Фильмы со ссылками в заданном диапазоне годов (включительно)"""
        result: Dict[int, List[str]] = defaultdict(list)
        for movie_id in self.links:
            title = self.movie_titles.get(movie_id, "")
            year = self._extract_year_from_title(title)
            if year and start_year <= year <= end_year:
                result[year].append(title)
        for year in result:
            result[year].sort()
        return dict(sorted(result.items()))

    def get_year_with_most_links(self) -> Tuple[int, int]:
        """Год, в котором больше всего фильмов со ссылками (год, количество)"""
        distribution = self.dist_by_year()
        if not distribution:
            return 0, 0
        year, count = max(distribution.items(), key=lambda x: x[1])
        return year, count

    def get_movies_by_title_pattern(self, pattern: str) -> List[str]:
        """Фильмы, названия которых содержат указанный паттерн (регистронезависимо)"""
        regex = re.compile(pattern, re.IGNORECASE)
        result: List[str] = []
        for movie_id in self.links:
            title = self.movie_titles.get(movie_id, "")
            if regex.search(title):
                result.append(title)
        return sorted(result)

    def compare_link_presence_by_decade(self) -> Dict[str, Dict[str, float]]:
        """
        Сравнение покрытия ссылками по десятилетиям.
        Возвращает словарь:
        decade -> {total_movies, with_links, without_links, coverage_percentage}
        """
        stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "with_links": 0, "without_links": 0}
        )

        for movie_id, title in self.movie_titles.items():
            year = self._extract_year_from_title(title)
            if not year:
                continue
            decade = (year // 10) * 10
            key = f"{decade}s"
            stats[key]["total"] += 1
            if movie_id in self.links:
                stats[key]["with_links"] += 1
            else:
                stats[key]["without_links"] += 1

        result: Dict[str, Dict[str, float]] = {}
        for decade, values in sorted(stats.items()):
            total = values["total"]
            if total:
                result[decade] = {
                    "total_movies": total,
                    "with_links": values["with_links"],
                    "without_links": values["without_links"],
                    "coverage_percentage": round(values["with_links"] / total * 100, 2),
                }
        return result

    def get_movies_with_special_characters(self) -> Dict[str, List[str]]:
        """
        Фильмы, в названиях которых содержатся некоторые "особые" символы
        (двоеточие, амперсанд, кавычки, апостроф и т.п.).
        Возвращает словарь тип_символа -> первые 10 фильмов (отсортированы)
        """
        special_patterns = {
            "colon": r":",
            "ampersand": r"&",
            "parentheses": r"\(.*\)",
            "roman_numerals": r"\b[IVXLCDM]+\b",
            "quotes": r"\"",
            "apostrophe": r"'",
        }
        result: Dict[str, List[str]] = {}
        for name, pattern in special_patterns.items():
            regex = re.compile(pattern)
            matches: List[str] = []
            for movie_id in self.links:
                title = self.movie_titles.get(movie_id, "")
                if regex.search(title):
                    matches.append(title)
            if matches:
                result[name] = sorted(matches)[:10]
        return result

    def get_movies_with_both_ids(self) -> List[str]:
        """Фильмы, у которых есть и imdb, и tmdb-id"""
        result: List[str] = []
        for movie_id, link_info in self.links.items():
            if link_info.get("imdb") and link_info.get("tmdb"):
                title = self.movie_titles.get(movie_id, f"Movie {movie_id}")
                result.append(title)
        return sorted(result)

    def get_movies_by_imdb_prefix(self, prefix: str) -> List[str]:
        """Фильмы, у которых imdb-id начинается с указанного префикса"""
        result: List[str] = []
        for movie_id, link_info in self.links.items():
            imdb_id = link_info.get("imdb")
            if imdb_id and imdb_id.startswith(prefix):
                title = self.movie_titles.get(movie_id, f"Movie {movie_id}")
                result.append(title)
        return sorted(result)

    def _load_cache(self) -> None:
        """Загружает self.imdb_data из JSON-кэша, если он существует"""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.imdb_data = json.load(f)
            else:
                self.imdb_data = {}
        except json.JSONDecodeError:
            self.imdb_data = {}
        except Exception as e:
            print(f"Warning: could not load cache: {e}")
            self.imdb_data = {}

    def _save_cache(self) -> None:
        """Сохраняет self.imdb_data в JSON-кэш"""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(obj=self.imdb_data, fp=f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: could not save cache: {e}")

    def _fetch_page(self, imdb_id: str) -> Optional[BeautifulSoup]:
        """Получает HTML-страницу фильма с IMDb и возвращает объект BeautifulSoup"""
        url = f"https://www.imdb.com/title/tt{imdb_id}/"
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            time.sleep(self.delay)
            return BeautifulSoup(resp.text, "html.parser")
        except requests.exceptions.Timeout:
            print(f"Request to {url} timed out.")
        except requests.exceptions.RequestException as e:
            print(f"Request to {url} failed: {e}")
        return None

    def _extract_director(self, soup: BeautifulSoup) -> str:
        """Извлекает имя режиссера"""
        if soup is None:
            return "N/A"

        crew_section = soup.find("div", {"data-testid": "title-pc-wide-screen"})
        if crew_section:
            label = crew_section.find("span", string=re.compile("Director", re.I))
            if label:
                link = label.find_next("a")
                if link and link.text:
                    return link.text.strip()

        link = soup.find("a", href=re.compile(r"/name/nm"))
        if link and link.text:
            return link.text.strip()
        return "N/A"

    def _extract_budget(self, soup: BeautifulSoup) -> str:
        """Извлекает бюджет фильма"""
        if soup is None:
            return "N/A"

        item = soup.find("li", {"data-testid": "title-boxoffice-budget"})
        if item:
            val = item.find("span", {"class": "ipc-metadata-list-item__list-content-item"})
            if val and val.text:
                return val.text.strip()

        tag = soup.find(string=re.compile("Budget", re.I))
        if tag:
            next_el = tag.find_next()
            if next_el and next_el.text:
                return next_el.text.strip()
        return "N/A"

    def _extract_gross(self, soup: BeautifulSoup) -> str:
        """Извлекает мировые кассовые сборы"""
        if soup is None:
            return "N/A"

        item = soup.find("li", {"data-testid": "title-boxoffice-cumulativeworldwidegross"})
        if item:
            val = item.find("span", {"class": "ipc-metadata-list-item__list-content-item"})
            if val and val.text:
                return val.text.strip()

        tag = soup.find(string=re.compile("Gross worldwide", re.I))
        if tag:
            next_el = tag.find_next()
            if next_el and next_el.text:
                return next_el.text.strip()
        return "N/A"

    def _extract_runtime(self, soup: BeautifulSoup) -> str:
        """Извлекает строку с длительностью фильма"""
        if soup is None:
            return "N/A"

        item = soup.find("li", {"data-testid": "title-techspec_runtime"})
        if item:
            val = item.find("div", {"class": "ipc-metadata-list-item__content-container"})
            if val and val.text:
                return val.text.strip()

        tag = soup.find(string=re.compile("Runtime", re.I))
        if tag:
            parent = tag.parent
            if parent and parent.text:
                return parent.text.strip()
        return "N/A"

    def _extract_fields(self, imdb_id: str, fields: List[str]) -> List[str]:
        """Извлекает указанные поля с IMDb-страницы"""
        soup = self._fetch_page(imdb_id)
        if not soup:
            return ["N/A"] * len(fields)

        mapping = {
            "director": self._extract_director,
            "budget": self._extract_budget,
            "cumulative worldwide gross": self._extract_gross,
            "runtime": self._extract_runtime,
        }

        result: List[str] = []
        for field in fields:
            key = field.lower()
            extractor = mapping.get(key)
            if extractor:
                result.append(extractor(soup))
            else:
                result.append("N/A")
        return result

    def collect_all_imdb_data(self, fields: List[str], save_every: int = 10) -> None:
        """
        Собирает данные для всех фильмов с imdb-id.
        Результат сохраняется в self.imdb_data и кэш
        """
        for i, (movie_id, imdb_id) in enumerate(self.movie_links.items()):
            if imdb_id in self.imdb_data:
                continue

            try:
                values = self._extract_fields(imdb_id, fields)
                self.imdb_data[imdb_id] = dict(zip(fields, values))

                if (i + 1) % save_every == 0:
                    self._save_cache()
            except Exception as e:
                print(f"[ERROR] Failed for tt{imdb_id}: {e}")

        self._save_cache()

    def _parse_money(self, text: str) -> int:
        """Преобразует строку с долларовой суммой в целое число (в долларах)"""
        if not text or text == "N/A":
            return 0

        s = text.lower().strip()

        multiplier = 1
        if "million" in s or re.search(r"\d+m\b", s):
            multiplier = 1_000_000
        elif "billion" in s or re.search(r"\d+b\b", s):
            multiplier = 1_000_000_000
        elif "thousand" in s or re.search(r"\d+k\b", s):
            multiplier = 1_000

        s = re.sub(r"[^\d.]", "", s)
        if not s:
            return 0

        try:
            if "." in s:
                return int(float(s) * multiplier)
            return int(s) * multiplier
        except (ValueError, TypeError):
            return 0

    def _parse_runtime(self, text: str) -> int:
        """Преобразует строку с длительностью ('2h 30min', '81 min') в минуты"""
        if not text or text == "N/A":
            return 0

        s = text.lower().strip()

        h_match = re.search(r"(\d+)\s*h", s)
        m_match = re.search(r"(\d+)\s*min", s)
        if h_match and m_match:
            return int(h_match.group(1)) * 60 + int(m_match.group(1))

        m_only = re.search(r"(\d+)\s*min", s)
        if m_only:
            return int(m_only.group(1))

        num = re.search(r"(\d+)", s)
        return int(num.group(1)) if num else 0

    def get_imdb(self, movie_ids: List[int], fields: List[str]) -> List[List[str]]:
        """
        Возвращает таблицу [title, field1, field2, ...] для указанных movie_id.
        Отсортировано по title
        """
        rows: List[List[str]] = []
        for movie_id in movie_ids:
            imdb_id = self.get_imdb_id(movie_id)
            if not imdb_id:
                continue

            data = self.imdb_data.get(imdb_id)
            if not data:
                continue

            title = self.movie_titles.get(movie_id, f"Movie {movie_id}")
            row = [title] + [data.get(field, "N/A") for field in fields]
            rows.append(row)

        rows.sort(key=lambda r: r[0])
        return rows

    def top_directors(self, n: int) -> Dict[str, int]:
        """Топ-N режиссеров по количеству фильмов в imdb_data"""
        counter: Counter = Counter()
        for data in self.imdb_data.values():
            director = data.get("Director") or data.get("director")
            if director and director != "N/A":
                counter[director] += 1
        return dict(counter.most_common(n))

    def most_expensive(self, n: int) -> Dict[str, int]:
        """Топ-N фильмов по бюджету"""
        rows: List[Tuple[str, int]] = []
        for movie_id, imdb_id in self.movie_links.items():
            data = self.imdb_data.get(imdb_id, {})
            budget = self._parse_money(data.get("Budget", "0"))
            if budget <= 0:
                continue
            title = self.movie_titles.get(movie_id, f"Movie {movie_id}")
            rows.append((title, budget))
        rows.sort(key=lambda x: -x[1])
        return dict(rows[:n])

    def most_profitable(self, n: int) -> Dict[str, int]:
        """Топ-N самых прибыльных фильмов (gross - budget)"""
        rows: List[Tuple[str, int]] = []
        for movie_id, imdb_id in self.movie_links.items():
            data = self.imdb_data.get(imdb_id, {})
            budget = self._parse_money(data.get("Budget", "0"))
            gross = self._parse_money(data.get("Cumulative Worldwide Gross", "0"))
            if budget <= 0 or gross <= 0:
                continue
            profit = gross - budget
            title = self.movie_titles.get(movie_id, f"Movie {movie_id}")
            rows.append((title, profit))
        rows.sort(key=lambda x: -x[1])
        return dict(rows[:n])

    def longest(self, n: int) -> Dict[str, int]:
        """Топ-N самых длинных фильмов (по длительности в минутах)"""
        rows: List[Tuple[str, int]] = []
        for movie_id, imdb_id in self.movie_links.items():
            data = self.imdb_data.get(imdb_id, {})
            runtime = self._parse_runtime(data.get("Runtime", "0"))
            if runtime <= 0:
                continue
            title = self.movie_titles.get(movie_id, f"Movie {movie_id}")
            rows.append((title, runtime))
        rows.sort(key=lambda x: -x[1])
        return dict(rows[:n])

    def top_cost_per_minute(self, n: int) -> Dict[str, float]:
        """Топ-N фильмов по стоимости минуты экранного времени"""
        rows: List[Tuple[str, float]] = []
        for movie_id, imdb_id in self.movie_links.items():
            data = self.imdb_data.get(imdb_id, {})
            budget = self._parse_money(data.get("Budget", "0"))
            runtime = self._parse_runtime(data.get("Runtime", "0"))
            if budget <= 0 or runtime <= 0:
                continue
            cpm = round(budget / runtime, 2)
            title = self.movie_titles.get(movie_id, f"Movie {movie_id}")
            rows.append((title, cpm))
        rows.sort(key=lambda x: -x[1])
        return dict(rows[:n])
