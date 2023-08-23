import os
import spotipy
from flask import render_template, session, request, redirect
from .app import create_app


app = create_app()  # Create Flask app with the configuration from config.py


def validate_time_range(time_range):
    """
    Validate time range and convert it to a more readable format

    Args:
        time_range (str): The time range to validate

    Returns:
        Tuple[str, str]: The time range and the amount of time it represents
    """
    time_ranges_map = {
        "long_term": "several years",
        "medium_term": "last 6 months",
        "short_term": "last 4 weeks"
    }
    if time_range not in time_ranges_map:
        time_range = "short_term"
    return time_range, time_ranges_map[time_range]


def validate_limit(limit):
    """
    Validate limit and convert it to a valid limit

    Args:
        limit (int): The limit to validate

    Returns:
        int: The valid limit
    """
    valid_limits = {12, 24, 48, 50}
    if limit not in valid_limits:
        return 12
    return limit


@app.errorhandler(404)
def page_not_found(e):
    """
    404 error page handler for page not found
    """
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    """
    500 error page handler for internal server error
    """
    return render_template("500.html"), 500


@app.route("/")
def index():
    """
    Render the welcome page

    Returns:
        template: The index.html template
        Context:
            - signed_in: Whether the user is signed in or not
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
    Handle the authentication process with Spotify and render the home page

    Returns:
        - redirect: Redirects to the home page if user authenticated
        - redirect: Redirects to the Spotify auth if user not authenticated
        Context:
            - user: The user's information
            - signed_in: Whether the user is signed in or not
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
    """
    Render the top tracks page

    Returns:
        - template: The top_tracks.html template
        - redirect: Redirects to the home page if user not authenticated
        Context:
            - top_tracks: A dictionary of the user's top tracks information
            - time_range: The time range of the top tracks
            - limit: The limit of the top tracks
            - time: The amount of time the time range represents
            - signed_in: Whether the user is signed in or not
        """
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
    time_range, time = validate_time_range(
        request.args.get("time_range", "short_term")
    )
    limit = validate_limit(int(request.args.get("limit", 12)))
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    top_tracks_list = spotify.current_user_top_tracks(
        limit=limit, time_range=time_range
    )
    top_tracks_json = {}
    for i, item in enumerate(top_tracks_list["items"]):
        artists = [artist["name"] for artist in item["artists"]]
        top_tracks_json[i] = {
            "name": item["name"],
            "artists": ", ".join(artists),
            "album": item["album"]["name"],
            "album_cover": item["album"]["images"][1]["url"],
            "url": item["external_urls"]["spotify"]
        }
    context = {
        "top_tracks": top_tracks_json,
        "time_range": time_range,
        "limit": limit,
        "time": time,
        "signed_in": signed_in
    }
    return render_template("top_tracks.html", **context)


@app.route("/top_artists")
def top_artists():
    """
    Render the top artists page

    Returns:
        - template: The top_artists.html template
        - redirect: Redirects to the home page if user not authenticated
        Context:
            - top_artists: A dictionary of the user's top artists information
            - time_range: The time range of the top artists
            - limit: The limit of the top artists
            - time: The amount of time the time range represents
            - signed_in: Whether the user is signed in or not
    """
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
    time_range, time = validate_time_range(
        request.args.get("time_range", "short_term")
    )
    limit = validate_limit(int(request.args.get("limit", 12)))
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    top_artists_list = spotify.current_user_top_artists(
        limit=limit, time_range=time_range
    )
    top_artists_json = {}
    for i, item in enumerate(top_artists_list["items"]):
        top_artists_json[i] = {
            "name": item["name"],
            "genres": ", ".join(item["genres"]),
            "image": item["images"][1]["url"],
            "url": item["external_urls"]["spotify"]
        }
    context = {
        "top_artists": top_artists_json,
        "time_range": time_range,
        "limit": limit,
        "time": time,
        "signed_in": signed_in
    }
    return render_template("top_artists.html", **context)


@app.route("/recently_played")
def recently_played():
    """
    Render the recently played page

    Returns:
        - template: The recently_played.html template
        - redirect: Redirects to the home page if user not authenticated
        Context:
            - recently_played: The user's recently played tracks information
            - limit: The limit of the recently played tracks
            - signed_in: Whether the user is signed in or not
    """
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
    limit = validate_limit(int(request.args.get("limit", 12)))
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    recently_played_list = spotify.current_user_recently_played(limit=limit)
    recently_played_json = {}
    for i, item in enumerate(recently_played_list["items"]):
        artists = [artist["name"] for artist in item["track"]["artists"]]
        recently_played_json[i] = {
            "name": item["track"]["name"],
            "artists": ", ".join(artists),
            "album": item["track"]["album"]["name"],
            "album_cover": item["track"]["album"]["images"][1]["url"],
            "url": item["track"]["external_urls"]["spotify"]
        }
    context = {
        "recently_played": recently_played_json,
        "limit": limit,
        "signed_in": signed_in
    }
    return render_template("recently_played.html", **context)


@app.route("/sign_out")
def sign_out():
    """
    Sign out the user

    Returns:
        - redirect: Redirects to the home page after signing out
    """
    session.pop("token_info", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(threaded=True)
