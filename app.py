#!/usr/bin/python3

from datetime import datetime
from flask import Flask, jsonify, request, abort
from models.city import City
from models.country import Country
from models.user import User
from models.amenity import Amenity
from models.place import Place
from models.review import Reviews
from data import country_data, place_data, amenity_data, place_to_amenity_data, review_data, user_data, city_data
from data.file_storage import FileStorage

app = Flask(__name__)

@app.route('/')
def hello_world():
    """ Hello world """
    return 'Hello World'

@app.route('/', methods=["POST"])
def hello_world_post():
    """ Hello world endpoint for POST requests """
    # curl -X POST localhost:5000/
    return "hello world\n"

# Examples
@app.route('/example/country_data')
def example_country_data():
    """ Example to show that we can view data loaded in the data module's init """
    return jsonify(country_data)

@app.route('/example/cities')
def example_cities():
    """ Example route to showing usage of the City model class """

    # We will be appending dictionaries to the list instead of City objects
    # This is so we can print them out on the webpage
    # If there is no need to display the data, we can consider storing the City objects themselves
    cities_list = []

    # the 'hello' and 'world' params below will be filtered off in City constructor
    cities_list.append(City(name="Gotham", hello="hello").__dict__)
    cities_list.append(City(name="Metropolis", world="world").__dict__)

    # Validation: The city with the invalid name is not appended to the list
    try:
        cities_list.append(City(name="#$%^&**", country_id=2).__dict__)
    except ValueError as exc:
        # This is printed internally in the server output. Not shown on website.
        print("City creation Error - ", exc)

    # Validation: The city with the invalid country_id is not appended to the list
    try:
        cities_list.append(City(name="Duckburg", country_id=1234).__dict__)
    except ValueError as exc:
        print("City creation Error - ", exc)

    # Note that private attributes have a weird key format. e.g. "_City__country_id"
    # This shows that the output of the City object's built-in __dict__ is not usable as-is

    return cities_list

@app.route('/example/places_amenties_raw')
def example_places_amenities_raw():
    """ Prints out the raw data for relationships between places and their amenities """
    return jsonify(place_to_amenity_data)

@app.route('/example/places_amenties_prettified_example')
def example_places_amenties_prettified():
    """ Prints out the relationships between places and their amenities using names """

    output = {}

    for place_key in place_to_amenity_data:
        place_name = place_data[place_key]['name']
        if place_name not in output:
            output[place_name] = []

        amenities_ids = place_to_amenity_data[place_key]
        for amenity_key in amenities_ids:
            amenity_name = amenity_data[amenity_key]['name']
            output[place_name].append(amenity_name)

    return jsonify(output)

@app.route('/example/places_reviews')
def example_places_reviews():
    """ prints out reviews of places """

    output = {}

    for key in review_data:
        row = review_data[key]
        place_id = row['place_id']
        place_name = place_data[place_id]['name']
        if place_name not in output:
            output[place_name] = []

        reviewer = user_data[row['commentor_user_id']]

        output[place_name].append({
            "review": row['feedback'],
            "rating": ' ' + '* ' * row['rating'],
            "reviewer": reviewer['first_name'] + " " + reviewer['last_name']
        })

    return jsonify(output)

# --- API endpoints ---
# --- USER ---
@app.route('/api/v1/users', methods=["GET"])
def users_get():
    """returns Users"""
    data = []

    for k, v in user_data.items():
        data.append({
            "id": v['id'],
            "first_name": v['first_name'],
            "last_name": v['last_name'],
            "email": v['email'],
            "password": v['password'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)

@app.route('/api/v1/users/<user_id>', methods=["GET"])
def users_specific_get(user_id):
    """returns specified user"""
    data = []

    if user_id not in user_data:
        # raise IndexError("User not found!")
        return "User not found!"

    v = user_data[user_id]
    data.append({
        "id": v['id'],
        "first_name": v['first_name'],
        "last_name": v['last_name'],
        "email": v['email'],
        "password": v['password'],
        "created_at": datetime.fromtimestamp(v['created_at']),
        "updated_at": datetime.fromtimestamp(v['updated_at'])
    })
    return jsonify(data)

@app.route('/api/v1/users', methods=["POST"])
def users_post():
    """ posts data for new user then returns the user data"""
    # -- Usage example --
    # curl -X POST [URL] /
    #    -H "Content-Type: application/json" /
    #    -d '{"key1":"value1","key2":"value2"}'

    # print(request.content_type)

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()
    if 'first_name' not in data:
        abort(400, "Missing first_name")
    if 'last_name' not in data:
        abort(400, "Missing last_name")
    if 'email' not in data:
        abort(400, "Missing email")
    for user in user_data:
        if data['email'] == user_data[user]['email']:
            abort(400, "Email must be unique")
    if 'password' not in data:
        abort(400, "Missing password")

    try:
        u = User(first_name=data["first_name"],last_name=data["last_name"], email=data["email"], password=data["password"])
    except ValueError as exc:
        return repr(exc) + "\n"

    # add new user data to user_data
    # note that the created_at and updated_at are using timestamps
    user_data[u.id] = {
        "id": u.id,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email,
        "password": u.password,
        "created_at": u.created_at,
        "updated_at": u.updated_at
    }

    # note that the created_at and updated_at are using readable datetimes
    attribs = {
        "id": u.id,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email,
        "password": u.password,
        "created_at": datetime.fromtimestamp(u.created_at),
        "updated_at": datetime.fromtimestamp(u.updated_at)
    }

    string_to_print = FileStorage().prettify_model_data("User", user_data)
    FileStorage().save_model_data("data/user.json", string_to_print)

    return jsonify(attribs)

@app.route('/api/v1/users/<user_id>', methods=["PUT"])
def users_put(user_id):
    """ updates existing user data using specified id """
    # -- Usage example --
    # curl -X PUT [URL] /
    #    -H "Content-Type: application/json" /
    #    -d '{"key1":"value1","key2":"value2"}'

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()

    if user_id not in user_data:
        abort(400, "User not found for id {}".format(user_id))
    if "email" in data:
        for user in user_data:
            if data['email'] == user_data[user]['email']:
                abort(400, "Email must be unique")

    u = user_data[user_id]

    # modify the values
    for k, v in data.items():
        # only first_name, last_name, email and password are allowed to be modified
        if k in ["first_name", "last_name", "email", "password"]:
            u[k] = v
    u["updated_at"] = datetime.now().timestamp()

    # update user_data with the new name - print user_data out to confirm it if you want
    user_data[user_id] = u

    attribs = {
        "id": u["id"],
        "first_name": u["first_name"],
        "last_name": u["last_name"],
        "email": u["email"],
        "password": u["password"],
        "created_at": datetime.fromtimestamp(u["created_at"]),
        "updated_at": datetime.fromtimestamp(u["updated_at"])
    }

    string_to_print = FileStorage().prettify_model_data("User", user_data)
    FileStorage().save_model_data("data/user.json", string_to_print)

    # print out the updated user details
    return jsonify(attribs)

@app.route('/api/v1/users/<user_id>', methods=["DELETE"])
def users_delete(user_id):
    """ deletes existing user data using specified id """
    # -- Usage example --
    # curl -X DELETE [URL] /
    #    -H "Content-Type: application/json"

    if user_id not in user_data:
        abort(400, "User not found for id {}".format(user_id))

    # This is to remove the review when the user is being deleted
    reviews_to_delete = []
    for k, v in review_data.items():
        if v["commentor_user_id"] == user_id:
            reviews_to_delete.append(k)

    for k in reviews_to_delete:
        reviews_delete(k)

    # This is to remove the place when the user is being deleted
    places_to_delete = []
    for k, v in place_data.items():
        if v["host_user_id"] == user_id:
            places_to_delete.append(k)

    for k in places_to_delete:
        places_delete(k)

    # Now delete the user from the data list (json)
    user_data.pop(user_id, None)

    string_to_print = FileStorage().prettify_model_data("User", user_data)
    FileStorage().save_model_data("data/user.json", string_to_print)

    data = []

    for k, v in user_data.items():
        data.append({
            "id": v['id'],
            "first_name": v['first_name'],
            "last_name": v['last_name'],
            "email": v['email'],
            "password": v['password'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)


# --- COUNTRY ---
@app.route('/api/v1/countries', methods=["GET"])
def countries_get():
    """ returns countires data """
    data = []

    for k, v in country_data.items():
        data.append({
            "id": v['id'],
            "name": v['name'],
            "code": v['code'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)

@app.route('/api/v1/countries/<country_id>', methods=["GET"])
def countries_specific_get(country_id):
    """ returns specific country data """
    for k, v in country_data.items():
        if v['id'] == country_id:
            data = v

    c = {
        "id": data['id'],
        "name": data['name'],
        "code": data['code'],
        "created_at": datetime.fromtimestamp(data['created_at']),
        "updated_at": datetime.fromtimestamp(data['updated_at'])
    }

    return jsonify(c)

@app.route('/api/v1/countries/<country_id>/cities', methods=["GET"])
def countries_specific_cities_get(country_id):
    """ returns cities data of specified country """

    data = []

    for k, v in city_data.items():
        if v['country_id'] == country_id:
            data.append({
                "id": v['id'],
                "name": v['name'],
                "country_id": v['country_id'],
                "created_at": datetime.fromtimestamp(v['created_at']),
                "updated_at": datetime.fromtimestamp(v['updated_at'])
            })

    return jsonify(data)

@app.route('/api/v1/countries', methods=["POST"])
def countries_post():
    """ posts data for new country then returns the country data"""
    # -- Usage example --
    # curl -X POST [URL] /
    #    -H "Content-Type: application/json" /
    #    -d '{"key1":"value1","key2":"value2"}'

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()
    if 'name' not in data:
        abort(400, "Missing name")
    for country in country_data:
        if data['name'] == country_data[country]['name']:
            abort(400, "Name must be unique")
    if 'code' not in data:
        abort(400, "Missing country code")
    for country in country_data:
        if data['code'] == country_data[country]['code']:
            abort(400, "Code must be unique")

    try:
        c = Country(name=data["name"],code=data["code"])
    except ValueError as exc:
        return repr(exc) + "\n"

    # add new country data to country_data
    # note that the created_at and updated_at are using timestamps
    country_data[c.id] = {
        "id": c.id,
        "name": c.name,
        "code": c.code,
        "created_at": c.created_at,
        "updated_at": c.updated_at
    }

    # note that the created_at and updated_at are using readable datetimes
    attribs = {
        "id": c.id,
        "name": c.name,
        "code": c.code,
        "created_at": datetime.fromtimestamp(c.created_at),
        "updated_at": datetime.fromtimestamp(c.updated_at)
    }

    string_to_print = FileStorage().prettify_model_data("Country", country_data)
    FileStorage().save_model_data("data/country.json", string_to_print)

    return jsonify(attribs)

@app.route('/api/v1/countries/<country_id>', methods=["PUT"])
def countries_put(country_id):
    """ updates existing user data using specified id """
    # -- Usage example --
    # curl -X PUT [URL] /
    #    -H "Content-Type: application/json" /
    #    -d '{"key1":"value1","key2":"value2"}'

    c = {}

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()

    if "name" in data:
        for country in country_data:
            if data['name'] == country_data[country]['name']:
                abort(400, "Name must be unique")

    if "code" in data:
        for country in country_data:
            if data['code'] == country_data[country]['code']:
                abort(400, "Code must be unique")


    for k, v in country_data.items():
        if v['id'] == country_id:
            c = v

    if not c:
        abort(400, "Country not found for id {}".format(country_id))

    # modify the values
    # only name and code are allowed to be modified
    for k, v in data.items():
        if k in ["name", "code"]:
            c[k] = v
    c["updated_at"] = datetime.now().timestamp()

    # update country_data with the new name - print country_data out to confirm it if you want
    country_data[c['id']] = c

    attribs = {
        "id": c["id"],
        "name": c["name"],
        "code": c["code"],
        "created_at": datetime.fromtimestamp(c["created_at"]),
        "updated_at": datetime.fromtimestamp(c["updated_at"])
    }

    string_to_print = FileStorage().prettify_model_data("Country", country_data)
    FileStorage().save_model_data("data/country.json", string_to_print)

    # print out the updated user details
    return jsonify(attribs)

@app.route('/api/v1/countries/<country_id>', methods=["DELETE"])
def countries_delete(country_id):
    """ deletes existing countries data using specified id """
    # -- Usage example --
    # curl -X DELETE [URL] /
    #    -H "Content-Type: application/json"

    if country_id not in country_data:
        abort(400, "Country not found for id {}".format(country_id))

    country_data.pop(country_id, None)

    string_to_print = FileStorage().prettify_model_data("Country", country_data)
    FileStorage().save_model_data("data/country.json", string_to_print)

    data = []

    for k, v in country_data.items():
        data.append({
            "id": v['id'],
            "name": v['name'],
            "code": v['code'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)

# --- CITIES ---
@app.route('/api/v1/cities', methods=["GET"])
def cities_get():
    """returns Cities"""
    data = []

    for k, v in city_data.items():
        data.append({
            "id": v['id'],
            "name": v['name'],
            "country_id": v['country_id'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)

@app.route('/api/v1/cities/<city_id>', methods=["GET"])
def cities_specific_get(city_id):
    """returns specified city"""
    if city_id not in city_data:
        return "City not found!"

    v = city_data[city_id]
    data = {
        "id": v['id'],
        "name": v['name'],
        "country_id": v['country_id'],
        "created_at": datetime.fromtimestamp(v['created_at']),
        "updated_at": datetime.fromtimestamp(v['updated_at'])
    }
    return jsonify(data)

@app.route('/api/v1/cities', methods=["POST"])
def cities_post():
    """ posts data for new city then returns the city data"""
    # -- Usage example --
    # curl -X POST [URL] /
    #    -H "Content-Type: application/json" /
    #     -d '{"key1":"value1","key2":"value2"}'

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()
    if 'name' not in data:
        abort(400, "Missing name")
    if 'country_id' not in data:
        abort(400, "Missing country code")

    try:
        c = City(name=data["name"],country_id=data["country_id"])
    except ValueError as exc:
        return repr(exc) + "\n"

    # add new user data to user_data
    # note that the created_at and updated_at are using timestamps
    city_data[c.id] = {
        "id": c.id,
        "name": c.name,
        "country_id": c.country_id,
        "created_at": c.created_at,
        "updated_at": c.updated_at
    }

    # note that the created_at and updated_at are using readable datetimes
    attribs = {
        "id": c.id,
        "name": c.name,
        "country_id": c.country_id,
        "created_at": datetime.fromtimestamp(c.created_at),
        "updated_at": datetime.fromtimestamp(c.updated_at)
    }

    string_to_print = FileStorage().prettify_model_data("City", city_data)
    FileStorage().save_model_data("data/city.json", string_to_print)

    return jsonify(attribs)

@app.route('/api/v1/cities/<city_id>', methods=["PUT"])
def cities_put(city_id):
    """ updates existing city data using specified id """
    # -- Usage example --
    # curl -X PUT [URL] /
    #    -H "Content-Type: application/json" /
    #    -d '{"key1":"value1","key2":"value2"}'

    c = {}

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()

    for k, v in city_data.items():
        if v['id'] == city_id:
            c = v

    if not c:
        abort(400, "City not found for id {}".format(city_id))

    # modify the values
    # only city name and country id is allowed to be modified
    for k, v in data.items():
        if k in ["name", "country_id"]:
            c[k] = v
    c["updated_at"] = datetime.now().timestamp()

    # update city_data with the new name - print city_data out to confirm it if you want
    city_data[city_id] = c

    attribs = {
        "id": c["id"],
        "name": c["name"],
        "country_id": c["country_id"],
        "created_at": datetime.fromtimestamp(c["created_at"]),
        "updated_at": datetime.fromtimestamp(c["updated_at"])
    }

    string_to_print = FileStorage().prettify_model_data("City", city_data)
    FileStorage().save_model_data("data/city.json", string_to_print)

    # print out the updated user details
    return jsonify(attribs)

@app.route('/api/v1/cities/<city_id>', methods=["DELETE"])
def cities_delete(city_id):
    """ deletes existing cities data using specified id """
    # -- Usage example --
    # curl -X DELETE [URL] /
    #    -H "Content-Type: application/json"

    if city_id not in city_data:
        abort(400, "City not found for id {}".format(city_id))

    city_data.pop(city_id, None)

    string_to_print = FileStorage().prettify_model_data("City", city_data)
    FileStorage().save_model_data("data/city.json", string_to_print)

    data = []

    for k, v in city_data.items():
        data.append({
            "id": v['id'],
            "name": v['name'],
            "country_id": v['country_id'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)


# --- AMENITIES ---
@app.route('/api/v1/amenities', methods=["GET"])
def amenities_get():
    """returns all Amenities"""
    data = []

    for k, v in amenity_data.items():
        data.append({
            "id": v['id'],
            "name": v['name'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)

@app.route('/api/v1/amenities/<amenity_id>', methods=["GET"])
def amenity_specific_get(amenity_id):
    """returns specified amenity"""
    if amenity_id not in amenity_data:
        return "Amenity not found!"

    v = amenity_data[amenity_id]
    data = {
        "id": v['id'],
        "name": v['name'],
        "created_at": datetime.fromtimestamp(v['created_at']),
        "updated_at": datetime.fromtimestamp(v['updated_at'])
    }
    return jsonify(data)

@app.route('/api/v1/amenities', methods=["POST"])
def amenities_post():
    """ posts data for new amenity then returns the amenity data"""
    # -- Usage example --
    # curl -X POST [URL] /
    #    -H "Content-Type: application/json" /
    #     -d '{"key1":"value1","key2":"value2"}'

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()
    if 'name' not in data:
        abort(400, "Missing name")
   # Amenity must be unique 
    for amenity in amenity_data:
        if data['name'] == amenity_data[amenity]['name']:
            abort(400, "Amenity must be unique")

    try:
        a = Amenity(name=data["name"])
    except ValueError as exc:
        return repr(exc) + "\n"

    # add new amenity data to amenity_data
    # note that the created_at and updated_at are using timestamps
    amenity_data[a.id] = {
        "id": a.id,
        "name": a.name,
        "created_at": a.created_at,
        "updated_at": a.updated_at
    }

    # note that the created_at and updated_at are using readable datetimes
    attribs = {
        "id": a.id,
        "name": a.name,
        "created_at": datetime.fromtimestamp(a.created_at),
        "updated_at": datetime.fromtimestamp(a.updated_at)
    }

    string_to_print = FileStorage().prettify_model_data("Amenity", amenity_data)
    FileStorage().save_model_data("data/amenity.json", string_to_print)

    return jsonify(attribs)

@app.route('/api/v1/amenities/<amenity_id>', methods=["PUT"])
def amenity_put(amenity_id):
    """ updates existing amenity data using specified id """
    # -- Usage example --
    # curl -X PUT [URL] /
    #    -H "Content-Type: application/json" /
    #    -d '{"key1":"value1","key2":"value2"}'

    c = {}

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()

    for k, v in amenity_data.items():
        if v['id'] == amenity_id:
            a = v

    if not a:
        abort(400, "Amenity not found for id {}".format(amenity_id))

    # modify the values
    # only amenity name is allowed to be modified
    for k, v in data.items():
        if k in ["name"]:
            a[k] = v
    a["updated_at"] = datetime.now().timestamp()

    # update amenity_data with the new name - print amenity_data out to confirm it if you want
    amenity_data[amenity_id] = a

    attribs = {
        "id": a["id"],
        "name": a["name"],
        "created_at": datetime.fromtimestamp(a["created_at"]),
        "updated_at": datetime.fromtimestamp(a["updated_at"])
    }

    string_to_print = FileStorage().prettify_model_data("Amenity", amenity_data)
    FileStorage().save_model_data("data/amenity.json", string_to_print)

    # print out the updated user details
    return jsonify(attribs)

@app.route('/api/v1/amenities/<amenity_id>', methods=["DELETE"])
def amenity_delete(amenity_id):
    """ deletes existing amenities data using specified id """
    # -- Usage example --
    # curl -X DELETE [URL] /
    #    -H "Content-Type: application/json"

    if amenity_id not in amenity_data:
        abort(400, "Amenity not found for id {}".format(amenity_id))

    amenity_data.pop(amenity_id, None)

    string_to_print = FileStorage().prettify_model_data("Amenity", amenity_data)
    FileStorage().save_model_data("data/amenity.json", string_to_print)

    data = []

    for k, v in amenity_data.items():
        data.append({
            "id": v['id'],
            "name": v['name'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)


# --- PLACES ---
@app.route('/api/v1/places', methods=["GET"])
def places_get():
    """returns all places"""
    data = []

    for k, v in place_data.items():
        data.append({
            "id": v['id'],
            "host_user_id": v['host_user_id'],
            "city_id": v['city_id'],
            "name": v['name'],
            "description": v['description'],
            "address": v['address'],
            "latitude": v['latitude'],
            "longitude": v['longitude'],
            "number_of_rooms": v['number_of_rooms'],
            "bathrooms": v['bathrooms'],
            "price_per_night": v['price_per_night'],
            "max_guests": v['max_guests'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)

@app.route('/api/v1/places/<place_id>', methods=["GET"])
def place_specific_get(place_id):
    """returns specified place"""
    if place_id not in place_data:
        return "Place not found!"

    v = place_data[place_id]
    data = {
        "id": v['id'],
        "host_user_id": v['host_user_id'],
        "name": v['name'],
        "city_id": v['city_id'],
        "description": v['description'],
        "address": v['address'],
        "latitude": v['latitude'],
        "longitude": v['longitude'],
        "number_of_rooms": v['number_of_rooms'],
        "bathrooms": v['bathrooms'],
        "price_per_night": v['price_per_night'],
        "max_guests": v['max_guests'],
        "created_at": datetime.fromtimestamp(v['created_at']),
        "updated_at": datetime.fromtimestamp(v['updated_at'])
    }
    return jsonify(data)

@app.route('/api/v1/places', methods=["POST"])
def places_post():
    """ posts data for new place then returns the place data"""
    # -- Usage example --
    # curl -X POST [URL] /
    #    -H "Content-Type: application/json" /
    #     -d '{"key1":"value1","key2":"value2"}'

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()
    for key in ["host_user_id", "city_id", "name","description", "address",
                "latitude", "longitude",  "number_of_rooms", "bathrooms",
                "price_per_night", "max_guests"]:
        if key not in data:
            abort(400, "Missing {}".format(key))

    try:
        p = Place(name=data["name"],
                  host_user_id=data["host_user_id"],
                  city_id=data["city_id"],
                  description=data["description"],
                  address=data["address"],
                  latitude=data["latitude"],
                  longitude=data["longitude"],
                  number_of_rooms=data["number_of_rooms"],
                  bathrooms=data["bathrooms"],
                  price_per_night=data["price_per_night"],
                  max_guests=data["max_guests"])
    except ValueError as exc:
        return repr(exc) + "\n"

    # add new place data to place_data
    # note that the created_at and updated_at are using timestamps
    place_data[p.id] = {
        "id": p.id,
        "name": p.name,
        "host_user_id": p.host_user_id,
        "city_id": p.city_id,
        "description": p.description,
        "address": p.address,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "number_of_rooms": p.number_of_rooms,
        "bathrooms": p.bathrooms,
        "price_per_night": p.price_per_night,
        "max_guests": p.max_guests,
        "created_at": p.created_at,
        "updated_at": p.updated_at
    }

    # note that the created_at and updated_at are using readable datetimes
    attribs = {
        "id": p.id,
        "name": p.name,
        "host_user_id": p.host_user_id,
        "city_id": p.city_id,
        "description": p.description,
        "address": p.address,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "number_of_rooms": p.number_of_rooms,
        "bathrooms": p.bathrooms,
        "price_per_night": p.price_per_night,
        "max_guests": p.max_guests,
        "created_at": datetime.fromtimestamp(p.created_at),
        "updated_at": datetime.fromtimestamp(p.updated_at)
    }

    string_to_print = FileStorage().prettify_model_data("Place", place_data)
    FileStorage().save_model_data("data/place.json", string_to_print)

    return jsonify(attribs)

@app.route('/api/v1/places/<place_id>', methods=["PUT"])
def places_put(place_id):
    """ updates existing place data using specified id """
    # -- Usage example --
    # curl -X PUT [URL] /
    #    -H "Content-Type: application/json" /
    #    -d '{"key1":"value1","key2":"value2"}'

    p = {}

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()

    for k, v in place_data.items():
        if v['id'] == place_id:
            p = v

    if not p:
        abort(400, "Place not found for id {}".format(place_id))

    # modify the values
    # only place name is allowed to be modified
    for k, v in data.items():
        if k in ["name", "host_user_id", "city_id","description", "address",
                "latitude", "longitude", "number_of_rooms", "bathrooms",
                "price_per_night", "max_guests"]:
            p[k] = v
    p["updated_at"] = datetime.now().timestamp()

    # update place_data with the new name - print place_data out to confirm it if you want
    place_data[place_id] = p
    attribs = {
        "id": p['id'],
        "name": p['name'],
        "host_user_id": p['host_user_id'],
        "city_id": p['city_id'],
        "description": p['description'],
        "address": p['address'],
        "latitude": p['latitude'],
        "longitude": p['longitude'],
        "number_of_rooms": p['number_of_rooms'],
        "bathrooms": p['bathrooms'],
        "price_per_night": p['price_per_night'],
        "max_guests": p['max_guests'],
        "created_at": datetime.fromtimestamp(p['created_at']),
        "updated_at": datetime.fromtimestamp(p['updated_at'])
    }

    string_to_print = FileStorage().prettify_model_data("Place", place_data)
    FileStorage().save_model_data("data/place.json", string_to_print)

    # print out the updated user details
    return jsonify(attribs)

@app.route('/api/v1/places/<place_id>', methods=["DELETE"])
def places_delete(place_id):
    """ deletes existing places data using specified id """
    # -- Usage example --
    # curl -X DELETE [URL] /
    #    -H "Content-Type: application/json"

    if place_id not in place_data:
        abort(400, "Place not found for id {}".format(place_id))

    # This is to remove the review when the place is being deleted
    reviews_to_delete = []
    for k, v in review_data.items():
        if v["place_id"] == place_id:
            reviews_to_delete.append(k)

    for k in reviews_to_delete:
        reviews_delete(k)

    # Now delete the place from the data list (json)
    place_data.pop(place_id, None)

    string_to_print = FileStorage().prettify_model_data("Place", place_data)
    FileStorage().save_model_data("data/place.json", string_to_print)

    data = []

    for k, v in place_data.items():
        data.append({
            "id": v['id'],
            "host_user_id": v['host_user_id'],
            "city_id": v['city_id'],
            "name": v['name'],
            "description": v['description'],
            "address": v['address'],
            "latitude": v['latitude'],
            "longitude": v['longitude'],
            "number_of_rooms": v['number_of_rooms'],
            "bathrooms": v['bathrooms'],
            "price_per_night": v['price_per_night'],
            "max_guests": v['max_guests'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)


# --- REVIEWS ---
@app.route('/api/v1/reviews', methods=["GET"])
def reviews_get():
    """returns all reviews"""
    data = []

    for k, v in review_data.items():
        data.append({
            "id": v['id'],
            "commentor_user_id": v['commentor_user_id'],
            "place_id": v['place_id'],
            "feedback": v['feedback'],
            "rating": v['rating'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)

@app.route('/api/v1/reviews/<review_id>', methods=["GET"])
def review_specific_get(review_id):
    """returns specified amenity"""
    if review_id not in review_data:
        return "Review not found!"

    v = review_data[review_id]
    data = {
        "id": v['id'],
        "commentor_user_id": v['commentor_user_id'],
        "place_id": v['place_id'],
        "feedback": v['feedback'],
        "rating": v['rating'],
        "created_at": datetime.fromtimestamp(v['created_at']),
        "updated_at": datetime.fromtimestamp(v['updated_at'])
    }
    return jsonify(data)

@app.route('/api/v1/reviews', methods=["POST"])
def reviews_post():
    """ posts data for new review then returns the review data"""
    # -- Usage example --
    # curl -X POST [URL] /
    #    -H "Content-Type: application/json" /
    #     -d '{"key1":"value1","key2":"value2"}'

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()

    for key in ["commentor_user_id", "place_id","feedback", "rating"]:
        if key not in data:
            abort(400, "Missing {}".format(key))

    try:
        r = Reviews(commentor_user_id=data["commentor_user_id"],
                    place_id=data["place_id"],
                    feedback=data["feedback"],
                    rating=data["rating"])
    except ValueError as exc:
        return repr(exc) + "\n"

    # add new amenity data to amenity_data
    # note that the created_at and updated_at are using timestamps
    review_data[r.id] = {
        "id": r.id,
        "commentor_user_id": r.commentor_user_id,
        "place_id": r.place_id,
        "feedback": r.feedback,
        "rating": r.rating,
        "created_at": r.created_at,
        "updated_at": r.updated_at
    }

    # note that the created_at and updated_at are using readable datetimes
    attribs = {
        "id": r.id,
        "commentor_user_id": r.commentor_user_id,
        "place_id": r.place_id,
        "feedback": r.feedback,
        "rating": r.rating,
        "created_at": datetime.fromtimestamp(r.created_at),
        "updated_at": datetime.fromtimestamp(r.updated_at)
    }

    string_to_print = FileStorage().prettify_model_data("Review", review_data)
    FileStorage().save_model_data("data/review.json", string_to_print)

    return jsonify(attribs)

@app.route('/api/v1/reviews/<review_id>', methods=["PUT"])
def reviews_put(review_id):
    """ updates existing review data using specified id """
    # -- Usage example --
    # curl -X PUT [URL] /
    #    -H "Content-Type: application/json" /
    #    -d '{"key1":"value1","key2":"value2"}'

    r = {}

    if request.get_json() is None:
        abort(400, "Not a JSON")

    data = request.get_json()

    for k, v in review_data.items():
        if v['id'] == review_id:
            r = v

    if not r:
        abort(400, "Review not found for id {}".format(review_id))

    # modify the values
    # only review name is allowed to be modified
    for k, v in data.items():
        if k in ["commentor_user_id", "place_id","feedback", "rating"]:
            r[k] = v
    r["updated_at"] = datetime.now().timestamp()

    # update review_data with the new name - print review_data out to confirm it if you want
    review_data[review_id] = r

    attribs = {
        "id": r["id"],
        "commentor_user_id": r["commentor_user_id"],
        "place_id": r["place_id"],
        "feedback": r["feedback"],
        "rating": r["rating"],
        "created_at": datetime.fromtimestamp(r["created_at"]),
        "updated_at": datetime.fromtimestamp(r["updated_at"])
    }

    string_to_print = FileStorage().prettify_model_data("Review", review_data)
    FileStorage().save_model_data("data/review.json", string_to_print)

    # print out the updated user details
    return jsonify(attribs)

@app.route('/api/v1/reviews/<review_id>', methods=["DELETE"])
def reviews_delete(review_id):
    """ deletes existing reviews data using specified id """
    # -- Usage example --
    # curl -X DELETE [URL] /
    #    -H "Content-Type: application/json"

    if review_id not in review_data:
        abort(400, "Review not found for id {}".format(review_id))

    review_data.pop(review_id, None)

    string_to_print = FileStorage().prettify_model_data("Review", review_data)
    FileStorage().save_model_data("data/review.json", string_to_print)

    data = []

    for k, v in review_data.items():
        data.append({
            "id": v['id'],
            "commentor_user_id": v['commentor_user_id'],
            "place_id": v['place_id'],
            "feedback": v['feedback'],
            "rating": v['rating'],
            "created_at": datetime.fromtimestamp(v['created_at']),
            "updated_at": datetime.fromtimestamp(v['updated_at'])
        })

    return jsonify(data)

# Set debug=True for the server to auto-reload when there are changes
if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
