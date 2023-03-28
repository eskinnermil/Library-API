from main import request, json, jsonify, make_response
from validation import request_validation_name, request_validation_date, request_validation_type
from main import datastore
from flask import Blueprint

client = datastore.Client()
LIBRARIES = "libraries"
COLLECTIONS = "collections"
MEDIA = "media"

view_media = Blueprint('view_media', __name__)


# POST Media to the site, GET Media
@view_media.route('/media', methods=['POST', 'GET'])
def media_get_post():
    if request.method == 'POST':
        if 'application/json' not in request.content_type:
            error = '{\n"415 Unsupported Media Type": "The server only supports JSON format."\n}'
            return (error, 415)
        content = request.get_json()
        for key in content.keys():
            if key != 'name' and key != 'type' and key != 'release_date':
                error = '{\n"400 Bad Request": "The request object contains an extraneous attribute."\n}'
                return (error, 400)
        if 'name' in content.keys() and 'type' in content.keys() and 'release_date' in content.keys():
            if request_validation_name(content["name"]) == "Forbidden":
                error = '{\n"403 Forbidden": "The name is already taken by an existing media."\n}'
                return (error, 403)
            if request_validation_name(content["name"]) \
                    and request_validation_type(content["type"]) \
                    and request_validation_date(content["release_date"]):
                new_media = datastore.entity.Entity(key=client.key(MEDIA))
                new_media.update({"name": content["name"], "type": content["type"],
                  "release_date": content["release_date"], "collection": None})
                client.put(new_media)
                new_media["id"] = new_media.key.id
                new_media["self"] = request.url + '/' + str(new_media.key.id)
                return jsonify(new_media), 201
        error = '{\n"400 Bad Request":  "The request object contained an invalid value."\n}'
        return (error, 400)
    elif request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            error = '{\n"406 Not Acceptable": "The media type is not accepted by the server."\n}'
            return (error, 406)
        # Show all media; paginated
        query = client.query(kind=MEDIA)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        prev_url = None
        if q_offset - q_limit >= 0:
            prev_offset = q_offset - q_limit
            prev_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(prev_offset)
        for e in results:
            e['id'] = e.key.id
            e['self'] = request.url + '/' + str(e.key.id)
            # if 'collection' in e.keys():
            #     collection_key = client.key(kind=COLLECTIONS)
            #     collection = client.get(key=collection_key)
            #     collection['id'] = collection.key.id
            #     collection['self'] = request.url + '/' + str(collection.key.id)
        total = len(list(query.fetch()))
        output = {"media": results, "total_items": total}
        if next_url:
            output["next"] = next_url
        if prev_url:
            output["prev"] = prev_url
        return (json.dumps(output)), 200
    else:
        return 'Method not recognized'


# DELETE, PUT, or PATCH a specific media
@view_media.route('/media/<mid>', methods=['DELETE', 'PATCH', 'PUT'])
def media_delete_put_patch(mid):
    if request.method == 'DELETE':
        media_query = client.query(kind=MEDIA)
        media = list(media_query.fetch())
        for med in media:
            med["id"] = med.key.id
            if med["id"] == int(mid):
                client.delete(med)
                return "", 204
        return '{\n"404 Not Found":  "No media with this media_id exists"\n}', 404
    elif request.method == 'PATCH':
        if 'application/json' not in request.content_type:
            error = '{\n"415 Unsupported Media Type": "The server only supports JSON format."\n}'
            return (error, 415)
        content = request.get_json()
        media_key = client.key("media", int(mid))
        media = client.get(key=media_key)
        if media:
            # handling invalid key (including ID)
            for key in content.keys():
                if key != 'name' and key != 'type' and key != 'release_date' or len(content.keys()) > 2:
                    error = '{\n"400 Bad Request": "The request object contains an extraneous attribute."\n}'
                    return (error, 400)

            # handling name/type patch
            if 'name' in content.keys() and 'type' in content.keys():
                if request_validation_name(content["name"]) and request_validation_type(content["type"]):
                    if request_validation_name(content["name"]) == "Forbidden":
                        error = '{\n"403 Forbidden": "The name is already taken by an existing media."\n}'
                        return (error, 403)
                    media.update({"name": content["name"], "type": content["type"]})
                    client.put(media)
                    media["id"] = media.key.id
                    media["self"] = request.url
                    return (json.dumps(media)), 200

            # handling name/release_date patch
            elif 'name' in content.keys() and 'release_date' in content.keys():
                if request_validation_name(content["name"]) == "Forbidden":
                    error = '{\n"403 Forbidden": "The name is already taken by an existing media."\n}'
                    return (error, 403)
                if request_validation_name(content["name"]) and request_validation_date(content["release_date"]):
                    media.update({"name": content["name"], "release_date": content["release_date"]})
                    client.put(media)
                    media["id"] = media.key.id
                    media["self"] = request.url
                    return (json.dumps(media)), 200

            # handling type/release_date patch
            elif 'type' in content.keys() and 'release_date' in content.keys():
                if request_validation_type(content["type"]) and request_validation_date(content["release_date"]):
                    media.update({"type": content["type"], "release_date": content["release_date"]})
                    client.put(media)
                    media["id"] = media.key.id
                    media["self"] = request.url
                    return (json.dumps(media)), 200

            # handling name patch
            elif 'name' in content.keys():
                if request_validation_name(content["name"]) == "Forbidden":
                    error = '{\n"403 Forbidden": "The name is already taken by an existing media."\n}'
                    return (error, 403)
                if request_validation_name(content["name"]):
                    media.update({"name": content["name"]})
                    client.put(media)
                    media["id"] = media.key.id
                    media["self"] = request.url
                    return (json.dumps(media)), 200

            # handling type patch
            elif 'type' in content.keys():
                if request_validation_type(content["type"]):
                    media.update({"type": content["type"]})
                    client.put(media)
                    media["id"] = media.key.id
                    media["self"] = request.url
                    return (json.dumps(media)), 200

            # handling last_updated patch
            elif 'release_date' in content.keys():
                if request_validation_date(content["release_date"]):
                    media.update({"release_date": content["release_date"]})
                    client.put(media)
                    media["id"] = media.key.id
                    media["self"] = request.url
                    return (json.dumps(media)), 200

            error = '{\n"400 Bad Request":  "The request object contained an invalid value."\n}'
            return (error, 400)
        # if there is no boat
        error = '{\n"404 Not Found":  "No media with this media_id exists"\n}'
        return (error, 404)
    elif request.method == 'PUT':
        if 'application/json' not in request.content_type:
            error = '{\n"415 Unsupported Media Type": "The server only supports JSON format."\n}'
            return (error, 415)
        content = request.get_json()
        media_key = client.key("media", int(mid))
        media = client.get(key=media_key)
        if media:

            # handling invalid key (including ID)
            for key in content.keys():
                if key != 'name' and key != 'type' and key != 'release_date':
                    error = '{\n"400 Bad Request": "The request object contains an extraneous attribute."\n}'
                    return (error, 400)
            # handling 3 attribute PUT
            if 'name' in content.keys() and 'type' in content.keys() and 'release_date' in content.keys():
                if request_validation_name(content["name"]) == "Forbidden":
                    error = '{\n"403 Forbidden": "The name is already taken by an existing media."\n}'
                    return (error, 403)
                if request_validation_name(content["name"]) \
                        and request_validation_type(content["type"]) \
                        and request_validation_date(content["release_date"]):
                    media.update({"name": content["name"], "type": content["type"], "release_date":
                        content["release_date"]})
                    client.put(media)
                    media["id"] = media.key.id  # Include ID in the JSON Representation
                    media["self"] = request.url
                    res = make_response(json.dumps(media))
                    res.headers.set('Location', request.url)
                    res.status_code = 303
                    return res
            error = '{\n"400 Bad Request":  "The request object contained an invalid value."\n}'
            return (error, 400)
        error = '{\n"404 Not Found":  "No media with this media_id exists"\n}'
        return (error, 404)
    else:
        return 'Method not recognized'


# GET the Selected Media's Info
@view_media.route('/media/<mid>', methods=['GET'])
def media_get(mid):
    if request.method == 'GET':
        media_key = client.key("media", int(mid))
        media = client.get(key=media_key)
        if media:
            media['id'] = request.url
            return json.dumps(media), 200
        error = '{\n"Error":  "No media with this media_id exists"\n}'
        return (error, 404)
