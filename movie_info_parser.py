'''
This module parse site film.ru and get information about movie, its poster, genre etc.
Next parse youtube and get movie trailer and then parse info from IMDB. All info it put to DB.
'''
import sqlite3
import sys
import time

import requests
from bs4 import BeautifulSoup

from config import token


def get_html(url):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
        }
    response = requests.get(url, headers=headers)
    return response


def get_movie_description(movieTitle):
    movieTitle = movieTitle.replace(' ', '+')

    URL = f'https://www.film.ru/search/result?text={movieTitle}&type=all'
    URL_base = 'https://www.film.ru'
    # Get search query page
    html = get_html(URL)
    soup = BeautifulSoup(html.text, 'lxml')
    try:
        movieLink = soup.find('div', class_='rating').find('a').get('href')
        # Get movie's page
        html = get_html(URL_base + movieLink)
        soup = BeautifulSoup(html.text, 'lxml')
        try:
            poster = soup.find('div', class_='movies-left').find('img').get('src')
        except:
            poster = 'Not found'
        try:
            description = soup.find('div', class_='synopsis').find('p').get_text()
        except:
            description = 'Not found'
        try:
            info = soup.find('h3').get_text()
            info = info.split(',')
            year = info[0]
            genre = info[1].title().strip()
        except:
            year = 'Not found'
            genre = 'Not found'
    except AttributeError:
        description = 'Not found'
        poster = 'Not found'
        year = 'Not found'
        genre = 'Not found'

    return (description, poster, year, genre)


def get_trailer(movieTitle):
    URL = f'https://www.googleapis.com/youtube/v3/search?q={movieTitle} трейлер&key={token}'

    response = get_html(URL)
    json_response = response.json()
    movie_id = json_response['items'][0]['id'].get('videoId')
    if movie_id is not None:
        return (f'https://www.youtube.com/watch?v={movie_id}',)
    return ('Not found',)


def get_imdb_id(movieTitle):
    URL = f'https://www.imdb.com/find?q={movieTitle}&ref_=nv_sr_sm'
    response = get_html(URL)
    soup = BeautifulSoup(response.text, 'lxml')
    try:
        linkMovie = soup.find('td', class_='result_text').find('a').get('href')
        movie_id = linkMovie.split('/')[2][2:]
    except AttributeError:
        movie_id = 'Not found'
    return (movie_id,)


def save_to_db(data):
    con = sqlite3.connect('DB/movies.db')
    cur = con.cursor()
    queryInsert = "INSERT INTO movies VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)"
    try:
        cur.execute(queryInsert, data)
    except sqlite3.DatabaseError as err:
        print('Error:', err)
    con.commit()
    cur.close()
    con.close()


def main():
    # Reads movies list
    with open('moviesList/test_movie.txt', 'r') as f:
    	movies = f.readlines()

    numberOfFilms = len(movies)
    numIter = 1

    print('MovieParser'.center(79, '-'))

    for movie in movies:
        movie = movie.strip()
        description = get_movie_description(movie)
        trailer = get_trailer(movie)
        imdb_id = get_imdb_id(movie)
        data = (movie,) + description + trailer + imdb_id
        save_to_db(data)

        sys.stdout.write("\rParsed: %s/%s movies." % (numIter, numberOfFilms))
        sys.stdout.flush()
        numIter += 1
        time.sleep(3)
    sys.stdout.write("\nProcess is over!\n")
    print('End'.center(79, '-'))


if __name__ == "__main__":
    main()
