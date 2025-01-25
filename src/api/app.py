from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from bson.errors import InvalidId

import bson
import os


app = Flask(__name__)

app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://admin:admin@mongodb_container:27017/weatherDB")

mongo = PyMongo(app)

# ----- Tari -----
@app.route('/api/countries', methods=['POST'])
def add_country():
    data = request.json
    nume = data.get('nume')
    latitudine = data.get('lat')
    longitudine = data.get('lon')

    # Check if all required fields are provided
    if not nume or not latitudine or not longitudine:
        return jsonify({'error': "Toate câmpurile sunt obligatorii"}), 400

    # Check if country already exists in the database
    if mongo.db.Tari.find_one({"nume_tara": nume}):
        return jsonify({'error': "Țara există deja"}), 400

    try:
        tara = mongo.db.Tari.insert_one({
            "nume_tara": nume,
            "latitudine": latitudine,
            "longitudine": longitudine
        })
        return jsonify({"id": str(tara.inserted_id)}), 201
    except DuplicateKeyError as e:
        return jsonify({'error': "Țara există deja (eroare de duplicat)"}), 400


@app.route('/api/countries', methods=['GET'])
def get_countries():
    tari = mongo.db.Tari.find()
    valid_countries = []

    for tara in tari:
        # Ensure all fields are valid before including them in the response
        if "nume_tara" in tara and "latitudine" in tara and "longitudine" in tara:
            valid_countries.append({
                "id": str(tara['_id']),
                "nume": tara['nume_tara'],
                "lat": tara['latitudine'],
                "lon": tara['longitudine']
            })
    return jsonify(valid_countries), 200



@app.route('/api/countries/<id>', methods=['PUT'])
def update_country(id):
    try:
        id = id.strip()  # Trim any surrounding spaces
        data = request.json
        nume = data.get('nume_tara')
        latitudine = data.get('latitudine')
        longitudine = data.get('longitudine')

        if not nume or not latitudine or not longitudine:
            return jsonify({'error': "Toate câmpurile sunt obligatorii"}), 400

        tara = mongo.db.Tari.find_one_and_update(
            {"_id": ObjectId(id)},  # Safely cast to ObjectId
            {"$set": {"nume_tara": nume, "latitudine": latitudine, "longitudine": longitudine}},
            return_document=True
        )
        
        if not tara:
            return jsonify({'error': "Țara nu există"}), 404

        return jsonify({"id": str(tara['_id'])}), 200

    except bson.errors.InvalidId:
        return jsonify({"error": "ID invalid: formatul nu este corect"}), 400



@app.route('/api/countries/<id>', methods=['DELETE'])
def delete_country(id):
    try:
        # Attempt to convert the provided ID into an ObjectId
        object_id = ObjectId(id)
    except InvalidId:
        return jsonify({'error': "ID-ul furnizat nu este valid"}), 404
    
    try:
        result = mongo.db.Tari.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            return jsonify({'error': "Țara nu există"}), 404
        return jsonify({"message": "Țara a fost ștearsă"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400



# ----- Orase -----
@app.route('/api/cities', methods=['POST'])
def add_city():
    data = request.json

    id_tara = data.get('idTara')
    nume = data.get('nume')
    latitudine = data.get('lat')
    longitudine = data.get('lon')

    try:
        latitudine = float(latitudine)
        longitudine = float(longitudine)
    except (ValueError, TypeError):
        return jsonify({'error': "Latitudinea și longitudinea trebuie să fie de tip Double (float, nu întregi)"}), 400


    if not nume or latitudine is None or longitudine is None or id_tara is None:
        return jsonify({'error': "Toate câmpurile (idTara, nume, lat, lon) sunt obligatorii"}), 400

   
    try:
        id_tara = ObjectId(id_tara)
    except Exception:
        return jsonify({'error': "idTara trebuie să fie un ObjectId valid"}), 400


    if not isinstance(nume, str):
        return jsonify({'error': "Numele orașului trebuie să fie un string"}), 400
    
    if not isinstance(latitudine, float) or not isinstance(longitudine, float):
        return jsonify({'error': "Latitudinea și longitudinea trebuie să fie de tip Double (float)"}), 400


    country = mongo.db.Tari.find_one({"_id": id_tara})
    if not country:
        return jsonify({'error': f"Țara cu idTara '{id_tara}' nu există în baza de date"}), 400

    existing_city_name = mongo.db.Orase.find_one({"nume_oras": {"$regex": f"^{nume}$", "$options": "i"}})
    if existing_city_name:
        return jsonify({'error': f"Orașul cu numele '{nume}' există deja în baza de date"}), 400


    existing_city = mongo.db.Orase.find_one({
        "nume_oras": nume,
        "id_tara": id_tara,
        "latitudine": latitudine,
        "longitudine": longitudine
    })
    if existing_city:
        return jsonify({'error': f"Orașul '{nume}' cu aceste coordonate există deja în această țară"}), 400

    try:
        oras = mongo.db.Orase.insert_one({
            "id_tara": id_tara,
            "nume_oras": nume,
            "latitudine": latitudine,
            "longitudine": longitudine
        })
        return jsonify({"id": str(oras.inserted_id)}), 201
    except Exception as e:
        return jsonify({'error': f"A apărut o eroare la inserarea în baza de date: {str(e)}"}), 500



@app.route('/api/cities', methods=['GET'])
def get_cities():
    try:
        id_tara = request.args.get('idTara')  
        
        query = {}
        if id_tara:
            try:
                # Validate idTara as ObjectId
                query['id_tara'] = ObjectId(id_tara)
            except Exception:
                return jsonify({"error": "idTara trebuie să fie un ObjectId valid"}), 400

        orase = mongo.db.Orase.find(query)
        
        result = []
        for oras in orase:
            city = {
                "id": str(oras['_id']),
                "idTara": str(oras['id_tara']), 
                "nume": oras['nume_oras'],    
                "lat": float(oras['latitudine']), 
                "lon": float(oras['longitudine'])
            }
            result.append(city)

        unique_result = [dict(t) for t in {tuple(city.items()) for city in result}]
        return jsonify(unique_result), 200

    except Exception as e:
        return jsonify({"error": f"A apărut o eroare la preluarea orașelor: {str(e)}"}), 500


@app.route('/api/cities/country/<country_id>', methods=['GET'])
def get_cities_by_country(country_id):
    try:
        country_object_id = ObjectId(country_id)
    except Exception as e:
        return jsonify({'error': 'Invalid country ID format'}), 400

    try:
        cities = mongo.db.Orase.find({"id_tara": country_object_id})
        
        result = []
        for oras in cities:
            city = {
                "id": str(oras['_id']),                   
                "idTara": str(oras['id_tara']),          
                "nume": oras['nume_oras'],             
                "lat": float(oras['latitudine']),      
                "lon": float(oras['longitudine'])      
            }
            result.append(city)
        
        unique_result = [dict(t) for t in {tuple(city.items()) for city in result}]
        
        return jsonify(unique_result), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/api/cities/<id>', methods=['PUT'])
def update_city(id):
    data = request.json
    nume = data.get('nume_oras')
    latitudine = data.get('latitudine')
    longitudine = data.get('longitudine')

    if not nume or not latitudine or not longitudine:
        return jsonify({'error': "Toate câmpurile sunt obligatorii"}), 400

    oras = mongo.db.Orase.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": {"nume_oras": nume, "latitudine": latitudine, "longitudine": longitudine}},
        return_document=True
    )
    if not oras:
        return jsonify({'error': "Orașul nu există"}), 404

    return jsonify({"id": str(oras['_id'])}), 200


@app.route('/api/cities/<id>', methods=['DELETE'])
def delete_city(id):
    try:
        object_id = ObjectId(id)
    except InvalidId:
        return jsonify({'error': "ID-ul furnizat nu este valid"}), 404


    result = mongo.db.Orase.delete_one({"_id": object_id})
    
    if result.deleted_count == 0:
        return jsonify({'error': "Orașul nu există"}), 404

    # Return success response
    return jsonify({"message": "Orașul a fost șters"}), 200

# ----- Temperaturi -----
@app.route('/api/temperatures', methods=['POST'])
def add_temperature():
    data = request.json
    id_oras = data.get('idOras')
    valoare = data.get('valoare')

    # Validate required fields
    if not valoare:
        return jsonify({'error': "Toate câmpurile sunt obligatorii (idOras și valoare)"}), 400

    # Validate id_oras
    try:
        id_oras = ObjectId(id_oras)
    except Exception:
        return jsonify({'error': "idOras trebuie să fie un ObjectId valid"}), 400

    # Validate valoare (should be a valid number or float)
    try:
        valoare = float(valoare)
    except ValueError:
        return jsonify({'error': "Valoarea temperaturii trebuie să fie un număr valid"}), 400

    # Store the timestamp as a datetime object
    timestamp = datetime.now(timezone.utc) # Store it as a Date object

    # Insert the temperature record into the database
    try:
        temperatura = mongo.db.Temperaturi.insert_one({
            "id_oras": id_oras,
            "valoare": valoare,
            "timestamp": timestamp  # Store as a Date object
        })
        return jsonify({"id": str(temperatura.inserted_id)}), 201
    except Exception as e:
        return jsonify({'error': f"A apărut o eroare la inserarea temperaturii: {str(e)}"}), 500

@app.route('/api/temperatures', methods=['GET'])
def get_temperatures():
    try:
        # Extract query parameters
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        date_from = request.args.get('from')  
        date_until = request.args.get('until')  

        # Find all cities matching lat and lon
        city_query = {}
        if lat is not None:
            city_query['latitudine'] = lat
        if lon is not None:
            city_query['longitudine'] = lon

        matching_city_ids = []
        if city_query:  # If latitude or longitude filters are provided
            cities = mongo.db.Orase.find(city_query)
            matching_city_ids = [city['_id'] for city in cities]
            
            if not matching_city_ids:
                return jsonify({"error": "No city found with the provided latitude and/or longitude."}), 404

        # Build the query for temperature data
        query = {}
        if matching_city_ids:
            query['id_oras'] = {'$in': matching_city_ids}  # Filter temperatures for matching cities

        if date_from or date_until:
            query['timestamp'] = {}
        if date_from:
            try:
                query['timestamp']['$gte'] = datetime.strptime(date_from, '%Y-%m-%d')
            except ValueError:
                return jsonify({"error": "Invalid 'from' date format. Use YYYY-MM-DD."}), 400
        if date_until:
            try:
                query['timestamp']['$lte'] = datetime.strptime(date_until, '%Y-%m-%d')
            except ValueError:
                return jsonify({"error": "Invalid 'until' date format. Use YYYY-MM-DD."}), 400

       
        temperatures = mongo.db.Temperaturi.find(query)

        result = []
        for temp in temperatures:
            temp_data = {
                "id": str(temp['_id']), 
                "valoare": float(temp['valoare']),  #
                "timestamp": temp['timestamp'].strftime('%Y-%m-%d')  
            }
            result.append(temp_data)

        
        unique_result = [dict(t) for t in {tuple(temp.items()) for temp in result}]

        return jsonify(unique_result), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/api/temperatures/cities/<id_oras>', methods=['GET'])
def get_temperatures_for_city(id_oras):
    try:
        # Validate id_oras
        try:
            id_oras = ObjectId(id_oras)  # Convert to ObjectId
        except Exception:
            return jsonify({'error': "idOras trebuie să fie un ObjectId valid"}), 400

        
        date_from = request.args.get('from')  
        date_until = request.args.get('until')  

        query = {'id_oras': id_oras}

        if date_from or date_until:
            query['timestamp'] = {}

        if date_from:
            try:
                query['timestamp']['$gte'] = datetime.strptime(date_from, '%Y-%m-%d')
            except ValueError:
                return jsonify({"error": "Formatul datei de început nu este valid. Folosiți formatul YYYY-MM-DD."}), 400

        if date_until:
            try:
                query['timestamp']['$lte'] = datetime.strptime(date_until, '%Y-%m-%d')
            except ValueError:
                return jsonify({"error": "Formatul datei de final nu este valid. Folosiți formatul YYYY-MM-DD."}), 400

        temperatures = mongo.db.Temperaturi.find(query)

        result = []
        for temp in temperatures:
            temp_data = {
                "id": str(temp['_id']),  # Ensure 'valoare' is a float
                "timestamp": temp['timestamp'].strftime('%Y-%m-%d') 
            }
            result.append(temp_data)

        unique_result = [dict(t) for t in {tuple(temp.items()) for temp in result}]

        return jsonify(unique_result), 200

    except Exception as e:
        return jsonify({"error": f"A apărut o eroare la obținerea temperaturilor: {str(e)}"}), 500

@app.route('/api/temperatures/countries/<id_tara>', methods=['GET'])
def get_temperatures_by_country(id_tara):
    try:
        
        date_from = request.args.get('from') 
        date_until = request.args.get('until')  

        #Find all cities in the specified country (Orase table)
        try:
            cities = mongo.db.Orase.find({"id_tara": ObjectId(id_tara)})
            city_ids = [city['_id'] for city in cities]
        except Exception:
            return jsonify({"error": "Invalid country ID format or country not found"}), 400

        if not city_ids:
            return jsonify({"error": "No cities found for the provided country ID"}), 404

        #  Build the query for temperatures
        query = {"id_oras": {"$in": city_ids}}

        
        if date_from or date_until:
            query['timestamp'] = {}

        if date_from:
            try:
                query['timestamp']['$gte'] = datetime.strptime(date_from, '%Y-%m-%d')
            except ValueError:
                return jsonify({"error": "Invalid 'from' date format. Use YYYY-MM-DD."}), 400

        if date_until:
            try:
                query['timestamp']['$lte'] = datetime.strptime(date_until, '%Y-%m-%d')
            except ValueError:
                return jsonify({"error": "Invalid 'until' date format. Use YYYY-MM-DD."}), 400

        # Query the Temperaturi table for matching records
        temperatures = mongo.db.Temperaturi.find(query)

        #  Build the response list
        result = []
        for temp in temperatures:
            temp_data = {
                "id": str(temp['_id']),  
                "valoare": float(temp['valoare']),  
                "timestamp": temp['timestamp'].strftime('%Y-%m-%d') 
            }
            result.append(temp_data)

        unique_result = [dict(t) for t in {tuple(temp.items()) for temp in result}]

        return jsonify(unique_result), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/api/temperatures/<id>', methods=['PUT'])
def update_temperature(id):
    data = request.json
    valoare = data.get('valoare')

    if not valoare:
        return jsonify({'error': "Valoarea este obligatorie"}), 400

    
    try:
        valoare = float(valoare)  # Convert to float
    except ValueError:
        return jsonify({'error': "Valoarea trebuie să fie un număr valid"}), 400

    temperatura = mongo.db.Temperaturi.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": {"valoare": valoare}},
        return_document=True
    )
    if not temperatura:
        return jsonify({'error': "Temperatura nu există"}), 404

    return jsonify({"id": str(temperatura['_id'])}), 200



@app.route('/api/temperatures/<id>', methods=['DELETE'])
def delete_temperature(id):
    try:
        
        object_id = ObjectId(id)
    except InvalidId:
        return jsonify({'error': "id invalid. Trebuie să fie un ObjectId valid"}), 404
    
    
    result = mongo.db.Temperaturi.delete_one({"_id": object_id})
    
    if result.deleted_count == 0:
        return jsonify({'error': "Temperatura nu există"}), 404
    
    return jsonify({"message": "Temperatura a fost ștearsă"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
