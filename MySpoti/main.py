import datetime
import html
import os
import time
import spotipy
from flask import json, render_template, session, request, redirect
from .app import create_app
# from keys import Client_ID, Client_Secret, Redirect_URI
# from flask_session import Session


app = create_app()


def validate_time_range(time_range):
    """
    Validate time range and return the amount of time
    """
    time_ranges_map = {
    "long_term": "several years",
    "medium_term": "last 6 months",
    "short_term": "last 4 weeks"
    }
    if time_range != "short_term" and time_range != "medium_term" and time_range != "long_term":
        time_range = "short_term"
    return time_range, time_ranges_map[time_range]


def validate_limit(limit):
    """
    Validate limit
    """
    if limit != 12 and limit != 24 and limit != 50 and limit != 48:
        return 12
    return limit


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500


@app.route("/")
def index():
    """
    Home page
    """
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=os.environ.get("Client_ID"),
        client_secret=os.environ.get("Client_Secret"),
        redirect_uri=os.environ.get("Redirect_URI"),
        cache_handler=cache_handler
    )
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        signed_in = False
    else:
        signed_in = True
    context = {
        "signed_in": signed_in
    }
    return render_template("index.html", **context)


@app.route("/home")
def home():
    """
    User login and authorization with Spotify API
    """
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=os.environ.get("Client_ID"), 
        client_secret=os.environ.get("Client_Secret"),
        redirect_uri=os.environ.get("Redirect_URI"),
        scope="user-read-currently-playing user-top-read user-read-recently-played",
        cache_handler=cache_handler,
        show_dialog=True
    )
    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect("/home")
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return redirect(auth_url)
    else:
        signed_in = True
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    context = {
        "user": spotify.me(),
        "signed_in": signed_in
    }
    return render_template("home.html", **context)


@app.route("/currently_playing")
def currently_playing():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=os.environ.get("Client_ID"),
        client_secret=os.environ.get("Client_Secret"),
        redirect_uri=os.environ.get("Redirect_URI"),
        cache_handler=cache_handler
    )
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/home")
    else:
        signed_in = True
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if track:
        artists = ", ".join([artist["name"] for artist in track["item"]["artists"]])
        return f'<h2>Currently playing: <a href="{track["item"]["external_urls"]["spotify"]}">{track["item"]["name"]}</a></h2>' \
               f'<h3>by {artists}</h3>' \
               f'<h3>from <a href="{track["item"]["album"]["external_urls"]["spotify"]}">{track["item"]["album"]["name"]}</a></h3>' \
               f'<img src="{track["item"]["album"]["images"][1]["url"]}" alt="album cover" width="300" height="300">'
    
    else:
        return "Nothing currently playing"


@app.route("/top_tracks")
def top_tracks():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=os.environ.get("Client_ID"),
        client_secret=os.environ.get("Client_Secret"),
        redirect_uri=os.environ.get("Redirect_URI"),
        cache_handler=cache_handler
    )
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/home")
    else:
        signed_in = True
    time_range, time = validate_time_range(request.args.get("time_range", "short_term"))
    limit = validate_limit(int(request.args.get("limit", 12)))
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    top_tracks_list = spotify.current_user_top_tracks(limit=limit, time_range=time_range)
    top_tracks = {}
    for i, item in enumerate(top_tracks_list["items"]):
        top_tracks[i] = {
            "name": item["name"],
            "artists": ", ".join([artist["name"] for artist in item["artists"]]),
            "album": item["album"]["name"],
            "album_cover": item["album"]["images"][1]["url"],
            "url": item["external_urls"]["spotify"]
        }
    context = {
        "top_tracks": top_tracks,
        "time_range": time_range,
        "limit": limit,
        "time": time,
        "signed_in": signed_in
    }
    return render_template("top_tracks.html", **context)


@app.route("/top_artists")
def top_artists():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=os.environ.get("Client_ID"),
        client_secret=os.environ.get("Client_Secret"),
        redirect_uri=os.environ.get("Redirect_URI"),
        cache_handler=cache_handler
    )
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/home")
    else:
        signed_in = True
    time_range, time = validate_time_range(request.args.get("time_range", "short_term"))
    limit = validate_limit(int(request.args.get("limit", 12)))
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    top_artists_list = spotify.current_user_top_artists(limit=limit, time_range=time_range)
    top_artists = {}
    for i, item in enumerate(top_artists_list["items"]):
        top_artists[i] = {
            "name": item["name"],
            "genres": ", ".join(item["genres"]),
            "image": item["images"][1]["url"],
            "url": item["external_urls"]["spotify"]
        }
    context = {
        "top_artists": top_artists,
        "time_range": time_range,
        "limit": limit,
        "time": time,
        "signed_in": signed_in
    }
    return render_template("top_artists.html", **context)


@app.route("/recently_played")
def recently_played():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=os.environ.get("Client_ID"),
        client_secret=os.environ.get("Client_Secret"),
        redirect_uri=os.environ.get("Redirect_URI"),
        cache_handler=cache_handler
    )
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect("/home")
    else:
        signed_in = True
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    recently_played_list = spotify.current_user_recently_played(limit=50)
    # return recently_played_list
    tracks = ""
    for i in range(len(recently_played_list["items"])):
        tracks += f'<h2><a href="{recently_played_list["items"][i]["track"]["external_urls"]["spotify"]}">{recently_played_list["items"][i]["track"]["name"]}</a></h2>'
        tracks += f'<h3>by {", ".join([artist["name"] for artist in recently_played_list["items"][i]["track"]["artists"]])}</h3>'
        tracks += f'<h3>from <a href="{recently_played_list["items"][i]["track"]["album"]["external_urls"]["spotify"]}">{recently_played_list["items"][i]["track"]["album"]["name"]}</a></h3>'
        tracks += f'<img src="{recently_played_list["items"][i]["track"]["album"]["images"][0]["url"]}" alt="album cover" width="300" height="300">'
    return tracks



@app.route("/sign_out")
def sign_out():
    """
    Sign out from Spotify
    """
    session.pop("token_info", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(threaded=True)