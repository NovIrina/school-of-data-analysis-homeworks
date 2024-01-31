# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from itemloaders.processors import Join, TakeFirst
from scrapy.item import Field, Item


class MovieItem(Item):
    """
    The structure of the movie item for the scrapy spider.

    Fields:
        title: The title of the movie.
        genre: The genre(s) of the movie.
        director: The director(s) of the movie.
        country: The country(ies) where the movie was produced.
        year: The release year of the movie.
        imdb_rating: The IMDb rating of the movie.
    """
    title = Field(output_processor=TakeFirst())
    genre = Field(output_processor=Join(", "))
    director = Field(output_processor=Join(", "))
    country = Field(output_processor=Join(", "))
    year = Field(output_processor=TakeFirst())
    imdb_rating = Field(output_processor=TakeFirst())
