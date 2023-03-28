from main import request, json, jsonify, make_response
from validation import request_validation_name, request_validation_date, request_validation_capacity
from main import datastore
from jwt import *
from flask import Blueprint

client = datastore.Client()
LIBRARIES = "libraries"
COLLECTIONS = "collections"
MEDIA = "media"

view_collections = Blueprint('view_collections', __name__)


# Create a collection if the Authorization header contains a valid JWT
@view_collections.route('/collections', methods=['POST', 'GET'])
def collections_get_post():
    if request.method == 'POST':
        if 'application/json' not in request.content_type:
            error = '{\n"415 Unsupported Media Type": "The server only supports JSON format."\n}'
            return (error, 415)
        payload = verify_jwt(request)
        content = request.get_json()
        for key in content.keys():
            if key != 'name' and key != 'capacity' and key != 'last_updated':
                error = '{\n"400 Bad Request": "The request object contains an extraneous attribute."\n}'
                return (error, 400)
        if 'name' in content.keys() and 'capacity' in content.keys() and 'last_updated' in content.keys():
            if request_validation_name(content["name"]) == "Forbidden":
                error = '{\n"403 Forbidden": "The name is already taken by an existing collection."\n}'
                return (error, 403)
            if request_validation_name(content["name"]) \
                    and request_validation_capacity(content["capacity"]) \
                    and request_validation_date(content["last_updated"]):
                new_collection = datastore.entity.Entity(key=client.key(COLLECTIONS))
                new_collection.update({"name": content["name"], "capacity": content["capacity"],
                  "last_updated": content["last_updated"], "media": [], "owner": payload["sub"]})
                client.put(new_collection)
                new_collection["id"] = new_collection.key.id
                new_collection["self"] = request.url + '/' + str(new_collection.key.id)
                return jsonify(new_collection), 201
        error = '{\n"400 Bad Request":  "The request object contained an invalid value."\n}'
        return (error, 400)
    elif request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            error = '{\n"406 Not Acceptable": "The media type is not accepted by the server."\n}'
            return (error, 406)
        try:  # Show only the authenticated user's collections
            payload = verify_jwt(request)
            query = client.query(kind=COLLECTIONS)
            query.add_filter("owner", "=", payload["sub"])
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
                e['self'] = request.url + '/collections/' + str(e.key.id)
                if 'media' in e.keys():
                    for mid in e['media']:
                        media_key = client.key(kind=MEDIA)
                        media = client.get(key=media_key)
                        mid['id'] = media.key.id
                        mid['self'] = request.url + '/media/' + str(media.key.id)
            total = len(list(query.fetch()))
            output = {"collections": results, "total_items": total}
            if next_url:
                output["next"] = next_url
            if prev_url:
                output["prev"] = prev_url
            return (json.dumps(output)), 200
        except:  # Show all collections; AKA Non-authenticated (Non-paginated)
            query = client.query(kind=COLLECTIONS)
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
                # if 'media' in e.keys():
                #     for mid in e['media']:
                #         media_key = client.key(kind=MEDIA)
                #         media = client.get(key=media_key)
                #         mid['id'] = media.key.id
                #         mid['self'] = request.url + '/media/' + str(media.key.id)
            total = len(list(query.fetch()))
            output = {"collections": results, "total_items": total}
            if next_url:
                output["next"] = next_url
            if prev_url:
                output["prev"] = prev_url
            return (json.dumps(output)), 200
    else:
        return jsonify(error='Method not recognized')


# DELETE, PUT, or PATCH a specific collection
@view_collections.route('/collections/<cid>', methods=['DELETE', 'PATCH', 'PUT'])
def collections_delete_put_patch(cid):
    if request.method == 'DELETE':
        payload = verify_jwt(request)
        collections_query = client.query(kind=COLLECTIONS)
        collections = list(collections_query.fetch())
        for collection in collections:
            collection["id"] = collection.key.id
            if collection["id"] == int(cid) \
             and collection.get("owner") == payload["sub"]:
                client.delete(collection)
                return "", 204
            if collection["id"] == int(cid) \
             and collection.get("owner") != payload["sub"]:
                return '{\n"403 Forbidden": "Collection is owned by someone else"\n}', 403
        return '{\n"404 Not Found":  "No collection with this collection_id exists"\n}', 404
    elif request.method == 'PATCH':
        if 'application/json' not in request.content_type:
            error = '{\n"415 Unsupported Media Type": "The server only supports JSON format."\n}'
            return (error, 415)
        payload = verify_jwt(request)
        content = request.get_json()
        collection_key = client.key("collections", int(cid))
        collection = client.get(key=collection_key)
        if collection:
            if collection["owner"] != payload["sub"] or not payload["sub"]:
                return '{\n"403 Forbidden": "Collection is owned by someone else"\n}', 403

            # handling invalid key (including ID)
            for key in content.keys():
                if key != 'name' and key != 'capacity' and key != 'last_updated' or len(content.keys()) > 2:
                    error = '{\n"400 Bad Request": "The request object contains an extraneous attribute."\n}'
                    return (error, 400)

            # handling name/capacity patch
            if 'name' in content.keys() and 'capacity' in content.keys():
                if request_validation_name(content["name"]) and request_validation_capacity(content["capacity"]):
                    if request_validation_name(content["name"]) == "Forbidden":
                        error = '{\n"403 Forbidden": "The name is already taken by an existing collection."\n}'
                        return (error, 403)
                    collection.update({"name": content["name"], "capacity": content["capacity"]})
                    client.put(collection)
                    collection["id"] = collection.key.id
                    collection["self"] = request.url
                    return (json.dumps(collection)), 200

            # handling name/last_updated patch
            elif 'name' in content.keys() and 'last_updated' in content.keys():
                if request_validation_name(content["name"]) == "Forbidden":
                    error = '{\n"403 Forbidden": "The name is already taken by an existing collection."\n}'
                    return (error, 403)
                if request_validation_name(content["name"]) and request_validation_date(content["last_updated"]):
                    collection.update({"name": content["name"], "last_updated": content["last_updated"]})
                    client.put(collection)
                    collection["id"] = collection.key.id
                    collection["self"] = request.url
                    return (json.dumps(collection)), 200

            # handling capacity/last_updated patch
            elif 'capacity' in content.keys() and 'last_updated' in content.keys():
                if request_validation_capacity(content["capacity"]) and request_validation_date(content["last_updated"]):
                    collection.update({"capacity": content["capacity"], "last_updated": content["last_updated"]})
                    client.put(collection)
                    collection["id"] = collection.key.id
                    collection["self"] = request.url
                    return (json.dumps(collection)), 200

            # handling name patch
            elif 'name' in content.keys():
                if request_validation_name(content["name"]) == "Forbidden":
                    error = '{\n"403 Forbidden": "The name is already taken by an existing collection."\n}'
                    return (error, 403)
                if request_validation_name(content["name"]):
                    collection.update({"name": content["name"]})
                    client.put(collection)
                    collection["id"] = collection.key.id
                    collection["self"] = request.url
                    return (json.dumps(collection)), 200

            # handling capacity patch
            elif 'capacity' in content.keys():
                if request_validation_capacity(content["capacity"]):
                    collection.update({"capacity": content["capacity"]})
                    client.put(collection)
                    collection["id"] = collection.key.id
                    collection["self"] = request.url
                    return (json.dumps(collection)), 200

            # handling last_updated patch
            elif 'last_updated' in content.keys():
                if request_validation_date(content["last_updated"]):
                    collection.update({"last_updated": content["last_updated"]})
                    client.put(collection)
                    collection["id"] = collection.key.id
                    collection["self"] = request.url
                    return (json.dumps(collection)), 200

            error = '{\n"400 Bad Request":  "The request object contained an invalid value."\n}'
            return (error, 400)
        # if there is no collection
        error = '{\n"404 Not Found":  "No collection with this collection_id exists"\n}'
        return (error, 404)
    elif request.method == 'PUT':
        if 'application/json' not in request.content_type:
            error = '{\n"415 Unsupported Media Type": "The server only supports JSON format."\n}'
            return (error, 415)
        payload = verify_jwt(request)
        content = request.get_json()
        collection_key = client.key("collections", int(cid))
        collection = client.get(key=collection_key)
        if collection:
            if collection["owner"] != payload["sub"] or not payload["sub"]:
                return '{\n"403 Forbidden": "Collection is owned by someone else"\n}', 403

            # handling invalid key (including ID)
            for key in content.keys():
                if key != 'name' and key != 'capacity' and key != 'last_updated':
                    error = '{\n"400 Bad Request": "The request object contains an extraneous attribute."\n}'
                    return (error, 400)
            # handling 3 attribute PUT
            if 'name' in content.keys() and 'capacity' in content.keys() and 'last_updated' in content.keys():
                if request_validation_name(content["name"]) == "Forbidden":
                    error = '{\n"403 Forbidden": "The name is already taken by an existing collection."\n}'
                    return (error, 403)
                if request_validation_name(content["name"]) \
                        and request_validation_capacity(content["capacity"]) \
                        and request_validation_date(content["last_updated"]):
                    collection.update({"name": content["name"], "capacity": content["capacity"], "last_updated":
                        content["last_updated"]})
                    client.put(collection)
                    collection["id"] = collection.key.id  # Include ID in the JSON Representation
                    collection["self"] = request.url
                    res = make_response(json.dumps(collection))
                    res.headers.set('Location', request.url)
                    res.status_code = 303
                    return res
            error = '{\n"400 Bad Request":  "The request object contained an invalid value."\n}'
            return (error, 400)
        error = '{\n"404 Not Found":  "No collection with this collection_id exists"\n}'
        return (error, 404)
    else:
        return 'Method not recognized'


# GET the Selected Collection's info
@view_collections.route('/collections/<cid>', methods=['GET'])
def collections_get(cid):
    if request.method == 'GET':
        collection_key = client.key("collections", int(cid))
        collection = client.get(key=collection_key)
        if collection:
            collection['id'] = request.url
            return json.dumps(collection), 200
        error = '{\n"Error":  "No collection with this collection_id exists"\n}'
        return (error, 404)
