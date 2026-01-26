import pytest
from movies import Movies  


@pytest.fixture
def movies_obj(tmp_path):
    p = tmp_path / "movies.csv"
    p.write_text(
        "movieId,title,genres\n"
        "1,Toy Story (1995),Adventure|Animation|Children\n"
        "2,Jumanji (1995),Adventure|Children|Fantasy\n"
        "3,Heat (1995),Action|Crime|Thriller\n",
        encoding="utf-8",
    )
    return Movies(str(p))


def test_genre_cooccurrence(movies_obj):
    res = movies_obj.genre_cooccurrence(top_k=10)

    assert isinstance(res, dict)

   
    assert ("Adventure", "Children") in res
    assert res[("Adventure", "Children")] == 2
