from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests


app = Flask(__name__)
# Add secret key
app.config['SECRET_KEY'] = ''
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my-top-movies.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

Bootstrap(app)

db = SQLAlchemy(app)

api_key_3 = ""
API_URL_SEARCH = "https://api.themoviedb.org/3/search/movie"
API_URL_DETAILS = "https://api.themoviedb.org/3/movie/"
POSTER_URL = "https://image.tmdb.org/t/p/w500"

# Proxy setup
proxies = None


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"<Movie {self.title}>"


class RatingForm(FlaskForm):
    rating = FloatField(label="Your Rating Out of 10 e.g. 7.5")
    review = StringField(label="Your Review")
    submit = SubmitField(label="Done")


class MovieTitleForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    for rank, movie in enumerate(movies):
        movie.ranking = len(movies) - rank
    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    title_id = request.args.get("title_id")
    if title_id:
        params = {'api_key': api_key_3}
        result = requests.get(url=API_URL_DETAILS + title_id, proxies=proxies, params=params)
        result.raise_for_status()
        movie_details = result.json()
        new_movie = Movie(
            title=movie_details.get('title'),
            year=movie_details.get('release_date')[:4],
            description=movie_details.get('overview'),
            img_url=f"{POSTER_URL}{movie_details.get('poster_path')}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', movie_id=new_movie.id))
    movie_id = request.args.get("movie_id")
    movie = Movie.query.get(movie_id)
    form = RatingForm()
    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = MovieTitleForm()
    if form.validate_on_submit():
        params = {'query': f'{form.title.data}', 'api_key': api_key_3}
        result = requests.get(url=API_URL_SEARCH, proxies=proxies, params=params)
        result.raise_for_status()
        search_result = result.json().get('results')
        found_titles = []
        for movie in search_result:
            found_titles.append((movie.get('title'), movie.get('release_date'), movie.get('id')))
        return render_template('select.html', found_titles=found_titles)
    return render_template('add.html', form=form)


@app.route('/delete')
def delete():
    movie_id = request.args.get("movie_id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
