-- database/create_database.sql
-- Complete database creation script for Cricbuzz LiveStats project

-- Create database
DROP DATABASE IF EXISTS cricket_db;
CREATE DATABASE cricket_db;
USE cricket_db;

-- Table 1: players_info (main players table)
CREATE TABLE players_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    role VARCHAR(50),
    batting_style VARCHAR(50),
    bowling_style VARCHAR(50),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table 2: crud_info (for CRUD operations)
CREATE TABLE crud_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    role VARCHAR(50),
    batting_style VARCHAR(50),
    bowling_style VARCHAR(50),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table 3: matches
CREATE TABLE matches (
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    team1 VARCHAR(100),
    team2 VARCHAR(100),
    date DATE,
    venue VARCHAR(100),
    city VARCHAR(100),
    status VARCHAR(100),
    result VARCHAR(200),
    toss_result VARCHAR(200),
    format VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 4: player_stats
CREATE TABLE player_stats (
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    match_id INT,
    runs INT,
    wickets INT,
    balls_faced INT,
    strike_rate DECIMAL(6,2),
    economy DECIMAL(5,2),
    bowling_avg DECIMAL(5,2),
    format VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players_info(id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

-- Table 5: venues
CREATE TABLE venues (
    venue_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(50),
    capacity INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 6: series
CREATE TABLE series (
    series_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    host_country VARCHAR(50),
    match_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    total_matches INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 7: teams
CREATE TABLE teams (
    team_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    coach VARCHAR(100),
    founded_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 8: batting_stats
CREATE TABLE batting_stats (
    batting_id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    match_id INT,
    innings INT,
    batting_position INT,
    runs INT,
    balls_faced INT,
    fours INT,
    sixes INT,
    strike_rate DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players_info(id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

-- Table 9: bowling_stats
CREATE TABLE bowling_stats (
    bowling_id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    match_id INT,
    innings INT,
    overs DECIMAL(4,1),
    maidens INT,
    runs_conceded INT,
    wickets INT,
    economy_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players_info(id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

-- INSERT 20 SAMPLE RECORDS INTO crud_info TABLE
INSERT INTO crud_info (name, country, role, batting_style, bowling_style, date_of_birth) VALUES
('Virat Kohli', 'India', 'Batsman', 'Right-handed', 'Right-arm medium', '1988-11-05'),
('MS Dhoni', 'India', 'Wicket-keeper', 'Right-handed', 'Right-arm medium', '1981-07-07'),
('Rohit Sharma', 'India', 'Batsman', 'Right-handed', 'Right-arm offbreak', '1987-04-30'),
('Jasprit Bumrah', 'India', 'Bowler', 'Right-handed', 'Right-arm fast', '1993-12-06'),
('Ravindra Jadeja', 'India', 'All-rounder', 'Left-handed', 'Left-arm orthodox', '1988-12-06'),
('Steve Smith', 'Australia', 'Batsman', 'Right-handed', 'Right-arm legbreak', '1989-06-02'),
('Kane Williamson', 'New Zealand', 'Batsman', 'Right-handed', 'Right-arm offbreak', '1990-08-08'),
('Ben Stokes', 'England', 'All-rounder', 'Left-handed', 'Right-arm fast-medium', '1991-06-04'),
('Babar Azam', 'Pakistan', 'Batsman', 'Right-handed', 'Right-arm offbreak', '1994-10-15'),
('Kagiso Rabada', 'South Africa', 'Bowler', 'Left-handed', 'Right-arm fast', '1995-05-25'),
('David Warner', 'Australia', 'Batsman', 'Left-handed', 'Right-arm legbreak', '1986-10-27'),
('Joe Root', 'England', 'Batsman', 'Right-handed', 'Right-arm offbreak', '1990-12-30'),
('Trent Boult', 'New Zealand', 'Bowler', 'Right-handed', 'Left-arm fast-medium', '1989-07-22'),
('Rashid Khan', 'Afghanistan', 'Bowler', 'Right-handed', 'Right-arm legbreak', '1998-09-20'),
('Shakib Al Hasan', 'Bangladesh', 'All-rounder', 'Left-handed', 'Left-arm orthodox', '1987-03-24'),
('Quinton de Kock', 'South Africa', 'Wicket-keeper', 'Left-handed', NULL, '1992-12-17'),
('Pat Cummins', 'Australia', 'Bowler', 'Right-handed', 'Right-arm fast', '1993-05-08'),
('KL Rahul', 'India', 'Batsman', 'Right-handed', NULL, '1992-04-18'),
('Jofra Archer', 'England', 'Bowler', 'Right-handed', 'Right-arm fast', '1995-04-01'),
('Kieron Pollard', 'West Indies', 'All-rounder', 'Right-handed', 'Right-arm medium', '1987-05-12');

-- Create indexes for better performance
CREATE INDEX idx_players_country ON players_info(country);
CREATE INDEX idx_players_role ON players_info(role);
CREATE INDEX idx_matches_date ON matches(date);
CREATE INDEX idx_player_stats_format ON player_stats(format);
CREATE INDEX idx_venues_capacity ON venues(capacity);
CREATE INDEX idx_series_dates ON series(start_date, end_date);

-- Verification query
SELECT 
    'Database created successfully!' as message,
    (SELECT COUNT(*) FROM crud_info) as copy_table_records,
    (SELECT COUNT(*) FROM players_info) as main_table_records;