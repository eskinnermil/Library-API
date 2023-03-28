from main import request, app, URL, json, datastore

client = datastore.Client()
LIBRARIES = "libraries"
COLLECTIONS = "collections"
MEDIA = "media"


# Put, Delete Collection's Media
@app.route('/collections/<cid>/media/<mid>', methods=['PUT', 'DELETE'])
def add_delete_media_collections(cid, mid):
    if request.method == 'PUT':
        collection_key = client.key("collections", int(cid))
        collection = client.get(key=collection_key)
        media_key = client.key("media", int(mid))
        media = client.get(key=media_key)
        if media and collection:
            if media['collection'] is not None:
                error = '{\n"Error":  "The media is already attached to a collection"\n}'
                return (error, 403)
            media['collection'] = {"id": collection.key.id, "name": collection['name'],
                               "self": URL + '/collections/' + str(collection.key.id)}
            client.put(media)
            collection['media'].append({"id": media.key.id,
                                  "self": URL + '/media/' + str(media.key.id)})
            client.put(collection)
            return ('', 204)
        error = '{\n"Error":  "The specified collection and/or media does not exist"\n}'
        return (error, 404)
    elif request.method == 'DELETE':
        collection_key = client.key("collections", int(cid))
        collection = client.get(key=collection_key)
        media_key = client.key("media", int(mid))
        media = client.get(key=media_key)
        if media and collection:
            if 'media' in collection.keys():
                for media_id in collection['media']:
                    if media_id['id'] == int(mid):
                        collection['media'].remove(media_id)
                        media['collection'] = None
                        client.put(collection)
                        client.put(media)
                        return ('', 204)
            error = '{\n"Error":  "No collection with this collection_id is attached with the media containing this ' \
                    'media_id"\n}'
            return (error, 404)
        error = '{\n"Error":  "No collection with this collection_id is attached with the media containing this ' \
                'media_id"\n}'
        return (error, 404)


# GET the Collection's media
@app.route('/collections/<cid>/media', methods=['GET'])
def collections_media_get(cid):
    if request.method == 'GET':
        collections_key = client.key("collections", int(cid))
        collection = client.get(key=collections_key)
        e = {}
        if collection:
            if 'media' in collection.keys():
                for md in collection['media']:
                    media_key = client.key("media", int(md['id']))
                    media = client.get(key=media_key)
                    md['id'] = media.key.id
                    md['self'] = URL + '/media/' + str(media.key.id)
                    md['collection'] = {'id': collection.key.id, 'name': collection['name'],
                                      'self': request.url + '/' + str(collection.key.id)}
                    md['name'] = media['name']
                    md['type'] = media['type']
                    md['release_date'] = media['release_date']
                collection['self'] = URL + '/collections/' + str(cid)
                e['media'] = collection['media']
                e['self'] = collection['self']
                return json.dumps(e), 200
        error = '{\n"Error":  "No collection with this collection_id exists"\n}'
        return (error, 404)
    else:
        return 'Method not recognized'
