-- USERS
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    college TEXT
);

-- COLLEGES
CREATE TABLE IF NOT EXISTS colleges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- HOSTELS
CREATE TABLE IF NOT EXISTS hostels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    college TEXT NOT NULL,
    total_rooms INTEGER,
    available_rooms INTEGER
);

-- APPLICATIONS
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    hostel_id INTEGER,
    document TEXT,
    status TEXT DEFAULT 'pending'
);

-- ATTENDANCE
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    status TEXT
);

-- ROOM PHOTOS
CREATE TABLE IF NOT EXISTS room_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT
);