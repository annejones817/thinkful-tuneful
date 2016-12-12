import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from tuneful import app
from .database import session
from .utils import upload_path

#JSON Schema describing structure of post
song_schema = {
    "properties" : {
        "file": {"type" : "object"},
        "id" : {"type" : "integer"}
    }, 
    "required": ["file", "id"]
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get(): 
    """Get a list of songs"""
    songs = session.query(models.Song).order_by(models.Song.id)
    
    #convert songs to JSON and return response
    data = json.dumps([song.as_dictionary() for song in songs])
    print(data)
    return Response(data, 200, mimetype="application/json")
    
@app.route("/api/songs/<int:id>", methods=["GET"])    
@decorators.accept("application/json")
def songs_get_by_id(id):
    """Single song endpoint"""
    #Get the song from the database
    
    song=session.query(models.Song).get(id)
    
    #Check whether song exists, if not return a 404 with a helpful message
    
    if not song: 
        message="Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")
        
    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype="application/json")    
    
@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_post(): 
    """Add a new song"""
    data = request.json
    
    """
    #Check for valid JSON, if not return 422 Unprocessable
    try: 
        validate(data, song_schema)
    except ValidationError as error: 
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
        """
    
    #Check that the id exists
    if not session.query(models.File).filter(models.File.id == data["file"]["id"]).first():
        message = "Could not find a song file with id {}".format(data["file"]["id"])
        data = {"message": message}
    
    #Add the song 
    song = models.Song()
    file = session.query(models.File).filter(models.File.id == data["file"]["id"]).first()
    file.song = song
    song.file_id = file.id
    session.add(song)
    session.commit()
    
    #Return 201 Created
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("songs_get_by_id", id=song.id)}
    return Response(data, 201, headers=headers, mimetype="application/json")