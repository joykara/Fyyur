#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from model import app, db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

#local postgresql DB

#----------------------------------------------------------------------------#
# Models.

from model import *

#----------------------------------------------------------------------------#

# Filters.
#----------------------------------------------------------------------------#

def format_datetime(data, format='medium'):
  date = dateutil.parser.parse(data)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  venues = Venue.query.order_by(db.desc(Venue.id)).limit(10).all()
  artists = Artist.query.order_by(db.desc(Artist.id)).limit(10).all()
  return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  venues = db.session.query(Venue.city,Venue.state).group_by(Venue.city, Venue.state).all()

  for area in venues:
    venues = db.session.query(Venue.id,Venue.name).filter(Venue.city==area[0],Venue.state==area[1]).all()
    data.append({
        "city": area[0],
        "state": area[1],
        "venues": venues
        })
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  data_returned = Venue.query.filter(Venue.name.ilike('%{}%'.format(request.form['search_term']))).all()

  response={
    "count": len(data_returned),
    "data": []
    }
  for venue in data_returned:
    response["data"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": db.session.query(Show).join(Venue).filter(Show.venue_id==venue.id).filter(Show.start_time>datetime.utcnow()).count()
    })

  return render_template('pages/search_venues.html', data_returned=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)

  past_shows = db.session.query(Show).join(Artist).filter(Show.start_time<= datetime.utcnow(), Show.venue_id==venue.id).all()
  upcoming_shows = db.session.query(Show).join(Artist).filter(Show.start_time> datetime.utcnow(), Show.venue_id==venue.id).all()
  shows = venue.shows
  current_time = datetime.utcnow()

  for show in shows:
    show_data = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
      }

    if (show.start_time>current_time):
        upcoming_shows.append(show_data)

    else:
        past_shows.append(show_data)

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": db.session.query(Show).join(Artist).filter(Show.start_time<= datetime.utcnow(), Show.venue_id==venue.id).count(),
    "upcoming_shows_count": db.session.query(Show).join(Artist).filter(Show.start_time> datetime.utcnow(), Show.venue_id==venue.id).count()
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead modify data to be the data object returned from db insertion
  form = VenueForm(request.form)

  if form.validate():
    try:
      venue= Venue(
        name = form.name.data,
        genres = form.genres.data,
        address = form.address.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data,
        image_link = form.image_link.data
      )

      db.session.add(venue)
      db.session.commit()
        # on successful db insert, flash success
      flash('Venue ' + form.name.data + ' was successfully listed!')

    except:
          db.session.rollback()
            # TODO: on unsuccessful db insert, flash an e
          flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')

    finally:
          db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Implement a button to delete a Venue on a Venue Page, then redirect the user to the homepage

  try:
        deleted_venue = Venue.query.filter_by(id=venue_id).delete()
        db.session.delete(deleted_venue)
        db.session.commit()
        flash("Venue " + deleted_venue.name + " was deleted successfully!")
  except:
        db.session.rollback()

        flash("Venue was not deleted successfully.")
  finally:
        db.session.close()

  return redirect(url_for("index"))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=db.session.query(Artist.id, Artist.name).all()

  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.

  data_returned = Artist.query.filter(Artist.name.ilike('%{}%'.format(request.form['search_term']))).all()

  response={
    "count": len(data_returned),
    "data": []
  }
  for artist in data_returned:
    response['data'].append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": db.session.query(Show,Venue).join(Venue).filter(Show.start_time<= datetime.utcnow(), Show.artist_id==artist.id).count()
      })

  return render_template('pages/search_artists.html', data_returned=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id

  artist = Artist.query.get(artist_id)

  shows = artist.shows
  current_time = datetime.utcnow()

  past_shows = db.session.query(Show,Venue).join(Venue).filter(Show.start_time<= datetime.utcnow(), Show.artist_id==artist.id).all()
  upcoming_shows = db.session.query(Show,Venue).join(Venue).filter(Show.start_time>datetime.utcnow(), Show.artist_id==artist.id).all()

  for show in shows:
    show_info = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.start_time)
    }

    if (show.start_time>current_time):
      upcoming_shows.append(show_info)

    else:
      past_shows.append(show_info)

  data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description":artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": db.session.query(Show,Venue).join(Venue).filter(Show.start_time<= datetime.utcnow(), Show.artist_id==artist.id).count(),
        "upcoming_shows_count": db.session.query(Show,Venue).join(Venue).filter(Show.start_time>datetime.utcnow(), Show.artist_id==artist.id).count()
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # TODO: populate form with fields from artist with ID <artist_id>

  form = ArtistForm(request.form)
  artist = db.session.query(Artist).filter(Artist.id == artist_id).one()

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take datas from the form submitted, and update existing

        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.facebook_link = request.form['facebook_link']
        artist.genres = request.form['genres']
        artist.image_link = request.form['image_link']
        artist.website_link = request.form['website_link']

        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: populate form with datas from venue with ID <venue_id>

  form = VenueForm(request.form)
  venue = db.session.query(Venue).filter(Venue.id == venue_id).one()

  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take datas from the form submitted, and update existing

        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.facebook_link = request.form['facebook_link']
        venue.genres = request.form['genres']
        venue.image_link = request.form['image_link']
        venue.website_link = request.form['website_link']

        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead. modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)

  if form.validate():
    try:
      artist = Artist(
        name = form.name.data,
        genres = form.genres.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data,
        image_link = form.image_link.data
      )
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + form.name.data + ' was successfully listed!')

    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')

    finally:
      db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows

  data = []
  shows = Show.query.all()

  for show in shows:
      data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
        })

  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form

  new_show = Show()
  new_show.artist_id = request.form['artist_id']
  new_show.venue_id = request.form['venue_id']
  new_show.start_time = request.form['start_time']

  try:
    db.session.add(new_show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')

  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')

  finally:
    db.session.close()
  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()
