# app.py - Ecological Observation System
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras # To use dictionary cursor
import cloudinary
import cloudinary.uploader
import cloudinary.api

load_dotenv()

# Cloudinary configuration for image uploads
cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET'),
    secure = True
)

app = Flask(__name__)

def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        if conn:
            conn.close()
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Create table if it doesn't exist
            cur.execute('''
                CREATE TABLE IF NOT EXISTS observations (
                    id SERIAL PRIMARY KEY,
                    species_name TEXT NOT NULL,
                    description TEXT,
                    observed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    photo_url TEXT,
                    latitude DECIMAL(10, 8),
                    longitude DECIMAL(11, 8),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Add location columns if they don't exist (for existing tables)
            try:
                cur.execute('''
                    ALTER TABLE observations 
                    ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8),
                    ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8);
                ''')
                print("Location columns added/verified successfully.")
            except Exception as alter_error:
                print(f"Note: Could not add location columns (may already exist): {alter_error}")
            
            conn.commit()
            print("observations table successfully initialized or already exists.")
            cur.close()
        except Exception as e:
            print(f"Error during table initialization: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
    else:
        print("Database connection failed, cannot initialize table.")

@app.route('/')
def home():
    return render_template('home.html', title="Technician Club")

@app.route('/observations')
def list_observations():
    conn = get_db_connection()
    observations_list = []
    if conn:
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute('SELECT id, species_name, description, observed_at, photo_url, latitude, longitude, created_at FROM observations ORDER BY created_at DESC;')
            observations_list = cur.fetchall()
            cur.close()
        except Exception as e:
            print(f"Error fetching observations: {e}")
        finally:
            if conn:
                conn.close()
    return render_template('observations_list.html', observations=observations_list, title="Ecological Observation Records")

# [MODIFIED] /add 라우트 수정
@app.route('/add', methods=['POST'])
def add_observation():
    try:
        species_name = request.form['species_name']
        description = request.form.get('description')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        lat_value = None
        lng_value = None
        try:
            if latitude and latitude.strip():
                lat_value = float(latitude)
            if longitude and longitude.strip():
                lng_value = float(longitude)
        except ValueError:
            # 유효하지 않은 위도/경도 형식은 None으로 유지
            pass
        
        photo_url_to_save = None

        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(photo_file, folder="school_forest_mvp")
                    photo_url_to_save = upload_result.get('secure_url')
                    print(f"Cloudinary upload successful. URL: {photo_url_to_save}")
                except Exception as e:
                    print(f"Error during Cloudinary upload: {e}")
    
        conn = get_db_connection()
        if not conn:
            # 데이터베이스 연결 실패 시 즉시 JSON 오류 반환
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        observation_id = None
        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO observations (species_name, description, photo_url, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            ''', (species_name, description, photo_url_to_save, lat_value, lng_value))
            observation_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            print(f"New observation record saved successfully with ID: {observation_id}")
            
            # 항상 JSON 응답을 반환합니다.
            return jsonify({
                'success': True, 
                'observation_id': observation_id,
                'message': 'Observation added successfully'
            })

        except Exception as e:
            if conn: conn.rollback()
            print(f"Error saving observation record: {e}")
            # 오류 발생 시에도 항상 JSON 응답을 반환합니다.
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn: conn.close()

    except Exception as e:
        # 폼 데이터 처리 등 초기 단계에서 오류 발생 시
        print(f"Error processing form data: {e}")
        return jsonify({'success': False, 'error': 'Error processing request data'}), 400

@app.route('/api/observations')
def api_observations():
    """API endpoint to return observations data for map visualization"""
    conn = get_db_connection()
    observations_list = []
    if conn:
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute('SELECT id, species_name, description, observed_at, photo_url, latitude, longitude, created_at FROM observations WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY created_at DESC;')
            observations_data = cur.fetchall()
            
            for obs in observations_data:
                observations_list.append({
                    'id': obs['id'],
                    'species_name': obs['species_name'],
                    'description': obs['description'],
                    'photo_url': obs['photo_url'],
                    'latitude': float(obs['latitude']) if obs['latitude'] else None,
                    'longitude': float(obs['longitude']) if obs['longitude'] else None,
                    'created_at': obs['created_at'].strftime('%Y-%m-%d %H:%M:%S') if obs['created_at'] else None,
                    'observed_at': obs['observed_at'].strftime('%Y-%m-%d %H:%M:%S') if obs['observed_at'] else None
                })
            
            cur.close()
        except Exception as e:
            print(f"Error fetching observations for API: {e}")
        finally:
            if conn:
                conn.close()
    
    return jsonify(observations_list)

@app.route('/test_map')
def test_map():
    """Test page for OpenStreetMap integration"""
    return render_template('test_map.html')

@app.route('/delete_observation/<int:obs_id>', methods=['DELETE'])
def delete_observation(obs_id):
    """Delete an observation record"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM observations WHERE id = %s', (obs_id,))
            
            if cur.rowcount > 0:
                conn.commit()
                cur.close()
                return '', 200 # 성공 시 빈 응답과 200 상태 코드
            else:
                cur.close()
                return 'Observation not found', 404
        except Exception as e:
            print(f"Error deleting observation: {e}")
            if conn:
                conn.rollback()
            return 'Server error', 500
        finally:
            if conn:
                conn.close()
    else:
        return 'Database connection failed', 500

# Database connection test route (for development)
@app.route('/db_test')
def db_test():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT version();')
            db_version = cur.fetchone()
            cur.close()
            conn.close()
            if db_version:
                return f"Database connection successful! PostgreSQL version: {db_version[0]}"
            else:
                return "Database connection successful, but could not retrieve version information."
        except Exception as e:
            if conn: conn.close()
            return f"Error during database operation: {e}"
    else:
        return "Database connection failed!"

# Asset Routes for Features
@app.route('/game-assets/<path:filename>')
def serve_game_assets(filename):
    """Serve game assets for modal integration"""
    return send_from_directory(os.path.join(app.static_folder, 'game_assets'), filename)

@app.route('/club-intro-assets/<path:filename>')
def serve_club_intro_assets(filename):
    """Serve club introduction assets for modal integration"""
    return send_from_directory(os.path.join(app.static_folder, 'club_intro_assets'), filename)

@app.route('/snake-game-assets/<path:filename>')
def serve_snake_game_assets(filename):
    """Serve snake game assets for modal integration"""
    return send_from_directory(os.path.join(app.static_folder, 'snake_game_assets'), filename)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    print("\n🏠 Ecological Observation System & Multi-Feature Platform")
    print("✨ Features:")
    print("   - Interactive OpenStreetMap integration")
    print("   - Satellite and standard map views")
    print("   - Click-to-add observation records")
    print("   - Map-based observation viewing and management")
    print("   - Multiple map layer support")
    print("   - Date-based color-coded markers")
    print("   - Photo upload and geolocation support")
    print("   - Detailed club introduction modal")
    print("   - Tech Jump Game integrated modal")
    print("   - Snake Game integrated modal")
    print("\n🗺️ Free OpenStreetMap integration - No API key required!")
    print("🌿 Ecological Observation System: http://127.0.0.1:5000/observations")
    print("🏠 Home with Features & Games: http://127.0.0.1:5000/")
    print("\n" + "="*70 + "\n")
    app.run(debug=True)