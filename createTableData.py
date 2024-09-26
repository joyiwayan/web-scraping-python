import mysql.connector

# Connect to DB
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="data_pendamping_halal"
)
cursor = db.cursor()

# Create table with updated fields
sql = """CREATE TABLE data_pph (
   id INT AUTO_INCREMENT PRIMARY KEY,
   email VARCHAR(255),
   name VARCHAR(255),
   no_telp VARCHAR(255),
   kabupaten VARCHAR(255),
   kecamatan VARCHAR(255),
   no_registrasi VARCHAR(20),
   tgl_terbit DATE,
   lembaga VARCHAR(255),
   pendampingan_pelaku_usaha TEXT
)"""
cursor.execute(sql)

print('Table data_pph created')
