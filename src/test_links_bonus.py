import pytest
from links import Links 


@pytest.fixture
def links_obj(tmp_path):
    datasets = tmp_path / "datasets"
    datasets.mkdir()

 
    (datasets / "links.csv").write_text(
        "movieId,imdbId,tmdbId\n"
        "10,0114709,862\n"
        "20,0113497,8844\n",
        encoding="utf-8",
    )

    # (без заголовка, потому что file_reader выкидывает header)
    (datasets / "data_imdb.csv").write_text(
        "imdb_id,title,director,budget,gross,runtime\n"
        "0114709,Toy Story,John Lasseter,30000000,373554033,81\n"
        "0113497,Jumanji,Joe Johnston,,262797249,104\n",
        encoding="utf-8",
    )

    import os
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        obj = Links(str(datasets / "links.csv"))
        yield obj
    finally:
        os.chdir(old)


def test_enrich_movies(links_obj):
    titles = {10: "Toy Story (1995)", 20: "Jumanji (1995)"}
    res = links_obj.enrich_movies([10, 20, 999], movies_titles=titles)

    assert isinstance(res, list)
    assert len(res) == 2

    
    assert res[0][0] == 20
    assert res[1][0] == 10

    
    assert res[0][3] == "Jumanji (1995)"
    assert res[1][3] == "Toy Story (1995)"

   
    assert res[0][4] == "Joe Johnston"
    assert res[1][4] == "John Lasseter"
