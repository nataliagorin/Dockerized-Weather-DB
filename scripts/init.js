const { MongoClient } = require('mongodb');

async function run() {
  try {
    // Connect to MongoDB with authentication
    const client = new MongoClient("mongodb://admin:admin@localhost:27017/?authSource=admin");

    await client.connect();

    const db = client.db("weatherDB");

    // Create a user with the required roles in weatherDB
    await db.command({
      createUser: "admin",
      pwd: "admin",
      roles: [{ role: "readWrite", db: "weatherDB" }]
    });

    console.log("User created successfully!");

    // Create the collections with the appropriate validation and indexes
    await db.createCollection("Tari", {
      validator: {
        $jsonSchema: {
          bsonType: "object",
          required: ["nume_tara", "latitudine", "longitudine"],
          properties: {
            nume_tara: {
              bsonType: "string",
              description: "unic"
            },
            latitudine: {
              bsonType: "double"
            },
            longitudine: {
              bsonType: "double"
            }
          }
        }
      }
    });

    await db.collection("Tari").createIndex({ nume_tara: 1 }, { unique: true });

    await db.createCollection("Orase", {
      validator: {
        $jsonSchema: {
          bsonType: "object",
          required: ["id_tara", "nume_oras", "latitudine", "longitudine"],
          properties: {
            id_tara: {
              bsonType: "objectId"
            },
            nume_oras: {
              bsonType: "string"
            },
            latitudine: {
              bsonType: "double"
            },
            longitudine: {
              bsonType: "double"
            }
          }
        }
      }
    });

    await db.collection("Orase").createIndex({ id_tara: 1, nume_oras: 1 }, { unique: true });

    await db.createCollection("Temperaturi", {
      validator: {
        $jsonSchema: {
          bsonType: "object",
          required: ["valoare", "timestamp", "id_oras"],
          properties: {
            valoare: {
              bsonType: "double"
            },
            timestamp: {
              bsonType: "date"
            },
            id_oras: {
              bsonType: "objectId"
            }
          }
        }
      }
    });

    await db.collection("Temperaturi").createIndex({ id_oras: 1, timestamp: 1 }, { unique: true });

    console.log("Collections and indexes created successfully!");

    await client.close();
  } catch (error) {
    console.error("Error occurred:", error);
  }
}

run();
