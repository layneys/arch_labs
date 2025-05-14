db = db.getSiblingDB('trip_service');

if (db.trips.countDocuments({}) === 0) {
    
    db.trips.insertMany([
        {
            route_id: 1,
            driver_id: 3,
            user_ids: [1],
            start_location: "Москва, Красная площадь",
            end_location: "Санкт-Петербург, Невский проспект",
            departure_time: ISODate("2024-03-27T08:00:00Z"),
            available_seats: 3,
            price: 1500.00,
            description: "Комфортабельный минивэн"
        },
        {
            route_id: 2,
            driver_id: 2,
            user_ids: [2],
            start_location: "Санкт-Петербург, Московский вокзал",
            end_location: "Великий Новгород, Кремль",
            departure_time: ISODate("2024-03-28T09:00:00Z"),
            available_seats: 4,
            price: 800.00,
            description: "Эконом-класс"
        }
    ]);
    
    print("Created indexes...");
    db.trips.createIndex({ driver_id: 1 });
    db.trips.createIndex({ start_location: 1 });
    db.trips.createIndex({ end_location: 1 });
    db.trips.createIndex({ departure_time: 1 });
    db.trips.createIndex({ id: 1 });
    db.trips.createIndex({ available_seats: 1 });
    db.trips.createIndex({ price: 1 });
} else {
    print("Database already contains data, skipping ...");
}

